import logging
import os
import json
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, InputMediaPhoto
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import html

# --- ЖӨНДӨӨЛӨР ---
BOT_TOKEN    = "8400265569:AAHQ21_zNVS3XPDlMoE9I8TW0JwaIaUuA1s"
LAVA_API     = "cUPUZBNvxATjd5ou8oodPIozLGb7dqzZx5eDYdYbkctCV9eRJBaDWpJKAkp8Bp8m"
SUPPORT_URL  = "https://t.me/kl_mub"
LAVA_MAIN_URL = "https://app.lava.top/products/db3d18c8-01e5-40f2-bf0a-e01842697312/8a98aa1a-78d0-4291-bf1e-6c143668cf15"

# Webhook үчүн жашыруун ачкыч (Lava'га да ушуну жазасыз)
WEBHOOK_SECRET_KEY = "mubvpn_secure_key_123"

FIREBASE_DB_URL    = "https://mubvpn-8b892-default-rtdb.firebaseio.com"
FIREBASE_DB_SECRET = "NgRNzmtQYdgUcFWXiDRPAHAsSURVni2WaIKTw9Re"

# Сүрөттөр
PHOTO_1 = "https://i.postimg.cc/8P89LdG2/image.png"
PHOTO_2 = "https://i.postimg.cc/xTfXyZzW/image.png"
PHOTO_3 = "https://i.postimg.cc/85zK09pG/image.png"
PHOTO_4 = "https://i.postimg.cc/8C5YxXq0/image.png"
PHOTO_5 = "https://i.postimg.cc/mD83Wfnd/image.png"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

# --- ФУНКЦИЯЛАР ---
def firebase_set_premium(uid: str, months: int) -> bool:
    try:
        expiry = (datetime.now() + timedelta(days=months * 30)).isoformat()
        url = f"{FIREBASE_DB_URL}/users/{uid}.json?auth={FIREBASE_DB_SECRET}"
        resp = requests.patch(url, json={"premium_expiry": expiry, "is_paid": True}, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        log.error(f"Firebase error: {e}")
        return False

# --- WEBHOOK КУТКОН СЕРВЕР ---
class WebhookHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"MubVPN Bot is running!")

    def do_POST(self):
        if self.path == '/lava-webhook':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data)
                log.info(f"📥 Webhook алынды: {data}")
                status = data.get('status')
                uid = data.get('additional_info') or data.get('comment')
                amount = float(data.get('amount', 0))
                if status in ('success', 'paid') and uid:
                    months = 12 if amount >= 1000 else (6 if amount >= 600 else (3 if amount >= 300 else 1))
                    if firebase_set_premium(str(uid), months):
                        log.info(f"✅ Webhook аркылуу Premium иштетилди: {uid}")
                self.send_response(200); self.end_headers()
            except Exception as e:
                log.error(f"Webhook error: {e}"); self.send_response(400); self.end_headers()
        else: self.send_response(404); self.end_headers()

def run_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), WebhookHandler)
    log.info(f"🌐 Webhook server started on port {port}")
    server.serve_forever()

# --- БОТТУН ТЕКСТТЕРИ ---
STRINGS = {
    "ky": {
        "welcome": "🛡 <b>mubVPN Premium</b>\n\nТандаңыз:",
        "btn_pay": "💳 Сатып алуу", "btn_how": "📖 Төлөө", "btn_support": "👨‍💻 Колдоо", "btn_share": "🤝 Бөлүшүү",
        "pay_text": "💳 <b>Төлөө барагына өтүү:</b>", "pay_btn_link": "💳 Telegram", "back": "⬅️ Артка", "next": "Кийинки ➡️",
        "menu_back": "Башкы меню:", "share_msg": "🛡 mubVPN - Эң тез VPN!",
        "how_1": "🚀 1: Планды тандаңыз.", "how_2": "📧 2: Почтаны жазыңыз.", "how_3": "💵 3: Валюта тандаңыз.", "how_4": "📱 4: Карта маалыматы.", "how_5": "💳 5: Төлөңүз."
    },
    "ru": {
        "welcome": "🛡 <b>mubVPN Premium</b>\n\nВыберите:",
        "btn_pay": "💳 Купить", "btn_how": "📖 Инструкция", "btn_support": "👨‍💻 Поддержка", "btn_share": "🤝 Поделиться",
        "pay_text": "💳 <b>Переход к оплате:</b>", "pay_btn_link": "💳 Telegram", "back": "⬅️ Назад", "next": "Далее ➡️",
        "menu_back": "Главное меню:", "share_msg": "🛡 mubVPN - Самый быстрый VPN!",
        "how_1": "🚀 1: Выберите план.", "how_2": "📧 2: Введите почту.", "how_3": "💵 3: Выберите валюту.", "how_4": "📱 4: Данные карты.", "how_5": "💳 5: Оплатите."
    }
}

