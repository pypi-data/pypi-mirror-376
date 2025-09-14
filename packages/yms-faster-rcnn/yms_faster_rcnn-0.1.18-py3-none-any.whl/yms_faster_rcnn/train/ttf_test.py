# import matplotlib.font_manager as fm
# from pathlib import Path
# import os
#
#
# def _register_custom_fonts():
#     """注册包内的自定义字体到 matplotlib"""
#     # 定位当前包的路径（__file__ 是当前模块的路径）
#     package_dir = Path(__file__).resolve().parent
#     font_dir = package_dir / "tff"  # 字体所在子目录
#
#     # 遍历并注册所有 .ttf 字体文件
#     for font_path in font_dir.glob("*.ttf"):
#         if font_path.exists():
#             fm.fontManager.addfont(str(font_path))  # 注册字体
#             print(f"已注册字体：{font_path.name}")
#
#
# # 导入包时自动执行注册
# _register_custom_fonts()
