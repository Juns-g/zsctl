# zsctl

Zero-config control plane CLI for **ZSpace (极空间) NAS** — manage Docker containers, Compose projects, storage pools, disk sleep diagnostics, and download tasks directly from your terminal or AI Agent.

## Features

- 🐳 **Docker & Compose**: View running containers (`ps`), stream logs (`logs`), restart/stop containers, and manage Docker Compose stacks without opening the web desktop.
- 💾 **Disks & Storage**: View storage pool capacities, disk models, serial numbers, live temperatures, and S.M.A.R.T. health reports in 30ms.
- 💤 **Disk Sleep Diagnostics**: Pinpoint exact system services (e.g. file indexing, document sync) preventing mechanical hard drives from hibernating.
- 📥 **Download Center / Xunlei**: Check active download speeds and tasks, submit HTTP/FTP/magnet links directly to your NAS.
- 📁 **File Management Bridge**: Seamlessly delegates POSIX-style file operations (`ls`, `find`, `mv`, `cp`) to `zs`.
- ⚡ **Blazing Fast**: Direct local proxy calls (~30-50ms) instead of heavy 30-second browser automation.
- 🔒 **Zero Password & No SSH**: Reuses official desktop client session (`vuex.json`), requiring no exposed passwords or warranty-voiding SSH root access.

---

## Prerequisites

1. 极空间 (ZSpace) macOS desktop client is installed and logged in.
2. The client is running (maintains local tunnel proxy on `127.0.0.1:13579`).

---

## Installation

```bash
pip install zsctl
# or via pipx
pipx install zsctl
```

---

## Quick Reference

### 1. Storage & Disks

```bash
# Check all storage pools, disk models, and temperatures
zsctl disk info

# Diagnose what is keeping mechanical disks awake
zsctl disk sleep-check

# Inspect detailed S.M.A.R.T. health for a disk
zsctl disk smart <SERIAL_NUMBER>
```

### 2. Docker Containers & Compose

```bash
# List all containers (Name, State, Status, Image)
zsctl docker ps

# Stream container logs
zsctl docker logs adguardhome -n 50

# Restart or stop a container
zsctl docker restart qbittorrent
zsctl docker stop homeassistant

# List all Docker Compose projects
zsctl docker compose ls

# Restart a Docker Compose project
zsctl docker compose restart tailscale
```

### 3. Downloader (Thunder / System Engine)

```bash
# List all active and completed downloads with real-time speeds
zsctl download ls

# Add a download task (magnet, HTTP, FTP)
zsctl download add "magnet:?xt=urn:btih:..."

# Add download task with custom save directory
zsctl download add "https://example.com/file.zip" -d /sata11/my/data/download

# Pause, resume, or delete download tasks
zsctl download pause <TASK_ID>
zsctl download resume <TASK_ID>
zsctl download del <TASK_ID>
```

### 4. System Overview & Machine Readable JSON

```bash
# View NAS model, uptime, and client versions
zsctl sys info

# Output clean JSON for automation / AI agents
zsctl --json docker ps
zsctl --json disk info
```

---

## AI Agent Integration (Skills)

This repository includes a ready-to-use Agent Skill in `skills/zsctl/SKILL.md`.

To equip your AI Agent (Hermes, Codex, Cursor, Claude Code, etc.) with `zsctl`:

```bash
# For global agent skills (Hermes, Codex):
mkdir -p ~/.agents/skills
cp -r skills/zsctl ~/.agents/skills/
```

Once installed, your AI Agent will automatically use `zsctl` for:
- *"Check NAS storage and disk temperatures"*
- *"List running Docker containers on my ZSpace NAS"*
- *"Why is my NAS hard drive not sleeping?"*
- *"Download this magnet link to my NAS"*

---

## License

MIT License.
