#!/usr/bin/env python3
"""
fix_product.py — 手动移除超标品/误上产品（从当日通过名单移入拒绝名单）并重新部署

用法:
    python3 fix_product.py <ASIN> [原因]

流程:
  1. 找最新含产品的 channels 文件（先备份到 /tmp）
  2. 从 products 移出 ASIN → 加入 rejected 文件（带 detail_reject_reason）
  3. 更新 stats（passed_filter / rejected / detail_reject 归类）
  4. 重新生成平台页 + 门户页
  5. GitHub API 推送 + git commit/push 双保险（防止下次扫描 stash 丢失修复）
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent


def find_latest():
    """最新一个含产品的 channels 主文件。"""
    files = sorted(
        (BASE / "data" / "channels").glob("*.json"),
        key=lambda f: f.stat().st_mtime, reverse=True,
    )
    for f in files:
        if "rejected" in f.name or "trends" in f.name or "raw" in f.name:
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if d.get("products"):
            return f, d
    return None, None


def _bucket(reason: str) -> str:
    if "重量" in reason:
        return "重量超标"
    if "尺寸" in reason or "包装" in reason:
        return "尺寸超标"
    return "其他"


def main():
    if len(sys.argv) < 2:
        print("用法: python3 fix_product.py <ASIN> [原因]")
        sys.exit(1)
    asin = sys.argv[1].strip().upper()
    reason = sys.argv[2] if len(sys.argv) > 2 else "手动移除(超标/误上)"

    f, data = find_latest()
    if f is None:
        print("❌ 未找到含产品的数据文件")
        sys.exit(1)
    print(f"📄 目标文件: {f.name}")

    prods = data.get("products", [])
    bad = [p for p in prods if (p.get("asin") or "").upper() == asin]
    if not bad:
        print(f"⚠️ {asin} 不在 {f.name} 的通过名单中，无需处理")
        sys.exit(0)

    # 备份
    bak = f"/tmp/{f.name}.bak-fix"
    shutil.copy(f, bak)
    print(f"💾 已备份: {bak}")

    # 1. 主文件：移出产品
    data["products"] = [p for p in prods if (p.get("asin") or "").upper() != asin]

    # 2. rejected 文件：追加
    rej_f = f.with_name(f.stem + "-rejected.json")
    rejected = []
    if rej_f.exists():
        try:
            rejected = json.loads(rej_f.read_text(encoding="utf-8"))
            if not isinstance(rejected, list):
                rejected = []
        except Exception:
            rejected = []
    for p in bad:
        p["detail_reject_reason"] = reason
        p["verify_status"] = "rejected"
        rejected.append(p)

    # 3. stats 更新
    n = len(bad)
    stats = data.setdefault("stats", {})
    stats["passed_filter"] = stats.get("passed_filter", len(prods)) - n
    stats["rejected"] = stats.get("rejected", 0) + n
    dr = stats.setdefault("detail_reject", {})
    bucket = _bucket(reason)
    dr[bucket] = dr.get(bucket, 0) + n

    # 4. 写回（防空：products 不能为空就拒绝写）
    if not data["products"]:
        print("❌ 移除后 products 为空，拒绝写入（防止清空好数据）")
        sys.exit(1)
    f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    rej_f.write_text(json.dumps(rejected, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 已移除 {n} 个: {bad[0].get('name', '')[:50]} | {reason}")

    # 5. 重新生成 + 部署
    for cmd in (["python3", "generate_platform.py"], ["python3", "generate_portal.py"]):
        r = subprocess.run(cmd, cwd=BASE, capture_output=True, text=True, timeout=120)
        print(f"   {'✅' if r.returncode == 0 else '⚠️'} {' '.join(cmd)}: "
              f"{'OK' if r.returncode == 0 else r.stderr[-200:]}")

    # 6. GitHub API 推送
    msg = f"fix: 移除 {asin} {reason}"
    r = subprocess.run(["python3", "github_api_push.py", msg], cwd=BASE,
                       capture_output=True, text=True, timeout=200)
    if r.returncode != 0:
        print(f"   ⚠️ GitHub API 推送失败: {r.stderr[-200:]}")
    else:
        print(f"   ✅ 已推送: {msg}")

    # 7. git 双保险（防 cron stash 吞修复）
    r = subprocess.run(
        ["git", "add", "-f", "data/channels/", "output/", "status.json"],
        cwd=BASE, capture_output=True, text=True, timeout=60)
    r = subprocess.run(["git", "commit", "-m", msg], cwd=BASE,
                       capture_output=True, text=True, timeout=60)
    if r.returncode == 0:
        subprocess.run(["git", "push", "origin", "main"], cwd=BASE,
                       capture_output=True, text=True, timeout=120)
        print("   ✅ git 已提交并推送")
    else:
        print(f"   ⚠️ git commit 跳过: {r.stdout.strip()[-100:]}")

    print("\n🎉 完成。页面已重新生成并部署。")


if __name__ == "__main__":
    main()
