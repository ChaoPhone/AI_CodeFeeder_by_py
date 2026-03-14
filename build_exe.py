import PyInstaller.__main__
import os
import shutil

def build():
    # 确保在项目根目录
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)

    # 1. 清理旧的构建文件
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"清理旧目录: {folder}")

    # 2. PyInstaller 参数
    params = [
        'CodeFeeder.pyw',                # 主入口文件
        '--name=AICodeFeeder',           # 生成的 exe 名称
        '--windowed',                    # 无控制台窗口
        '--onefile',                     # 打包成单个 exe
        # '--icon=icon.ico',             # 如果有图标的话可以加上
        
        # 包含必要的资源文件
        '--add-data=Core/config.json;Core',
        
        # 包含整个 AppUI 和 Core 文件夹（作为模块）
        '--add-data=AppUI;AppUI',
        '--add-data=Core;Core',
        
        # 排除不必要的库
        '--exclude-module=matplotlib',
        '--exclude-module=notebook',
        '--exclude-module=jedi',
        
        # 强制包含某些可能被遗漏的库
        '--hidden-import=pystray._win32',
        '--hidden-import=PIL._tkinter_finder',
    ]

    print(f"开始打包...")
    PyInstaller.__main__.run(params)
    print(f"打包完成！生成的 exe 位于 dist/AICodeFeeder.exe")

    # 3. 同时也打包 install_menu.py 为 exe (可选，为了方便分发)
    print(f"开始打包安装程序...")
    install_params = [
        'install_menu.py',
        '--name=Install_Menu',
        '--console',                     # 安装程序需要控制台
        '--onefile',
        '--uac-admin',                   # 请求管理员权限
    ]
    PyInstaller.__main__.run(install_params)
    print(f"安装程序打包完成！生成的 exe 位于 dist/Install_Menu.exe")

if __name__ == "__main__":
    build()
