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

MASTER_UUID = "2e922e6a-65db-4767-8216-a4b6b501b3b8"
SERVER_IP   = "167.235.22.54"
PBK         = "0CIqFJJXUoImvhH9fBIBBsW0G798Q9WpwWDdhbdw93M"
SID         = "7682624ec01fe9"
SNI         = "www.sony.com"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

# --- ТЕКСТТЕР (7 ТИЛ) ---
STRINGS = {
    "ky": {
        "welcome": "🚀 <b>mubVPN — Эң тез жана коопсуз!</b>\n\n🌍 Чектөөсүз интернетке жол ачыңыз.",
        "btn_pay": "💳 Сатып алуу", "btn_my_vpn": "🔑 Менин шилтемем", "btn_referral": "🎁 Акысыз Premium", "btn_download": "🚀 Жүктөө", "btn_support": "👨‍💻 Колдоо",
        "pay_text": "💳 Планды тандаңыз:", "back": "⬅️ Артка", "no_premium": "⚠️ Premium жок",
        "trial_msg": "🎁 Сизге 3 күндүк акысыз Premium берилди!\nШилтемеңиз:",
        "ref_text": "🎁 Досторду чакырып, +10 күн алыңыз!\nШилтемеңиз:\n<code>{link}</code>",
        "dl_text": "🚀 <b>mubVPN колдонмосун жүктөп алыңыз:</b>\n\n🤖 Android: <a href='https://play.google.com/store/apps/details?id=com.happproxy'>Happ Proxy</a>\n🍎 iOS: <a href='https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973'>Happ Proxy</a>"
    },
    "ru": {
        "welcome": "🚀 <b>mubVPN — Самый быстрый и безопасный!</b>\n\n🌍 Свободный интернет.",
        "btn_pay": "💳 Купить", "btn_my_vpn": "🔑 Моя ссылка", "btn_referral": "🎁 Бесплатный Premium", "btn_download": "🚀 Скачать", "btn_support": "👨‍💻 Поддержка",
        "pay_text": "💳 Выберите тариф:", "back": "⬅️ Назад", "no_premium": "⚠️ Нет Premium",
        "trial_msg": "🎁 Вам начислено 3 дня бесплатно!\nСсылка:",
        "ref_text": "🎁 Приглашайте друзей и получайте +10 дней!\nСсылка:\n<code>{link}</code>",
        "dl_text": "🚀 <b>Скачать приложение mubVPN:</b>\n\n🤖 Android: <a href='https://play.google.com/store/apps/details?id=com.happproxy'>Happ Proxy</a>\n🍎 iOS: <a href='https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973'>Happ Proxy</a>"
    },
    "en": {"welcome": "🚀 <b>mubVPN — Fast & Safe!</b>", "btn_pay": "💳 Buy", "btn_my_vpn": "🔑 My Link", "btn_referral": "🎁 Free Premium", "btn_download": "🚀 Download", "btn_support": "👨‍💻 Support", "pay_text": "Choose plan:", "back": "⬅️ Back", "no_premium": "No Premium", "trial_msg": "3 days trial granted!", "ref_text": "Link: {link}", "dl_text": "Download App: Happ Proxy"},
    "uz": {"welcome": "🚀 <b>mubVPN — Tez va xavfsiz!</b>", "btn_pay": "💳 Sotib olish", "btn_my_vpn": "🔑 Mening havolam", "btn_referral": "🎁 Bepul Premium", "btn_download": "🚀 Yuklash", "btn_support": "👨‍💻 Yordam", "pay_text": "Tarifni tanlang:", "back": "⬅️ Orqaga", "no_premium": "Premium yo'q", "trial_msg": "3 kunlik trial berildi!", "ref_text": "Havola: {link}", "dl_text": "Ilovani yuklang: Happ Proxy"},
    "kk": {"welcome": "🚀 <b>mubVPN — Жылдам және қауіпсіз!</b>", "btn_pay": "💳 Сатып алу", "btn_my_vpn": "🔑 Менің сілтемем", "btn_referral": "🎁 Тегін Premium", "btn_download": "🚀 Жүктеу", "btn_support": "👨‍💻 Қолдау", "pay_text": "Тариф таңдаңыз:", "back": "⬅️ Артқа", "no_premium": "Premium жоқ", "trial_msg": "3 күндік тегін Premium берилди!", "ref_text": "Сілтеме: {link}", "dl_text": "Жүктеу: Happ Proxy"},
    "tg": {"welcome": "🚀 <b>mubVPN — Зуд ва бехатар!</b>", "btn_pay": "💳 Харидан", "btn_my_vpn": "🔑 Истиноди ман", "btn_referral": "🎁 Premium-и ройгон", "btn_download": "🚀 Боргирӣ", "btn_support": "👨‍💻 Дастгирӣ", "pay_text": "Тарифро интихоб кунед:", "back": "⬅️ Ба ақиб", "no_premium": "Premium надоред", "trial_msg": "3 рӯз ройгон дода шуд!", "ref_text": "Истинод: {link}", "dl_text": "Боргирӣ: Happ Proxy"},
    "tr": {"welcome": "🚀 <b>mubVPN — Hızlı ve Güvenli!</b>", "btn_pay": "💳 Satın Al", "btn_my_vpn": "🔑 Benim Linkim", "btn_referral": "🎁 Ücretsiz Premium", "btn_download": "🚀 Иndir", "btn_support": "👨‍💻 Destek", "pay_text": "Plan seçin:", "back": "⬅️ Geri", "no_premium": "Premium yok", "trial_msg": "3 günlük ücretsiz Premium verildi!", "ref_text": "Link: {link}", "dl_text": "İndir: Happ Proxy"}
}

