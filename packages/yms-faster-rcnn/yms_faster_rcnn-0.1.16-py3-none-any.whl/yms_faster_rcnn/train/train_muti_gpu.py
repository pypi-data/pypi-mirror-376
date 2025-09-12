import time
import os
import datetime
import torch
from torch.optim.lr_scheduler import ReduceLROnPlateau

from yms_faster_rcnn.train_utils.my_dataset import VOCDataSet
from yms_faster_rcnn.backbone import resnet50_fpn_backbone
from yms_faster_rcnn.network_files import FasterRCNN, FastRCNNPredictor, AnchorsGenerator
from yms_faster_rcnn import train_utils as utils
from yms_faster_rcnn.train_utils import GroupedBatchSampler, create_aspect_ratio_groups, init_distributed_mode, save_on_master, mkdir, transforms
from yms_faster_rcnn.train_utils.train_eval_utils import train_one_epoch, evaluate


def create_model(num_classes, pretrain_path, coco_path=None):
    """
    创建模型，支持灵活配置预训练权重
    :param num_classes: 类别数（包含背景）
    :param pretrain_path: backbone预训练权重路径
    :param coco_path: COCO预训练模型路径
    :return: 构建好的FasterRCNN模型
    """
    # 构建backbone，支持自定义预训练权重
    backbone = resnet50_fpn_backbone(pretrain_path=pretrain_path,
                                     norm_layer=torch.nn.BatchNorm2d,
                                     trainable_layers=3)

    # 自定义锚点生成器
    anchor_sizes = ((14,), (7,), (32,), (48,), (21,))
    aspect_ratios = ((0.4010903, 0.7580582, 1.4109948),) * len(anchor_sizes)
    rpn_anchor_generator = AnchorsGenerator(anchor_sizes, aspect_ratios)

    # 构建FasterRCNN模型
    model = FasterRCNN(backbone=backbone, num_classes=91,
                       min_size=1000, max_size=1000,
                       rpn_anchor_generator=rpn_anchor_generator)

    # 加载COCO预训练权重（如果提供）
    if coco_path is not None and os.path.exists(coco_path):
        weights_dict = torch.load(coco_path, map_location='cpu')
        missing_keys, unexpected_keys = model.load_state_dict(weights_dict, strict=False)
        if len(missing_keys) != 0 or len(unexpected_keys) != 0:
            print("missing_keys: ", missing_keys)
            print("unexpected_keys: ", unexpected_keys)

    # 替换分类头
    in_features = model.roi_heads.box_predictor.cls_score.in_features
    model.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)

    return model


