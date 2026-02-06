
***

# 🚀 AI\_CodeFeeder (V1.5.0 GUI Edition)

> **Stop Copy-Pasting. Start Coding.**
>
> 拒绝繁琐的复制粘贴，让 AI 更懂你的代码架构。

祝看到这里的同学期末周科科满绩！！！送你一锅重庆鸡公煲🫕🥰🥰🥰

## 📖 简介

**众所周知，大多数 AI（如 DeepSeek, 豆包, ChatGPT, Claude, Gemini）不允许直接上传代码文件夹。**

劳累了一天的人们，往往还要不厌其烦地打开一个个文件，复制、粘贴，或者被迫使用 IDE 内置的昂贵或不够聪明的 AI 插件。这种方式不仅效率低下，而且丢失了项目原本的文件结构上下文，导致 AI 的回答往往不够准确。

**AI\_CodeFeeder** 因此诞生。👍🤓

它是一个基于 Python 的轻量级工具，能够**一键扫描**你的工程目录，智能过滤掉无关文件（如 `build`, `.git`, `node_modules` 以及 STM32/Unity 的垃圾文件），生成一份包含**完整目录树**和**所有源码内容**的 Markdown 文件。

**V1.5.0 版本全新升级了图形化界面 (GUI)**，支持可视化选择文件、多种代码压缩模式，让投喂 AI 变得更加精准和优雅。

***

## ✨ V1.5.0 新版特性

* **🖥️ 图形化交互界面**：告别黑乎乎的命令行，采用深色主题 (Dark Blue) 界面，颜值与实用并存。

* **🌳 可视化目录树**：采用 Unix Tree 风格 (`├──`) 展示项目结构，支持**点击文件**进行「选中/忽略」切换。

* **🎛️ 三种投喂模式**：

  * **Normal**: 完整代码，原汁原味。

  * **Gap**: 自动去除所有注释和空行，大幅节省 Token。

  * **Skeleton**: 仅保留类和函数定义（骨架），适合让 AI 理解大型项目架构。

* **🖱️ 右键菜单集成**：支持注册到 Windows 右键菜单，在任意文件夹上右键即可启动。

* **📄 双格式输出**：支持同时生成 `.md` 和 `.txt` 文件，满足不同 AI 模型的上传需求。

***

## 🛠️ 使用步骤

### 1. 环境准备

确保电脑已安装 Python 3.x。

### 2. 首次安装（右键菜单集成）

为了获得最佳体验，建议运行注册脚本，将工具集成到系统右键菜单：

1. **以管理员身份**运行 CMD 或 PowerShell。

2. 进入项目根目录，运行：

   Bash

   ```
   python install_menu.py
   ```

   _(注：如果文件夹中没有此脚本，请忽略此步，直接运行 CodeFeeder.py 即可)_

### 3. 开始使用

**方式 A：右键启动（推荐）**

在任意代码文件夹上 **右键** -> 选择 **📂 使用 AI CodeFeeder 打开**。

**方式 B：直接运行**

双击运行 `CodeFeeder.py`，然后点击界面上的 "📂 Browse" 选择项目路径。

### 4. 界面操作流程

1. **检查目录树**：左侧窗口会列出所有代码文件。

   * **高亮 (白色)**：将被包含在生成文件中。

   * **灰显 + 删除线**：将被忽略。

   * _操作_：点击文件名可手动切换选中状态。

2. **选择模式 (Mode)**：在底部选择 `Normal` (全量)、`Gap` (去注释) 或 `Skeleton` (仅骨架)。

3. **附加选项**：勾选 `Also .txt` 可额外生成一份纯文本副本。

4. **生成**：点击右下角的 **🚀 Generate Markdown**。

5. **完成**：程序会自动打开生成文件所在的文件夹，直接把 `.md` 或 `.txt` 拖给 AI 即可。

***

## 🏗️ 架构说明

V1.5.0 采用了 **MVC (Model-View-Controller)** 分层架构，实现了逻辑与界面的彻底解耦，便于后续扩展。

Plaintext

```
AI_CodeFeeder/
├── CodeFeeder.py          # [入口] 程序启动器，负责引导环境
├── AppUI/                 # [视图层] 负责所有界面显示
│   ├── MainWindow.py      # 主窗口逻辑、事件绑定、多线程调度
│   └── Tree.py            # 视觉组件：负责计算 ASCII 目录树结构
├── Core/                  # [模型层] 核心业务逻辑
│   ├── Analyzer.py        # 文件扫描、过滤、Pipeline 流水线处理
│   ├── CodeCleaner.py     # 代码清洗算法 (正则去注释、提取骨架)
│   ├── ConfigLoader.py    # 配置加载器
│   └── config.json        # [配置] 用户自定义规则
└── README.md              # 说明文档
```

* **AppUI**: 这里的代码只负责“长什么样”和“怎么点”。

* **Core**: 这里的代码只负责“读文件”、“洗代码”和“写文件”，完全不知道界面的存在。

* **CodeFeeder.py**: 极简入口，防止 Python 路径混淆。

***

## ⚙️ 配置说明 (Advanced)

所有的过滤规则都存储在 `Core/config.json` 中，你可以直接编辑它来定制你的规则：

* **`allowed_extensions`**: 定义哪些后缀的文件会被扫描（如 `.py`, `.c`, `.cpp`, `.java` 等）。

* **`ignore_dirs`**: 递归扫描时强制跳过的文件夹（如 `.git`, `node_modules`, `build`）。

* **`ignore_prefixes`**: 针对嵌入式开发（STM32 CubeMX），忽略特定前缀的自动生成文件。

* **`ignore_files`**: 精确忽略特定的文件名。

***

## 👨‍💻 版本与作者

**AI\_CodeFeeder V1.5.0 (Pipeline Edition)**

* **Original Author**: ChaoPhone

* **Refactored By**: AI Assistant & User

* **Last Update**: 2026/02/06

***

**V1.5.0** [GUI版本]  Updated by **ChaoPhone** on 2026.02.06

**V1.0.8** [MVP版本] Updated by **ChaoPhone** on 2026.01.18

---
*Happy Coding!*

