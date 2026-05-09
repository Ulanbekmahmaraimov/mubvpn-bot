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
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nЭң тез жана коопсуз интернетке жол ачыңыз. Төлөм жүргүзүү же тиркемени жүктөө үчүн төмөнкү баскычтарды колдонуңуз:",
        "btn_pay": "💳 Сатып алуу", "btn_how": "📖 Кантип төлөйм?",
        "btn_download": "🚀 Тиркемени жүктөө",
        "btn_support": "👨‍💻 Колдоо", "btn_share": "🤝 Бөлүшүү",
        "pay_text": "💳 <b>Төлөөгө өтүү</b>\n\nТөлөм Telegram ичинде коопсуз өтөт:",
        "pay_btn_link": "💳 Telegram", "back": "⬅️ Артка", "next": "Кийинки ➡️",
        "check_btn": "✅ Төлөдүм (Текшерүү)",
        "checking": "⏳ Төлөм текшерилүүдө...",
        "success": "🎉 <b>Premium активдешти!</b>\n\nТиркемени ачып, VPN'ди колдоно бериңиз!",
        "not_found": "⚠️ Төлөм табылган жок. Төлөп бүтсөңүз, 1-2 мүнөт күтүп кайра басыңыз.",
        "how_step_1": "🚀 <b>1-КАДАМ: План тандоо</b>\n\n'Сатып алуу' баскычын басып, мөөнөттү тандаңыз. 1 жылдык план эң пайдалуу! ✅",
        "how_step_2": "📧 <b>2-КАДАМ: Почтаны жазуу</b>\n\nТөлөм барагында Email-ди жазыңыз. 📩",
        "how_step_3": "💵 <b>3-КАДАМ: Валюта тандоо</b>\n\nКомиссия аз болушу үчүн <b>RUB</b> же <b>KGS</b> тандаңыз. 💰",
        "how_step_4": "📱 <b>4-КАДАМ: Карта маалыматы</b>\n\nКарта номерин жана CVC-кодун жазыңыз. 💳",
        "how_step_5": "✅ <b>5-КАДАМ: Төлөмдү бүтүрүү</b>\n\n'Оплатить' баскычын басып, SMS кодду киргизиңиз. 🎉",
        "how_step_6": "🛠 <b>6-КАДАМ: Текшерүү</b>\n\nЭгер Premium иштебесе, боттогу 'Текшерүү' баскычын басыңыз. @kl_mub дайыма жардамга даяр! 👨‍💻",
        "menu_back": "Башкы меню:", "share_msg": "🚀 mubVPN — Android үчүн эң тез жана коопсуз VPN!\n\n✅ Блоктоолорду айланып өтөт\n✅ Маалыматтарды коргойт\n✅ Чектөөсүз интернет\n\nАзыр жүктөп ал! 👇",
        "share_title": "🤝 <b>Бөлүшүү:</b>", "btn_share_now": "📲 Бөлүшүү"
    },
    "ru": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nОткройте доступ к самому быстрому и безопасному интернету. Используйте кнопки ниже для оплаты или загрузки приложения:",
        "btn_pay": "💳 Купить", "btn_how": "📖 Как оплатить?",
        "btn_download": "🚀 Скачать приложение",
        "btn_support": "👨‍💻 Поддержка", "btn_share": "🤝 Поделиться",
        "pay_text": "💳 <b>Переход к оплате</b>\n\nОплата проходит безопасно внутри Telegram:",
        "pay_btn_link": "💳 Telegram", "back": "⬅️ Назад", "next": "Далее ➡️",
        "check_btn": "✅ Я оплатил (Проверять)",
        "checking": "⏳ Проверка платежа...",
        "success": "🎉 <b>Premium активирован!</b>\n\nОткройте приложение и наслаждайтесь VPN!",
        "not_found": "⚠️ Платеж не найден. Если вы оплатили, подождите 1-2 минуты и нажмите снова.",
        "how_step_1": "🚀 <b>ШАГ 1: Выбор тарифа</b>\n\nНажмите 'Купить' и выберите период. Годовой план самый выгодный! ✅",
        "how_step_2": "📧 <b>ШАГ 2: Ввод почты</b>\n\nУкажите Email для получения чека. 📩",
        "how_step_3": "💵 <b>ШАГ 3: Выбор валюты</b>\n\nВыбирайте <b>RUB</b> или <b>KGS</b> для минимальной комиссии. 💰",
        "how_step_4": "📱 <b>ШАГ 4: Данные карты</b>\n\nВведите номер карты и CVC-код. 💳",
        "how_step_5": "✅ <b>ШАГ 5: Завершение</b>\n\nНажмите 'Оплатить' и введите код из СМС. 🎉",
        "how_step_6": "🛠 <b>ШАГ 6: Проверка</b>\n\nЕсли Premium не активен, нажмите 'Проверить' в боте. @kl_mub на связи! 👨‍💻",
        "menu_back": "Главное меню:", "share_msg": "🚀 mubVPN — Самый быстрый и безопасный VPN для Android!\n\n✅ Обходит любые блокировки\n✅ Надежно защищает данные\n✅ Интернет без границ\n\nСкачай сейчас! 👇",
        "share_title": "🤝 <b>Поделиться:</b>", "btn_share_now": "📲 Поделиться"
    },
    "uz": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nEng tezkor va xavfsiz internetga ega bo'ling. To'lov qilish yoki ilovani yuklab olish uchun quyidagi tugmalardan foydalaning:",
        "btn_pay": "💳 Sotib olish", "btn_how": "📖 Qanday to'lash kerak?",
        "btn_download": "🚀 Ilovani yuklab olish",
        "btn_support": "👨‍💻 Qo'llab-quvvatlash", "btn_share": "🤝 Ulashish",
        "pay_text": "💳 <b>To'lovga o'tish</b>\n\nTo'lov Telegram ichida xavfsiz amalga oshiriladi:",
        "pay_btn_link": "💳 Telegram", "back": "⬅️ Orqaga", "next": "Keyingi ➡️",
        "check_btn": "✅ To'ladim (Tekshirish)",
        "checking": "⏳ To'lov tekshirilmoqda...",
        "success": "🎉 <b>Premium faollashdi!</b>\n\nIlovani oching va VPN-dan foydalaning!",
        "not_found": "⚠️ To'lov topilmadi. Agar to'lagan bo'lsangiz, 1-2 daqiqa kutib qayta bosing.",
        "how_step_1": "🚀 <b>1-QADAM: Tarifni tanlash</b>\n\n'Sotib olish' tugmasini bosing va muddatni tanlang. 1 yillik plan eng foydali! ✅",
        "how_step_2": "📧 <b>2-QADAM: Pochta kiritish</b>\n\nTo'lov sahifasida Email-ingizni yozing. 📩",
        "how_step_3": "💵 <b>3-QADAM: Valyuta tanlash</b>\n\nKomissiya kam bo'lishi uchun <b>RUB</b> yoki <b>KGS</b> tanlang. 💰",
        "how_step_4": "📱 <b>4-QADAM: Karta ma'lumotlari</b>\n\nKarta raqami va CVC-kodni yozing. 💳",
        "how_step_5": "✅ <b>5-QADAM: Yakunlash</b>\n\n'To'lash' tugmasini bosing va SMS kodni kiriting. 🎉",
        "how_step_6": "🛠 <b>6-QADAM: Tekshirish</b>\n\nAgar Premium ishlamasa, ботdagi 'Tekshirish' tugmasini bosing. @kl_mub yordamga tayyor! 👨‍💻",
        "menu_back": "Asosiy menyu:", "share_msg": "🚀 mubVPN — Android uchun eng tezkor va xavfsiz VPN!\n\n✅ Blokirovkalarni aylanib o'tadi\n✅ Ma'lumotlarni himoya qiladi\n✅ Cheksiz internet\n\nHozir yuklab ol! 👇",
        "share_title": "🤝 <b>Ulashish:</b>", "btn_share_now": "📲 Ulashish"
    },
    "tg": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nБа интернети зудтарин ва бехатар дастрасӣ пайдо кунед. Барои пардохт ё боргирии барнома аз тугмаҳои зерин истифода баред:",
        "btn_pay": "💳 Харидан", "btn_how": "📖 Чӣ тавр бояд пардохт кард?",
        "btn_download": "🚀 Боргирии барнома",
        "btn_support": "👨‍💻 Дастгирӣ", "btn_share": "🤝 Ирсол",
        "pay_text": "💳 <b>Гузаштан ба пардохт</b>\n\nПардохт дар дохили Telegram бехатар мегузарад:",
        "pay_btn_link": "💳 Telegram", "back": "⬅️ Ба ақиб", "next": "Оянда ➡️",
        "check_btn": "✅ Ман пардохт кардам (Санҷиш)",
        "checking": "⏳ Санҷиши пардохт...",
        "success": "🎉 <b>Premium фаъол шуд!</b>\n\nБарномаро кушоед ва аз VPN лаззат баред!",
        "not_found": "⚠️ Пардохт ёфт нашуд. Агар пардохт карда бошед, 1-2 дақиқа интизор шавед.",
        "how_step_1": "🚀 <b>ҚАДАМИ 1: Интихоби тариф</b>\n\n'Харидан'-ро пахш кунед. Нақшаи солона беҳтарин аст! ✅",
        "how_step_2": "📧 <b>ҚАДАМИ 2: Ворид кардани почта</b>\n\nEmail-и худро ворид кунед. 📩",
        "how_step_3": "💵 <b>ҚАДАМИ 3: Интихоби асъор</b>\n\n<b>RUB</b> ё <b>KGS</b>-ро интихоб кунед. 💰",
        "how_step_4": "📱 <b>ҚАДАМИ 4: Маълумоти корт</b>\n\nРақами корт ва рамзи CVC-ро ворид кунед. 💳",
        "how_step_5": "✅ <b>ҚАДАМИ 5: Анҷоми пардохт</b>\n\n'Пардохт кардан'-ро пахш кунед ва рамзи СМС-ро ворид кунед. 🎉",
        "how_step_6": "🛠 <b>ҚАДАМИ 6: Санҷиш</b>\n\nАгар Premium фаъол нашуда бошад, тугмаи 'Санҷиш'-ро пахш кунед. @kl_mub ҳамеша тайёр аст! 👨‍💻",
        "menu_back": "Менюи асосӣ:", "share_msg": "🚀 mubVPN — VPN-и зудтарин ва бехатар барои Android!\n\n✅ Маҳдудиятҳоро давр мезанад\n✅ Маълумотро ҳифз мекунад\n✅ Интернети бемаҳдуд\n\nHоло боргирӣ кун! 👇",
        "share_title": "🤝 <b>Ирсол:</b>", "btn_share_now": "📲 Ирсол"
    },
    "kk": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nЕң жылдам және қауіпсіз интернетке жол ашыңыз. Төлөм жасау немесе қосымшаны жүктеу үчүн төмендегі батырмаларды қолданыңыз:",
        "btn_pay": "💳 Сатып алу", "btn_how": "📖 Қалай төлеу керек?",
        "btn_download": "🚀 Қосымшаны жүктеу",
        "btn_support": "👨‍💻 Қолдау", "btn_share": "🤝 Бөлісу",
        "pay_text": "💳 <b>Төлемге өту</b>\n\nТөлем Telegram ішінде қауіпсіз өтеді:",
        "pay_btn_link": "💳 Telegram", "back": "⬅️ Артқа", "next": "Келесі ➡️",
        "check_btn": "✅ Төледім (Тексеру)",
        "checking": "⏳ Төлем тексерілуде...",
        "success": "🎉 <b>Premium белсендірілді!</b>\n\nҚосымшаны ашып, VPN-ді қолдана беріңіз!",
        "not_found": "⚠️ Төлем табылмады. Егер төлеген болсаңыз, 1-2 минут күтіңіз.",
        "how_step_1": "🚀 <b>1-ҚАДАМ: Тариф таңдау</b>\n\n'Сатып алу' батырмасын басыңыз. 1 жылдық жоспар ең тиімді! ✅",
        "how_step_2": "📧 <b>2-ҚАДАМ: Поштаны енгізу</b>\n\nEmail-іңізді жазыңыз. 📩",
        "how_step_3": "💵 <b>3-ҚАДАМ: Валютаны таңдау</b>\n\nКомиссия аз болуы үчүн <b>RUB</b> немесе <b>KGS</b> таңдаңыз. 💰",
        "how_step_4": "📱 <b>4-ҚАДАМ: Карта мәліметтері</b>\n\nКарта нөмірін жана CVC-кодты енгізіңіз. 💳",
        "how_step_5": "✅ <b>5-ҚАДАМ: Аяқтау</b>\n\n'Төлеу' батырмасын басып, СМС кодты енгізіңіз. 🎉",
        "how_step_6": "🛠 <b>6-ҚАДАМ: Тексеру</b>\n\nЕгер жұмыс істемесе, боттағы 'Тексеру' батырмасын басыңыз. @kl_mub көмектеседі! 👨‍💻",
        "menu_back": "Басты мәзір:", "share_msg": "🚀 mubVPN — Android үшін ең жылдам және қауіпсіз VPN!\n\n✅ Блоктауларды айналып өтеді\n✅ Деректерді қорғайды\n✅ Шектеусіз интернет\n\nҚазір жүктеп ал! 👇",
        "share_title": "🤝 <b>Бөлісу:</b>", "btn_share_now": "📲 Бөлісу"
    },
    "tr": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nEn hızlı ve en güvenli internetin keyfini çıkarın. Ödeme yapmak veya uygulamayı indirmek için aşağıdaki butonları kullanın:",
        "btn_pay": "💳 Satın Al", "btn_how": "📖 Nasıl ödenir?",
        "btn_download": "🚀 Uygulamayı İndir",
        "btn_support": "👨‍💻 Destek", "btn_share": "🤝 Paylaş",
        "pay_text": "💳 <b>Ödemeye Geç</b>\n\nÖdeme Telegram içinde güvenli bir şekilde yapılır:",
        "pay_btn_link": "💳 Telegram", "back": "⬅️ Geri", "next": "İleri ➡️",
        "check_btn": "✅ Ödedim (Kontrol Et)",
        "checking": "⏳ Ödeme kontrol ediliyor...",
        "success": "🎉 <b>Premium Aktif Edildi!</b>\n\nUygulamayı açın ve VPN'in tadını çıkarın!",
        "not_found": "⚠️ Ödeme bulunamadı. Ödeme yaptıysanız 1-2 dakika bekleyin.",
        "how_step_1": "🚀 <b>ADIM 1: Plan seçimi</b>\n\n'Satın Al'а tıklayın. Yıllık plan en karlı olanıdır! ✅",
        "how_step_2": "📧 <b>ADIM 2: E-posta girin</b>\n\nÖdeme sayfasında Email adresinizi girin. 📩",
        "how_step_3": "💵 <b>ADIM 3: Para birimi seçin</b>\n\n<b>RUB</b> veya <b>KGS</b> seçin. 💰",
        "how_step_4": "📱 <b>ADIM 4: Kart bilgileri</b>\n\nKart numaranızı ve CVC kodunuzu girin. 💳",
        "how_step_5": "✅ <b>ADIM 5: Ödemeyi tamamla</b>\n\n'Öde'ye tıklayın ve SMS kodunu girin. 🎉",
        "how_step_6": "🛠 <b>ADIM 6: Doğrulama</b>\n\nAktif değilse ботта 'Kontrol Et'e tıklayın. @kl_mub yardıma hazır! 👨‍💻",
        "menu_back": "Ana Menü:", "share_msg": "🚀 mubVPN — Android үчүн en hızlı ve güvenli VPN!\n\n✅ Tüm engelleri aşar\n✅ Verileri korur\n✅ Sınırsız İnternet\n\nHemen indir! 👇",
        "share_title": "🤝 <b>Paylaş:</b>", "btn_share_now": "📲 Paylaş"
    },
    "en": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nUnlock the fastest and most secure internet access. Use the buttons below to pay or download the application:",
        "btn_pay": "💳 Buy", "btn_how": "📖 How to pay?",
        "btn_download": "🚀 Download App",
        "btn_support": "👨‍💻 Support", "btn_share": "🤝 Share",
        "pay_text": "💳 <b>Proceed to Payment</b>\n\nThe payment is secure within Telegram:",
        "pay_btn_link": "💳 Telegram", "back": "⬅️ Back", "next": "Next ➡️",
        "check_btn": "✅ I have paid (Check)",
        "checking": "⏳ Checking payment...",
        "success": "🎉 <b>Premium activated!</b>\n\nOpen the app and enjoy your VPN!",
        "not_found": "⚠️ Payment not found. If you have paid, wait 1-2 minutes.",
        "how_step_1": "🚀 <b>STEP 1: Choose plan</b>\n\nClick 'Buy'. Yearly plan is the best value! ✅",
        "how_step_2": "📧 <b>STEP 2: Enter Email</b>\n\nEnter your Email on the payment page. 📩",
        "how_step_3": "💵 <b>STEP 3: Choose currency</b>\n\nChoose <b>RUB</b> or <b>KGS</b> for minimum commission. 💰",
        "how_step_4": "📱 <b>STEP 4: Card details</b>\n\nEnter card number and CVC code. 💳",
        "how_step_5": "✅ <b>STEP 5: Complete</b>\n\nClick 'Pay' and enter the SMS code. 🎉",
        "how_step_6": "🛠 <b>STEP 6: Verification</b>\n\nCheck the app. If not active, click 'Check' in the bot. @kl_mub is here to help! 👨‍💻",
        "menu_back": "Main Menu:", "share_msg": "🚀 mubVPN — The fastest and safest VPN for Android!\n\n✅ Bypasses all blocks\n✅ Protects your data\n✅ Unlimited Internet\n\nDownload now! 👇",
        "share_title": "🤝 <b>Share:</b>", "btn_share_now": "📲 Share"
    }
}

