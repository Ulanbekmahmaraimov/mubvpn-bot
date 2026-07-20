import logging
import os
import json
import httpx
import asyncio
import base64
import secrets
import urllib.parse
import threading
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

# --- ЖӨНДӨӨЛӨР ---
BOT_TOKEN    = "8400265569:AAHQ21_zNVS3XPDlMoE9I8TW0JwaIaUuA1s"
SUPPORT_URL  = "https://t.me/kl_mub"
FIREBASE_URL = "https://mubvpn-8b892-default-rtdb.firebaseio.com"
FIREBASE_SEC = "NgRNzmtQYdgUcFWXiDRPAHAsSURVni2WaIKTw9Re"

PLATEGA_MERCHANT_ID = "7daa1458-3248-4106-bc81-bfe7f33b742f"
PLATEGA_API_KEY     = "Ia6n9MgN172IKWWOGAzkfQveSZ4ZIq2ktTpkt5hiBNpCfbtrX4V4XLozuKarEB2OzkNEEfHDsaTZadGJhZUJ6He7AtQFGS0U6Lud"

MASTER_UUID = "2e922e6a-65db-4767-8216-a4b6b501b3b8"
SERVER_IP   = "167.235.22.54"
PBK         = "0CIqFJJXUoImvhH9fBIBBsW0G798Q9WpwWDdhbdw93M"
SID         = "7682624ec01fe9"
SNI         = "www.sony.com"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

PLANS = {
    "1m": {"ky": "1 ай", "ru": "1 месяц", "en": "1 month", "rub": 109.99},
    "3m": {"ky": "3 ай", "ru": "3 месяца", "en": "3 months", "rub": 309.99},
    "6m": {"ky": "6 ай", "ru": "6 месяцев", "en": "6 months", "rub": 599.99},
    "1y": {"ky": "1 жыл", "ru": "1 год", "en": "1 year", "rub": 1099.99},
}

STRINGS = {
    "ky": {
        "welcome": "🚀 <b>mubVPN — Эң тез жана коопсуз!</b>\n\n🌍 Чектөөсүз интернетке жол ачыңыз.\n⚡️ Жогорку ылдамдык (1 Гбит/с чейин).\n🛡 Коопсуздук жана купуялык.",
        "btn_pay": "💳 Сатып алуу", "btn_my_vpn": "🔑 Менин шилтемем", "btn_referral": "🎁 Акысыз Premium", "btn_download": "🚀 Жүктөө", "btn_support": "👨‍💻 Колдоо",
        "pay_text": "💳 Планды тандаңыз:", "back": "⬅️ Артка", "no_premium": "⚠️ Сизде Premium жок",
        "trial_msg": "🎁 Сизге 3 күндүк акысыз Premium берилди!\nШилтемеңиз:",
        "ref_text": "🎁 Досторду чакырып, +10 күн алыңыз!\nШилтемеңиз:\n<code>{link}</code>",
        "dl_text": "🚀 <b>mubVPN колдонмосун жүктөп алыңыз:</b>\n\n🤖 Android: <a href='https://play.google.com/store/apps/details?id=com.happproxy'>Happ Proxy</a>\n🍎 iOS: <a href='https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973'>Happ Proxy</a>",
        "pay_info": "💳 <b>{name} Premium</b>\n\nБаасы: {rub} RUB\n\nТөлөө үчүн төмөнкү баскычты басыңыз. Төлөмдөн кийин Premium автоматтык түрдө берилет."
    },
    "ru": {
        "welcome": "🚀 <b>mubVPN — Самый быстрый и безопасный!</b>\n\n🌍 Откройте доступ к свободному интернету.\n⚡️ Скорость до 1 Гбит/с.\n🛡 Полная приватность.",
        "btn_pay": "💳 Купить", "btn_my_vpn": "🔑 Моя ссылка", "btn_referral": "🎁 Бесплатный Premium", "btn_download": "🚀 Скачать", "btn_support": "👨‍💻 Поддержка",
        "pay_text": "💳 Выберите тариф:", "back": "⬅️ Назад", "no_premium": "⚠️ У вас нет Premium",
        "trial_msg": "🎁 Вам начислено 3 дня бесплатно!\nВаша ссылка:",
        "ref_text": "🎁 Приглашайте друзей и получайте +10 дней!\nСсылка:\n<code>{link}</code>",
        "dl_text": "🚀 <b>Скачать приложение mubVPN:</b>\n\n🤖 Android: <a href='https://play.google.com/store/apps/details?id=com.happproxy'>Happ Proxy</a>\n🍎 iOS: <a href='https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973'>Happ Proxy</a>",
        "pay_info": "💳 <b>{name} Premium</b>\n\nЦена: {rub} RUB\n\nНажмите кнопку ниже для оплаты. Premium активируется автоматически."
    }
}
# Fallback and other languages
for lang in ["en", "uz", "kk", "tg", "tr"]:
    STRINGS[lang] = STRINGS["ru"]

