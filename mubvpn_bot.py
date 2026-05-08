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

# ─── ИНСТРУКЦИЯЛАР (Сүрөтсүз, текст аркылуу) ────────────────────
# Сүрөттөрдү жүктөөдө ката чыккандыктан, эң ишенимдүү тексттик режимге өттүк.

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
        "how_step_1": "🚀 <b>1-КАДАМ: План тандоо</b>\n\n'Сатып алуу' баскычын басып, өзүңүзгө жаккан мөөнөттү тандаңыз (1 ай, 3 ай ж.б.). 1 жылдык план эң пайдалуу! ✅",
        "how_step_2": "📧 <b>2-КАДАМ: Почтаны жазуу</b>\n\nТөлөм барагында электрондук почтаңызды (Email) жазыңыз. Бул сизге чек алуу жана Premium активдештирүү үчүн керек. 📩",
        "how_step_3": "💵 <b>3-КАДАМ: Валюта тандоо</b>\n\nЭгер сиз МИР картасы (Элкарт) менен төлөсөңүз, валютаны <b>RUB</b> же <b>KGS</b> кылып тандаңыз. Бул комиссияны азайтат. 💰",
        "how_step_4": "📱 <b>4-КАДАМ: Карта маалыматы</b>\n\nКартаңыздын номерин, мөөнөтүн жана CVC-кодун жазыңыз. Эгер маалыматтар жаныңызда жок болсо, банк тиркемесинен көчүрүп алсаңыз болот. 💳",
        "how_step_5": "✅ <b>5-КАДАМ: Төлөмдү бүтүрүү</b>\n\n'Оплатить' баскычын басып, банктан келген SMS кодду киргизиңиз. Төлөм бүткөндө система автоматтык түрдө Premium иштетет! 🎉",
        "how_step_6": "🛠 <b>6-КАДАМ: Текшерүү</b>\n\nТөлөп бүткөндөн кийин тиркемеге кириңиз. Эгер Premium иштебесе, боттогу 'Текшерүү' баскычын басыңыз. @kl_mub дайыма жардамга даяр! 👨‍💻",
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
        "how_step_1": "🚀 <b>ШАГ 1: Выбор тарифа</b>\n\nНажмите 'Купить' и выберите подходящий период (1 месяц, 1 год и т.д.). Годовой план самый выгодный! ✅",
        "how_step_2": "📧 <b>ШАГ 2: Ввод почты</b>\n\nНа странице оплаты введите ваш Email. Это нужно для получения чека и активации Премиума. 📩",
        "how_step_3": "💵 <b>ШАГ 3: Выбор валюты</b>\n\nПри оплате картой МИР (Элкарт) выбирайте валюту <b>RUB</b> или <b>KGS</b> для минимальной комиссии. 💰",
        "how_step_4": "📱 <b>ШАГ 4: Данные карты</b>\n\nВведите номер карты, срок действия и CVC-код. Реквизиты можно скопировать в приложении вашего банка. 💳",
        "how_step_5": "✅ <b>ШАГ 5: Завершение</b>\n\nНажмите 'Оплатить' и введите код из СМС. После оплаты система автоматически включит Premium! 🎉",
        "how_step_6": "🛠 <b>ШАГ 6: Проверка</b>\n\nВернитесь в приложение. Если Premium не включился сразу, нажмите кнопку 'Проверить' в боте. @kl_mub всегда на связи! 👨‍💻",
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
        "how_step_1": "🚀 <b>STEP 1: Choose a plan</b>\n\nClick 'Buy' and select your preferred duration. The annual plan is the most profitable! ✅",
        "how_step_2": "📧 <b>STEP 2: Enter Email</b>\n\nEnter your email on the payment page to receive a receipt and activate Premium. 📩",
        "how_step_3": "💵 <b>STEP 3: Choose currency</b>\n\nSelect <b>RUB</b> or <b>KGS</b> for lower fees if paying with a local bank card. 💰",
        "how_step_4": "📱 <b>STEP 4: Card details</b>\n\nEnter your card number, expiry date, and CVC. You can find these in your bank's mobile app. 💳",
        "how_step_5": "✅ <b>STEP 5: Complete payment</b>\n\nClick 'Pay' and enter the SMS code from your bank. Premium activates automatically! 🎉",
        "how_step_6": "🛠 <b>STEP 6: Verification</b>\n\nCheck the app. If Premium is not active, click 'Check Payment' in the bot. @kl_mub is here to help! 👨‍💻",
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
        texts = {"1": L["how_step_1"], "2": L["how_step_2"], "3": L["how_step_3"], "4": L["how_step_4"], "5": L["how_step_5"], "6": L["how_step_6"]}

        next_step = str(int(step) + 1) if int(step) < 6 else "menu"
        back_step = str(int(step) - 1) if int(step) > 1 else "main"

        kb = []
        row = []
        if back_step == "main": row.append(InlineKeyboardButton(L["back"], callback_data='main_menu'))
        else: row.append(InlineKeyboardButton(L["back"], callback_data=f'how_{back_step}'))

        if next_step != "menu": row.append(InlineKeyboardButton(L["next"], callback_data=f'how_{next_step}'))
        else: row.append(InlineKeyboardButton("🏠 Menu", callback_data='main_menu'))
        kb.append(row)

        if query.message.photo: await query.message.delete()
        
        try:
            await query.message.edit_text(texts[step], reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
        except:
            await context.bot.send_message(chat_id=query.message.chat_id, text=texts[step], reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
            await query.message.delete()

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
  .download-btn {
    display: inline-flex; align-items: center; justify-content: center; gap: 8px;
    background: linear-gradient(135deg, #00F5A0, #00D9F5);
    color: #000;
    font-weight: 700;
    font-size: 16px;
    padding: 14px 28px;
    border-radius: 100px;
    text-decoration: none;
    box-shadow: 0 10px 20px rgba(0,245,160,0.2);
    transition: all 0.3s ease;
  }
  .download-btn:hover { transform: translateY(-2px); box-shadow: 0 15px 25px rgba(0,245,160,0.3); }
</style>
</head>
<body>
<div class="glow"></div>
<div class="glow2"></div>

<div class="card">
  <div class="logo">
    <div class="logo-icon">🛡</div>
    <div class="logo-text">
      <h1>mubVPN</h1>
      <p>Тез жана коопсуз VPN</p>
    </div>
  </div>
  <div class="status-badge"><div class="dot"></div> Активдүү / Active</div>
  
  <div style="margin-top: 30px; text-align: center;">
    <h2 style="font-size: 20px; font-weight: 800; margin-bottom: 10px;">Тиркемени Жүктөп Алуу</h2>
    <p style="font-size: 14px; color: rgba(255,255,255,0.6); margin-bottom: 20px;">
      Android үчүн эң акыркы версиясын көчүрүп алыңыз.
    </p>
    <a href="/download" class="download-btn">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
      Жүктөө (APK)
    </a>
  </div>
</div>

<div class="card">
  <div class="info-row">
    <span class="info-label">Платформа</span>
    <span class="info-value">Android 🤖</span>
  </div>
  <div class="info-row">
    <span class="info-label">Telegram Бот</span>
    <a href="https://t.me/mubvpn_pay_bot" class="info-value">@mubvpn_pay_bot 🤖</a>
  </div>
  <div class="info-row">
    <span class="info-label">Колдоо</span>
    <a href="https://t.me/kl_mub" class="info-value">@kl_mub 👨‍💻</a>
  </div>
</div>

<p class="footer">mubVPN © 2025</p>
</body>
</html>"""

    class DashboardHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path == '/webhook':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                try:
                    import json
                    data = json.loads(post_data.decode('utf-8'))
                    log.info(f"📥 Webhook келди: {data}")

                    # Lava.top'тон келген маалыматтар
                    status = data.get('status')
                    # additional_info ичинде колдонуучунун UID номери болот
                    uid = data.get('additional_info') or data.get('additionalFields')
                    amount = float(data.get('amount', 0))

                    if status in ('success', 'paid') and uid:
                        # Суммасына карап планды аныктайбыз
                        if amount >= 1000: months = 12
                        elif amount >= 600: months = 6
                        elif amount >= 350: months = 3
                        else: months = 1
                        
                        if firebase_set_premium(str(uid), months):
                            log.info(f"✅ Webhook аркылуу Premium иштетилди: {uid}")
                            self.send_response(200)
                            self.end_headers()
                            self.wfile.write(b"OK")
                            return

                    self.send_response(400)
                    self.end_headers()
                except Exception as e:
                    log.error(f"Webhook error: {e}")
                    self.send_response(500)
                    self.end_headers()
                return

        def do_GET(self):
            if self.path == '/download':
                apk_path = 'mubvpn.apk'
                if os.path.exists(apk_path):
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/vnd.android.package-archive')
                    self.send_header('Content-Disposition', 'attachment; filename="mubVPN.apk"')
                    self.send_header('Content-Length', str(os.path.getsize(apk_path)))
                    self.end_headers()
                    with open(apk_path, 'rb') as f:
                        self.wfile.write(f.read())
                else:
                    self.send_response(404)
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write("<h1>APK файл табылган жок. Админге кайрылыңыз (@kl_mub)</h1>".encode('utf-8'))
                return

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