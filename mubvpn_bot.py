import logging
import os
import json
import requests
import threading
import time
import html
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode

# --- ЖӨНДӨӨЛӨР ---
BOT_TOKEN    = "8400265569:AAHQ21_zNVS3XPDlMoE9I8TW0JwaIaUuA1s"
LAVA_API     = "cUPUZBNvxATjd5ou8oodPIozLGb7dqzZx5eDYdYbkctCV9eRJBaDWpJKAkp8Bp8m"
SUPPORT_URL  = "https://t.me/kl_mub"
LAVA_MAIN_URL = "https://app.lava.top/products/db3d18c8-01e5-40f2-bf0a-e01842697312/8a98aa1a-78d0-4291-bf1e-6c143668cf15?currency=RUB"

FIREBASE_DB_URL    = "https://mubvpn-8b892-default-rtdb.firebaseio.com"
FIREBASE_DB_SECRET = "NgRNzmtQYdgUcFWXiDRPAHAsSURVni2WaIKTw9Re"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

# --- ФУНКЦИЯЛАР ---
def firebase_set_premium(uid: str, months: int) -> bool:
    try:
        expiry = (datetime.now() + timedelta(days=months * 30)).isoformat()
        url = f"{FIREBASE_DB_URL}/users/{uid}.json?auth={FIREBASE_DB_SECRET}"
        resp = requests.patch(url, json={"premium_expiry": expiry, "is_paid": True})
        return resp.status_code == 200
    except Exception as e:
        log.error(f"Firebase error: {e}")
        return False

# --- БОТТУН ТЕКСТТЕРИ ---
STRINGS = {
    "ky": {
        "welcome": "🛡 <b>mubVPN Premium</b>\n\nТөлөм жүргүзүү үчүн төмөнкү баскычтарды колдонуңуз:",
        "btn_pay": "💳 Сатып алуу", "btn_how": "📖 Төлөөнү үйрөнүү",
        "btn_download": "⬇️ Тиркемени жүктөө",
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
        "menu_back": "Башкы меню:", "share_msg": "🛡 mubVPN - Эң тез жана коопсуз VPN!"
    },
    "ru": {
        "welcome": "🛡 <b>mubVPN Premium</b>\n\nВыберите действие:",
        "btn_pay": "💳 Купить", "btn_how": "📖 Как оплатить?",
        "btn_download": "⬇️ Скачать приложение",
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
        "menu_back": "Главное меню:", "share_msg": "🛡 mubVPN - Самый быстрый и безопасный VPN!"
    },
    "en": {
        "welcome": "🛡 <b>mubVPN Premium</b>\n\nPlease choose an option:",
        "btn_pay": "💳 Buy", "btn_how": "📖 How to pay?",
        "btn_download": "⬇️ Download App",
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
        "menu_back": "Main Menu:", "share_msg": "🛡 mubVPN - The fastest and safest VPN!"
    }
}

# --- КЛАВИАТУРАЛАР ---
def get_lang_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🇰🇬 Кыргызча", callback_data='set_lang_ky')], [InlineKeyboardButton("🇷🇺 Русский", callback_data='set_lang_ru')], [InlineKeyboardButton("🇺🇸 English", callback_data='set_lang_en')]])

def get_main_keyboard(lang):
    L = STRINGS[lang]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(L["btn_download"], url=f'https://mubvpn-bot.onrender.com/?lang={lang}')],
        [InlineKeyboardButton(L["btn_pay"], callback_data='pay_menu')], 
        [InlineKeyboardButton(L["btn_how"], callback_data='how_1')], 
        [InlineKeyboardButton(L["btn_share"], callback_data='share_app')], 
        [InlineKeyboardButton(L["btn_support"], url=SUPPORT_URL)]
    ])

