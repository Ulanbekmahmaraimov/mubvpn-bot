import logging
import os
import json
import requests
import threading
import html
import urllib.parse
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

# --- CONFIG ---
BOT_TOKEN    = "8400265569:AAHQ21_zNVS3XPDlMoE9I8TW0JwaIaUuA1s"
LAVA_API     = "cUPUZBNvxATjd5ou8oodPIozLGb7dqzZx5eDYdYbkctCV9eRJBaDWpJKAkp8Bp8m"
SUPPORT_URL  = "https://t.me/kl_mub"
LAVA_MAIN_URL = "https://app.lava.top/products/db3d18c8-01e5-40f2-bf0a-e01842697312/8a98aa1a-78d0-4291-bf1e-6c143668cf15?currency=RUB"
FIREBASE_DB_URL    = "https://mubvpn-8b892-default-rtdb.firebaseio.com"
FIREBASE_DB_SECRET = "NgRNzmtQYdgUcFWXiDRPAHAsSURVni2WaIKTw9Re"
WELCOME_PHOTO      = "https://raw.githubusercontent.com/Ulanbekmahmaraimov/mubvpn-bot/main/assets/preview.png"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

# --- HELPERS ---
def firebase_set_premium(uid: str, months: int) -> bool:
    try:
        expiry = (datetime.now() + timedelta(days=months * 30)).isoformat()
        url = f"{FIREBASE_DB_URL}/users/{uid}.json?auth={FIREBASE_DB_SECRET}"
        resp = requests.patch(url, json={"premium_expiry": expiry, "is_paid": True})
        return resp.status_code == 200
    except Exception as e:
        log.error(f"Firebase error: {e}"); return False

# --- STRINGS ---
STRINGS = {
    "ky": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nЭң тез жана коопсуз интернетке жол ачыңыз. Төлөм жүргүзүү же тиркемени жүктөө үчүн төмөнкү баскычтарды колдонуңуз:",
        "btn_pay": "💳 Сатып алуу", "btn_how": "📖 Кантип төлөйм?", "btn_download": "🚀 Тиркемени жүктөө", "btn_support": "👨‍💻 Колдоо", "btn_share": "🤝 Бөлүшүү",
        "pay_text": "💳 <b>Төлөөгө өтүү</b>\n\nТөлөм Telegram ичинде коопсуз өтөт:", "pay_btn_link": "💳 Telegram", "back": "⬅️ Артка", "next": "Кийинки ➡️",
        "share_title": "🤝 <b>Бөлүшүү:</b>", "btn_share_now": "📲 Бөлүшүү", "share_msg": "🚀 mubVPN — Android үчүн эң тез жана коопсуз VPN!"
    },
    "ru": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nОткройте доступ к самому быстрому и безопасному интернету:",
        "btn_pay": "💳 Купить", "btn_how": "📖 Как оплатить?", "btn_download": "🚀 Скачать", "btn_support": "👨‍💻 Поддержка", "btn_share": "🤝 Поделиться",
        "pay_text": "💳 <b>Переход к оплате</b>", "pay_btn_link": "💳 Оплатить", "back": "⬅️ Назад", "next": "Далее ➡️",
        "share_title": "🤝 <b>Поделиться:</b>", "btn_share_now": "📲 Поделиться", "share_msg": "🚀 mubVPN — Самый быстрый VPN!"
    },
    "uz": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nEng tezkor va xavfsiz internet:",
        "btn_pay": "💳 Sotib olish", "btn_how": "📖 Qanday to'lash?", "btn_download": "🚀 Yuklab olish", "btn_support": "👨‍💻 Yordam", "btn_share": "🤝 Ulashish",
        "pay_text": "💳 <b>To'lovga o'tish</b>", "pay_btn_link": "💳 To'lash", "back": "⬅️ Orqaga", "next": "Keyingi ➡️",
        "share_title": "🤝 <b>Ulashish:</b>", "btn_share_now": "📲 Ulashish", "share_msg": "🚀 mubVPN — Android uchun VPN!"
    },
    "tg": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nЗудтарин ва бехатар:",
        "btn_pay": "💳 Харидан", "btn_how": "📖 Чӣ тавр?", "btn_download": "🚀 Боргирӣ", "btn_support": "👨 staff-💻 Дастгирӣ", "btn_share": "🤝 Ирсол",
        "pay_text": "💳 <b>Гузаштан ба пардохт</b>", "pay_btn_link": "💳 Пардохт", "back": "⬅️ Ба ақиб", "next": "Оянда ➡️",
        "share_title": "🤝 <b>Ирсол:</b>", "btn_share_now": "📲 Ирсол", "share_msg": "🚀 mubVPN — VPN-и беҳтарин!"
    },
    "kk": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nЕң жылдам және қауіпсіз:",
        "btn_pay": "💳 Сатып алу", "btn_how": "📖 Қалай?", "btn_download": "🚀 Жүктеу", "btn_support": "👨 staff-💻 Қолдау", "btn_share": "🤝 Бөлісу",
        "pay_text": "💳 <b>Төлемге өту</b>", "pay_btn_link": "💳 Төлеу", "back": "⬅️ Артқа", "next": "Келесі ➡️",
        "share_title": "🤝 <b>Бөлісу:</b>", "btn_share_now": "📲 Бөлісу", "share_msg": "🚀 mubVPN — Android үшін VPN!"
    },
    "tr": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nEn hızlı ve güvenli:",
        "btn_pay": "💳 Satın Al", "btn_how": "📖 Nasıl?", "btn_download": "🚀 İndir", "btn_support": "👨 staff-💻 Destek", "btn_share": "🤝 Paylaş",
        "pay_text": "💳 <b>Ödemeye Geç</b>", "pay_btn_link": "💳 Öde", "back": "⬅️ Geri", "next": "İleri ➡️",
        "share_title": "🤝 <b>Paylaş:</b>", "btn_share_now": "📲 Paylaş", "share_msg": "🚀 mubVPN — En hızlı VPN!"
    },
    "en": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nUnlock fastest internet access:",
        "btn_pay": "💳 Buy", "btn_how": "📖 How?", "btn_download": "🚀 Download", "btn_support": "👨 staff-💻 Support", "btn_share": "🤝 Share",
        "pay_text": "💳 <b>Proceed to Payment</b>", "pay_btn_link": "💳 Pay", "back": "⬅️ Back", "next": "Next ➡️",
        "share_title": "🤝 <b>Share:</b>", "btn_share_now": "📲 Share", "share_msg": "🚀 mubVPN — Best VPN for Android!"
    }
}

