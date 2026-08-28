#!/usr/bin/env python3
"""Gộp 4 snapshot báo cáo sales (Huyền/Trang/CRM-activity/Leads) -> mã hoá -> push GitHub Pages.
Chạy hàng ngày sau 15:10 (sau khi cả 4 báo cáo đã gửi mail xong lúc ~15:00-15:02).
Không gửi mail gì cả - chỉ đọc lại các file snapshot mà mỗi script báo cáo đã tự ghi lúc gửi.
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SNAP_DIR = HERE / "snapshots"
DATA_PRIVATE = HERE / "data-private"
DATA_PRIVATE.mkdir(exist_ok=True)

VPS_HOST = "root@45.251.115.47"
VPS_KEY = str(Path.home() / ".ssh/icd_vps_automation")
VPS_SNAPSHOT_PATH = "/opt/icd-chatbot/nhat-ky-truy-cap/dashboard-snapshot.json"

REPORT_IDS = [
    "crm-activity", "huyen", "trang", "leads",
    "crm-activity-year", "huyen-year", "trang-year", "leads-year",
]


def pull_vps_snapshot():
    """scp snapshot 'crm-activity' từ VPS về local snapshots/. Lỗi -> bỏ qua, dùng bản cũ nếu có."""
    dest = SNAP_DIR / "crm-activity.json"
    try:
        r = subprocess.run(
            ["scp", "-i", VPS_KEY, "-o", "ConnectTimeout=10",
             f"{VPS_HOST}:{VPS_SNAPSHOT_PATH}", str(dest)],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode != 0:
            print(f"[WARN] Không kéo được snapshot VPS: {r.stderr.strip()}", file=sys.stderr)
    except Exception as e:
        print(f"[WARN] Lỗi scp VPS: {e}", file=sys.stderr)


def load_snapshot(report_id):
    f = SNAP_DIR / f"{report_id}.json"
    if not f.exists():
        return {}
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[WARN] Snapshot {report_id} lỗi đọc: {e}", file=sys.stderr)
        return {}


def load_archive(name):
    f = DATA_PRIVATE / name
    if not f.exists():
        return {}
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[WARN] {name} lỗi đọc: {e}", file=sys.stderr)
        return {}


def main():
    pull_vps_snapshot()

    reports = {rid: load_snapshot(rid) for rid in REPORT_IDS}
    crm_activity_daily = load_archive("crm-activity-daily-archive.json")
    saleorder_daily = load_archive("saleorder-daily.json")
    leads_daily = load_archive("leads-daily.json")
    dashboard = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "reports": reports,
        "crmActivityDaily": crm_activity_daily.get("days", {}),
        "saleorderDaily": {
            "huyen": saleorder_daily.get("huyen", {}),
            "trang": saleorder_daily.get("trang", {}),
        },
        "leadsDaily": leads_daily.get("days", {}),
    }
    (DATA_PRIVATE / "dashboard.json").write_text(
        json.dumps(dashboard, ensure_ascii=False), encoding="utf-8"
    )
    have = [rid for rid, r in reports.items() if r.get("html")]
    print(f"Đã gộp {len(have)}/{len(REPORT_IDS)} báo cáo snapshot: {', '.join(have) or 'không có'}")
    print(f"Archive theo ngày: CRM activity {len(dashboard['crmActivityDaily'])} ngày, "
          f"Huyền {len(dashboard['saleorderDaily']['huyen'])} ngày, "
          f"Trang {len(dashboard['saleorderDaily']['trang'])} ngày, "
          f"Leads {len(dashboard['leadsDaily'])} ngày")

    r = subprocess.run(["node", "build-enc.mjs"], cwd=str(HERE), capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode != 0:
        print(f"[ERROR] Mã hoá thất bại: {r.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    subprocess.run(["git", "add", "-f", "data-enc.json"], cwd=str(HERE), check=True)
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(HERE))
    if diff.returncode == 0:
        print("Không có thay đổi - bỏ qua push.")
        return
    today = datetime.now().strftime("%Y-%m-%d")
    subprocess.run(["git", "commit", "-q", "-m", f"auto-sync: cap nhat bao cao ({today})"],
                    cwd=str(HERE), check=True)
    subprocess.run(["git", "push", "-q", "origin", "main"], cwd=str(HERE), check=True)
    print("Đã push. Dashboard cập nhật sau ~1 phút.")


if __name__ == "__main__":
    main()
