---
name: zsctl
description: >-
  Control plane CLI for ZSpace (极空间) NAS — manage Docker containers, compose projects,
  storage pools, disk health, disk sleep diagnostics, and downloads without browser automation.
  Use when the user mentions 极空间, ZSpace, NAS operations, Docker on NAS, disk sleep, or downloads.
---

# zsctl - ZSpace NAS Control Plane CLI

`zsctl` 提供极空间 NAS 的系统运维与控制面能力。遵循 **“CLI/API 优先，Ego 浏览器兜底”** 规范。

## 适用场景与分工

1. **运维与控制面（一律优先使用 `zsctl`）**：
   - Docker 容器查看、启停、重启、日志查看
   - Docker Compose 堆栈查看与启停
   - 存储池容量、硬盘型号、SN、实时温度与挂载点
   - 硬盘休眠诊断（查看阻止机械盘休眠的服务及优化建议）
   - 硬盘 S.M.A.R.T. 健康报告
   - 迅雷/离线下载中心任务查看、提交下载、暂停/继续/删除
   - NAS 系统运行时间与设备概览
2. **文件管理面（优先使用 `zs` 或 `zsctl file`）**：
   - 目录翻阅、全盘关键词检索、文件移动、重命名、上传、下载。
   - 大数据批量传输优先走本地 SMB 挂载卷。
3. **沉浸式交互与特殊长尾（回退至浏览器）**：
   - 极相册人脸圈选、极影视海报拖拽排序、在线 OnlyOffice 文档协同编辑，或非官方 API 遇阻时，回退至浏览器自动化。

---

## 常用命令参考

### 1. 存储池与硬盘 (`zsctl disk`)
```bash
# 查看所有存储池容量、硬盘型号、SN、实时温度与挂载点 (30ms)
zsctl disk info

# 诊断是哪些服务在阻止机械硬盘休眠
zsctl disk sleep-check

# 查询指定硬盘的详细 S.M.A.R.T. 健康报告
zsctl disk smart <SERIAL_NUMBER>
```

### 2. Docker 容器管理 (`zsctl docker`)
```bash
# 列出全部容器 (Name, State, Status, Image)
zsctl docker ps

# 查看指定容器日志 (默认 50 行)
zsctl docker logs <name_or_id> -n 50

# 容器操作
zsctl docker restart <name_or_id>
zsctl docker stop <name_or_id>
zsctl docker start <name_or_id>

# Docker Compose 堆栈管理
zsctl docker compose ls
zsctl docker compose restart <project_name>
```

### 3. 下载中心与迅雷 (`zsctl download`)
```bash
# 查看当前下载任务与实时上下行速度
zsctl download ls

# 提交下载任务 (HTTP / HTTPS / FTP / 磁力链)
zsctl download add "magnet:?xt=urn:btih:..."

# 指定下载保存目录 (默认 /sata11/my/data/download)
zsctl download add "<url>" -d /sata11/my/data/download

# 任务控制
zsctl download pause <id>
zsctl download resume <id>
zsctl download del <id>
```

### 4. 系统概况 (`zsctl sys`)
```bash
zsctl sys info
```

所有命令均支持 `--json` 选项，输出机器可读的结构化 JSON。
