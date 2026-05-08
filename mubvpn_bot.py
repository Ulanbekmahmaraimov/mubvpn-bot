import logging
import requests
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, InputMediaPhoto
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import html

# Логдорду жөндөө
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

# ─── ЖӨНДӨӨЛӨР ───
BOT_TOKEN    = "8400265569:AAHQ21_zNVS3XPDlMoE9I8TW0JwaIaUuA1s"
LAVA_API     = "cUPUZBNvxATjd5ou8oodPIozLGb7dqzZx5eDYdYbkctCV9eRJBaDWpJKAkp8Bp8m"
SUPPORT_URL  = "https://t.me/kl_mub"

# Төлөм шилтемеси (Lava.top)
LAVA_MAIN_URL = "https://app.lava.top/products/db3d18c8-01e5-40f2-bf0a-e01842697312/8a98aa1a-78d0-4291-bf1e-6c143668cf15"

# Пландар
PLANS = {
    "1m":  {"name": "1 ай",  "months": 1},
    "3m":  {"name": "3 ай",  "months": 3},
    "6m":  {"name": "6 ай",  "months": 6},
    "1y":  {"name": "1 жыл", "months": 12},
}

# ─── FIREBASE ЖӨНДӨӨЛӨРҮ ───
FIREBASE_DB_URL    = "https://mubvpn-8b892-default-rtdb.firebaseio.com"
FIREBASE_DB_SECRET = "NgRNzmtQYdgUcFWXiDRPAHAsSURVni2WaIKTw9Re"

# ─── ИНСТРУКЦИЯ СҮРӨТТӨРҮ (URL колдонобуз, бул ишенимдүү) ───
PHOTO_1 = "https://i.postimg.cc/8P89LdG2/image.png"  # План тандоо
PHOTO_2 = "https://i.postimg.cc/xTfXyZzW/image.png"  # Почтаны жазуу
PHOTO_3 = "https://i.postimg.cc/85zK09pG/image.png"  # Валюта тандоо
PHOTO_4 = "https://i.postimg.cc/8C5YxXq0/image.png"  # Банк маалыматы
PHOTO_5 = "https://i.postimg.cc/mD83Wfnd/image.png"  # Төлөмдү бүтүрүү

