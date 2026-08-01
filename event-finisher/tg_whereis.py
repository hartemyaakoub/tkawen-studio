# -*- coding: utf-8 -*-
"""Prove exactly which Telegram chat received the deliveries."""
import json, urllib.parse, urllib.request

ENVP = r"C:\Users\YAAKOUB DEV\tkawen-remote-bot\bot.env"
d = {}
for line in open(ENVP, encoding="utf-8-sig"):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        d[k.strip()] = v.strip().strip('"').strip("'")
TOKEN, CHAT = d["TKAWEN_BOT_TOKEN"], d["TKAWEN_OWNER_CHAT_ID"]


def call(method, **params):
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TOKEN}/{method}",
        data=urllib.parse.urlencode(params).encode())
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


me = call("getMe")["result"]
print("bot      :", "@" + me["username"], "| id", me["id"])
chat = call("getChat", chat_id=CHAT).get("result", {})
print("chat_id  :", CHAT)
print("recipient:", chat.get("first_name", ""), chat.get("last_name", ""),
      "| @" + str(chat.get("username")), "| type", chat.get("type"))

r = call("sendMessage", chat_id=CHAT, parse_mode="HTML", text=(
    "\U0001F4CD <b>فهرس ما أُرسل اليوم في هذه المحادثة</b>\n\n"
    "1. ألبوم: قبل/بعد + بطاقة داكنة + بطاقة فاتحة + ستوري\n"
    "2. ملفّ: لوحة 92 بطاقة\n"
    "3. ألبوم: 9 بطاقات عيّنة\n"
    "4. ألبوم: تصحيح اللون (v1 مقابل v2) + صورتان + بطاقة بـQR\n"
    "5. فيديو: <b>فيلم التخرّج 68 ثانية</b>\n"
    "6. ملفّ: لوحة 92 بطاقة (النسخة النهائيّة بـQR)\n\n"
    "كلّها هنا — مرّر لأعلى في هذه المحادثة نفسها.\n"
    "والأصل الكامل على الحاسوب في <code>D:\\f05\\_out</code>"))
print("index message_id:", r["result"]["message_id"], "-> chat",
      r["result"]["chat"]["id"], r["result"]["chat"].get("first_name", ""))
