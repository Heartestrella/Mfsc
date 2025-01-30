# Minecraft Fast Server Cli

这是一个用于下载和部署 Minecraft 服务端（支持 Paper 和 Fabric）并支持安装 Geyser 插件的脚本工具。

## 功能介绍

- **更新 JSON 配置文件**：自动从远程更新版本信息。
- **下载服务端**：支持下载 Minecraft Paper 和 Fabric 服务端。
- **管理 Fabric 下载链接**：从官方 Fabric API 获取稳定版本链接并更新配置文件。
- **自动安装 Java**：根据所需版本自动下载并安装 Java 环境。
- **检测服务端端口状态**：检测服务端及 Geyser 插件是否正常启动。
- **安装 Geyser 插件**：支持为服务端安装 Geyser 插件，实现与基岩版玩家的联机。
- **启动服务端**：自动创建服务器文件夹并启动服务端。

## 环境需求

- **操作系统**：
  - Windows 64 位（仅支持 AMD/Arm64 架构）
  - Linux 64 位
- **Python 环境**：Python 3.x
- **依赖库**：
  - `requests`
  - `tqdm`

安装依赖库：
```bash
pip install requests tqdm
```

## 使用
- **以源代码**:
```bash
python3 main.py
```
- **以可执行文件**:

在项目中下载可执行文件并以管理员运行

Windows用户最好在Powershell用执行文件方便查看输出

## 提交错误
该项目未测试所有版本的运行是否正常,若您的使用时遇到问题欢迎提交以便于我们改进

## 更新
V1.0.1:完善项目大致框架实现基础功能
V1.0.2:完善对系统已有Java的支持，并修Linux用户退格识别为Ctrl^H的问题