# --- KEYBOARDS ---
def get_lang_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇰🇬 Кыргызча", callback_data='set_lang_ky'), InlineKeyboardButton("🇷🇺 Русский", callback_data='set_lang_ru')],
        [InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data='set_lang_uz'), InlineKeyboardButton("🇹🇯 Тоҷикӣ", callback_data='set_lang_tg')],
        [InlineKeyboardButton("🇰🇿 Қазақша", callback_data='set_lang_kk'), InlineKeyboardButton("🇹🇷 Türkçe", callback_data='set_lang_tr')],
        [InlineKeyboardButton("🇺🇸 English", callback_data='set_lang_en')]
    ])

def get_main_keyboard(lang):
    L = STRINGS[lang]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(L["btn_download"], url=f'https://mubvpn-bot.onrender.com/?lang={lang}')],
        [InlineKeyboardButton(L["btn_pay"], callback_data='pay_menu')],
        [InlineKeyboardButton(L["btn_how"], callback_data='how_1')],
        [InlineKeyboardButton(L["btn_share"], callback_data='share_app')],
        [InlineKeyboardButton(L["btn_support"], url=SUPPORT_URL)]
    ])

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args: context.user_data['uid'] = context.args[0]
    text = "🌐 Choose language / Тилди тандаңыз / Выберите язык:"
    try:
        if update.message: await update.message.reply_photo(photo=WELCOME_PHOTO, caption=text, reply_markup=get_lang_keyboard())
        else: await update.callback_query.message.edit_media(media=InputMediaPhoto(media=WELCOME_PHOTO, caption=text), reply_markup=get_lang_keyboard())
    except:
        if update.message: await update.message.reply_text(text, reply_markup=get_lang_keyboard())
        else: await update.callback_query.message.edit_text(text, reply_markup=get_lang_keyboard())

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    data = query.data; lang = context.user_data.get('lang', 'ky')
    if data.startswith('set_lang_'):
        lang = data.split('_')[2]; context.user_data['lang'] = lang
        await query.message.edit_caption(caption=STRINGS[lang]["welcome"], reply_markup=get_main_keyboard(lang), parse_mode=ParseMode.HTML)
    elif data == 'pay_menu':
        L = STRINGS[lang]; uid = context.user_data.get('uid', query.from_user.id)
        link = f"{LAVA_MAIN_URL}&additional_info={uid}" if '?' in LAVA_MAIN_URL else f"{LAVA_MAIN_URL}?additional_info={uid}"
        kb = [[InlineKeyboardButton(L["pay_btn_link"], web_app=WebAppInfo(url=link))], [InlineKeyboardButton(L["back"], callback_data='main_menu')]]
        await query.message.edit_caption(caption=L["pay_text"], reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
    elif data == 'share_app':
        L = STRINGS[lang]
        share_url = f"https://t.me/share/url?url=https://mubvpn-bot.onrender.com/?lang={lang}&text={html.escape(L['share_msg'])}"
        kb = [[InlineKeyboardButton(L["btn_share_now"], url=share_url)], [InlineKeyboardButton(L["back"], callback_data='main_menu')]]
        await query.message.edit_caption(caption=L["share_title"], reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
    elif data.startswith('how_'):
        step = data.split('_')[1]; L = STRINGS[lang]
        texts = {"1": "🚀 1-Step: Click Buy", "2": "📧 2-Step: Enter Email", "3": "💵 3-Step: Choose Currency", "4": "📱 4-Step: Enter Card", "5": "✅ 5-Step: Complete", "6": "🛠 6-Step: Verify"}
        nxt = str(int(step)+1) if int(step) < 6 else "menu"; prv = str(int(step)-1) if int(step) > 1 else "main"
        row = [InlineKeyboardButton(L["back"], callback_data='main_menu' if prv=="main" else f'how_{prv}')]
        if nxt != "menu": row.append(InlineKeyboardButton(L["next"], callback_data=f'how_{nxt}'))
        await query.message.edit_caption(caption=texts[step], reply_markup=InlineKeyboardMarkup([row]), parse_mode=ParseMode.HTML)
    elif data == 'main_menu':
        await query.message.edit_caption(caption=STRINGS[lang]["welcome"], reply_markup=get_main_keyboard(lang), parse_mode=ParseMode.HTML)

# --- DASHBOARD ---
def get_dashboard_html(lang):
    t_list = {
        'ky': {'badge': 'NEXT-GEN SECURITY', 'h1': 'mubVPN — Android үчүн тез жана коопсуз VPN', 'sub': '🚀 mubVPN — чектөөсүз интернетке коопсуз жол!', 'btn_dl': 'Android үчүн жүктөө'},
        'ru': {'badge': 'БЕЗОПАСНОСТЬ НОВОГО ПОКОЛЕНИЯ', 'h1': 'mubVPN — Быстрый и безопасный VPN', 'sub': '🚀 mubVPN — ваш безопасный доступ без ограничений!', 'btn_dl': 'Скачать для Android'}
    }
    t = t_list.get(lang, t_list['ru'])
    return f"""<!DOCTYPE html>
<html lang="{lang}"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{t['h1']}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;900&display=swap');
body {{ font-family: 'Inter', sans-serif; background: radial-gradient(circle at top right, #0a2e22 0%, #051610 100%); background-attachment: fixed; color: #fff; text-align: center; margin: 0; padding: 40px 20px; }}
@keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
.badge {{ display: inline-block; background: rgba(0,229,160,0.1); color: #00E5A0; padding: 10px 20px; border-radius: 100px; font-size: 12px; font-weight: 900; margin-bottom: 25px; border: 1px solid rgba(0,229,160,0.2); animation: fadeIn 1s ease; }}
h1 {{ font-size: clamp(30px, 8vw, 50px); font-weight: 900; margin-bottom: 20px; animation: fadeIn 1.2s ease; }}
.btn-download {{ display: inline-flex; align-items: center; background: #00E5A0; color: #000; padding: 20px 40px; border-radius: 20px; text-decoration: none; font-weight: 900; font-size: 20px; animation: fadeIn 1.5s ease; transition: 0.3s; }}
.btn-download:hover {{ transform: scale(1.05); }}
</style></head>
<body><div class="badge">✦ {t['badge']}</div><h1>{t['h1']}</h1><p style="max-width:700px; margin: 0 auto 40px; color:rgba(255,255,255,0.7);">{t['sub']}</p><a href="/download" class="btn-download">{t['btn_dl']}</a></body></html>"""

class BotHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/download':
            self.send_response(302); self.send_header('Location', 'https://github.com/Ulanbekmahmaraimov/mubvpn-bot/releases/download/v1.0.0/mubvpn.apk'); self.end_headers(); return
        query = urllib.parse.parse_qs(parsed.query); lang = query.get('lang', ['ky'])[0]
        self.send_response(200); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.end_headers(); self.wfile.write(get_dashboard_html(lang).encode('utf-8'))
    def do_POST(self):
        if self.path == '/webhook':
            try:
                cl = int(self.headers['Content-Length']); data = json.loads(self.rfile.read(cl).decode())
                uid = data.get('additional_info') or data.get('comment')
                if data.get('status') in ('success', 'paid') and uid: firebase_set_premium(str(uid), 1)
                self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
            except: self.send_response(500); self.end_headers()

def main():
    threading.Thread(target=lambda: HTTPServer(('0.0.0.0', int(os.environ.get('PORT', 8080))), BotHandler).serve_forever(), daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start)); app.add_handler(CallbackQueryHandler(handle_callback)); app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()