#!/usr/bin/env python3
import re
import json
import argparse
import subprocess
import urllib.request
from typing import Iterable, Set, List, Optional, Tuple
from datetime import datetime, date, timezone

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

def get_view_data_by_bvid(bvid: str) -> Optional[dict]:
    api = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    try:
        j = http_get_json(api)
    except Exception:
        return None
    if j.get("code") != 0:
        return None
    return j.get("data") or None

def get_pubdate_epoch(bvid: str) -> Optional[int]:
    """Return Unix epoch seconds for publication date, or None if unavailable."""
    d = get_view_data_by_bvid(bvid)
    if not d:
        return None
    pub = d.get("pubdate")
    return int(pub) if isinstance(pub, (int, float)) else None

def expand_ugc_season_bvids(seed_bvid: str) -> Set[str]:
    """
    调用 view 接口：
      - 若存在 ugc_season.sections[].episodes[].bvid => 返回整个合集所有 bvid
      - 否则返回自己（非合集/接口没给时）
    """
    d = get_view_data_by_bvid(seed_bvid)
    if not d:
        return {seed_bvid}

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

def parse_after_date(s: str) -> date:
    # 支持 YYYY-MM-DD
    return datetime.strptime(s, "%Y-%m-%d").date()

def run_bbdown(bbdown_path: str, urls: Iterable[str], extra_args: List[str]) -> int:
    rc = 0
    for url in urls:
        cmd = [bbdown_path, url] + extra_args
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
    parser.add_argument("--no-download", action="store_true", help="Do not call BBDown")
    parser.add_argument("--after", default=None, help="Only keep videos published on/after YYYY-MM-DD")
    parser.add_argument("--bbdown", default="./BBDown", help="Path to BBDown executable (default: ./BBDown)")
    parser.add_argument(
        "--bbdown-args",
        nargs=argparse.REMAINDER,
        default=[],
        help="Arguments passed to BBDown (everything after --bbdown-args). Example: --bbdown-args -ia -tv",
    )
    args = parser.parse_args()

    after_d: Optional[date] = parse_after_date(args.after) if args.after else None
    after_epoch: Optional[int] = None
    if after_d:
        # 以 UTC 的 00:00:00 为边界（你也可以改为本地时区）
        after_epoch = int(datetime(after_d.year, after_d.month, after_d.day, tzinfo=timezone.utc).timestamp())

    seeds = read_lines(args.seeds)

    seed_bvids: List[str] = []
    for s in seeds:
        bvid = extract_bvid(s)
        if bvid:
            seed_bvids.append(bvid)
        else:
            print(f"[WARN] 跳过无法识别BV的行: {s}")

    # 1) 展开所有合集 bvid
    all_bvids: Set[str] = set()
    for bvid in seed_bvids:
        all_bvids |= expand_ugc_season_bvids(bvid)

    # 2) 按日期过滤（需要对每个 bvid 取 pubdate）
    kept: List[Tuple[str, Optional[int]]] = []
    dropped: List[Tuple[str, Optional[int]]] = []

    for bvid in sorted(all_bvids):
        pub = get_pubdate_epoch(bvid) if after_epoch is not None else None
        if after_epoch is None:
            kept.append((bvid, None))
        else:
            # pubdate 取不到：保守策略 -> 丢弃（你也可以改成保留）
            if pub is None:
                dropped.append((bvid, None))
                continue
            if pub >= after_epoch:
                kept.append((bvid, pub))
            else:
                dropped.append((bvid, pub))

    urls = [f"https://www.bilibili.com/video/{bvid}" for (bvid, _) in kept]

    with open(args.output, "w", encoding="utf-8") as f:
        f.write("\n".join(urls) + ("\n" if urls else ""))

    if after_d:
        print(f"[OK] 过滤条件：pubdate >= {after_d.isoformat()}，保留 {len(kept)} 个，丢弃 {len(dropped)} 个；已写入 {args.output}")
    else:
        print(f"[OK] 收集到 {len(urls)} 个唯一视频URL，已写入 {args.output}")

    if args.dry_run or args.no_download:
        print("\n[DRY-RUN] 将要下载的URL如下：\n")
        for u in urls:
            print(u)
        if after_d and dropped:
            print("\n[INFO] 被过滤/取不到日期而丢弃的 BV（仅供核对）:")
            for bvid, pub in dropped[:30]:
                print(f"  {bvid}  pubdate={pub}")
            if len(dropped) > 30:
                print(f"  ... 还有 {len(dropped)-30} 个")
        print("\n[DRY-RUN] 未调用 BBDown")
        return

    exit_code = run_bbdown(args.bbdown, urls, args.bbdown_args)
    raise SystemExit(exit_code)

if __name__ == "__main__":
    main()

