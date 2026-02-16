#!/usr/bin/env python3
import re
import json
import argparse
import subprocess
import urllib.request
from typing import Iterable, Set, List, Optional

BV_RE = re.compile(r"(BV[0-9A-Za-z]{10})")

def extract_bvid(s: str) -> Optional[str]:
    m = BV_RE.search(s)
    return m.group(1) if m else None

def http_get_json(url: str, timeout: int = 15) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.bilibili.com/",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))

def expand_ugc_season_bvids(seed_bvid: str) -> Set[str]:
    """
    调用 view 接口：
      - 若存在 ugc_season.sections[].episodes[].bvid => 返回整个合集所有 bvid
      - 否则返回自己（非合集/接口没给时）
    """
    api = f"https://api.bilibili.com/x/web-interface/view?bvid={seed_bvid}"
    try:
        data = http_get_json(api)
    except Exception:
        return {seed_bvid}

    if data.get("code") != 0:
        return {seed_bvid}

    d = data.get("data") or {}
    ugc = d.get("ugc_season")
    if not ugc:
        return {seed_bvid}

    out: Set[str] = set()
    sections = ugc.get("sections") or []
    for sec in sections:
        eps = sec.get("episodes") or []
        for ep in eps:
            bvid = ep.get("bvid")
            if bvid and BV_RE.fullmatch(bvid):
                out.add(bvid)

    return out or {seed_bvid}

def read_lines(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

def run_bbdown(urls: Iterable[str], extra_args: List[str]) -> int:
    rc = 0
    for url in urls:
        cmd = ["./BBDown", url] + extra_args
        print(">>", " ".join(cmd))
        p = subprocess.run(cmd)
        rc = rc or p.returncode
    return rc

def main():
    parser = argparse.ArgumentParser(
        description="Expand bilibili ugc_season collections from seed BV/URLs and optionally download via BBDown."
    )
    parser.add_argument("--seeds", default="seeds.txt", help="Seed input file, one BV/URL per line (default: seeds.txt)")
    parser.add_argument("--output", default="all_urls.txt", help="Output url list file (default: all_urls.txt)")
    parser.add_argument("--dry-run", action="store_true", help="Only print/write urls; DO NOT call BBDown")
    parser.add_argument("--no-download", action="store_true", help="Do not call BBDown (same effect as dry-run but quieter intent)")
    parser.add_argument(
        "--bbdown-args",
        nargs=argparse.REMAINDER,
        default=[],
        help="Arguments passed to BBDown after '--'. Example: --bbdown-args -- -ia -tv",
    )
    args = parser.parse_args()

    seeds = read_lines(args.seeds)

    seed_bvids: List[str] = []
    for s in seeds:
        bvid = extract_bvid(s)
        if bvid:
            seed_bvids.append(bvid)
        else:
            print(f"[WARN] 跳过无法识别BV的行: {s}")

    all_bvids: Set[str] = set()
    for bvid in seed_bvids:
        expanded = expand_ugc_season_bvids(bvid)
        all_bvids |= expanded

    urls = [f"https://www.bilibili.com/video/{bvid}" for bvid in sorted(all_bvids)]

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(urls) + ("\n" if urls else ""))

    print(f"[OK] 收集到 {len(urls)} 个唯一视频URL，已写入 {args.output}")

    # dry-run / no-download：只展示要下载什么，不执行
    if args.dry_run or args.no_download:
        print("\n[DRY-RUN] 将要下载的URL如下：\n")
        for u in urls:
            print(u)
        print("\n[DRY-RUN] 未调用 BBDown（因为启用了 --dry-run/--no-download）")
        return

    # 真正下载
    extra_args = args.bbdown_args
    exit_code = run_bbdown(urls, extra_args)
    raise SystemExit(exit_code)

if __name__ == "__main__":
    main()