def main(args):
    # 初始化保存路径
    print(args)
    save_path = args.output_dir
    os.makedirs(save_path, exist_ok=True)
    init_distributed_mode(args)

    device = torch.device(args.device)
    print("Using {} device training.".format(device.type))

    # 结果记录文件
    results_file = os.path.join(save_path, "results{}.txt".format(
        datetime.datetime.now().strftime("%Y%m%d-%H%M%S")))

    # 数据变换配置
    data_transform = {
        "train": transforms.Compose([transforms.ToTensor(),
                                     transforms.RandomHorizontalFlip(0.5)]),
        "val": transforms.Compose([transforms.ToTensor()])
    }

    # 数据路径检查
    VOC_root = args.data_path
    if not os.path.exists(os.path.join(VOC_root, "VOCdevkit")):
        raise FileNotFoundError("VOCdevkit dose not in path:'{}'.".format(VOC_root))

    # 加载数据集
    train_dataset = VOCDataSet(VOC_root, "2012", data_transform["train"],
                              "train.txt", json_file=args.json_path)
    val_dataset = VOCDataSet(VOC_root, "2012", data_transform["val"],
                            "val.txt", json_file=args.json_path)

    # 分布式采样器配置
    print("Creating data loaders")
    if args.distributed:
        train_sampler = torch.utils.data.distributed.DistributedSampler(train_dataset)
        test_sampler = torch.utils.data.distributed.DistributedSampler(val_dataset)
    else:
        train_sampler = torch.utils.data.RandomSampler(train_dataset)
        test_sampler = torch.utils.data.SequentialSampler(val_dataset)

    # 按比例分组采样（节省显存）
    if args.aspect_ratio_group_factor >= 0:
        group_ids = create_aspect_ratio_groups(train_dataset, k=args.aspect_ratio_group_factor)
        train_batch_sampler = GroupedBatchSampler(train_sampler, group_ids, args.batch_size)
    else:
        train_batch_sampler = torch.utils.data.BatchSampler(
            train_sampler, args.batch_size, drop_last=True)

    # 计算合适的worker数量
    nw = min([os.cpu_count(), args.batch_size if args.batch_size > 1 else 0, 16])
    print(f'Using {nw} dataloader workers')

    # 构建数据加载器
    data_loader = torch.utils.data.DataLoader(
        train_dataset, batch_sampler=train_batch_sampler, num_workers=nw,
        collate_fn=train_dataset.collate_fn, pin_memory=True)

    data_loader_test = torch.utils.data.DataLoader(
        val_dataset, batch_size=1, sampler=test_sampler, num_workers=nw,
        collate_fn=val_dataset.collate_fn, pin_memory=True)

    # 创建模型
    print("Creating model")
    model = create_model(num_classes=args.num_classes + 1,
                         pretrain_path=args.backbone_path,
                         coco_path=args.coco_path)
    model.to(device)

    # 分布式同步BN配置
    if args.distributed and args.sync_bn:
        model = torch.nn.SyncBatchNorm.convert_sync_batchnorm(model)

    # 分布式模型包装
    model_without_ddp = model
    if args.distributed:
        model = torch.nn.parallel.DistributedDataParallel(model, device_ids=[args.gpu])
        model_without_ddp = model.module

    # 优化器配置
    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.SGD(
        params, lr=args.lr, momentum=args.momentum, weight_decay=args.weight_decay)

    # 混合精度训练配置
    scaler = torch.cuda.amp.GradScaler() if args.amp else None

    # 学习率调度器（支持ReduceLROnPlateau）
    if args.lr_scheduler == "plateau":
        lr_scheduler = ReduceLROnPlateau(optimizer, mode='max', factor=0.1,
                                        patience=5, min_lr=1e-8)
    else:
        lr_scheduler = torch.optim.lr_scheduler.MultiStepLR(
            optimizer, milestones=args.lr_steps, gamma=args.lr_gamma)

    # 断点续训
    if args.resume:
        checkpoint = torch.load(args.resume, map_location='cpu')
        model_without_ddp.load_state_dict(checkpoint['model'])
        optimizer.load_state_dict(checkpoint['optimizer'])
        lr_scheduler.load_state_dict(checkpoint['lr_scheduler'])
        args.start_epoch = checkpoint['epoch'] + 1
        if args.amp and "scaler" in checkpoint:
            scaler.load_state_dict(checkpoint["scaler"])
        print(f"Resume training from epoch {args.start_epoch}")

    # 仅测试模式
    if args.test_only:
        utils.evaluate(model, data_loader_test, device=device)
        return

    # 训练指标记录
    train_loss = []
    learning_rate = []
    val_map = []          # mAP@0.5
    map0595 = []          # mAP@0.5:0.95
    recall = []           # 召回率
    max_map = -1          # 最佳mAP@0.5
    max_recall = -1       # 最佳召回率
    best_model_path = None
    best_recall_path = None
    last_model_path = None

    print("Start training")
    start_time = time.time()
    for epoch in range(args.start_epoch, args.epochs):
        if args.distributed:
            train_sampler.set_epoch(epoch)  # 分布式训练中打乱数据

        # 训练一个epoch
        mean_loss, lr = train_one_epoch(model, optimizer, data_loader,
                                              device, epoch, args.print_freq,
                                              warmup=True, scaler=scaler)
        train_loss.append(mean_loss.item())
        learning_rate.append(lr)

        # 评估
        coco_info = evaluate(model, data_loader_test, device=device)
        val_map.append(coco_info[1])       # mAP@0.5
        map0595.append(coco_info[0])       # mAP@0.5:0.95
        recall.append(coco_info[12])       # 召回率

        # 学习率更新（根据调度器类型）
        if args.lr_scheduler == "plateau":
            lr_scheduler.step(coco_info[1])  # 基于mAP更新
        else:
            lr_scheduler.step()

        # 主进程写入结果
        if args.rank in [-1, 0]:
            with open(results_file, "a") as f:
                result_info = [f"{i:.4f}" for i in coco_info + [mean_loss.item()]] + [f"{lr:.6f}"]
                txt = f"epoch:{epoch} " + '  '.join(result_info)
                f.write(txt + "\n")

        # 模型保存（仅主进程）
        if args.output_dir and args.rank in [-1, 0]:

            # 保存当前epoch模型（并删除上一个）
            current_model_path = os.path.join(save_path, f'model_{epoch}.pth')
            torch.save(model_without_ddp.state_dict(), current_model_path)
            if last_model_path and os.path.exists(last_model_path):
                os.remove(last_model_path)
            last_model_path = current_model_path

            # 保存最佳mAP模型
            if coco_info[1] > max_map:
                max_map = coco_info[1]
                if best_model_path and os.path.exists(best_model_path):
                    os.remove(best_model_path)
                best_model_path = os.path.join(save_path, f'best_model_{epoch}.pth')
                torch.save(model_without_ddp.state_dict(), best_model_path)

            # 保存最佳召回率模型
            if coco_info[12] > max_recall:
                max_recall = coco_info[12]
                if best_recall_path and os.path.exists(best_recall_path):
                    os.remove(best_recall_path)
                best_recall_path = os.path.join(save_path, f'best_recall_{epoch}.pth')
                torch.save(model_without_ddp.state_dict(), best_recall_path)

    # 训练结束处理
    total_time = time.time() - start_time
    total_time_str = str(datetime.timedelta(seconds=int(total_time)))
    print(f'Training time {total_time_str}')

    # 主进程处理最终模型和可视化
    if args.rank in [-1, 0]:
        # 重命名最终模型
        if last_model_path:
            os.rename(last_model_path, os.path.join(save_path, "last_model.pth"))
        if best_model_path:
            os.rename(best_model_path, os.path.join(save_path, "best_model.pth"))
        if best_recall_path:
            os.rename(best_recall_path, os.path.join(save_path, "best_recall.pth"))

        # 绘制训练曲线
        from yms_faster_rcnn.train_utils.plot_curve import plot_loss_and_lr, plot_single
        if train_loss and learning_rate:
            plot_loss_and_lr(train_loss, learning_rate, os.path.join(save_path, 'loss_and_lr.png'))
        if val_map:
            plot_single(val_map, "mAP@0.5", os.path.join(save_path, 'mAP50.png'))
        if map0595:
            plot_single(map0595, 'mAP@0.5-0.95', os.path.join(save_path, 'mAP05-95.png'))
        if recall:
            plot_single(recall, "Recall", os.path.join(save_path, 'Recall.png'))

        print(f"Best model saved to: {os.path.join(save_path, 'best_model.pth')}")
        print(f"Last model saved to: {os.path.join(save_path, 'last_model.pth')}")


