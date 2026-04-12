***
# 🚀 AI_CodeFeeder (V1.9.7 重构版)

![Version](https://img.shields.io/badge/version-1.9.7-blue.svg)
![Build](https://img.shields.io/badge/build-passing-brightgreen.svg)
![Python](https://img.shields.io/badge/python-3.x-blue.svg)
![Tkinter](https://img.shields.io/badge/UI-Tkinter-orange.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)

> **Stop Copy-Pasting. Start Coding.**
>
> 拒绝繁琐的复制粘贴，让 AI 更懂你的代码架构。

祝看到这里的同学期末周科科满绩！！！送你一锅重庆鸡公煲🫕🥰🥰🥰

## 🚀 快速开始

### 方式一：exe 用户（推荐）

**只需下载一个 `AICodeFeeder.exe`：**

1. 下载 `AICodeFeeder.exe`
2. 双击运行
3. 首次运行会弹窗询问是否注册右键菜单 → 点击「立即注册」
4. 完成！

之后可：
- **右键文件夹/文件** → 选择「使用 AI CodeFeeder 打开」
- **快捷键 Ctrl+`** → 快速唤起
- **双击 exe** → 打开主界面手动选择目录

### 方式二：源码用户

```bash
python setup.py              # 安装依赖到 .venv
python setup.py --register   # 注册右键菜单（需管理员权限）
```

之后双击 `CodeFeeder.pyw` 即可运行。

---

## 📖 简介

**众所周知，大多数 AI（如 DeepSeek, 豆包, ChatGPT, Claude, Gemini）不允许直接上传代码文件夹。**

劳累了一天的人们，往往还要不厌其烦地打开一个个文件，复制、粘贴，或者被迫使用 IDE 内置的昂贵或不够聪明的 AI 插件。这种方式不仅效率低下，而且丢失了项目原本的文件结构上下文，导致 AI 的回答往往不够准确。

**AI_CodeFeeder** 因此诞生。👍🤓

它是一个基于 Python 的 light-weight 工具，能够**一键扫描**你的工程目录，智能过滤掉无关文件（如 `build`, `.git`, `node_modules` 以及 STM32/Unity 的垃圾文件），生成一份包含**完整目录树**和**所有源码内容**的 Markdown 文件。

**适合场景：**
- 向 DeepSeek、豆包、ChatGPT、Claude 等不支持文件夹上传的 AI 提供完整代码上下文
- 快速整理代码结构，用于技术文档或代码审查

---

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| 🧠 自适应加载 | 大项目自动回退到扩展名过滤，避免超时 |
| 📂 目录树可视化 | 点击文件夹批量选择，点击文件单独排除 |
| ⚙️ 输出模式切换 | 普通 / 简洁 / 骨架 三种模式 |
| 🖱️ 右键菜单集成 | 在任意文件夹/文件上右键快速打开 |
| ⌨️ 全局快捷键 | Ctrl+` 快速唤起当前资源管理器中的路径 |
| 🌙 系统托盘 | 后台静默运行，随时唤起 |
| 📌 生成后高亮 | 自动在资源管理器中高亮输出文件 |

---

## 🏗️ 架构

```
AI_CodeFeeder/
├── CodeFeeder.pyw          # 入口（支持 exe/源码双模式）
├── setup.py                # 源码安装脚本
├── build_exe.py            # 打包脚本
├── Core/
│   ├── Installer.py        # 内置注册器（exe首次运行调用）
│   ├── RuntimeBootstrap.py # 源码模式依赖检测
│   ├── ConfigLoader.py     # 配置加载
│   ├── Analyzer.py         # 文件扫描处理
│   ├── CodeCleaner.py      # 代码清洗算法
│   ├── services/           # 服务层
│   │   ├── ConfigService.py
│   │   ├── HotkeyService.py
│   │   ├── TrayService.py
│   │   └── StartupService.py
│   └── config.json         # 配置文件
└── AppUI/
    ├── MainWindow.py       # 主窗口控制器
    ├── controllers/        # 控制器层
    │   ├── ScanController.py
    │   ├── GenerateController.py
    │   └── SettingsController.py
    ├── models/             # 模型层
    │   └── AppState.py
    ├── Views.py            # 视图层
    ├── Components.py       # UI组件库
    ├── Theme.py            # 视觉常量
    ├── Tree.py             # 目录树数据处理
    └── BootstrapDialog.py  # 依赖引导对话框
```

---

## 📦 打包

```bash
pip install pyinstaller
python build_exe.py
```

生成 `dist/AICodeFeeder.exe`（单文件，约 15MB）。

---

## ⚙️ 配置

编辑 `Core/config.json`：

- `allowed_extensions`: 扫描的文件后缀
- `ignore_dirs`: 跳过的目录
- `ignore_files`: 跳过的文件名
- `full_load_timeout_seconds`: 全量扫描超时时间
- `default_mode`: 默认输出模式

---

## 🔧 故障排除

| 问题 | 解决方案 |
|------|----------|
| exe 无响应 | 检查是否被杀毒软件拦截 |
| 右键菜单无效 | 以管理员权限重新运行 exe，托盘菜单中选择「注册右键菜单」 |
| 快捷键冲突 | 托盘菜单 → 设置中修改热键 |
| 源码模式依赖缺失 | 运行 `python setup.py --verify` |

---

## 👨‍💻 版本历史

**V1.9.7** [配置修复版] 2026.04.12
- 修复设置保存后配置不生效问题（ScanController manager 引用同步）
- 修复大文件夹展开后消失问题（添加 user_expanded_folders 记忆）
- 设置窗口扩大到 1000x800

**V1.9.6** [设置页面修复版] 2026.04.12
- 修复设置页面加载失败（移除分页逻辑，统一单页滚动式布局）
- 修正默认配置值（default_mode=normal, save_txt=false）
- 移除未使用的分页切换方法

**V1.9.5** [架构重构版] 2026.04.11
- 分离控制器层（ScanController, GenerateController, SettingsController）
- 分离模型层（AppState）
- 分离服务层（ConfigService, HotkeyService, TrayService, StartupService）
- MVC 架构清晰化

**V1.9.0-V1.9.4** [重构迭代版] 2026.04.10-11
- 逐步重构架构，分离关注点
- 优化代码组织，提升可维护性

**V1.8.0** [单文件版] 2026.04.05
- 简化为单个 exe，首次运行自动注册
- 托盘菜单增加注册/卸载选项
- 入口统一处理 exe/源码双模式

**V1.7.0** [自适应加载版] 2026.04.05
- 5秒自适应预加载，大项目自动回退

**V1.6.2** [BugFix版本] 2026.03.14
- 修复了在其他 Windows 电脑上注册表注册失败的问题
- 优化了右键菜单对不同类型（文件夹/文件）的参数处理
- 增加了启动错误日志记录功能

**V1.6.1** [架构重构版] 2026.02.14
- 分层模块化架构、深色主题、系统托盘

**V1.5.0** [GUI版本] 2026.02.06

**V1.0.8** [MVP版本] 2026.01.18

---
*Happy Coding!*