# --- КОМАНДАЛАР ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args: context.user_data['uid'] = context.args[0]
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
        # Шилтемеге UID кошуу (эгер '?' бар болсо '&' колдонобуз)
        separator = '&' if '?' in LAVA_MAIN_URL else '?'
        link = f"{LAVA_MAIN_URL}{separator}additional_info={uid}"
        kb = [[InlineKeyboardButton(L["pay_btn_link"], web_app=WebAppInfo(url=link))], [InlineKeyboardButton(L["back"], callback_data='main_menu')]]
        await query.message.edit_text(L["pay_text"], reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif data == 'share_app':
        L = STRINGS[lang]; bot = await context.bot.get_me(); share_url = f"https://t.me/share/url?url=https://t.me/{bot.username}&text={html.escape(L['share_msg'])}"
        kb = [[InlineKeyboardButton("📲 Бөлүшүү / Поделиться", url=share_url)], [InlineKeyboardButton(L["back"], callback_data='main_menu')]]
        await query.message.edit_text("🤝 <b>Share:</b>", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif data.startswith('how_'):
        step = data.split('_')[1]; L = STRINGS[lang]
        texts = {"1": L["how_step_1"], "2": L["how_step_2"], "3": L["how_step_3"], "4": L["how_step_4"], "5": L["how_step_5"], "6": L["how_step_6"]}
        nxt = str(int(step)+1) if int(step) < 6 else "menu"
        prv = str(int(step)-1) if int(step) > 1 else "main"
        row = [InlineKeyboardButton(L["back"], callback_data='main_menu' if prv=="main" else f'how_{prv}')]
        if nxt != "menu": row.append(InlineKeyboardButton(L["next"], callback_data=f'how_{nxt}'))
        
        if query.message.photo: await query.message.delete()
        await query.message.edit_text(texts[step], reply_markup=InlineKeyboardMarkup([row]), parse_mode=ParseMode.HTML)

    elif data == 'main_menu':
        if query.message.photo: await query.message.delete()
        await query.message.edit_text(STRINGS[lang]["welcome"], reply_markup=get_main_keyboard(lang), parse_mode=ParseMode.HTML)

# --- WEB SERVER (DASHBOARD & WEBHOOK) ---
def get_dashboard_html(lang):
    texts = {
        'ky': {'title': 'Эң акыркы версиясын көчүрүп алып, чектөөсүз интернетке жол ачыңыз.', 'btn': 'Жүктөө (APK)'},
        'ru': {'title': 'Скачайте последнюю версию и получите доступ к безграничному интернету.', 'btn': 'Скачать (APK)'},
        'en': {'title': 'Download the latest version and unlock unlimited internet access.', 'btn': 'Download (APK)'}
    }
    t = texts.get(lang, texts['ky'])
    
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>mubVPN Premium</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;900&display=swap');
  
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  
  body {{ 
    font-family: 'Inter', sans-serif; 
    background-color: #06090D; 
    color: #fff; 
    display: flex; 
    flex-direction: column; 
    align-items: center; 
    justify-content: center; 
    min-height: 100vh; 
    overflow: hidden;
    position: relative;
  }}

  /* Animated Background Elements */
  .bg-orb-1 {{
    position: absolute; width: 400px; height: 400px;
    background: radial-gradient(circle, rgba(0,229,160,0.15) 0%, rgba(0,0,0,0) 70%);
    top: -100px; right: -100px; border-radius: 50%;
    animation: pulse 6s infinite alternate; z-index: 0;
  }}
  .bg-orb-2 {{
    position: absolute; width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(0,217,245,0.1) 0%, rgba(0,0,0,0) 70%);
    bottom: -50px; left: -100px; border-radius: 50%;
    animation: pulse 8s infinite alternate-reverse; z-index: 0;
  }}

  @keyframes pulse {{
    0% {{ transform: scale(1) translate(0, 0); }}
    100% {{ transform: scale(1.2) translate(20px, 20px); }}
  }}

  /* Glassmorphism Card */
  .card {{ 
    background: rgba(255, 255, 255, 0.03); 
    border: 1px solid rgba(255, 255, 255, 0.08); 
    border-radius: 32px; 
    padding: 50px 40px; 
    max-width: 420px; 
    width: 90%; 
    backdrop-filter: blur(20px); 
    -webkit-backdrop-filter: blur(20px);
    box-shadow: 0 30px 60px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.1);
    text-align: center;
    z-index: 10;
    position: relative;
    transform: translateY(20px);
    opacity: 0;
    animation: slideUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  }}

  @keyframes slideUp {{
    to {{ transform: translateY(0); opacity: 1; }}
  }}

  /* Shield Icon */
  .icon-wrapper {{
    width: 80px; height: 80px;
    background: linear-gradient(135deg, #00E5A0, #00896A);
    border-radius: 22px;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 24px;
    box-shadow: 0 10px 25px rgba(0, 229, 160, 0.4);
    position: relative;
  }}
  .icon-wrapper::after {{
    content: ''; position: absolute; inset: 0; border-radius: 22px;
    box-shadow: inset 0 2px 0 rgba(255,255,255,0.4);
  }}
  .icon-wrapper svg {{ width: 40px; height: 40px; fill: #fff; }}

  h1 {{ 
    font-size: 34px; font-weight: 900; margin-bottom: 12px; letter-spacing: -0.5px;
    background: linear-gradient(to right, #ffffff, #a8b2c1);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
  }}
  
  p.subtitle {{ 
    color: rgba(255,255,255,0.5); 
    font-size: 15px; line-height: 1.5; margin-bottom: 40px; font-weight: 400;
  }}

  /* Cyber Download Button */
  .download-btn {{ 
    display: flex; align-items: center; justify-content: center; gap: 10px; 
    background: #00E5A0; color: #06090D; font-weight: 700; font-size: 16px;
    padding: 18px 32px; border-radius: 100px; text-decoration: none; 
    box-shadow: 0 0 20px rgba(0, 229, 160, 0.3); 
    transition: all 0.3s ease;
    position: relative; overflow: hidden;
  }}
  
  .download-btn::before {{
    content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
    transition: all 0.5s ease;
  }}

  .download-btn:hover {{ 
    transform: translateY(-3px); 
    box-shadow: 0 10px 30px rgba(0, 229, 160, 0.5); 
    background: #00F5A0;
  }}
  
  .download-btn:hover::before {{ left: 100%; }}
  
  .download-btn svg {{ width: 20px; height: 20px; fill: #06090D; }}

  .footer {{ 
    margin-top: 40px; font-size: 13px; color: rgba(255,255,255,0.2); z-index: 10;
    font-weight: 600; letter-spacing: 1px;
  }}
</style>
</head>
<body>
  <div class="bg-orb-1"></div>
  <div class="bg-orb-2"></div>

  <div class="card">
    <div class="icon-wrapper">
      <svg viewBox="0 0 24 24"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/></svg>
    </div>
    <h1>mubVPN</h1>
    <p class="subtitle">{t['title']}</p>
    
    <a href="/download" class="download-btn">
      <svg viewBox="0 0 24 24"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>
      {t['btn']}
    </a>
  </div>
  
  <p class="footer">MUBVPN © 2025 | @KL_MUB</p>
</body>
</html>"""

import urllib.parse

class BotHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        if path == '/download':
            apk_url = 'https://github.com/Ulanbekmahmaraimov/mubvpn-bot/releases/download/v1.0.0/mubvpn.apk.apk'
            self.send_response(302)
            self.send_header('Location', apk_url)
            self.end_headers()
            return
            
        # Get language from URL params, default to 'ky'
        query_params = urllib.parse.parse_qs(parsed_path.query)
        lang = query_params.get('lang', ['ky'])[0]
        
        html_content = get_dashboard_html(lang)
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))

    def do_POST(self):
        if self.path == '/webhook':
            try:
                cl = int(self.headers['Content-Length'])
                body = self.rfile.read(cl).decode()
                data = json.loads(body)
                log.info(f"📥 Webhook received: {data}")

                status = data.get('status')
                # Lava кээде маалыматты ар кандай талааларга салат
                uid = data.get('additional_info') or data.get('additionalFields') or data.get('comment')
                amount = float(data.get('amount', 0))

                if status in ('success', 'paid') and uid:
                    # Суммага жараша айларды аныктоо (тиркемедегидей эле логика)
                    months = 1
                    if amount >= 1000: months = 12
                    elif amount >= 600: months = 6
                    elif amount >= 300: months = 3
                    
                    if firebase_set_premium(str(uid), months):
                        log.info(f"✅ Premium activated via Webhook for UID: {uid}")
                    else:
                        log.error(f"❌ Failed to update Firebase for UID: {uid}")
                
                self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
            except Exception as e:
                log.error(f"⚠️ Webhook error: {e}")
                self.send_response(500); self.end_headers()

def run_server():
    port = int(os.environ.get('PORT', 8080))
    HTTPServer(('0.0.0.0', port), BotHandler).serve_forever()

def keep_awake():
    while True:
        try: requests.get("https://mubvpn-bot.onrender.com", timeout=10)
        except: pass
        time.sleep(600)

def main():
    threading.Thread(target=run_server, daemon=True).start()
    threading.Thread(target=keep_awake, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    log.info("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()