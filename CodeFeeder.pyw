import os
import sys
import traceback
import datetime

# --- 全局异常捕获与日志记录 ---
# 设置日志文件路径 (与脚本同目录)
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "launch_error.log")

def log_error(message):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass # 如果写日志都失败了，那就没办法了

def exception_hook(exctype, value, tb):
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    log_error(f"Uncaught exception:\n{error_msg}")
    # 尝试弹窗提示
    try:
        import tkinter.messagebox
        import tkinter as tk
        # 隐藏主窗口
        root = tk.Tk()
        root.withdraw()
        tkinter.messagebox.showerror("CodeFeeder Error", f"启动发生错误，请查看日志:\n{LOG_FILE}\n\n{value}")
        root.destroy()
    except:
        pass
    sys.exit(1)

sys.excepthook = exception_hook
# ---------------------------

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
