# 代码文件变更监控工具

这是一个基于Python的命令行工具，用于监控指定目录下Python文件的变更，并通过集成的静态分析工具（如flake8、pylint、mypy和bandit）自动分析这些变更。该工具特别适用于处理由大型语言模型（LLMs）如GitHub Copilot自动生成的代码。

## 功能特点

- 实时监控指定目录下的Python文件变更。
- 自动调用flake8、pylint、mypy和bandit等静态分析工具。
- 根据变更的代码行进行精确分析，专注于AI生成的代码。
- 支持Windows 11、macOS和Ubuntu操作系统。

## 安装指南

### 前提条件

确保您的机器已安装Python 3.6或更高版本。您可以通过运行`python --version`来检查当前Python版本。

### 安装步骤

1. 克隆仓库到本地：
   ```bash
   git clone https://github.com/HanchengZuo/CodeWatchdog.git
   ```
2. 进入项目目录：
   ```bash
   cd CodeWatchdog
   ```
3. 安装必要的依赖：
   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

启动监控程序，需指定要监控的目录路径：
```bash
python main.py <directory_to_watch>
```
替换`<directory_to_watch>`为您希望监控的目录。

请你在获取AI生成的代码之后立即保存对应的文件，以使工具能检测到更改的代码。

## FAQ

**Q: 如何停止监控？**
A: 监控运行在命令行窗口，可以通过在命令行中使用`Ctrl+C`来安全停止监控。

**Q: 支持哪些类型的代码分析？**
A: 当前支持flake8、pylint、mypy和bandit。这些工具覆盖了代码风格检查、错误检测、类型检查以及安全性分析。