def get_args(args=None):
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)

    # 数据与模型路径配置
    parser.add_argument('--data-path', default='./', help='dataset root path')
    parser.add_argument('--json-path', default=None, help='classes json file path')
    parser.add_argument('--backbone-path', default=None, help='backbone pretrained weights path')
    parser.add_argument('--coco-path', default=None, help='COCO pretrained model path')
    parser.add_argument('--output-dir', default='./multi_train', help='path to save outputs')

    # 训练参数配置
    parser.add_argument('--device', default='cuda', help='device (cuda/cpu)')
    parser.add_argument('--num-classes', default=20, type=int, help='number of classes (excluding background)')
    parser.add_argument('-b', '--batch-size', default=4, type=int, help='batch size per GPU')
    parser.add_argument('--start-epoch', default=0, type=int, help='start epoch')
    parser.add_argument('--epochs', default=20, type=int, help='total training epochs')
    parser.add_argument('-j', '--workers', default=4, type=int, help='number of data loading workers')
    parser.add_argument('--lr', default=0.02, type=float, help='initial learning rate')
    parser.add_argument('--momentum', default=0.9, type=float, help='SGD momentum')
    parser.add_argument('--wd', '--weight-decay', default=1e-4, type=float, dest='weight_decay')

    # 学习率调度器配置
    parser.add_argument('--lr-scheduler', default='plateau', choices=['multi_step', 'plateau'],
                        help='learning rate scheduler type')
    parser.add_argument('--lr-steps', default=[7, 12], nargs='+', type=int, help='multi step milestones')
    parser.add_argument('--lr-gamma', default=0.1, type=float, help='learning rate decay factor')

    # 其他配置
    parser.add_argument('--print-freq', default=20, type=int, help='print frequency')
    parser.add_argument('--resume', default='', help='resume from checkpoint')
    parser.add_argument('--aspect-ratio-group-factor', default=3, type=int)
    parser.add_argument('--test-only', action='store_true', help='only test model')
    parser.add_argument('--sync-bn', type=bool, default=False, help='use sync batch norm')
    parser.add_argument('--amp', action='store_true', help='use mixed precision training')

    # 分布式训练配置
    parser.add_argument('--world-size', default=4, type=int, help='number of distributed processes')
    parser.add_argument('--dist-url', default='env://', help='distributed training url')

    return parser.parse_args(args if args else [])


if __name__ == "__main__":
    opts = get_args()
    main(opts)