#!/bin/bash
# Chay hang ngay TRUOC 15h00: keo du lieu moi (SaleOrder API, Leads, CRM activity
# tu file da tai), gop + ma hoa + push dashboard - de link dashboard trong mail
# tong hop (09-crm-sales/daily_sales_digest.py, gui luc 15h00 qua launchd rieng
# com.icd.daily-sales-digest) luon co du lieu moi nhat cua NGAY DANG BAO CAO khi
# nguoi nhan bam vao xem. Email KHONG gui tu script nay nua (rule Hieu 2026-08-29:
# gop con so CRM/Huyen/Trang/Ly/Lead vao 1 mail duy nhat - xem daily_sales_digest.py).
set -e
cd "$(dirname "$0")"

PY=/opt/anaconda3/bin/python3
HUYEN_TRANG_DIR="../09-crm-sales/bao-cao-icd-misa/Huyen_Trang"
NHAT_KY_DIR="../09-crm-sales/nhat-ky-truy-cap"

echo "=== $(date) - Bat dau daily pipeline ==="

echo "--- SaleOrder (Huyen/Trang) tu MISA API ---"
(cd "$HUYEN_TRANG_DIR" && "$PY" gen_saleorder_daily.py) || echo "[WARN] gen_saleorder_daily.py loi, dung du lieu cu"

echo "--- Leads tu leads.db (qua ssh) ---"
ssh -i ~/.ssh/icd_vps_automation -o ConnectTimeout=10 root@45.251.115.47 "cd /opt/icd-chatbot && python3 -c \"
import leads_store, json
from datetime import datetime, timezone, timedelta
TZ = timezone(timedelta(hours=7))
start = datetime(2020,1,1, tzinfo=TZ).timestamp()
end = datetime(2030,1,1, tzinfo=TZ).timestamp()
leads = leads_store.list_leads(start, end)
print(json.dumps(leads, ensure_ascii=False))
\"" > /tmp/leads-all-raw.json 2>/tmp/leads-pipeline-err.log || echo "[WARN] Khong keo duoc leads qua ssh"
"$PY" gen_leads_daily.py || echo "[WARN] gen_leads_daily.py loi, dung du lieu cu"

echo "--- CRM activity tu file da tai (neu co file moi) ---"
(cd "$NHAT_KY_DIR" && "$PY" gen_daily_archive.py) || echo "[WARN] gen_daily_archive.py loi, dung du lieu cu"

echo "--- Gop + ma hoa + push dashboard ---"
"$PY" collect_and_push.py

echo "=== $(date) - Xong (email gui rieng luc 15h00 qua daily_sales_digest.py) ==="
