"""Build bao cao "Khach hang chuyen sales - Ca nam 2026" tu du lieu leads.db tren VPS
(da pull ve /tmp/leads-2026-raw.json qua ssh, xem lenh chay kem). Khong gui email,
chi luu snapshot cho dashboard-noi-bo.
"""
import json
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

TZ = timezone(timedelta(hours=7))
HERE = Path(__file__).resolve().parent

with open("/tmp/leads-2026-raw.json", encoding="utf-8") as f:
    leads = json.load(f)

by_month = defaultdict(int)
by_staff = defaultdict(int)
rows = []
for l in leads:
    dt = datetime.fromtimestamp(l["ts"], TZ)
    month_key = dt.strftime("%Y-%m")
    by_month[month_key] += 1
    for r in [x.strip() for x in (l.get("recipients") or "").split(",") if x.strip()]:
        by_staff[r] += 1
    rows.append((dt, l))

rows.sort(key=lambda x: x[0], reverse=True)

months_html = ""
for m in sorted(by_month.keys()):
    months_html += f"""<tr>
        <td style='padding:6px 12px;border-bottom:1px solid #eee;font-weight:bold'>{m}</td>
        <td style='padding:6px 12px;border-bottom:1px solid #eee;text-align:center'>{by_month[m]}</td>
    </tr>"""

staff_html = ""
for s, c in sorted(by_staff.items(), key=lambda x: -x[1]):
    staff_html += f"""<tr>
        <td style='padding:6px 12px;border-bottom:1px solid #eee'>{s}</td>
        <td style='padding:6px 12px;border-bottom:1px solid #eee;text-align:center'>{c}</td>
    </tr>"""

detail_html = ""
for dt, l in rows:
    ten = l.get("company") or l.get("name") or "—"
    detail_html += f"""<tr>
        <td style='padding:5px 10px;border-bottom:1px solid #f0f0f0;white-space:nowrap;font-size:12.5px;color:#666'>{dt.strftime('%d/%m/%Y %H:%M')}</td>
        <td style='padding:5px 10px;border-bottom:1px solid #f0f0f0'>{ten}</td>
        <td style='padding:5px 10px;border-bottom:1px solid #f0f0f0'>{l.get('phone') or '—'}</td>
        <td style='padding:5px 10px;border-bottom:1px solid #f0f0f0;font-size:12.5px;color:#555'>{l.get('needs') or '—'}</td>
        <td style='padding:5px 10px;border-bottom:1px solid #f0f0f0;font-size:12.5px'>{l.get('recipients') or '—'}</td>
    </tr>"""

first_dt = min(dt for dt, _ in rows) if rows else None
note = (f"Dữ liệu từ {first_dt.strftime('%d/%m/%Y')} (thời điểm hệ thống bắt đầu ghi nhận) đến nay — "
        "chưa có dữ liệu trước mốc này." if first_dt else "Chưa có dữ liệu.")

html = f"""
<html><body style='font-family:Arial,sans-serif;color:#333;max-width:980px;margin:0 auto'>
<div style='background:#1a5fa8;padding:16px 24px;border-radius:6px 6px 0 0'>
    <h2 style='color:white;margin:0'>Khách hàng chuyển sales — Cả năm 2026</h2>
    <p style='color:#cce0ff;margin:4px 0 0;font-size:13px'>{note}</p>
</div>
<div style='background:#f0f4ff;padding:16px 24px;border:1px solid #dde4f5;text-align:center'>
    <div style='font-size:32px;font-weight:bold;color:#1a5fa8'>{len(leads)}</div>
    <div style='font-size:13px;color:#666'>Tổng khách hàng đã chuyển cho nhân viên (đã gộp trùng theo khách)</div>
</div>
<div style='padding:16px 24px;border:1px solid #dde4f5;border-top:none'>
    <h3 style='color:#1a5fa8;margin:0 0 12px'>Theo tháng</h3>
    <table style='width:100%;border-collapse:collapse;font-size:13px;max-width:320px'>
        <tr style='background:#1a5fa8;color:white'><th style='padding:8px 12px;text-align:left'>Tháng</th><th style='padding:8px 12px;text-align:center'>Số khách</th></tr>
        {months_html}
    </table>
</div>
<div style='padding:16px 24px;border:1px solid #dde4f5;border-top:none'>
    <h3 style='color:#27ae60;margin:0 0 12px'>Theo nhân viên nhận</h3>
    <table style='width:100%;border-collapse:collapse;font-size:13px;max-width:420px'>
        <tr style='background:#27ae60;color:white'><th style='padding:8px 12px;text-align:left'>Nhân viên</th><th style='padding:8px 12px;text-align:center'>Số khách</th></tr>
        {staff_html}
    </table>
</div>
<div style='padding:16px 24px;border:1px solid #dde4f5;border-top:none'>
    <h3 style='color:#8e44ad;margin:0 0 12px'>Chi tiết toàn bộ ({len(leads)} khách, mới nhất trước)</h3>
    <table style='width:100%;border-collapse:collapse'>
        <tr style='background:#8e44ad;color:white'>
            <th style='padding:8px 10px;text-align:left'>Thời gian</th>
            <th style='padding:8px 10px;text-align:left'>Khách hàng</th>
            <th style='padding:8px 10px;text-align:left'>SĐT</th>
            <th style='padding:8px 10px;text-align:left'>Nhu cầu</th>
            <th style='padding:8px 10px;text-align:left'>Chuyển cho</th>
        </tr>
        {detail_html}
    </table>
</div>
<div style='padding:12px 24px;font-size:11px;color:#999;text-align:center'>Dashboard nội bộ ICD Việt Nam — dữ liệu tự động, không gửi qua email.</div>
</body></html>
"""

out_dir = HERE / "snapshots"
out_dir.mkdir(exist_ok=True)
(out_dir / "leads-year.json").write_text(
    json.dumps({"subject": "Khách hàng chuyển sales - Cả năm 2026", "html": html,
                "updated_at": datetime.now(TZ).isoformat(timespec="seconds")}, ensure_ascii=False),
    encoding="utf-8",
)
print(f"Đã lưu leads-year.json ({len(html)} ký tự, {len(leads)} khách)")
