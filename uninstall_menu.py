import os
import sys
import winreg
import ctypes

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def uninstall_context_menu():
    key_name = "AI_CodeFeeder_Pipeline"
    # 需要清理的所有注册表路径
    reg_paths = [
        r"Directory\shell",
        r"Directory\Background\shell",
        r"*\shell"
    ]

    success_count = 0
    fail_count = 0

    print("开始卸载 AI CodeFeeder 右键菜单...")

    for base in reg_paths:
        try:
            key_path = f"{base}\\{key_name}"
            # Windows 注册表删除需要先删除子项
            try:
                # 尝试打开 command 子项并删除
                winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, f"{key_path}\\command")
            except FileNotFoundError:
                pass
            
            # 删除主项
            winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, key_path)
            print(f"✅ 已移除: HKEY_CLASSES_ROOT\\{key_path}")
            success_count += 1
        except FileNotFoundError:
            # 路径不存在，跳过
            continue
        except Exception as e:
            print(f"❌ 移除 {base} 失败: {e}")
            fail_count += 1

    # --- 添加开机自启动卸载逻辑 ---
    print("\n正在清理开机自启动项...")
    try:
        startup_key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, startup_key_path, 0, winreg.KEY_SET_VALUE) as key:
            try:
                winreg.DeleteValue(key, "AICodeFeeder")
                print("✅ 已移除开机自启动项。")
            except FileNotFoundError:
                print("ℹ️ 未发现开机自启动项。")
    except Exception as e:
        print(f"❌ 清理自启动项失败: {e}")

    if success_count > 0:
        print(f"\n🎉 卸载完成！成功移除 {success_count} 个项目。")
    elif fail_count == 0:
        print("\nℹ️ 未发现已安装的右键菜单项。")
    
    if fail_count > 0:
        print(f"⚠️ 有 {fail_count} 个项目移除失败。")

if __name__ == "__main__":
    if is_admin():
        uninstall_context_menu()
        print("\n[提示] 如果菜单依然显示，请重启资源管理器 (explorer.exe) 以刷新缓存。")
        input("\n按回车键退出...")
    else:
        # 申请管理员权限重新运行
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
