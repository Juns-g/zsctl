"""zsctl - ZSpace (极空间) NAS Management CLI.

Control plane management for ZSpace NAS Docker containers, compose projects,
storage pools, disk health, sleep diagnostics, and download tasks.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

from zspace_cli.client import ZSpaceClient, ZSpaceError


def get_client() -> ZSpaceClient:
    return ZSpaceClient()


# ── Subcommand Handlers ────────────────────────────────────────────────────────

def cmd_disk_info(client: ZSpaceClient, args):
    res = client._post("/zspool/info")
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    pools = res.get("data", {}).get("pool_list", [])
    print(f"\n[ZSpace Storage Pools] ({len(pools)} pools found)")
    for p in pools:
        name = p.get("name")
        ptype = p.get("pool_type")
        status = p.get("status")
        total_tb = p.get("total_size", 0) / (1024**4)
        free_tb = p.get("free_size", 0) / (1024**4)
        used_pct = int(((total_tb - free_tb) / total_tb) * 100) if total_tb > 0 else 0
        print(f"\n  • Pool: {name} ({ptype}) - Status: {status}")
        print(f"    Capacity: {total_tb:.2f} TB total, {free_tb:.2f} TB free ({used_pct}% used)")
        for d in p.get("disk_list", []):
            model = d.get("model") or "Generic"
            sn = d.get("sn") or d.get("serial_number") or "N/A"
            temp = d.get("temp")
            temp_str = f"{temp}°C" if temp is not None else "N/A"
            mnt = d.get("mnt") or ""
            print(f"    - Disk: {model:<25} | SN: {sn:<18} | Temp: {temp_str:<5} | Mount: {mnt}")
    print()


def cmd_disk_sleep(client: ZSpaceClient, args):
    res = client._post("/disk/sleep_check")
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    items = res.get("data", {}).get("list", [])
    print(f"\n[Disk Sleep Diagnostics] ({len(items)} blockers detected)")
    if not items:
        print("  ✓ No active service is blocking mechanical disk sleep.")
    for idx, item in enumerate(items, 1):
        title = item.get("title")
        reason = item.get("reason")
        advice = item.get("advice")
        print(f"\n  {idx}. {title}")
        print(f"     Reason: {reason}")
        print(f"     Advice: {advice}")
    print()


def cmd_disk_smart(client: ZSpaceClient, args):
    sn = args.sn.strip()
    res = client._post("/zspool/smart/report2", {"sn": sn})
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    data = res.get("data", {})
    health = data.get("health", "unknown")
    is_ssd = data.get("is_ssd", False)
    print(f"\n[SMART Report for {sn}]")
    print(f"  Type: {'NVMe / SSD' if is_ssd else 'Mechanical HDD'}")
    print(f"  Health: {str(health).upper()}")
    attrs = data.get("attributes", [])
    if attrs:
        print("  Attributes:")
        for a in attrs:
            name = a.get("name") or a.get("id") or "Attribute"
            val = a.get("value")
            raw = a.get("raw")
            if val is not None or raw is not None:
                print(f"    - {name:<20}: value={val}, raw={raw}")
    print()


def cmd_docker_ps(client: ZSpaceClient, args):
    headers = {"Content-Type": "application/json"}
    payload = client._common_params()
    res = client._send("POST", client._url("/zdocker/v2/container_list"), json=payload, headers=headers)
    containers = res.get("data", [])
    if args.json:
        print(json.dumps(containers, ensure_ascii=False, indent=2))
        return

    print(f"\n[Docker Containers] ({len(containers)} total)")
    print(f"  {'NAME':<20} {'STATE':<10} {'STATUS':<24} {'IMAGE'}")
    print(f"  {'-'*18:<20} {'-'*8:<10} {'-'*22:<24} {'-'*30}")
    for c in containers:
        names = ", ".join(n.lstrip("/") for n in c.get("Names", []))
        state = c.get("State", "")
        status = c.get("Status", "")
        image = c.get("Image", "")
        print(f"  {names:<20} {state:<10} {status:<24} {image}")
    print()


def cmd_docker_op(client: ZSpaceClient, action: str, target: str):
    headers = {"Content-Type": "application/json"}
    payload = client._common_params()
    res = client._send("POST", client._url("/zdocker/v2/container_list"), json=payload, headers=headers)
    containers = res.get("data", [])
    cid = target
    for c in containers:
        c_names = [n.lstrip("/") for n in c.get("Names", [])]
        if target in c_names or c.get("Id", "").startswith(target):
            cid = c.get("Id")
            break

    params = client._common_params()
    params.update({"container_id": cid, "action": action})
    print(f"Executing '{action}' on container '{target}' ({cid[:12]})...")
    client._send("GET", client._url("/zdocker/container_op"), params=params)
    print(f"✓ Container '{target}' {action} completed.")


def cmd_docker_logs(client: ZSpaceClient, args):
    headers = {"Content-Type": "application/json"}
    payload = client._common_params()
    res = client._send("POST", client._url("/zdocker/v2/container_list"), json=payload, headers=headers)
    containers = res.get("data", [])
    cid = args.name
    for c in containers:
        c_names = [n.lstrip("/") for n in c.get("Names", [])]
        if args.name in c_names or c.get("Id", "").startswith(args.name):
            cid = c.get("Id")
            break

    params = client._common_params()
    params.update({"container_id": cid, "tail": args.tail})
    raw_logs = client._send("GET", client._url("/zdocker/container_logs"), params=params)
    data = raw_logs.get("data", "") if isinstance(raw_logs, dict) else str(raw_logs)
    clean_lines = []
    for line in data.splitlines():
        clean = re.sub(r"^[\x00-\x1f]+", "", line)
        if clean:
            clean_lines.append(clean)
    print("\n".join(clean_lines[-args.tail:]))


def cmd_compose_ls(client: ZSpaceClient, args):
    headers = {"Content-Type": "application/json"}
    payload = client._common_params()
    res = client._send("POST", client._url("/zdocker/v2/compose/list_projects"), json=payload, headers=headers)
    projects = res.get("data", [])
    if args.json:
        print(json.dumps(projects, ensure_ascii=False, indent=2))
        return

    print(f"\n[Docker Compose Projects] ({len(projects)} total)")
    print(f"  {'PROJECT':<20} {'STATUS':<15} {'CONFIG PATH'}")
    print(f"  {'-'*18:<20} {'-'*13:<15} {'-'*45}")
    for p in projects:
        pname = p.get("projectName", "")
        status = p.get("status", "")
        fpath = p.get("filePath", "")
        print(f"  {pname:<20} {status:<15} {fpath}")
    print()


def cmd_compose_op(client: ZSpaceClient, action: str, project_name: str):
    endpoint = f"/zdocker/compose_{action}_project"
    params = client._common_params()
    params.update({"projectName": project_name})
    print(f"Executing compose {action} on project '{project_name}'...")
    client._send("GET", client._url(endpoint), params=params)
    print(f"✓ Compose project '{project_name}' {action} triggered.")


def cmd_download_ls(client: ZSpaceClient, args):
    res = client._post("/downloader/list")
    data = res.get("data", {})
    tasks = data.get("list", [])
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    down_rate = data.get("totalRateDownload", 0) / 1024
    up_rate = data.get("totalRateUpload", 0) / 1024
    print(f"\n[Downloader Tasks] (Total: {data.get('total', 0)} | Down: {down_rate:.1f} KB/s | Up: {up_rate:.1f} KB/s)")
    if not tasks:
        print("  No active or queued download tasks.")
    for t in tasks:
        tid = t.get("id")
        name = t.get("name") or "Unknown"
        state = t.get("state") or t.get("status") or "loading"
        pct = t.get("percent") or 0
        speed = (t.get("rateDownload") or 0) / 1024
        print(f"  • [{tid}] {name}")
        print(f"    State: {state} | Progress: {pct}% | Speed: {speed:.1f} KB/s")
    print()


def cmd_download_add(client: ZSpaceClient, args):
    uri = args.uri.strip()
    save_dir = args.dir or "/sata11/my/data/download"
    print(f"Adding download task: {uri}")
    print(f"Save destination: {save_dir}")
    res = client._post("/downloader/add/link", {"uri": uri, "dir": save_dir})
    print(f"✓ Download task successfully created. (ts={res.get('ts')})")


def cmd_download_del(client: ZSpaceClient, args):
    tids = [int(i) for i in args.ids]
    print(f"Deleting download task(s): {tids}...")
    client._post("/downloader/del", {"id": tids})
    print(f"✓ Task(s) deleted.")


def cmd_download_op(client: ZSpaceClient, action: str, ids: List[str]):
    tids = [int(i) for i in ids]
    endpoint = f"/downloader/{action}"
    client._post(endpoint, {"id": tids})
    print(f"✓ Download task(s) {ids} {action} completed.")


def cmd_sys_info(client: ZSpaceClient, args):
    res = client._post("/system/polling2")
    data = res.get("data", {})
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return

    boot_time = data.get("uptime_abs", 0)
    uptime_sec = int(time.time()) - boot_time if boot_time > 0 else 0
    days = uptime_sec // 86400
    hours = (uptime_sec % 86400) // 3600
    print(f"\n[ZSpace NAS System Overview]")
    print(f"  NAS ID: {client._creds.nas_id}")
    print(f"  User: {client._creds.username}")
    print(f"  OS Client Ver: {data.get('pcversion')}")
    print(f"  Storage Server: {data.get('storage_server')}")
    print(f"  Uptime: {days} days, {hours} hours (booted at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(boot_time))})")
    print()


# ── Main Entrypoint ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(prog="zsctl", description="ZSpace (极空间) NAS Management CLI")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    subparsers = parser.add_subparsers(dest="category", required=True)

    # docker
    p_docker = subparsers.add_parser("docker", help="Manage Docker containers and compose projects")
    docker_sub = p_docker.add_subparsers(dest="docker_cmd", required=True)
    
    docker_sub.add_parser("ps", help="List containers")
    docker_sub.add_parser("ls", help="Alias for ps")
    
    d_logs = docker_sub.add_parser("logs", help="Get container logs")
    d_logs.add_argument("name", help="Container name or ID")
    d_logs.add_argument("-n", "--tail", type=int, default=50, help="Number of lines to tail (default 50)")

    d_restart = docker_sub.add_parser("restart", help="Restart container")
    d_restart.add_argument("name", help="Container name or ID")
    
    d_stop = docker_sub.add_parser("stop", help="Stop container")
    d_stop.add_argument("name", help="Container name or ID")

    d_start = docker_sub.add_parser("start", help="Start container")
    d_start.add_argument("name", help="Container name or ID")

    d_compose = docker_sub.add_parser("compose", help="Manage Docker Compose projects")
    compose_sub = d_compose.add_subparsers(dest="compose_cmd", required=True)
    compose_sub.add_parser("ls", help="List compose projects")
    compose_sub.add_parser("ps", help="Alias for ls")
    
    c_restart = compose_sub.add_parser("restart", help="Restart compose project")
    c_restart.add_argument("name", help="Project name")
    
    c_start = compose_sub.add_parser("start", help="Start compose project")
    c_start.add_argument("name", help="Project name")
    
    c_stop = compose_sub.add_parser("stop", help="Stop compose project")
    c_stop.add_argument("name", help="Project name")

    # disk
    p_disk = subparsers.add_parser("disk", help="Storage pools, disk temperature, and sleep diagnostics")
    disk_sub = p_disk.add_subparsers(dest="disk_cmd", required=True)
    disk_sub.add_parser("info", help="Storage pools and disk temperatures")
    disk_sub.add_parser("ls", help="Alias for info")
    disk_sub.add_parser("sleep-check", help="Diagnose services preventing disk sleep")
    
    d_smart = disk_sub.add_parser("smart", help="Query disk SMART report")
    d_smart.add_argument("sn", help="Disk serial number (e.g. from zsctl disk info)")

    # download
    p_dl = subparsers.add_parser("download", help="Manage downloader / Xunlei tasks")
    dl_sub = p_dl.add_subparsers(dest="dl_cmd", required=True)
    dl_sub.add_parser("ls", help="List active and completed downloads")
    dl_sub.add_parser("list", help="Alias for ls")
    
    dl_add = dl_sub.add_parser("add", help="Add download task (HTTP, FTP, magnet)")
    dl_add.add_argument("uri", help="Download URL or magnet link")
    dl_add.add_argument("-d", "--dir", default=None, help="Save directory (default: /sata11/my/data/download)")

    dl_del = dl_sub.add_parser("del", help="Delete download task")
    dl_del.add_argument("ids", nargs="+", help="Task ID(s)")

    dl_stop = dl_sub.add_parser("pause", help="Pause download task")
    dl_stop.add_argument("ids", nargs="+", help="Task ID(s)")

    dl_start = dl_sub.add_parser("resume", help="Resume download task")
    dl_start.add_argument("ids", nargs="+", help="Task ID(s)")

    # sys
    p_sys = subparsers.add_parser("sys", help="System overview and uptime")
    sys_sub = p_sys.add_subparsers(dest="sys_cmd", required=True)
    sys_sub.add_parser("info", help="System uptime, versions, and server status")

    # file pass-through to zs
    p_file = subparsers.add_parser("file", help="Pass-through file operations to zs (ls, find, mv, cp)")
    p_file.add_argument("zs_args", nargs=argparse.REMAINDER, help="Arguments to pass to zs")

    # help subcommand
    p_help = subparsers.add_parser("help", help="Show help for zsctl or a subcommand")
    p_help.add_argument("topic", nargs="?", help="Subcommand topic (docker, disk, download, sys, file)")

    sub_parsers_map = {
        "docker": p_docker,
        "disk": p_disk,
        "download": p_dl,
        "sys": p_sys,
        "file": p_file,
    }

    # Intercept empty argv
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    # Intercept 'zsctl <category>' with no further args
    if len(sys.argv) == 2 and sys.argv[1] in sub_parsers_map:
        sub_parsers_map[sys.argv[1]].print_help()
        sys.exit(0)

    # Intercept 'zsctl docker compose' with no further args
    if len(sys.argv) == 3 and sys.argv[1] == "docker" and sys.argv[2] == "compose":
        d_compose.print_help()
        sys.exit(0)

    args = parser.parse_args()

    # Handle help subcommand
    if args.category == "help":
        if args.topic and args.topic in sub_parsers_map:
            sub_parsers_map[args.topic].print_help()
        else:
            parser.print_help()
        return

    # Pass-through to zs
    if args.category == "file":
        zs_cmd = ["zs"] + args.zs_args
        subprocess.run(zs_cmd)
        return

    client = get_client()

    try:
        if args.category == "disk":
            if args.disk_cmd in ("info", "ls"):
                cmd_disk_info(client, args)
            elif args.disk_cmd == "sleep-check":
                cmd_disk_sleep(client, args)
            elif args.disk_cmd == "smart":
                cmd_disk_smart(client, args)

        elif args.category == "docker":
            if args.docker_cmd in ("ps", "ls"):
                cmd_docker_ps(client, args)
            elif args.docker_cmd == "logs":
                cmd_docker_logs(client, args)
            elif args.docker_cmd in ("restart", "stop", "start"):
                cmd_docker_op(client, args.docker_cmd, args.name)
            elif args.docker_cmd == "compose":
                if args.compose_cmd in ("ls", "ps"):
                    cmd_compose_ls(client, args)
                elif args.compose_cmd in ("restart", "start", "stop"):
                    cmd_compose_op(client, args.compose_cmd, args.name)

        elif args.category == "download":
            if args.dl_cmd in ("ls", "list"):
                cmd_download_ls(client, args)
            elif args.dl_cmd == "add":
                cmd_download_add(client, args)
            elif args.dl_cmd == "del":
                cmd_download_del(client, args)
            elif args.dl_cmd == "pause":
                cmd_download_op(client, "stop", args.ids)
            elif args.dl_cmd == "resume":
                cmd_download_op(client, "start", args.ids)

        elif args.category == "sys":
            if args.sys_cmd == "info":
                cmd_sys_info(client, args)

    except ZSpaceError as e:
        sys.exit(f"ZSpace error: {e}")
    except Exception as e:
        sys.exit(f"Error: {e}")


if __name__ == "__main__":
    main()
