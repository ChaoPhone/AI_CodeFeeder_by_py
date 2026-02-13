import os
import sys

# 将工作目录切换到脚本所在目录，确保资源加载正确
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
# 确保导入的是 AppUI 包下的 MainWindow
from AppUI.MainWindow import CodeFeederApp


def main():
    # 1. 检查是否有命令行参数 (右键菜单传入的路径)
    init_dir = None
    if len(sys.argv) > 1:
        potential_path = sys.argv[1]
        if os.path.isdir(potential_path):
            init_dir = potential_path

    # 2. 启动 GUI
    root = tk.Tk()

    # 加上自爆路径标题，方便你确认运行的是否是新版
    current_file_path = os.path.abspath(__file__)
    root.title(f"✅ 新版运行中: {current_file_path}")

    app = CodeFeederApp(root, init_dir)
    root.mainloop()


if __name__ == "__main__":
    main()
