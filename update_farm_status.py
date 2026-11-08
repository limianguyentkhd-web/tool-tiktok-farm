import json
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import sys

sys.stdout.reconfigure(encoding='utf-8')

MAPPING = [
    {
        "serial": "9889da304447393259",
        "username": "user91630728678294",
        "pass": "@L42bvieWIrygp",
        "email": "pnbuohvf4532@primehubcloud.com",
        "proxy": "160.250.185.49:14102:ntnKhj:oExYql",
        "status": "Đã đăng nhập TikTok (Live)"
    },
    {
        "serial": "988a17344c564b5657",
        "username": "user84009697968164",
        "pass": "@L88jTPasitdUg",
        "email": "dluvzhltaf7199@megacloudx.com",
        "proxy": "160.250.166.242:22393:ntnKhj:oExYql",
        "status": "Đã đăng nhập TikTok (Live)"
    },
    {
        "serial": "ce01182188dbdcee0c",
        "username": "user3607950285377",
        "pass": "@L63aGrj5m9POZ",
        "email": "hmpqybusgl4490@trustlark.com",
        "proxy": "160.250.183.232:30546:ntnKhj:oExYql",
        "status": "Đã đăng nhập TikTok (Live)"
    },
    {
        "serial": "ce011821c38b263b05",
        "username": "user5878212175691",
        "pass": "@L206ThnU0ortn",
        "email": "lcqskhcot3161@primehubcloud.com",
        "proxy": "160.30.191.96:18817:ntnKhj:oExYql",
        "status": "Đã đăng nhập TikTok (Live)"
    },
    {
        "serial": "ce011821c45dc4060c",
        "username": "user1251955152358",
        "pass": "@L65rnkDswvCwq",
        "email": "kehysptsc3316@trustlark.com",
        "proxy": "157.15.38.228:30096:ntnKhj:oExYql",
        "status": "Đã đăng nhập TikTok (Live)"
    }
]

# 1. Update JSON
with open('d:/TOOL TIKTOK/tai_khoan_farm.json', 'r', encoding='utf-8') as f:
    farm = json.load(f)

for m in MAPPING:
    for item in farm:
        if item.get("serial") == m["serial"]:
            item["username"] = m["username"]
            item["login_user"] = m["username"]
            item["login_pass"] = m["pass"]
            item["recovery_email"] = m["email"]
            item["proxy"] = m["proxy"]
            item["status"] = m["status"]

with open('d:/TOOL TIKTOK/tai_khoan_farm.json', 'w', encoding='utf-8') as f:
    json.dump(farm, f, ensure_ascii=False, indent=2)

print("[✓] Đã cập nhật xong tai_khoan_farm.json")

# 2. Update Excel
excel_path = r"d:\TOOL TIKTOK\danh_sach_nick_tiktok.xlsx"
wb = openpyxl.load_workbook(excel_path)
ws = wb.active

# Ensure header has Serial column
if ws.cell(row=1, column=9).value != "Máy Serial gán":
    ws.cell(row=1, column=9).value = "Máy Serial gán"
    ws.cell(row=1, column=9).font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    ws.cell(row=1, column=9).fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    ws.cell(row=1, column=9).alignment = Alignment(horizontal="center", vertical="center")
    ws.column_dimensions["I"].width = 24

for row in range(2, ws.max_row + 1):
    u = ws.cell(row=row, column=2).value
    for m in MAPPING:
        if u == m["username"]:
            ws.cell(row=row, column=8).value = "Đã đăng nhập TikTok (Có Proxy)"
            ws.cell(row=row, column=8).font = Font(name="Calibri", size=10, bold=True, color="006100")
            ws.cell(row=row, column=9).value = m["serial"]
            ws.cell(row=row, column=9).alignment = Alignment(horizontal="center", vertical="center")

wb.save(excel_path)
print("[✓] Đã cập nhật xong danh_sach_nick_tiktok.xlsx")