# --- КЛАВИАТУРАЛАР ---
def get_lang_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🇰🇬 Кыргызча", callback_data='set_lang_ky')], [InlineKeyboardButton("🇷🇺 Русский", callback_data='set_lang_ru')]])

def get_main_kb(lang):
    L = STRINGS[lang]
    return InlineKeyboardMarkup([[InlineKeyboardButton(L["btn_pay"], callback_data='pay_menu')], [InlineKeyboardButton(L["btn_how"], callback_data='how_1')], [InlineKeyboardButton(L["btn_share"], callback_data='share_app')], [InlineKeyboardButton(L["btn_support"], url=SUPPORT_URL)]])

# --- КОМАНДАЛАР ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args: context.user_data['uid'] = context.args[0]
    await (update.message.reply_text if update.message else update.callback_query.message.edit_text)("🌐 Language / Тилди тандаңыз:", reply_markup=get_lang_kb())

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer(); d = q.data; lang = context.user_data.get('lang', 'ru')
    if d.startswith('set_lang_'):
        lang = d.split('_')[2]; context.user_data['lang'] = lang
        await q.message.edit_text(STRINGS[lang]["welcome"], reply_markup=get_main_kb(lang), parse_mode=ParseMode.HTML)
    elif d == 'pay_menu':
        L = STRINGS[lang]; uid = context.user_data.get('uid', q.from_user.id)
        kb = [[InlineKeyboardButton(L["pay_btn_link"], web_app=WebAppInfo(url=f"{LAVA_MAIN_URL}?additional_info={uid}"))], [InlineKeyboardButton(L["back"], callback_data='main_menu')]]
        await q.message.edit_text(L["pay_text"], reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
    elif d.startswith('how_'):
        step = d.split('_')[1]; L = STRINGS[lang]
        photos = {"1": PHOTO_1, "2": PHOTO_2, "3": PHOTO_3, "4": PHOTO_4, "5": PHOTO_5}
        texts = {"1": L["how_1"], "2": L["how_2"], "3": L["how_3"], "4": L["how_4"], "5": L["how_5"]}
        nxt = str(int(step)+1) if int(step) < 5 else "menu"
        prv = str(int(step)-1) if int(step) > 1 else "main"
        row = [InlineKeyboardButton(L["back"], callback_data='main_menu' if prv=="main" else f'how_{prv}')]
        if nxt != "menu": row.append(InlineKeyboardButton(L["next"], callback_data=f'how_{nxt}'))
        try:
            if q.message.photo: await q.message.edit_media(InputMediaPhoto(photos[step], caption=texts[step], parse_mode=ParseMode.HTML), reply_markup=InlineKeyboardMarkup([row]))
            else:
                await context.bot.send_photo(q.message.chat_id, photos[step], caption=texts[step], reply_markup=InlineKeyboardMarkup([row]), parse_mode=ParseMode.HTML)
                await q.message.delete()
        except: await q.message.edit_text(texts[step], reply_markup=InlineKeyboardMarkup([row]))
    elif d == 'main_menu':
        if q.message.photo: await q.message.delete()
        await context.bot.send_message(q.message.chat_id, STRINGS[lang]["menu_back"], reply_markup=get_main_kb(lang), parse_mode=ParseMode.HTML)

def main():
    threading.Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()

if __name__ == "__main__":
    main()