"""Build kho leads THEO TUNG NGAY (khong chi nam) tu leads.db (da pull qua ssh
vao /tmp/leads-all-raw.json). Dung cho dashboard xem theo ngay/tuan/thang, va
cho tab Ly (loc theo recipients chua "Ly").
Output: data-private/leads-daily.json {"2026-08-28": [ {ts,name,phone,needs,recipients}, ...], ...}
"""
import json
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

TZ = timezone(timedelta(hours=7))
HERE = Path(__file__).resolve().parent
DATA_DIR = HERE / "data-private"

with open("/tmp/leads-all-raw.json", encoding="utf-8") as f:
    leads = json.load(f)

by_day = defaultdict(list)
for l in leads:
    dt = datetime.fromtimestamp(l["ts"], TZ)
    day = dt.date().isoformat()
    by_day[day].append({
        "gio": dt.strftime("%H:%M"),
        "ten": l.get("company") or l.get("name") or "—",
        "sdt": l.get("phone") or "",
        "nhu_cau": l.get("needs") or "",
        "recipients": l.get("recipients") or "",
    })

for day in by_day:
    by_day[day].sort(key=lambda x: x["gio"], reverse=True)

DATA_DIR.mkdir(exist_ok=True)
out_path = DATA_DIR / "leads-daily.json"
out_path.write_text(json.dumps({
    "generated_at": datetime.now(TZ).isoformat(timespec="seconds"),
    "days": dict(by_day),
}, ensure_ascii=False), encoding="utf-8")
print(f"Đã lưu {out_path} — {len(by_day)} ngày, {len(leads)} lead tổng")
