from .version import __version__
import matplotlib.font_manager as fm
from pathlib import Path


def _register_custom_fonts():
    # 1. 获取包根目录（__init__.py所在的目录）
    package_dir = Path(__file__).resolve().parent  # 此时package_dir是your_package/
    print(f"包根目录：{package_dir}")

    # 2. 拼接字体子文件夹路径（package_dir/ttf/）
    font_dir = package_dir / "ttf"
    print(f"字体文件夹路径：{font_dir}")

    # 3. 检查字体文件夹是否存在
    if not font_dir.exists():
        print(f"❌ 字体文件夹不存在：{font_dir}")
        return

    # 4. 查找所有.ttf字体文件
    font_files = list(font_dir.glob("*.ttf"))
    print(f"在ttf文件夹中找到{len(font_files)}个字体文件")

    # 5. 逐个注册字体
    for font_file in font_files:
        try:
            fm.fontManager.addfont(str(font_file))  # 注册到matplotlib
            print(f"✅ 已注册：{font_file.name}")
        except Exception as e:
            print(f"❌ 注册失败 {font_file.name}：{str(e)[:50]}")


# 导入包时自动执行注册
_register_custom_fonts()
TIMES_NEW_ROMAN = "Times New Roman"
SIM_HEI = "SimHei"