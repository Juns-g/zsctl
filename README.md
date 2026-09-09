# zsctl

**简体中文** · [English](README_EN.md)

专为**极空间 (ZSpace) NAS** 打造的免配置运维控制面 CLI 工具 —— 直接在终端或通过 AI Agent 管理 Docker 容器、Compose 堆栈、存储池、硬盘温度、硬盘休眠诊断以及迅雷/离线下载任务，彻底告别慢速繁琐的网页端点击。

---

## 核心特性

- 🐳 **Docker 与 Compose 运维**：秒查运行容器（`ps`）、实时查看日志（`logs`）、启停/重启容器，管理 Docker Compose 堆栈，无需进入 Web 桌面。
- 💾 **存储池与硬盘状态**：30 毫秒秒级查询存储空间容量、各硬盘型号、序列号、实时运行温度及底层 S.M.A.R.T. 健康报告。
- 💤 **硬盘休眠诊断**：精准检测当前阻止机械硬盘进入休眠的具体系统服务（如文件全量索引、文档同步、缩略图生成等）并提供优化建议。
- 📥 **下载中心与迅雷管理**：查看下载任务进度与实时上下行速度，支持命令行直接投递 HTTP、FTP、磁力链接（magnet）下载任务。
- 📁 **无缝文件管理桥接**：提供 `zsctl file` 接口，自动透传调用标准 POSIX 风格文件管理工具 `zs`（列目录、跨盘全局搜文件、移动重命名）。
- ⚡ **极致响应**：直接与本地客户端直连通道（`127.0.0.1:13579`）进行 HTTP 交互，响应仅需 30~50 毫秒，彻底摒弃消耗数万 Token 且耗时数十秒的浏览器模拟点击。
- 🔒 **零密码与无需开启 SSH**：自动探测已登录的极空间官方桌面客户端凭证（`vuex.json`），无需暴露账号密码，无需承担开启宿主 SSH 带来的失去官方软件售后风险。

---

## 前置要求

1. 本机已安装并登录**极空间官方 macOS 客户端**。
2. 极空间客户端处于运行状态（其在后台维护了与 NAS 通信的本地加密代理 `127.0.0.1:13579`）。

---

## 安装方式

```bash
pip install zsctl
# 或者推荐使用 pipx 隔离安装
pipx install zsctl
```

---

## 常用命令速查

### 1. 存储池与硬盘管理 (`disk`)

```bash
# 查看所有存储池容量、硬盘型号、SN、实时温度与挂载点 (约 35ms)
zsctl disk info

# 诊断当前阻止机械硬盘休眠的服务
zsctl disk sleep-check

# 查询指定硬盘的详细 S.M.A.R.T. 健康报告与属性
zsctl disk smart <硬盘序列号SN>
```

### 2. Docker 容器与 Compose 堆栈 (`docker`)

```bash
# 列出所有容器（名称、运行状态、运行时长、镜像）
zsctl docker ps

# 查看指定容器的最近 50 行运行日志
zsctl docker logs adguardhome -n 50

# 重启或停止容器
zsctl docker restart qbittorrent
zsctl docker stop homeassistant

# 列出所有 Docker Compose 项目及配置文件路径
zsctl docker compose ls

# 重启指定的 Docker Compose 项目
zsctl docker compose restart tailscale
```

### 3. 下载中心与迅雷任务 (`download`)

```bash
# 查看当前所有下载任务与实时上下行速度
zsctl download ls

# 提交磁力链下载任务（默认存入 /sata11/my/data/download）
zsctl download add "magnet:?xt=urn:btih:..."

# 提交普通 HTTP 下载并指定存放目录
zsctl download add "https://example.com/file.zip" -d /sata11/my/data/download

# 暂停、继续或删除下载任务
zsctl download pause <任务ID>
zsctl download resume <任务ID>
zsctl download del <任务ID>
```

### 4. 系统概况与程序化 JSON 输出

```bash
# 查看 NAS 设备型号、系统启动时间及版本
zsctl sys info

# 输出纯 JSON 数据供自动化脚本或 AI Agent 读取
zsctl --json docker ps
zsctl --json disk info
```

---

## AI Agent / 技能集成 (Skills)

本项目在 `skills/zsctl/SKILL.md` 中自带了标准的 Agent 技能定义文件。

如果你使用 AI 编码助手或个人 Agent（如 Hermes、Codex、Cursor、Claude Code、Windsurf 等），可以通过以下方式一键赋予 AI 操控极空间的能力：

```bash
# 复制到你的全局 Agent 技能目录（适用于 Hermes、Codex 等）：
mkdir -p ~/.agents/skills
cp -r skills/zsctl ~/.agents/skills/
```

配置完成后，你可以在聊天中直接对你的 AI 下达自然语言指令：
- *“帮我查一下极空间 NAS 硬盘的温度和健康度”*
- *“看下 NAS 上现在跑了哪些 Docker 容器”*
- *“为什么我的机械硬盘一直不休眠？”*
- *“把这个磁力链添加到 NAS 下载中心”*

AI 将会自动优先通过 `zsctl` 毫秒级直连执行，彻底告别浏览器抓瞎。

---

## 开源协议

MIT License.