def get_main_kb(lang):
    L = STRINGS.get(lang, STRINGS["ky"])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(L["btn_download"], callback_data='dl_platforms')],
        [InlineKeyboardButton(L["btn_my_vpn"], callback_data='my_vpn')],
        [InlineKeyboardButton(L["btn_pay"], callback_data='pay_menu')],
        [InlineKeyboardButton(L["btn_referral"], callback_data='referral_menu')],
        [InlineKeyboardButton(L["btn_support"], url=SUPPORT_URL)]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{FIREBASE_URL}/telegram_to_uid/{tg_id}.json?auth={FIREBASE_SEC}")
            uid = r.json()
            if not uid:
                uid = secrets.token_urlsafe(12).replace('-', '')[:16]
                await client.put(f"{FIREBASE_URL}/telegram_to_uid/{tg_id}.json?auth={FIREBASE_SEC}", json=uid)

                # Check referral
                if context.args and context.args[0].startswith('ref_'):
                    inviter_uid = context.args[0].replace('ref_', '')
                    # Award inviter +10 days
                    inv_r = await client.get(f"{FIREBASE_URL}/users/{inviter_uid}.json?auth={FIREBASE_SEC}")
                    inv_data = inv_r.json()
                    if inv_data:
                        cur_exp = inv_data.get("premium_expiry")
                        now = datetime.now()
                        base_date = datetime.fromisoformat(cur_exp) if cur_exp and datetime.fromisoformat(cur_exp) > now else now
                        new_exp = (base_date + timedelta(days=10)).isoformat()
                        await client.patch(f"{FIREBASE_URL}/users/{inviter_uid}.json?auth={FIREBASE_SEC}", json={"premium_expiry": new_exp, "isPremium": True})
                        # Notify inviter
                        inv_tg = inv_data.get("telegram_id")
                        if inv_tg:
                            try: await context.bot.send_message(chat_id=inv_tg, text="🎁 Досуңуз чакырууну кабыл алды! Сизге <b>+10 күн</b> акысыз Premium берилди! 🎉", parse_mode=ParseMode.HTML)
                            except: pass

                expiry = (datetime.now() + timedelta(days=3)).isoformat()
                await client.patch(f"{FIREBASE_URL}/users/{uid}.json?auth={FIREBASE_SEC}", json={
                    "telegram_id": tg_id, "isPremium": True, "premium_expiry": expiry,
                    "trial_given": True, "vpn_uuid": MASTER_UUID, "created_at": datetime.now().isoformat()
                })
                context.user_data['just_reg'] = True

        context.user_data['uid'] = uid
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇰🇬 Кыргызча", callback_data='sl_ky'), InlineKeyboardButton("🇷🇺 Русский", callback_data='sl_ru')],
            [InlineKeyboardButton("🇺🇸 English", callback_data='sl_en'), InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data='sl_uz')],
            [InlineKeyboardButton("🇰🇿 Қазақша", callback_data='sl_kk'), InlineKeyboardButton("🇹🇯 Тоҷикӣ", callback_data='sl_tg')],
            [InlineKeyboardButton("🇹🇷 Türkçe", callback_data='sl_tr')]
        ])
        await update.message.reply_text("Тилди тандаңыз / Выберите язык / Choose language:", reply_markup=kb)
    except Exception as e: log.error(f"Start error: {e}")

