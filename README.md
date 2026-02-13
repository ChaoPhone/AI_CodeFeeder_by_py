
***

# 🚀 AI_CodeFeeder (V1.6.0 ctrl+`极速版！)

![Version](https://img.shields.io/badge/version-1.6.0-blue.svg)
![Build](https://img.shields.io/badge/build-passing-brightgreen.svg)
![Python](https://img.shields.io/badge/python-3.x-blue.svg)
![Tkinter](https://img.shields.io/badge/UI-Tkinter-orange.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)

> **Stop Copy-Pasting. Start Coding.**
>
> 拒绝繁琐的复制粘贴，让 AI 更懂你的代码架构。

祝看到这里的同学期末周科科满绩！！！送你一锅重庆鸡公煲🫕🥰🥰🥰

## 📖 简介

**众所周知，大多数 AI（如 DeepSeek, 豆包, ChatGPT, Claude, Gemini）不允许直接上传代码文件夹。**

劳累了一天的人们，往往还要不厌其烦地打开一个个文件，复制、粘贴，或者被迫使用 IDE 内置的昂贵或不够聪明的 AI 插件。这种方式不仅效率低下，而且丢失了项目原本的文件结构上下文，导致 AI 的回答往往不够准确。

**AI_CodeFeeder** 因此诞生。👍🤓

它是一个基于 Python 的 light-weight 工具，能够**一键扫描**你的工程目录，智能过滤掉无关文件（如 `build`, `.git`, `node_modules` 以及 STM32/Unity 的垃圾文件），生成一份包含**完整目录树**和**所有源码内容**的 Markdown 文件。

**V1.6.0 版本迎来重大架构升级**，采用了分层模块化设计，大幅提升了系统的稳定性和可维护性，并优化了多项用户体验。

***

## 🛠️ 使用步骤

### 1. 环境准备

确保电脑已安装 Python 3.x。

### 2. 首次安装（右键菜单集成）

为了获得最佳体验，建议运行注册脚本，将工具集成到系统右键菜单：

1. **以管理员身份**运行 CMD 或 PowerShell。
2. 进入项目根目录，运行：
   ```bash
   python install_menu.py
   ```
3. 脚本会自动请求权限并完成右键菜单及开机自启动的注册。

### 3. 开始使用

**方式 A：右键启动（推荐）**
在任意代码文件夹上 **右键** -> 选择 **📂 使用 AI CodeFeeder 打开**。

**方式 B：快捷键启动**
按下 **Ctrl + `** (反引号，Esc 下方) 即可快速呼出程序。

**方式 C：直接运行**
双击运行 `CodeFeeder.pyw`。

***

## ✨ V1.6.0 新版特性

* **🏗️ 分层模块化架构**：将代码重构为 UI 层、系统层和业务逻辑层。告别 500+ 行的“上帝类”，代码更清晰，扩展更简单。
* **🌙 现代深色主题 (VS Code 风格)**：采用更加细腻的配色方案，支持自定义圆角按钮和分栏框，视觉体验更统一。
* **🌳 深度优化的目录树**：
  * **更清晰的缩进**：层级缩进增加至 48px，项目结构一目了然。
  * **直观的状态反馈**：忽略文件时，图标与文字同步变灰并增加删除线，操作反馈更明显。
  * **自适应行高**：树状图行高根据内容自动适配，在高 DPI 屏幕下表现更佳。
* **🔄 后台静默运行**：生成任务结束后程序不再强制退出，而是缩回系统托盘保持静默，支持通过快捷键随时唤起。
* **⌨️ 全局热键唤起 (Ctrl + `)**：在 Windows 资源管理器中选中文件夹或在窗口内，通过快捷键即可快速呼出并自动加载当前路径。
* **🖱️ 右键菜单集成**：通过 `install_menu.py` 快速将工具集成到系统右键菜单，支持无窗口静默运行。

***

## 🏗️ 架构说明 (V1.6.0+)

采用了 **Layered Architecture (分层架构)**，实现了界面、系统交互与核心逻辑的深度解耦。

```text
AI_CodeFeeder/
├── CodeFeeder.pyw         # [入口] 无窗口启动器
├── AppUI/                 # [UI & 系统层]
│   ├── MainWindow.py      # 控制器：协调 UI 与后台服务
│   ├── Views.py           # 视图层：界面布局逻辑
│   ├── Components.py      # 组件库：RoundedButton, RoundedFrame
│   ├── SystemServices.py  # 系统服务：热键、托盘、注册表操作
│   ├── Theme.py           # 视觉常量：颜色、字体、圆角
│   └── Tree.py            # 数据处理：计算目录树结构
├── Core/                  # [核心业务层]
│   ├── Analyzer.py        # 文件扫描、Pipeline 流水线处理
│   ├── CodeCleaner.py     # 代码清洗算法 (正则去注释、提取骨架)
│   ├── ConfigLoader.py    # 配置加载器
│   └── config.json        # [配置] 用户自定义规则
├── install_menu.py        # 右键菜单/自启动注册脚本
└── uninstall_menu.py      # 菜单/自启动卸载脚本
```

***

## ⚙️ 配置说明 (Advanced)

所有的过滤规则都存储在 `Core/config.json` 中，你可以直接编辑它来定制你的规则：

* **`allowed_extensions`**: 定义哪些后缀的文件会被扫描。
* **`ignore_dirs`**: 递归扫描时强制跳过的文件夹（如 `.git`, `node_modules`）。
* **`ignore_prefixes`**: 针对特定开发环境（如 STM32）忽略特定前缀的自动生成文件。
* **`ignore_files`**: 精确忽略特定的文件名。

***

## 👨‍💻 版本与作者

**AI_CodeFeeder V1.6.0 (Refactor Edition)**

* **Original Author**: ChaoPhone
* **Refactored By**: AI Assistant & User
* **Last Update**: 2026/02/13

***

**V1.6.0** [OMG版本] Updated by **ChaoPhone** with **Gemini 3 Pro** on 2026.02.13

**V1.5.0** [GUI版本] Updated by **ChaoPhone** on 2026.02.06

**V1.0.8** [MVP版本] Updated by **ChaoPhone** on 2026.01.18

---
*Happy Coding!*
