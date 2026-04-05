"""
简化打包脚本 - 只生成单个 AICodeFeeder.exe
用户首次运行时会自动提示注册右键菜单
"""
import PyInstaller.__main__
import os
import shutil


def build():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)

    # 清理旧构建
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"清理旧目录: {folder}")

    # 单 exe 打包
    params = [
        'CodeFeeder.pyw',
        '--name=AICodeFeeder',
        '--windowed',
        '--onefile',
        '--clean',

        # 内置资源
        '--add-data=Core/config.json;Core',
        '--add-data=AppUI;AppUI',
        '--add-data=Core;Core',

        # 收集所有子模块（一劳永逸）
        '--collect-submodules=AppUI',
        '--collect-submodules=Core',

        # 隐藏导入
        '--hidden-import=pystray._win32',
        '--hidden-import=PIL._tkinter_finder',
        '--hidden-import=win32api',
        '--hidden-import=win32con',
        '--hidden-import=win32com.client',

        # 排除大库
        '--exclude-module=matplotlib',
        '--exclude-module=notebook',
        '--exclude-module=jedi',
        '--exclude-module=numpy',
        '--exclude-module=pandas',

        # 图标（如果有）
        # '--icon=icon.ico',
    ]

    print("开始打包 AICodeFeeder.exe...")
    PyInstaller.__main__.run(params)
    print("打包完成！")
    print(f"生成文件: dist/AICodeFeeder.exe")
    print()
    print("使用方式:")
    print("  1. 双击 AICodeFeeder.exe 运行")
    print("  2. 首次运行会弹窗提示注册右键菜单")
    print("  3. 注册后可右键文件夹/文件快速打开，或用 Ctrl+` 快捷键唤起")


if __name__ == "__main__":
    build()