# --- КЛАВИАТУРАЛАР ---
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
        L = STRINGS[lang]
        # Боттун шилтемесин эмес, Render сайтынын шилтемесин бөлүшөбүз (ал сүрөтү менен чыгат)
        share_url = f"https://t.me/share/url?url=https://mubvpn-bot.onrender.com/?lang={lang}&text={html.escape(L['share_msg'])}"
        kb = [[InlineKeyboardButton(L["btn_share_now"], url=share_url)], [InlineKeyboardButton(L["back"], callback_data='main_menu')]]
        await query.message.edit_text(L["share_title"], reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

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
        'ky': {
            'h1': 'mubVPN — Android үчүн тез жана коопсуз VPN',
            'sub': '🚀 mubVPN — чектөөсүз интернетке коопсуз жол!\n\n✅ Блоктоолорду айланып өтөт\n✅ Маалыматтарды ишенимдүү шифрлейт\n✅ Бир таптоо менен туташуу\n✅ Жогорку ылдамдык\n\nАзыр жүктөп алып, эркиндиктен ырахат алыңыз! 👇',
            'btn_dl': 'Android үчүн жүктөө',
            'features_title': 'Эмне үчүн mubVPN тандашат?',
            'f1_t': 'Smart Route', 'f1_d': 'Ылдам иштөө үчүн автоматтык жол тандоо.',
            'f2_t': 'Коопсуздук', 'f2_d': 'Маалыматтарыңызды шифрлөө менен коргойт.',
            'f3_t': 'Android үчүн', 'f3_d': 'Заманбап интерфейс.',
            'steps_title': 'Орнотуу 3 кадамда',
            's1_t': 'Жүктөп алыңыз', 's1_d': 'Жүктөө баскычын басып, APK күтүңүз.',
            's2_t': 'Орнотуңуз', 's2_d': 'Файлды ачып, орнотууну ырастаңыз.',
            's3_t': 'Туташыңыз', 's3_d': 'Тиркемени ачып, коргоону иштетиңиз.'
        },
        'ru': {
            'h1': 'mubVPN — Быстрый и безопасный VPN для Android',
            'sub': '🚀 mubVPN — ваш безопасный доступ к любимым сервисам без ограничений!\n\n✅ Обходит любые блокировки\n✅ Надежно защищает ваши данные\n✅ Подключение в один тап\n✅ Высокая и стабильная скорость\n\nСкачай и пользуйся без ограничений уже сейчас! 👇',
            'btn_dl': 'Скачать для Android',
            'features_title': 'Почему выбирают mubVPN?',
            'f1_t': 'Smart Route', 'f1_d': 'Автоподбор лучшего маршрута.',
            'f2_t': 'Безопасность', 'f2_d': 'Шифрование и полная анонимность.',
            'f3_t': 'Android-first', 'f3_d': 'Оптимизированный интерфейс.',
            'steps_title': 'Установка за 3 шага',
            's1_t': 'Скачайте файл', 's1_d': 'Нажмите кнопку загрузки и дождитесь APK.',
            's2_t': 'Установите APK', 's2_d': 'Откройте файл и подтвердите установку.',
            's3_t': 'Пользуйтесь!', 's3_d': 'Запустите приложение и включите защиту.'
        },
        'uz': {
            'h1': 'mubVPN — Android uchun tezkor va xavfsiz VPN',
            'sub': '🚀 mubVPN — sevimli xizmatlaringizga cheklovlarsiz xavfsiz kirish!\n\n✅ Toʻsiqlarni aylanib oʻtadi\n✅ Maʼlumotlaringizni xavfsiz himoya qiladi\n✅ Bir marta bosish bilan ulanish\n✅ Yuqori va barqaror tezlik\n\nHoziroq yuklab oling va cheklovsiz foydalaning! 👇',
            'btn_dl': 'Android uchun yuklash',
            'features_title': 'Nima uchun mubVPN?',
            'f1_t': 'Smart Route', 'f1_d': 'Tezlik uchun eng yaxshi yoʻnalish.',
            'f2_t': 'Xavfsizlik', 'f2_d': 'Maʼlumotlarni shifrlash.',
            'f3_t': 'Android-first', 'f3_d': 'Qulay interfeys.',
            'steps_title': '3 qadamda oʻrnatish',
            's1_t': 'Yuklab oling', 's1_d': 'Tugmani bosing va APKni kuting.',
            's2_t': 'Oʻrnating', 's2_d': 'Faylni oching va tasdiqlang.',
            's3_t': 'Ulaning', 's3_d': 'Ilovani oching va himoyani yoqing.'
        },
        'tg': {
            'h1': 'mubVPN — VPN-и тез ва бехатар барои Android',
            'sub': '🚀 mubVPN — дастрасии бехатари шумо ба хидматҳои дӯстдошта бе маҳдудият!\n\n✅ Маҳдудиятҳоро давр мезанад\n✅ Маълумоти шуморо боэътимод ҳифз мекунад\n✅ Пайвастшавӣ бо як клик\n✅ Суръати баланд ва устувор\n\nHоло боргирӣ кунед ва истифода баред! 👇',
            'btn_dl': 'Боргирӣ барои Android',
            'features_title': 'Чаро mubVPN?',
            'f1_t': 'Smart Route', 'f1_d': 'Интихоби автоматии масир.',
            'f2_t': 'Бехатарӣ', 'f2_d': 'Рамзгузории додаҳо.',
            'f3_t': 'Android-first', 'f3_d': 'Интерфейси зебо.',
            'steps_title': 'Насб дар 3 марҳила',
            's1_t': 'Боргирӣ кунед', 's1_d': 'Тугмаро пахш кунед ва APK-ро интизор шавед.',
            's2_t': 'Насб кунед', 's2_d': 'Файлро кушоед ва тасдиқ кунед.',
            's3_t': 'Истифода баред!', 's3_d': 'Барномаро оғоз кунед ва муҳофизатро фаъол кунед.'
        },
        'kk': {
            'h1': 'mubVPN — Android үшін жылдам және қауіпсіз VPN',
            'sub': '🚀 mubVPN — сүйікті қызметтеріңізге шектеусіз қауіпсіз кіру!\n\n✅ Блоктауларды айналып өтеді\n✅ Деректеріңізді сенімді қорғайды\n✅ Бір рет басу арқылы қосылу\n✅ Жоғары және тұрақты жылдамдық\n\nҚазір жүктеп алыңыз және шектеусіз пайдаланыңыз! 👇',
            'btn_dl': 'Android үшін жүктеу',
            'features_title': 'Неліктен mubVPN?',
            'f1_t': 'Smart Route', 'f1_d': 'Ең жақсы жолды таңдау.',
            'f2_t': 'Қауіпсіздік', 'f2_d': 'Деректерді шифрлау.',
            'f3_t': 'Android-first', 'f3_d': 'Ыңғайлы интерфейс.',
            'steps_title': '3 қадамда орнату',
            's1_t': 'Жүктеп алыңыз', 's1_d': 'Батырманы басып, APK күтіңіз.',
            's2_t': 'Орнатыңыз', 's2_d': 'Файлды ашып, растаңыз.',
            's3_t': 'Қосылыңыз!', 's3_d': 'Қорғауды қосыңыз.'
        },
        'tr': {
            'h1': 'mubVPN — Android için Hızlı и Güvenli VPN',
            'sub': '🚀 mubVPN — favori hizmetlerinize kısıtlama olmadan güvenli erişim!\n\n✅ Tüm engelleri aşar\n✅ Verilerinizi güvenle korur\n✅ Tek dokunuşla bağlantı\n✅ Yüksek ve istikrarlı hız\n\nHemen indirin ve özgürlüğün tadını çıkarın! 👇',
            'btn_dl': 'Android için İndir',
            'features_title': 'Neden mubVPN?',
            'f1_t': 'Smart Route', 'f1_d': 'En iyi rotanın otomatik seçimi.',
            'f2_t': 'Güvenlik', 'f2_d': 'Veri şifreleme.',
            'f3_t': 'Android-first', 'f3_d': 'Optimize arayüz.',
            'steps_title': '3 Adımda Kurulum',
            's1_t': 'Dosyayı İndir', 's1_d': 'Düğmeye basın ve APKyı bekleyin.',
            's2_t': 'Kurulumu Yap', 's2_d': 'Dosyayı açın ve onaylayın.',
            's3_t': 'Kullanmaya Başla!', 's3_d': 'Korumayı açın.'
        },
        'en': {
            'h1': 'mubVPN — Fast & Secure VPN for Android',
            'sub': '🚀 mubVPN — your secure access to favorite services without limits!\n\n✅ Bypasses all restrictions\n✅ Reliability protects your data\n✅ One-tap connection\n✅ High and stable speed\n\nDownload and use without limits now! 👇',
            'btn_dl': 'Download for Android',
            'features_title': 'Why choose mubVPN?',
            'f1_t': 'Smart Route', 'f1_d': 'Auto-selection of the best route.',
            'f2_t': 'Security', 'f2_d': 'End-to-end encryption.',
            'f3_t': 'Android-first', 'f3_d': 'Sleek interface.',
            'steps_title': 'Setup in 3 steps',
            's1_t': 'Download', 's1_d': 'Click download and wait for the APK.',
            's2_t': 'Install', 's2_d': 'Open the file and confirm.',
            's3_t': 'Connect', 's3_d': 'Enjoy freedom.'
        }
    }
    t = texts.get(lang, texts['ru'])
    
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{t['h1']}</title>
<!-- Open Graph / Social Media Preview -->
<meta property="og:type" content="website">
<meta property="og:url" content="https://mubvpn-bot.onrender.com/">
<meta property="og:title" content="🛡 {t['h1']}">
<meta property="og:description" content="{t['sub']}">
<meta property="og:image" content="https://raw.githubusercontent.com/Ulanbekmahmaraimov/mubvpn-bot/main/assets/preview.png">
<meta property="og:image:secure_url" content="https://raw.githubusercontent.com/Ulanbekmahmaraimov/mubvpn-bot/main/assets/preview.png">
<meta property="og:image:type" content="image/png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="🛡 {t['h1']}">
<meta name="twitter:description" content="{t['sub']}">
<meta name="twitter:image" content="https://raw.githubusercontent.com/Ulanbekmahmaraimov/mubvpn-bot/main/assets/preview.png">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
  
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  
  body {{ 
    font-family: 'Inter', sans-serif; 
    background-color: #03060a; 
    color: #fff; 
    line-height: 1.6;
    overflow-x: hidden;
    position: relative;
    min-height: 100vh;
  }}

  .container {{
    max-width: 1100px;
    margin: 0 auto;
    padding: 0 24px;
    position: relative;
    z-index: 10;
  }}

  /* Ultra Premium Background Orbs */
  .bg-orb {{
    position: fixed; border-radius: 50%; z-index: 0; filter: blur(100px); opacity: 0.35;
    animation: orbMove 20s infinite alternate cubic-bezier(0.45, 0, 0.55, 1);
  }}
  .orb-1 {{ width: 600px; height: 600px; background: #00E5A0; top: -200px; right: -100px; animation-duration: 15s; }}
  .orb-2 {{ width: 500px; height: 500px; background: #00896A; bottom: -150px; left: -150px; animation-duration: 25s; }}
  .orb-3 {{ width: 300px; height: 300px; background: #004d40; top: 40%; left: 30%; opacity: 0.2; }}

  @keyframes orbMove {{
    0% {{ transform: translate(0, 0) scale(1); }}
    100% {{ transform: translate(50px, 50px) scale(1.1); }}
  }}

  /* Header */
  header {{
    padding: 40px 0;
    display: flex;
    justify-content: center;
  }}

  .logo {{
    font-weight: 900;
    font-size: 32px;
    letter-spacing: -2px;
    background: linear-gradient(135deg, #fff 30%, #00E5A0);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 0 20px rgba(0, 229, 160, 0.3));
  }}

  /* Hero Section - Ultra Glass */
  .hero {{
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.01));
    border: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(40px);
    -webkit-backdrop-filter: blur(40px);
    border-radius: 48px;
    padding: 100px 40px;
    text-align: center;
    margin-bottom: 60px;
    box-shadow: 0 50px 100px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.1);
    position: relative;
    overflow: hidden;
  }}

  .hero::after {{
    content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%;
    background: conic-gradient(from 0deg, transparent, rgba(0,229,160,0.1), transparent);
    animation: rotate 10s linear infinite; z-index: -1;
  }}

  @keyframes rotate {{ 100% {{ transform: rotate(360deg); }} }}

  .badge {{
    display: inline-block;
    padding: 10px 20px;
    background: rgba(0, 229, 160, 0.15);
    border: 1px solid rgba(0, 229, 160, 0.3);
    border-radius: 100px;
    color: #00E5A0;
    font-size: 12px;
    font-weight: 900;
    margin-bottom: 40px;
    text-transform: uppercase;
    letter-spacing: 3px;
    animation: pulse 2s infinite;
  }}

  @keyframes pulse {{
    0% {{ box-shadow: 0 0 0 0 rgba(0, 229, 160, 0.4); }}
    70% {{ box-shadow: 0 0 0 15px rgba(0, 229, 160, 0); }}
    100% {{ box-shadow: 0 0 0 0 rgba(0, 229, 160, 0); }}
  }}

  h1 {{
    font-size: clamp(36px, 9vw, 72px);
    font-weight: 950;
    line-height: 0.95;
    margin-bottom: 30px;
    letter-spacing: -3px;
    background: linear-gradient(to bottom, #fff, #888);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }}

  .hero p {{
    font-size: 20px;
    color: rgba(255,255,255,0.6);
    max-width: 700px;
    margin: 0 auto 60px;
    font-weight: 500;
  }}

  .btn-download {{
    display: inline-flex;
    align-items: center;
    gap: 16px;
    background: linear-gradient(135deg, #00E5A0, #00C58A);
    color: #03060a;
    padding: 24px 60px;
    border-radius: 24px;
    font-weight: 900;
    font-size: 22px;
    text-decoration: none;
    box-shadow: 0 25px 50px rgba(0, 229, 160, 0.4);
    transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  }}

  .btn-download:hover {{
    transform: translateY(-8px) scale(1.05);
    box-shadow: 0 35px 70px rgba(0, 229, 160, 0.6);
  }}

  /* Floating Features Grid */
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 30px;
    margin-bottom: 80px;
  }}

  .glass-card {{
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(25px);
    -webkit-backdrop-filter: blur(25px);
    padding: 48px;
    border-radius: 40px;
    transition: all 0.4s ease;
    animation: float 6s infinite ease-in-out;
  }}
  .glass-card:nth-child(2) {{ animation-delay: 1s; }}
  .glass-card:nth-child(3) {{ animation-delay: 2s; }}

  @keyframes float {{
    0%, 100% {{ transform: translateY(0); }}
    50% {{ transform: translateY(-15px); }}
  }}

  .glass-card:hover {{
    background: rgba(255, 255, 255, 0.06);
    border-color: #00E5A0;
    transform: translateY(-20px) scale(1.02);
  }}

  .f-icon {{
    width: 64px; height: 64px;
    background: rgba(0, 229, 160, 0.1);
    border-radius: 20px;
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 30px;
    color: #00E5A0;
    border: 1px solid rgba(0, 229, 160, 0.2);
    box-shadow: 0 10px 20px rgba(0, 229, 160, 0.1);
  }}

  .glass-card h3 {{ font-size: 24px; font-weight: 800; margin-bottom: 16px; letter-spacing: -0.5px; }}
  .glass-card p {{ color: rgba(255,255,255,0.5); font-size: 16px; line-height: 1.6; }}

  /* Steps Section - Ultra Premium */
  .steps-title {{ text-align: center; font-size: 40px; font-weight: 950; margin: 100px 0 50px; letter-spacing: -1.5px; }}
  
  .step-card {{
    display: flex;
    align-items: flex-start;
    gap: 30px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    padding: 40px;
    border-radius: 32px;
    margin-bottom: 24px;
    backdrop-filter: blur(15px);
    transition: 0.3s;
  }}
  .step-card:hover {{ transform: scale(1.01); background: rgba(255, 255, 255, 0.05); }}

  .step-num {{
    flex-shrink: 0;
    width: 60px; height: 60px;
    background: linear-gradient(135deg, #00E5A0, #00896A);
    color: #03060a;
    border-radius: 18px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 950; font-size: 24px;
    box-shadow: 0 10px 20px rgba(0, 229, 160, 0.3);
  }}

  .step-content h4 {{ font-size: 20px; font-weight: 800; margin-bottom: 8px; }}
  .step-content p {{ color: rgba(255,255,255,0.5); font-size: 16px; }}

  footer {{
    padding: 100px 0 60px;
    text-align: center;
    color: rgba(255,255,255,0.3);
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
  }}

  @media (max-width: 768px) {{
    .hero {{ padding: 80px 24px; }}
    h1 {{ font-size: 48px; }}
    .grid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
  <div class="bg-orb orb-1"></div>
  <div class="bg-orb orb-2"></div>
  <div class="bg-orb orb-3"></div>

  <div class="container">
    <header>
      <div class="logo">mubVPN</div>
    </header>

    <section class="hero">
      <div class="badge">💎 Next-Gen Security</div>
      <h1>{t['h1']}</h1>
      <p>{t['sub']}</p>
      <a href="/download" class="btn-download">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
        {t['btn_dl']}
      </a>
    </section>

    <div class="grid">
      <div class="glass-card">
        <div class="f-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg></div>
        <h3>{t['f1_t']}</h3>
        <p>{t['f1_d']}</p>
      </div>
      <div class="glass-card">
        <div class="f-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg></div>
        <h3>{t['f2_t']}</h3>
        <p>{t['f2_d']}</p>
      </div>
      <div class="glass-card">
        <div class="f-icon"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect><line x1="12" y1="18" x2="12.01" y2="18"></line></svg></div>
        <h3>{t['f3_t']}</h3>
        <p>{t['f3_d']}</p>
      </div>
    </div>

    <h2 class="steps-title">{t['steps_title']}</h2>
    
    <div class="step-card">
      <div class="step-num">01</div>
      <div class="step-content">
        <h4>{t['s1_t']}</h4>
        <p>{t['s1_d']}</p>
      </div>
    </div>
    
    <div class="step-card">
      <div class="step-num">02</div>
      <div class="step-content">
        <h4>{t['s2_t']}</h4>
        <p>{t['s2_d']}</p>
      </div>
    </div>
    
    <div class="step-card">
      <div class="step-num">03</div>
      <div class="step-content">
        <h4>{t['s3_t']}</h4>
        <p>{t['s3_d']}</p>
      </div>
    </div>

    <footer>
      MUBVPN ULTRA PREMIUM © 2025 | @KL_MUB
    </footer>
  </div>
</body>
</html>"""

import urllib.parse

class BotHandler(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        if path == '/download':
            apk_url = 'https://github.com/Ulanbekmahmaraimov/mubvpn-bot/releases/download/v1.0.0/mubvpn.apk'
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
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()