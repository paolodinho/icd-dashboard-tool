// build-enc.mjs — Mã hóa data-private/dashboard.json (4 báo cáo sales hàng ngày)
// thành data-enc.json (an toàn để đưa lên repo public + GitHub Pages).
// Dùng: DASH_PASS="matkhau" node build-enc.mjs
// Bản mã AES-256-GCM, khóa dẫn xuất PBKDF2-SHA256 250k vòng. Không có mật khẩu = không giải ra được.
// Mẫu sao chép nguyên xi từ 08-tools/quote-generator/build-enc.mjs (đã chạy thật, đã audit bảo mật).
import fs from "fs";
import crypto from "crypto";
import path from "path";
import { fileURLToPath } from "url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
let PASS = process.env.DASH_PASS;
if (!PASS) {
  const pf = path.join(HERE, "data-private", ".enc-pass");
  if (fs.existsSync(pf)) PASS = fs.readFileSync(pf, "utf8").trim();
}
if (!PASS || PASS.length < 4) { console.error("Thiếu mật khẩu (DASH_PASS hoặc data-private/.enc-pass)."); process.exit(1); }

const dataPath = path.join(HERE, "data-private", "dashboard.json");
if (!fs.existsSync(dataPath)) { console.error(`Thiếu ${dataPath} — chạy collect_and_push.py trước.`); process.exit(1); }
const payload = fs.readFileSync(dataPath, "utf8");

const ITER = 250000;
const salt = crypto.randomBytes(16);
const iv = crypto.randomBytes(12);
const key = crypto.pbkdf2Sync(PASS, salt, ITER, 32, "sha256");
const cipher = crypto.createCipheriv("aes-256-gcm", key, iv);
const ct = Buffer.concat([cipher.update(payload, "utf8"), cipher.final()]);
const tag = cipher.getAuthTag();

const out = {
  v: 1, iter: ITER,
  salt: salt.toString("base64"),
  iv: iv.toString("base64"),
  ct: Buffer.concat([ct, tag]).toString("base64"),
};
fs.writeFileSync(path.join(HERE, "data-enc.json"), JSON.stringify(out));
console.log(`Mã hóa xong -> data-enc.json (${Math.round(out.ct.length/1024)}KB base64).`);