def get_main_kb(lang):
    L = STRINGS.get(lang, STRINGS["ru"])
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
        if update.message:
            await update.message.reply_text("Выберите язык / Тилди тандаңыз:", reply_markup=kb)
    except Exception as e:
        log.error(f"Start error: {e}")

async def handle_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    data = query.data; tg_id = query.from_user.id

    # UIDти базадан кайра текшерүү (коопсуздук үчүн)
    if 'uid' not in context.user_data:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{FIREBASE_URL}/telegram_to_uid/{tg_id}.json?auth={FIREBASE_SEC}")
            context.user_data['uid'] = r.json()

    uid = context.user_data.get('uid')
    lang = context.user_data.get('lang', 'ru')

    if data.startswith('sl_'):
        lang = data.split('_')[1]; context.user_data['lang'] = lang
        L = STRINGS.get(lang, STRINGS['ru'])
        await query.message.edit_text(L["welcome"], reply_markup=get_main_kb(lang), parse_mode=ParseMode.HTML)
        if context.user_data.get('just_reg'):
            app_url = os.environ.get('RENDER_EXTERNAL_URL', "https://mubvpn-bot-vy55.onrender.com")
            await context.bot.send_message(chat_id=tg_id, text=f"{L['trial_msg']}\n\n<code>{app_url}/s/{uid}</code>", parse_mode=ParseMode.HTML)
            context.user_data['just_reg'] = False

    elif data == 'my_vpn':
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{FIREBASE_URL}/users/{uid}.json?auth={FIREBASE_SEC}")
            user = r.json()
        if user and user.get("isPremium"):
            app_url = os.environ.get('RENDER_EXTERNAL_URL', "https://mubvpn-bot-vy55.onrender.com")
            await query.message.edit_text(f"🔑 Шилтемеңиз:\n<code>{app_url}/s/{uid}</code>", reply_markup=get_main_kb(lang), parse_mode=ParseMode.HTML)
        else:
            await query.message.edit_text(STRINGS[lang]["no_premium"], reply_markup=get_main_kb(lang))

    elif data == 'referral_menu':
        bot_info = await context.bot.get_me()
        link = f"https://t.me/{bot_info.username}?start=ref_{uid}"
        await query.message.edit_text(STRINGS[lang]["ref_text"].format(link=link), reply_markup=get_main_kb(lang), parse_mode=ParseMode.HTML)

    elif data == 'dl_platforms':
        await query.message.edit_text(STRINGS[lang]["dl_text"], reply_markup=get_main_kb(lang), parse_mode=ParseMode.HTML)

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
        self.send_response(200); self.end_headers(); self.wfile.write(b"Active")

def run_server():
    port = int(os.environ.get('PORT', 8080))
    HTTPServer(('0.0.0.0', port), BotHandler).serve_forever()

def main():
    threading.Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_cb))
    log.info("🤖 Bot starting...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