def firebase_set_premium(uid: str, months: int) -> bool:
    """Firebase базасына Premium статусун жазат."""
    try:
        expiry = (datetime.now() + timedelta(days=months * 30)).isoformat()
        url = f"{FIREBASE_DB_URL}/users/{uid}.json?auth={FIREBASE_DB_SECRET}"
        resp = requests.patch(url, json={"premium_expiry": expiry, "is_paid": True}, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        log.error(f"Firebase error: {e}")
        return False

def lava_check_payment(uid: str) -> dict | None:
    """Lava API аркылуу төлөмдү текшерет."""
    try:
        resp = requests.get(
            'https://gate.lava.top/api/v2/invoices',
            headers={'X-Api-Key': LAVA_API, 'Accept': 'application/json'},
            timeout=10
        )
        if resp.status_code == 200:
            for inv in resp.json().get('items', []):
                # 'additional_info' талаасынан колдонуучунун UID номерин издейбиз
                info = str(inv.get('additionalFields', inv.get('additional_info', '')))
                if uid in info and inv.get('status') in ('success', 'paid'):
                    amount = float(inv.get('amount', 0))
                    # Суммасына карап планды аныктайбыз
                    if amount >= 1000: plan = "1y"
                    elif amount >= 600: plan = "6m"
                    elif amount >= 350: plan = "3m"
                    else: plan = "1m"
                    return {"plan": plan}
    except Exception as e:
        log.error(f'Lava check error: {e}')
    return None

STRINGS = {
    "ky": {
        "welcome": "🛡 <b>mubVPN Premium</b>\n\nТөлөм жүргүзүү үчүн төмөнкү баскычтарды колдонуңуз:",
        "btn_pay": "💳 Сатып алуу", "btn_how": "📖 Төлөөнү үйрөнүү",
        "btn_support": "👨‍💻 Колдоо", "btn_share": "🤝 Бөлүшүү",
        "pay_text": "💳 <b>Төлөөгө өтүү</b>\n\nТөлөм Telegram ичинде коопсуз өтөт:",
        "pay_btn_link": "💳 Telegram", "back": "⬅️ Артка", "next": "Кийинки ➡️",
        "check_btn": "✅ Төлөдүм (Текшерүү)",
        "checking": "⏳ Төлөм текшерилүүдө...",
        "success": "🎉 <b>Premium активдешти!</b>\n\nТиркемени ачып, VPN'ди колдоно бериңиз!",
        "not_found": "⚠️ Төлөм табылган жок. Төлөп бүтсөңүз, 1-2 мүнөт күтүп кайра басыңыз.",
        "how_step_1": "🚀 1-КАДАМ: Планды тандаңыз.",
        "how_step_2": "📧 2-КАДАМ: Тиркемедеги почтаңызды жазыңыз.",
        "how_step_3": "💵 3-КАДАМ: Валютаны (RUB/KGS) тандаңыз.",
        "how_step_4": "📱 4-КАДАМ: Карта маалыматын даярдаңыз.",
        "how_step_5": "💳 5-КАДАМ: 'Оплатить' баскычын басыңыз.",
        "menu_back": "Башкы меню:",
        "share_msg": "🛡 mubVPN - Эң тез жана коопсуз VPN!"
    },
    "ru": {
        "welcome": "🛡 <b>mubVPN Premium</b>\n\nВыберите действие:",
        "btn_pay": "💳 Купить", "btn_how": "📖 Как оплатить?",
        "btn_support": "👨‍💻 Поддержка", "btn_share": "🤝 Поделиться",
        "pay_text": "💳 <b>Переход к оплате</b>\n\nОплата проходит внутри Telegram:",
        "pay_btn_link": "💳 Telegram", "back": "⬅️ Назад", "next": "Далее ➡️",
        "check_btn": "✅ Я оплатил (Проверить)",
        "checking": "⏳ Проверка платежа...",
        "success": "🎉 <b>Premium активирован!</b>\n\nОткройте приложение и пользуйтесь VPN!",
        "not_found": "⚠️ Платеж не найден. Если вы оплатили, подождите 1-2 минуты и нажмите снова.",
        "how_step_1": "🚀 ШАГ 1: Выберите тариф.",
        "how_step_2": "📧 ШАГ 2: Введите почту из приложения.",
        "how_step_3": "💵 ШАГ 3: Выберите валюту (RUB/KGS).",
        "how_step_4": "📱 ШАГ 4: Подготовьте данные карты.",
        "how_step_5": "💳 ШАГ 5: Нажмите 'Оплатить'.",
        "menu_back": "Главное меню:",
        "share_msg": "🛡 mubVPN - Самый быстрый и безопасный VPN!"
    },
    "en": {
        "welcome": "🛡 <b>mubVPN Premium</b>\n\nPlease choose an option:",
        "btn_pay": "💳 Buy", "btn_how": "📖 How to pay?",
        "btn_support": "👨‍💻 Support", "btn_share": "🤝 Share",
        "pay_text": "💳 <b>Proceed to Payment</b>\n\nThe payment is secure within Telegram:",
        "pay_btn_link": "💳 Telegram", "back": "⬅️ Back", "next": "Next ➡️",
        "check_btn": "✅ I have paid (Check)",
        "checking": "⏳ Checking payment...",
        "success": "🎉 <b>Premium activated!</b>\n\nOpen the app and enjoy your VPN!",
        "not_found": "⚠️ Payment not found. If you paid, wait 1-2 minutes and try again.",
        "how_step_1": "🚀 STEP 1: Choose a plan.",
        "how_step_2": "📧 STEP 2: Enter your email from the app.",
        "how_step_3": "💵 STEP 3: Choose currency (RUB/KGS).",
        "how_step_4": "📱 STEP 4: Prepare card details.",
        "how_step_5": "💳 STEP 5: Click 'Pay'.",
        "menu_back": "Main Menu:",
        "share_msg": "🛡 mubVPN - The fastest and safest VPN!"
    }
}

def get_lang_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🇰🇬 Кыргызча", callback_data='set_lang_ky')], [InlineKeyboardButton("🇷🇺 Русский", callback_data='set_lang_ru')], [InlineKeyboardButton("🇺🇸 English", callback_data='set_lang_en')]])

def get_main_keyboard(lang):
    L = STRINGS[lang]
    return InlineKeyboardMarkup([[InlineKeyboardButton(L["btn_pay"], callback_data='pay_menu')], [InlineKeyboardButton(L["btn_how"], callback_data='how_1')], [InlineKeyboardButton(L["btn_share"], callback_data='share_app')], [InlineKeyboardButton(L["btn_support"], url=SUPPORT_URL)]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        context.user_data['uid'] = context.args[0]
        log.info(f"UID сакталды: {context.args[0]}")

    text = "🌐 Choose language / Тилди тандаңыз / Выберите язык:"
    if update.message: await update.message.reply_text(text, reply_markup=get_lang_keyboard())
    else: await update.callback_query.message.edit_text(text, reply_markup=get_lang_keyboard())

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer()
    data = query.data; lang = context.user_data.get('lang', 'ru')

    if data.startswith('set_lang_'):
        lang = data.split('_')[2]; context.user_data['lang'] = lang
        await query.message.edit_text(STRINGS[lang]["welcome"], reply_markup=get_main_keyboard(lang), parse_mode=ParseMode.HTML)

    elif data == 'pay_menu':
        L = STRINGS[lang]; uid = context.user_data.get('uid', query.from_user.id)
        link = f"{LAVA_MAIN_URL}?additional_info={uid}"
        kb = [[InlineKeyboardButton(L["pay_btn_link"], web_app=WebAppInfo(url=link))], [InlineKeyboardButton(L["check_btn"], callback_data='check_pay')], [InlineKeyboardButton(L["back"], callback_data='main_menu')]]
        await query.message.edit_text(L["pay_text"], reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif data == 'check_pay':
        L = STRINGS[lang]; uid = context.user_data.get('uid', str(query.from_user.id))
        await query.message.edit_text(L["checking"])
        result = lava_check_payment(uid)
        if result:
            plan_id = result['plan']
            months = PLANS[plan_id]['months']
            if firebase_set_premium(uid, months):
                await query.message.edit_text(L["success"], parse_mode=ParseMode.HTML)
            else:
                await query.message.edit_text("❌ Firebase Error. Contact @kl_mub")
        else:
            kb = [[InlineKeyboardButton("🔄 " + L["check_btn"], callback_data='check_pay')], [InlineKeyboardButton(L["back"], callback_data='main_menu')]]
            await query.message.edit_text(L["not_found"], reply_markup=InlineKeyboardMarkup(kb))

    elif data == 'share_app':
        L = STRINGS[lang]; bot = await context.bot.get_me(); share_url = f"https://t.me/share/url?url=https://t.me/{bot.username}&text={html.escape(L['share_msg'])}"
        kb = [[InlineKeyboardButton("📲 Бөлүшүү / Поделиться", url=share_url)], [InlineKeyboardButton(L["back"], callback_data='main_menu')]]
        await query.message.edit_text("🤝 <b>Share:</b>", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif data.startswith('how_'):
        step = data.split('_')[1]; L = STRINGS[lang]
        photos = {"1": PHOTO_1, "2": PHOTO_2, "3": PHOTO_3, "4": PHOTO_4, "5": PHOTO_5}
        texts = {"1": L["how_step_1"], "2": L["how_step_2"], "3": L["how_step_3"], "4": L["how_step_4"], "5": L["how_step_5"]}

        next_step = str(int(step) + 1) if int(step) < 5 else "menu"
        back_step = str(int(step) - 1) if int(step) > 1 else "main"

        kb = []
        row = []
        if back_step == "main": row.append(InlineKeyboardButton(L["back"], callback_data='main_menu'))
        else: row.append(InlineKeyboardButton(L["back"], callback_data=f'how_{back_step}'))

        if next_step != "menu": row.append(InlineKeyboardButton(L["next"], callback_data=f'how_{next_step}'))
        else: row.append(InlineKeyboardButton("🏠 Menu", callback_data='main_menu'))
        kb.append(row)

        try:
            if query.message.photo:
                await query.message.edit_media(media=InputMediaPhoto(photos[step], caption=texts[step], parse_mode=ParseMode.HTML), reply_markup=InlineKeyboardMarkup(kb))
            else:
                await context.bot.send_photo(chat_id=query.message.chat_id, photo=photos[step], caption=texts[step], reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
                await query.message.delete()
        except:
            await query.message.edit_text(texts[step], reply_markup=InlineKeyboardMarkup(kb))

    elif data == 'main_menu':
        L = STRINGS[lang]
        if query.message.photo: await query.message.delete()
        await context.bot.send_message(chat_id=query.message.chat_id, text=L["menu_back"], reply_markup=get_main_keyboard(lang), parse_mode=ParseMode.HTML)

def main():
    import threading
    import os
    import time
    from http.server import HTTPServer, BaseHTTPRequestHandler

    # Статистика (жашоо мезгилинде гана сакталат)
    stats = {"users": 0, "payments": 0, "started": time.strftime("%Y-%m-%d %H:%M:%S")}

    DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>mubVPN Bot Dashboard</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Inter', sans-serif;
    background: #030303;
    color: #fff;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 24px;
  }
  .glow { position: fixed; top: -200px; right: -100px; width: 600px; height: 600px;
    background: radial-gradient(circle, rgba(0,245,160,0.08) 0%, transparent 70%); pointer-events: none; }
  .glow2 { position: fixed; bottom: -200px; left: -100px; width: 500px; height: 500px;
    background: radial-gradient(circle, rgba(0,150,255,0.06) 0%, transparent 70%); pointer-events: none; }
  .card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 24px;
    padding: 32px;
    margin-bottom: 20px;
    width: 100%;
    max-width: 600px;
    backdrop-filter: blur(20px);
  }
  .logo { display: flex; align-items: center; gap: 16px; margin-bottom: 32px; }
  .logo-icon {
    width: 60px; height: 60px;
    background: linear-gradient(135deg, #00F5A0, #00D9F5);
    border-radius: 18px;
    display: flex; align-items: center; justify-content: center;
    font-size: 28px;
    box-shadow: 0 0 30px rgba(0,245,160,0.3);
  }
  .logo-text h1 { font-size: 24px; font-weight: 900; }
  .logo-text p { color: rgba(255,255,255,0.4); font-size: 13px; margin-top: 2px; }
  .status-badge {
    display: inline-flex; align-items: center; gap: 8px;
    background: rgba(0,245,160,0.1);
    border: 1px solid rgba(0,245,160,0.3);
    border-radius: 100px;
    padding: 6px 16px;
    font-size: 13px;
    font-weight: 600;
    color: #00F5A0;
  }
  .dot {
    width: 8px; height: 8px;
    background: #00F5A0;
    border-radius: 50%;
    animation: pulse 2s infinite;
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.8); }
  }
  .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 24px; }
  .stat {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 20px;
    text-align: center;
  }
  .stat-value { font-size: 32px; font-weight: 900; color: #00F5A0; }
  .stat-label { font-size: 12px; color: rgba(255,255,255,0.4); margin-top: 4px; text-transform: uppercase; letter-spacing: 1px; }
  .info-row { display: flex; justify-content: space-between; align-items: center;
    padding: 14px 0; border-bottom: 1px solid rgba(255,255,255,0.05); }
  .info-row:last-child { border-bottom: none; }
  .info-label { color: rgba(255,255,255,0.4); font-size: 13px; }
  .info-value { font-size: 13px; font-weight: 600; }
  .footer { text-align: center; color: rgba(255,255,255,0.2); font-size: 12px; margin-top: 8px; }
  a { color: #00F5A0; text-decoration: none; }
</style>
</head>
<body>
<div class="glow"></div>
<div class="glow2"></div>

<div class="card">
  <div class="logo">
    <div class="logo-icon">🛡</div>
    <div class="logo-text">
      <h1>mubVPN Bot</h1>
      <p>Telegram Payment Bot</p>
    </div>
  </div>
  <div class="status-badge"><div class="dot"></div> Online & Running</div>
  <div class="stats-grid">
    <div class="stat">
      <div class="stat-value" id="users">—</div>
      <div class="stat-label">Total Users</div>
    </div>
    <div class="stat">
      <div class="stat-value" id="payments">—</div>
      <div class="stat-label">Payments</div>
    </div>
  </div>
</div>

<div class="card">
  <div class="info-row">
    <span class="info-label">Bot Status</span>
    <span class="info-value" style="color:#00F5A0">🟢 Active</span>
  </div>
  <div class="info-row">
    <span class="info-label">Platform</span>
    <span class="info-value">Render Cloud ☁️</span>
  </div>
  <div class="info-row">
    <span class="info-label">Payment Provider</span>
    <span class="info-value">Lava.top 💳</span>
  </div>
  <div class="info-row">
    <span class="info-label">Database</span>
    <span class="info-value">Firebase Realtime DB 🔥</span>
  </div>
  <div class="info-row">
    <span class="info-label">Languages</span>
    <span class="info-value">🇰🇬 🇷🇺 🇺🇸</span>
  </div>
  <div class="info-row">
    <span class="info-label">Support</span>
    <a href="https://t.me/kl_mub" class="info-value">@kl_mub</a>
  </div>
</div>

<p class="footer">mubVPN © 2025 · <a href="https://t.me/mubvpn_pay_bot">Open Bot</a></p>
</body>
</html>"""

    class DashboardHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode('utf-8'))
        def do_HEAD(self):
            self.send_response(200)
            self.end_headers()
        def log_message(self, format, *args):
            pass  # Лог спамын токтот

    def run_server():
        port = int(os.environ.get('PORT', 8080))
        server = HTTPServer(('0.0.0.0', port), DashboardHandler)
        log.info(f"🌐 Dashboard иштеп жатат: http://0.0.0.0:{port}")
        server.serve_forever()

    def keep_awake():
        time.sleep(60)  # Баштоодон кийин 1 мүнөт күт
        while True:
            try:
                import requests as req
                req.get("https://mubvpn-bot.onrender.com", timeout=10)
                log.info("💓 Keep-alive ping жиберилди")
            except:
                pass
            time.sleep(600)  # 10 мүнөт сайын

    threading.Thread(target=run_server, daemon=True).start()
    threading.Thread(target=keep_awake, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    log.info("🤖 Bot polling башталды...")
    app.run_polling()

if __name__ == "__main__":
    main()