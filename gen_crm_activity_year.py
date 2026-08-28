"""Build bao cao "So hoat dong CRM - Ca nam 2026" tu .crm-activity-monthly.json
(da pull ve /tmp/crm-activity-monthly.json qua ssh). Khong gui email, chi luu snapshot.
"""
import json
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

TZ = timezone(timedelta(hours=7))
HERE = Path(__file__).resolve().parent

with open("/tmp/crm-activity-monthly.json", encoding="utf-8") as f:
    store = json.load(f)

months = sorted(store.keys())
total_all = 0
month_blocks = ""
staff_total_all = defaultdict(int)

for month_key in months:
    people = store[month_key]
    month_total = 0
    rows = ""
    for name, info in sorted(people.items(), key=lambda x: -sum(x[1]["days"].values())):
        days = info["days"]
        person_total = sum(days.values())
        month_total += person_total
        staff_total_all[f"{name} ({info.get('dept','—')})"] += person_total
        day_list = ", ".join(f"{d[8:10]}/{d[5:7]}: {c}" for d, c in sorted(days.items()))
        rows += f"""<tr>
            <td style='padding:6px 12px;border-bottom:1px solid #eee;font-weight:bold'>{name}</td>
            <td style='padding:6px 12px;border-bottom:1px solid #eee;font-size:12px;color:#777'>{info.get('dept','—')}</td>
            <td style='padding:6px 12px;border-bottom:1px solid #eee;text-align:center;font-weight:bold;color:#1a5fa8'>{person_total}</td>
            <td style='padding:6px 12px;border-bottom:1px solid #eee;font-size:11.5px;color:#888'>{day_list}</td>
        </tr>"""
    total_all += month_total
    month_blocks += f"""
    <div style='padding:16px 24px;border:1px solid #dde4f5;border-top:none'>
        <h3 style='color:#1a5fa8;margin:0 0 12px'>Tháng {month_key} <span style='font-weight:normal;font-size:13px;color:#888'>· {month_total} lượt truy cập</span></h3>
        <table style='width:100%;border-collapse:collapse;font-size:13px'>
            <tr style='background:#1a5fa8;color:white'>
                <th style='padding:8px 12px;text-align:left'>Nhân viên</th>
                <th style='padding:8px 12px;text-align:left'>Phòng ban</th>
                <th style='padding:8px 12px;text-align:center'>Tổng lượt</th>
                <th style='padding:8px 12px;text-align:left'>Chi tiết theo ngày</th>
            </tr>
            {rows}
        </table>
    </div>"""

staff_html = ""
for s, c in sorted(staff_total_all.items(), key=lambda x: -x[1]):
    staff_html += f"""<tr>
        <td style='padding:6px 12px;border-bottom:1px solid #eee'>{s}</td>
        <td style='padding:6px 12px;border-bottom:1px solid #eee;text-align:center;font-weight:bold'>{c}</td>
    </tr>"""

note = (f"Dữ liệu từ tháng {months[0]} (thời điểm hệ thống bắt đầu ghi nhận nhật ký truy cập CRM) đến nay."
        if months else "Chưa có dữ liệu.")

html = f"""
<html><body style='font-family:Arial,sans-serif;color:#333;max-width:980px;margin:0 auto'>
<div style='background:#1a5fa8;padding:16px 24px;border-radius:6px 6px 0 0'>
    <h2 style='color:white;margin:0'>Số hoạt động CRM — Cả năm 2026</h2>
    <p style='color:#cce0ff;margin:4px 0 0;font-size:13px'>{note}</p>
</div>
<div style='background:#f0f4ff;padding:16px 24px;border:1px solid #dde4f5;text-align:center'>
    <div style='font-size:32px;font-weight:bold;color:#1a5fa8'>{total_all}</div>
    <div style='font-size:13px;color:#666'>Tổng lượt truy cập CRM (toàn bộ nhân viên, cả năm)</div>
</div>
<div style='padding:16px 24px;border:1px solid #dde4f5;border-top:none'>
    <h3 style='color:#27ae60;margin:0 0 12px'>Tổng theo nhân viên (cả năm)</h3>
    <table style='width:100%;border-collapse:collapse;font-size:13px;max-width:520px'>
        <tr style='background:#27ae60;color:white'><th style='padding:8px 12px;text-align:left'>Nhân viên</th><th style='padding:8px 12px;text-align:center'>Tổng lượt</th></tr>
        {staff_html}
    </table>
</div>
{month_blocks}
<div style='padding:12px 24px;font-size:11px;color:#999;text-align:center'>Dashboard nội bộ ICD Việt Nam — dữ liệu tự động, không gửi qua email.</div>
</body></html>
"""

out_dir = HERE / "snapshots"
out_dir.mkdir(exist_ok=True)
(out_dir / "crm-activity-year.json").write_text(
    json.dumps({"subject": "Số hoạt động CRM - Cả năm 2026", "html": html,
                "updated_at": datetime.now(TZ).isoformat(timespec="seconds")}, ensure_ascii=False),
    encoding="utf-8",
)
print(f"Đã lưu crm-activity-year.json ({len(html)} ký tự, tổng {total_all} lượt)")