async def handle_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    data = query.data; tg_id = query.from_user.id

    try:
        if 'uid' not in context.user_data:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{FIREBASE_URL}/telegram_to_uid/{tg_id}.json?auth={FIREBASE_SEC}")
                context.user_data['uid'] = r.json()

        uid = context.user_data.get('uid')
        lang = context.user_data.get('lang', 'ky')

        if data.startswith('sl_'):
            lang = data.split('_')[1]; context.user_data['lang'] = lang
            L = STRINGS.get(lang, STRINGS['ky'])
            await query.message.edit_text(L["welcome"], reply_markup=get_main_kb(lang), parse_mode=ParseMode.HTML)
            if context.user_data.get('just_reg'):
                app_url = os.environ.get('RENDER_EXTERNAL_URL', "https://mubvpn-bot-vy55.onrender.com")
                msg = L["trial_msg"]
                await context.bot.send_message(chat_id=tg_id, text=f"{msg}\n\n<code>{app_url}/s/{uid}</code>", parse_mode=ParseMode.HTML)
                context.user_data['just_reg'] = False

        elif data == 'my_vpn':
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{FIREBASE_URL}/users/{uid}.json?auth={FIREBASE_SEC}")
                user = r.json()
            L = STRINGS.get(lang, STRINGS['ky'])
            if user and user.get("isPremium"):
                app_url = os.environ.get('RENDER_EXTERNAL_URL', "https://mubvpn-bot-vy55.onrender.com")
                await query.message.edit_text(f"🔑 Шилтемеңиз / Ваша ссылка:\n<code>{app_url}/s/{uid}</code>", reply_markup=get_main_kb(lang), parse_mode=ParseMode.HTML)
            else: await query.message.edit_text(L["no_premium"], reply_markup=get_main_kb(lang))

        elif data == 'pay_menu':
            L = STRINGS.get(lang, STRINGS['ky'])
            kb = []
            for k, p in PLANS.items():
                name = p.get(lang, p['ky'])
                kb.append([InlineKeyboardButton(f"{name} — {p['rub']} RUB", callback_data=f'buy_{k}')])
            kb.append([InlineKeyboardButton(L["back"], callback_data='main_menu')])
            await query.message.edit_text(L["pay_text"], reply_markup=InlineKeyboardMarkup(kb))

        elif data.startswith('buy_'):
            plan_id = data.split('_')[1]
            plan = PLANS.get(plan_id)
            L = STRINGS.get(lang, STRINGS['ky'])
            try:
                async with httpx.AsyncClient() as client:
                    p_url = "https://app.platega.io/v2/transaction/process"
                    headers = {"X-MerchantId": PLATEGA_MERCHANT_ID, "X-Secret": PLATEGA_API_KEY, "Content-Type": "application/json"}
                    payload = {
                        "paymentMethod": 2, # SBP
                        "paymentDetails": {"amount": float(plan['rub']), "currency": "RUB"},
                        "description": f"mubVPN {plan_id} Premium",
                        "payload": f"{uid}:{plan_id}"
                    }
                    resp = await client.post(p_url, json=payload, headers=headers)
                    pay_link = resp.json().get("url")
                    if pay_link:
                        name = plan.get(lang, plan['ky'])
                        txt = L["pay_info"].format(name=name, rub=plan['rub'])
                        kb = [[InlineKeyboardButton("💳 Төлөө / Оплатить", url=pay_link)], [InlineKeyboardButton(L["back"], callback_data='pay_menu')]]
                        await query.message.edit_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
                    else: await query.message.edit_text("Error creating payment link.", reply_markup=get_main_kb(lang))
            except: await query.message.edit_text("Payment service error.", reply_markup=get_main_kb(lang))

        elif data == 'main_menu':
            L = STRINGS.get(lang, STRINGS['ky'])
            await query.message.edit_text(L["welcome"], reply_markup=get_main_kb(lang), parse_mode=ParseMode.HTML)

        elif data == 'referral_menu':
            bot_info = await context.bot.get_me()
            link = f"https://t.me/{bot_info.username}?start=ref_{uid}"
            L = STRINGS.get(lang, STRINGS['ky'])
            await query.message.edit_text(L["ref_text"].format(link=link), reply_markup=get_main_kb(lang), parse_mode=ParseMode.HTML)

        elif data == 'dl_platforms':
            L = STRINGS.get(lang, STRINGS['ky'])
            await query.message.edit_text(L["dl_text"], reply_markup=get_main_kb(lang), parse_mode=ParseMode.HTML)
    except Exception as e: log.error(f"CB Error: {e}")

# --- WEB SERVER ---
class BotHandler(BaseHTTPRequestHandler):
    def do_HEAD(self): self.send_response(200); self.end_headers()
    def do_GET(self):
        if self.path.startswith('/s/'):
            uid = self.path.split('/')[2]
            ua = self.headers.get('User-Agent', '').lower()
            is_app = any(x in ua for x in ['v2ray', 'clash', 'shadowrocket', 'happ', 'dart', 'okhttp'])
            sub_url = f"https://{self.headers.get('Host')}/s/{uid}"
            config = f"vless://{MASTER_UUID}@{SERVER_IP}:8443?encryption=none&flow=xtls-rprx-vision&type=tcp&security=reality&sni={SNI}&fp=chrome&pbk={PBK}&sid={SID}#mubVPN_Premium"
            if is_app:
                self.send_response(200); self.send_header('Content-Type', 'text/plain')
                self.end_headers(); b64 = base64.b64encode(config.encode()).decode()
                self.wfile.write(b64.encode()); return
            else:
                qr = urllib.parse.quote(sub_url)
                html = f"<html><body style='background:#000;color:white;text-align:center;font-family:sans-serif;padding:50px;'><h1>mubVPN Premium</h1><img src='https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={qr}'><br><br><code>{sub_url}</code><br><br><a href='v2rayng://install-config?url={sub_url}' style='display:block;padding:15px;background:#4facfe;color:black;text-decoration:none;border-radius:10px;font-weight:bold;'>Import to mubVPN</a></body></html>"
                self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers(); self.wfile.write(html.encode()); return
        self.send_response(200); self.end_headers(); self.wfile.write(b"mubVPN Bot Active")

def run_server():
    port = int(os.environ.get('PORT', 8080))
    HTTPServer(('0.0.0.0', port), BotHandler).serve_forever()

def keep_alive():
    app_url = os.environ.get('RENDER_EXTERNAL_URL')
    if not app_url: return
    while True:
        try: requests.get(app_url, timeout=10)
        except: pass
        threading.Event().wait(600)

def main():
    threading.Thread(target=run_server, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_cb))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__": main()
