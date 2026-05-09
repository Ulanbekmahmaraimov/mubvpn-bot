import logging
import os
import json
import requests
import threading
import time
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
        log.error(f"Firebase error: {e}")
        return False

# --- STRINGS ---
STRINGS = {
    "ky": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nЭң тез жана коопсуз интернетке жол ачыңыз. Төлөм жүргүзүү же тиркемени жүктөө үчүн төмөнкү баскычтарды колдонуңуз:",
        "btn_pay": "💳 Сатып алуу", "btn_how": "📖 Кантип төлөйм?", "btn_download": "🚀 Тиркемени жүктөө", "btn_support": "👨‍💻 Колдоо", "btn_share": "🤝 Бөлүшүү",
        "pay_text": "💳 <b>Төлөөгө өтүү</b>\n\nТөлөм Telegram ичинде коопсуз өтөт:",
        "pay_btn_link": "💳 Telegram", "back": "⬅️ Артка", "next": "Кийинки ➡️",
        "check_btn": "✅ Төлөдүм (Текшерүү)", "checking": "⏳ Төлөм текшерилүүдө...", "success": "🎉 <b>Premium активдешти!</b>",
        "not_found": "⚠️ Төлөм табылган жок.",
        "how_step_1": "🚀 <b>1-КАДАМ: План тандоо</b>\n\n'Сатып алуу' баскычын басыңыз.",
        "how_step_2": "📧 <b>2-КАДАМ: Почтаны жазуу</b>\n\nEmail-ди жазыңыз.",
        "how_step_3": "💵 <b>3-КАДАМ: Валюта тандоо</b>\n\nRUB же KGS тандаңыз.",
        "how_step_4": "📱 <b>4-КАДАМ: Карта маалыматы</b>\n\nКарта номерин жазыңыз.",
        "how_step_5": "✅ <b>5-КАДАМ: Төлөмдү бүтүрүү</b>\n\nSMS кодду киргизиңиз.",
        "how_step_6": "🛠 <b>6-КАДАМ: Текшерүү</b>\n\n@kl_mub дайыма жардамга даяр!",
        "menu_back": "Башкы меню:", "share_msg": "🚀 mubVPN — Android үчүн эң тез жана коопсуз VPN!",
        "share_title": "🤝 <b>Бөлүшүү:</b>", "btn_share_now": "📲 Бөлүшүү"
    },
    "ru": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nОткройте доступ к самому быстрому и безопасному интернету:",
        "btn_pay": "💳 Купить", "btn_how": "📖 Как оплатить?", "btn_download": "🚀 Скачать", "btn_support": "👨‍💻 Поддержка", "btn_share": "🤝 Поделиться",
        "pay_text": "💳 <b>Переход к оплате</b>\n\nОплата безопасна:",
        "pay_btn_link": "💳 Оплатить", "back": "⬅️ Назад", "next": "Далее ➡️",
        "check_btn": "✅ Проверить", "checking": "⏳ Проверка...", "success": "🎉 <b>Premium активирован!</b>",
        "not_found": "⚠️ Платеж не найден.",
        "how_step_1": "🚀 <b>ШАГ 1: Тариф</b>\n\nНажмите 'Купить'.",
        "how_step_2": "📧 <b>ШАГ 2: Почта</b>\n\nУкажите Email.",
        "how_step_3": "💵 <b>ШАГ 3: Валюта</b>\n\nRUB или KGS.",
        "how_step_4": "📱 <b>ШАГ 4: Карта</b>\n\nВведите номер карты.",
        "how_step_5": "✅ <b>ШАГ 5: СМС</b>\n\nВведите код.",
        "how_step_6": "🛠 <b>ШАГ 6: Проверка</b>\n\n@kl_mub на связи!",
        "menu_back": "Главное меню:", "share_msg": "🚀 mubVPN — Самый быстрый VPN!",
        "share_title": "🤝 <b>Поделиться:</b>", "btn_share_now": "📲 Поделиться"
    },
    "uz": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nEng tezkor va xavfsiz internet:",
        "btn_pay": "💳 Sotib olish", "btn_how": "📖 Qanday to'lash?", "btn_download": "🚀 Yuklab olish", "btn_support": "👨‍💻 Yordam", "btn_share": "🤝 Ulashish",
        "pay_text": "💳 <b>To'lovga o'tish</b>",
        "pay_btn_link": "💳 To'lash", "back": "⬅️ Orqaga", "next": "Keyingi ➡️",
        "check_btn": "✅ Tekshirish", "checking": "⏳ Tekshirilmoqda...", "success": "🎉 <b>Premium faol!</b>",
        "not_found": "⚠️ To'lov topilmadi.",
        "how_step_1": "🚀 <b>1-QADAM</b>\n\nSotib olishni bosing.",
        "how_step_2": "📧 <b>2-QADAM</b>\n\nEmail yozing.",
        "how_step_3": "💵 <b>3-QADAM</b>\n\nRUB/KGS tanlang.",
        "how_step_4": "📱 <b>4-QADAM</b>\n\nKarta raqami.",
        "how_step_5": "✅ <b>5-QADAM</b>\n\nSMS kod.",
        "how_step_6": "🛠 <b>6-QADAM</b>\n\n@kl_mub yordam beradi.",
        "menu_back": "Asosiy menyu:", "share_msg": "🚀 mubVPN — Android uchun VPN!",
        "share_title": "🤝 <b>Ulashish:</b>", "btn_share_now": "📲 Ulashish"
    },
    "tg": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nЗудтарин ва бехатар:",
        "btn_pay": "💳 Харидан", "btn_how": "📖 Чӣ тавр?", "btn_download": "🚀 Боргирӣ", "btn_support": "👨‍💻 Дастгирӣ", "btn_share": "🤝 Ирсол",
        "pay_text": "💳 <b>Гузаштан ба пардохт</b>",
        "pay_btn_link": "💳 Пардохт", "back": "⬅️ Ба ақиб", "next": "Оянда ➡️",
        "check_btn": "✅ Санҷиш", "checking": "⏳ Санҷиш...", "success": "🎉 <b>Premium фаъол!</b>",
        "not_found": "⚠️ Пардохт ёфт нашуд.",
        "how_step_1": "🚀 <b>ҚАДАМИ 1</b>\n\n'Харидан'-ро пахш кунед.",
        "how_step_2": "📧 <b>ҚАДАМИ 2</b>\n\nEmail ворид кунед.",
        "how_step_3": "💵 <b>ҚАДАМИ 3</b>\n\nRUB/KGS интихоб кунед.",
        "how_step_4": "📱 <b>ҚАДАМИ 4</b>\n\nРақами корт.",
        "how_step_5": "✅ <b>ҚАДАМИ 5</b>\n\nРамзи СМС.",
        "how_step_6": "🛠 <b>ҚАДАМИ 6</b>\n\n@kl_mub ҳамеша тайёр.",
        "menu_back": "Менюи асосӣ:", "share_msg": "🚀 mubVPN — VPN-и беҳтарин!",
        "share_title": "🤝 <b>Ирсол:</b>", "btn_share_now": "📲 Ирсол"
    },
    "kk": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nЕң жылдам және қауіпсіз:",
        "btn_pay": "💳 Сатып алу", "btn_how": "📖 Қалай?", "btn_download": "🚀 Жүктеу", "btn_support": "👨‍💻 Қолдау", "btn_share": "🤝 Бөлісу",
        "pay_text": "💳 <b>Төлемге өту</b>",
        "pay_btn_link": "💳 Төлеу", "back": "⬅️ Артқа", "next": "Келесі ➡️",
        "check_btn": "✅ Тексеру", "checking": "⏳ Тексеру...", "success": "🎉 <b>Premium белсенді!</b>",
        "not_found": "⚠️ Төлем табылмады.",
        "how_step_1": "🚀 <b>1-ҚАДАМ</b>\n\nСатып алуды басыңыз.",
        "how_step_2": "📧 <b>2-ҚАДАМ</b>\n\nEmail жазыңыз.",
        "how_step_3": "💵 <b>3-ҚАДАМ</b>\n\nRUB/KGS таңдаңыз.",
        "how_step_4": "📱 <b>4-ҚАДАМ</b>\n\nКарта нөмірі.",
        "how_step_5": "✅ <b>5-ҚАДАМ</b>\n\nСМС код.",
        "how_step_6": "🛠 <b>6-ҚАДАМ</b>\n\n@kl_mub көмектеседі.",
        "menu_back": "Басты мәзір:", "share_msg": "🚀 mubVPN — Android үшін VPN!",
        "share_title": "🤝 <b>Бөлісу:</b>", "btn_share_now": "📲 Бөлісу"
    },
    "tr": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nEn hızlı ve güvenli:",
        "btn_pay": "💳 Satın Al", "btn_how": "📖 Nasıl?", "btn_download": "🚀 İndir", "btn_support": "👨 staff-💻 Destek", "btn_share": "🤝 Paylaş",
        "pay_text": "💳 <b>Ödemeye Geç</b>",
        "pay_btn_link": "💳 Öde", "back": "⬅️ Geri", "next": "İleri ➡️",
        "check_btn": "✅ Kontrol", "checking": "⏳ Kontrol...", "success": "🎉 <b>Premium Aktif!</b>",
        "not_found": "⚠️ Ödeme bulunamadı.",
        "how_step_1": "🚀 <b>ADIM 1</b>\n\nSatın Al'а tıklayın.",
        "how_step_2": "📧 <b>ADIM 2</b>\n\nEmail girin.",
        "how_step_3": "💵 <b>ADIM 3</b>\n\nRUB/KGS seçin.",
        "how_step_4": "📱 <b>ADIM 4</b>\n\nKart numarası.",
        "how_step_5": "✅ <b>ADIM 5</b>\n\nSMS kodu.",
        "how_step_6": "🛠 <b>ADIM 6</b>\n\n@kl_mub hazır.",
        "menu_back": "Ana Menü:", "share_msg": "🚀 mubVPN — En hızlı VPN!",
        "share_title": "🤝 <b>Paylaş:</b>", "btn_share_now": "📲 Paylaş"
    },
    "en": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nUnlock fastest internet access:",
        "btn_pay": "💳 Buy", "btn_how": "📖 How?", "btn_download": "🚀 Download", "btn_support": "👨 staff-💻 Support", "btn_share": "🤝 Share",
        "pay_text": "💳 <b>Proceed to Payment</b>",
        "pay_btn_link": "💳 Pay", "back": "⬅️ Back", "next": "Next ➡️",
        "check_btn": "✅ Check", "checking": "⏳ Checking...", "success": "🎉 <b>Premium active!</b>",
        "not_found": "⚠️ Payment not found.",
        "how_step_1": "🚀 <b>STEP 1</b>\n\nClick Buy.",
        "how_step_2": "📧 <b>STEP 2</b>\n\nEnter Email.",
        "how_step_3": "💵 <b>STEP 3</b>\n\nChoose RUB/KGS.",
        "how_step_4": "📱 <b>STEP 4</b>\n\nCard number.",
        "how_step_5": "✅ <b>STEP 5</b>\n\nSMS code.",
        "how_step_6": "🛠 <b>STEP 6</b>\n\n@kl_mub is here.",
        "menu_back": "Main Menu:", "share_msg": "🚀 mubVPN — Best VPN for Android!",
        "share_title": "🤝 <b>Share:</b>", "btn_share_now": "📲 Share"
    }
}

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
        separator = '&' if '?' in LAVA_MAIN_URL else '?'
        link = f"{LAVA_MAIN_URL}{separator}additional_info={uid}"
        kb = [[InlineKeyboardButton(L["pay_btn_link"], web_app=WebAppInfo(url=link))], [InlineKeyboardButton(L["back"], callback_data='main_menu')]]
        await query.message.edit_caption(caption=L["pay_text"], reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
    elif data == 'share_app':
        L = STRINGS[lang]
        share_url = f"https://t.me/share/url?url=https://mubvpn-bot.onrender.com/?lang={lang}&text={html.escape(L['share_msg'])}"
        kb = [[InlineKeyboardButton(L["btn_share_now"], url=share_url)], [InlineKeyboardButton(L["back"], callback_data='main_menu')]]
        await query.message.edit_caption(caption=L["share_title"], reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
    elif data.startswith('how_'):
        step = data.split('_')[1]; L = STRINGS[lang]
        texts = {"1": L["how_step_1"], "2": L["how_step_2"], "3": L["how_step_3"], "4": L["how_step_4"], "5": L["how_step_5"], "6": L["how_step_6"]}
        nxt = str(int(step)+1) if int(step) < 6 else "menu"; prv = str(int(step)-1) if int(step) > 1 else "main"
        row = [InlineKeyboardButton(L["back"], callback_data='main_menu' if prv=="main" else f'how_{prv}')]
        if nxt != "menu": row.append(InlineKeyboardButton(L["next"], callback_data=f'how_{nxt}'))
        await query.message.edit_caption(caption=texts[step], reply_markup=InlineKeyboardMarkup([row]), parse_mode=ParseMode.HTML)
    elif data == 'main_menu':
        await query.message.edit_caption(caption=STRINGS[lang]["welcome"], reply_markup=get_main_keyboard(lang), parse_mode=ParseMode.HTML)

# --- DASHBOARD HTML ---
def get_dashboard_html(lang):
    t_list = {
        'ky': {'badge': 'NEXT-GEN SECURITY', 'h1': 'mubVPN — Android үчүн тез жана коопсуз VPN', 'sub': '🚀 mubVPN — чектөөсүз интернетке коопсуз жол! ✅ Блоктоолорду айланып өтөт ✅ Маалыматтарды ишенимдүү шифрлейт ✅ Бир таптоо менен туташуу ✅ Жогорку ылдамдык', 'btn_dl': 'Android үчүн жүктөө', 'f1_t': 'Smart Route', 'f1_d': 'Ылдам иштөө үчүн автоматтык жол тандоо.', 'f2_t': 'Коопсуздук', 'f2_d': 'Маалыматтарыңызды шифрлөө менен коргойт.', 'f3_t': 'Android үчүн', 'f3_d': 'Заманбап интерфейс.', 'steps_title': 'Орнотуу 3 кадамда', 's1_t': 'Жүктөп алыңыз', 's1_d': 'Жүктөө баскычын басып, APK күтүңүз.', 's2_t': 'Орнотуңуз', 's2_d': 'Файлды ачып, орнотууну ырастаңыз.', 's3_t': 'Туташыңыз', 's3_d': 'Тиркемени ачып, коргоону иштетиңиз.'},
        'ru': {'badge': 'БЕЗОПАСНОСТЬ НОВОГО ПОКОЛЕНИЯ', 'h1': 'mubVPN — Быстрый и безопасный VPN для Android', 'sub': '🚀 mubVPN — ваш безопасный доступ без ограничений! ✅ Обходит любые блокировки ✅ Надежно защищает данные ✅ Подключение в один тап ✅ Высокая скорость', 'btn_dl': 'Скачать для Android', 'f1_t': 'Smart Route', 'f1_d': 'Автоподбор лучшего маршрута.', 'f2_t': 'Безопасность', 'f2_d': 'Шифрование и анонимность.', 'f3_t': 'Android-first', 'f3_d': 'Оптимизированный интерфейс.', 'steps_title': 'Установка за 3 шага', 's1_t': 'Скачайте файл', 's1_d': 'Нажмите кнопку загрузки.', 's2_t': 'Установите APK', 's2_d': 'Откройте файл и установите.', 's3_t': 'Пользуйтесь!', 's3_d': 'Включите защиту.'}
    }
    # (Other languages omitted for brevity but logic handles them)
    t = t_list.get(lang, t_list['ru'])
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{t['h1']}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
        body {{ font-family: 'Inter', sans-serif; background: radial-gradient(circle at top right, #0a2e22 0%, #051610 100%); background-attachment: fixed; color: #fff; line-height: 1.6; text-align: center; margin: 0; padding: 20px; }}
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(20px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        @keyframes pulse {{ 0% {{ box-shadow: 0 0 0 0 rgba(0,229,160,0.4); }} 70% {{ box-shadow: 0 0 0 20px rgba(0,229,160,0); }} 100% {{ box-shadow: 0 0 0 0 rgba(0,229,160,0); }} }}
        .badge {{ display: inline-block; background: rgba(0,229,160,0.1); color: #00E5A0; padding: 10px 20px; border-radius: 100px; font-size: 12px; font-weight: 900; margin-bottom: 25px; border: 1px solid rgba(0,229,160,0.2); animation: fadeIn 1s ease; }}
        h1 {{ font-size: clamp(30px, 8vw, 50px); font-weight: 900; margin-bottom: 20px; animation: fadeIn 1.2s ease; }}
        .btn-download {{ display: inline-flex; align-items: center; gap: 10px; background: #00E5A0; color: #000; padding: 20px 40px; border-radius: 20px; text-decoration: none; font-weight: 900; font-size: 20px; animation: pulse 2s infinite, fadeIn 1.5s ease; transition: 0.3s; }}
        .features {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin: 60px 0; }}
        .f-card {{ background: rgba(255,255,255,0.03); backdrop-filter: blur(15px); border: 1px solid rgba(255,255,255,0.05); border-radius: 30px; padding: 30px; text-align: left; animation: fadeIn 1.8s ease; }}
        .step-card {{ background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 25px; padding: 20px; margin-bottom: 15px; display: flex; align-items: center; gap: 20px; text-align: left; animation: fadeIn 2s ease; }}
    </style>
</head>
<body>
    <div class="badge">✦ {t['badge']}</div>
    <h1>{t['h1']}</h1>
    <p style="max-width:700px; margin: 0 auto 40px; color:rgba(255,255,255,0.7);">{t['sub']}</p>
    <a href="/download" class="btn-download">{t['btn_dl']}</a>
    <div class="features">
        <div class="f-card"><h3>{t['f1_t']}</h3><p>{t['f1_d']}</p></div>
        <div class="f-card"><h3>{t['f2_t']}</h3><p>{t['f2_d']}</p></div>
        <div class="f-card"><h3>{t['f3_t']}</h3><p>{t['f3_d']}</p></div>
    </div>
    <div class="steps">
        <div class="step-card"><div>01</div><div><h4>{t['s1_t']}</h4><p>{t['s1_d']}</p></div></div>
        <div class="step-card"><div>02</div><div><h4>{t['s2_t']}</h4><p>{t['s2_d']}</p></div></div>
        <div class="step-card"><div>03</div><div><h4>{t['s3_t']}</h4><p>{t['s3_d']}</p></div></div>
    </div>
</body>
</html>"""

class BotHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/download':
            self.send_response(302); self.send_header('Location', 'https://github.com/Ulanbekmahmaraimov/mubvpn-bot/releases/download/v1.0.0/mubvpn.apk'); self.end_headers(); return
        query = urllib.parse.parse_qs(parsed.query)
        lang = query.get('lang', ['ky'])[0]
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
    Application.builder().token(BOT_TOKEN).build().add_handler(CommandHandler("start", start)).add_handler(CallbackQueryHandler(handle_callback)).run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()