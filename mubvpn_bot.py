import logging
import os
import json
import requests
import threading
import time
import html
import asyncio
import urllib.parse
from datetime import datetime, timedelta

from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, InputMediaPhoto

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from telegram.constants import ParseMode



# --- ЖӨНДӨӨЛӨР ---

BOT_TOKEN    = "8400265569:AAHQ21_zNVS3XPDlMoE9I8TW0JwaIaUuA1s"

SUPPORT_URL  = "https://t.me/kl_mub"



FIREBASE_DB_URL    = "https://mubvpn-8b892-default-rtdb.firebaseio.com"

FIREBASE_DB_SECRET = "NgRNzmtQYdgUcFWXiDRPAHAsSURVni2WaIKTw9Re"



logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

log = logging.getLogger(__name__)


# Төлөм пландары
PLANS = {
    "1m":  {"name_key": "plan_1m", "months": 1,  "rub": 109.99, "kgs": 110,  "usd": 1.3},
    "3m":  {"name_key": "plan_3m", "months": 3,  "rub": 309.99, "kgs": 310,  "usd": 3.5},
    "6m":  {"name_key": "plan_6m", "months": 6,  "rub": 599.99, "kgs": 600,  "usd": 7.0},
    "1y":  {"name_key": "plan_1y", "months": 12, "rub": 1099.99, "kgs": 1100, "usd": 12.0},
}


# --- ФУНКЦИЯЛАР ---

def firebase_set_premium(uid: str, months: int) -> bool:

    try:

        url = f"{FIREBASE_DB_URL}/users/{uid}.json?auth={FIREBASE_DB_SECRET}"

        resp = requests.get(url)

        start_date = datetime.now()

        if resp.status_code == 200 and resp.json():

            current_expiry_str = resp.json().get("premium_expiry")

            if current_expiry_str:

                try:

                    current_expiry = datetime.fromisoformat(current_expiry_str)

                    if current_expiry > start_date:

                        start_date = current_expiry

                except Exception as ex:

                    log.error(f"Error parsing existing premium_expiry: {ex}")

        expiry = (start_date + timedelta(days=months * 30)).isoformat()

        resp_patch = requests.patch(url, json={"premium_expiry": expiry, "is_paid": True, "isPremium": True})

        return resp_patch.status_code == 200

    except Exception as e:

        log.error(f"Firebase error: {e}")

        return False



def register_referral(new_user_tg_id: int, inviter_id: str) -> tuple[bool, str]:

    try:

        ref_check_url = f"{FIREBASE_DB_URL}/referrals/{new_user_tg_id}.json?auth={FIREBASE_DB_SECRET}"

        resp_check = requests.get(ref_check_url)

        if resp_check.status_code == 200 and resp_check.json() is not None:

            return False, "already_referred"

        inviter_uid = None

        if len(str(inviter_id)) == 28:

            inviter_uid = inviter_id

        else:

            map_url = f"{FIREBASE_DB_URL}/telegram_to_uid/{inviter_id}.json?auth={FIREBASE_DB_SECRET}"

            resp_map = requests.get(map_url)

            if resp_map.status_code == 200 and resp_map.json():

                inviter_uid = resp_map.json()

        if not inviter_uid:

            return False, "inviter_not_found"

        inviter_url = f"{FIREBASE_DB_URL}/users/{inviter_uid}.json?auth={FIREBASE_DB_SECRET}"

        resp_inviter = requests.get(inviter_url)

        if resp_inviter.status_code == 200 and resp_inviter.json():

            inviter_data = resp_inviter.json()

            if str(inviter_data.get("telegram_id")) == str(new_user_tg_id):

                return False, "self_referral"

        else:

            return False, "inviter_not_found"

        current_days = inviter_data.get("referral_days_granted", 0)

        max_days = 365

        if current_days >= max_days:

            days_to_add = 0

        else:

            days_to_add = min(10, max_days - current_days)

        new_days = current_days + days_to_add

        new_count = inviter_data.get("referral_count", 0) + 1

        start_date = datetime.now()

        current_expiry_str = inviter_data.get("premium_expiry")

        if current_expiry_str:

            try:

                current_expiry = datetime.fromisoformat(current_expiry_str)

                if current_expiry > start_date:

                    start_date = current_expiry

            except:

                pass

        updates = {

            "referral_days_granted": new_days,

            "referral_count": new_count

        }

        if days_to_add > 0:

            new_expiry = (start_date + timedelta(days=days_to_add)).isoformat()

            updates["premium_expiry"] = new_expiry

            updates["is_paid"] = True

            updates["isPremium"] = True

        requests.patch(inviter_url, json=updates)

        ref_data = {

            "inviter_uid": inviter_uid,

            "timestamp": datetime.now().isoformat(),

            "days_granted": days_to_add

        }

        requests.put(ref_check_url, json=ref_data)

        return True, "success"

    except Exception as e:

        log.error(f"Error registering referral: {e}")

        return False, "error"



# --- БОТТУН ТЕКСТТЕРИ ---

STRINGS = {
    "ky": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nЭң тез жана коопсуз интернетке жол ачыңыз. Төлөм жүргүзүү же тиркемени жүктөө үчүн төмөнкү баскычтарды колдонуңуз:",
        "btn_pay": "💳 Сатып алуу", "btn_how": "📖 Кантип төлөйм?",
        "btn_download": "🚀 Жүктөп алуу",
        "btn_support": "👨‍💻 Колдоо", "btn_share": "🤝 Бөлүшүү",
        "pay_text": "💳 <b>Планды тандаңыз</b>\n\nТөлөм кабыл алуу үчүн биздин операторго жазыңыз:",
        "pay_btn_link": "💳 Операторго жазуу", "back": "⬅️ Артка", "next": "Кийинки ➡️",
        "check_btn": "✅ Төлөдүм (Текшерүү)",
        "checking": "⏳ Төлөм текшерилүүдө...",
        "success": "🎉 <b>Premium активдешти!</b>\n\nТиркемени ачып, VPN'ди колдоно бериңиз!",
        "not_found": "⚠️ Төлөм табылган жок. Операторго чек жибергениңизди текшериңиз.",
        "how_step_1": "🚀 <b>1-КАДАМ: План тандоо</b>\n\n'Сатып алуу' баскычын басып, мөөнөттү тандаңыз.",
        "how_step_2": "💬 <b>2-КАДАМ: Операторго жазуу</b>\n\n'Операторго жазуу' баскычын басып, чек жибериңиз.",
        "how_step_3": "✅ <b>3-КАДАМ: Активдештирүү</b>\n\nОператор төлөмдү текшергенден кийин Premium иштеп баштайт.",
        "menu_back": "Башкы меню:",
        "share_msg": "🚀 mubVPN — Android үчүн эң тез жана коопсуз VPN!\n\nАзыр жүктөп ал! 👇",
        "share_title": "🤝 <b>Бөлүшүү:</b>", "btn_share_now": "📲 Бөлүшүү",
        "btn_referral": "🎁 Акысыз Premium (Рефералы)",
        "btn_my_vpn": "🔑 Менин шилтемем",
        "my_vpn_text": "👤 <b>Сиздин жазылууңуз</b>\n\n• Статус: {status}\n• Мөөнөтү: {expiry}\n\n🔑 <b>Сиздин жеке шилтемеңиз:</b>\n<code>{vpn_link}</code>\n\n⚠️ <i>Бул шилтеме бир гана түзүлүш үчүн! Башкаларга бербеңиз.</i>",
        "no_premium": "⚠️ <b>Сизде Premium жок</b>\n\nШилтеме алуу үчүн жазылуу сатып алыңыз.",
        "ref_menu_text": "🎁 <b>Рефераалдык программа!</b>\n\nДосторуңузду чакырып, <b>бекер Premium</b> алыңыз!\n\n• Ар бир чакырылган дос үчүн: <b>+10 күн акысыз Premium</b>.\n\n🔗 <b>Сиздин шилтемеңиз:</b>\n<code>{ref_link}</code>",
        "plan_1m": "1 ай", "plan_3m": "3 ай", "plan_6m": "6 ай", "plan_1y": "1 жыл",
        "pay_info": "💳 <b>{name} Premium</b>\n\nБаасы:\n🇷🇺 {rub} RUB\n🇰🇬 {kgs} KGS\n🌐 {usd} $\n\n⚠️ Төлөм кабыл алуу үчүн операторго жазыңыз.\nТөлөмдөн кийин чек жибериңиз.\n\nАдмин: @kl_mub",
        "dl_title": "🚀 <b>Түзмөгүңүздү тандаңыз</b>\n\nmubVPN бардык платформаларда иштейт. Жүктөө үчүн төмөнкүлөрдүн бирин тандаңыз:",
        "dl_pc_desc": "💻 <b>Clash Verge Rev (v2.5.1)</b>\n\nКомпьютер үчүн сунушталган версия. VLESS, Reality протоколдорун колдойт жана өтө тез иштейт.",
        "dl_mobile_desc": "📱 <b>Мобилдик тиркемелер</b>\n\nAndroid жана iOS үчүн расмий дүкөндөрдөн жүктөп алыңыз.",
        "btn_legal": "📄 Юридикалык маалымат",
        "legal_text": "📄 <b>Юридикалык документтер</b>\n\nБиздин кызматты колдонуудан мурун келишимдер менен таанышып чыгыңыз:",
        "policy": "Купуялык саясаты", "terms": "Колдонуучу келишими"
    },
    "ru": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nОткройте доступ к быстрому и безопасному интернету. Используйте кнопки ниже для оплаты или загрузки приложения:",
        "btn_pay": "💳 Купить", "btn_how": "📖 Как оплатить?",
        "btn_download": "🚀 Скачать приложение",
        "btn_support": "👨‍💻 Поддержка", "btn_share": "🤝 Поделиться",
        "pay_text": "💳 <b>Выберите план</b>\n\nДля оплаты напишите нашему оператору:",
        "pay_btn_link": "💳 Написать оператору", "back": "⬅️ Назад", "next": "Далее ➡️",
        "check_btn": "✅ Я оплатил (Проверять)",
        "checking": "⏳ Проверка платежа...",
        "success": "🎉 <b>Premium активирован!</b>\n\nОткройте приложение и наслаждайтесь VPN!",
        "not_found": "⚠️ Платеж не найден. Убедитесь, что вы отправили чек оператору.",
        "how_step_1": "🚀 <b>ШАГ 1: Выбор тарифа</b>\n\nНажмите 'Купить' и выберите период.",
        "how_step_2": "💬 <b>ШАГ 2: Написать оператору</b>\n\nНажмите 'Написать оператору' и отправьте чек.",
        "how_step_3": "✅ <b>ШАГ 3: Активация</b>\n\nPremium активируется после проверки оплаты оператором.",
        "menu_back": "Главное меню:",
        "share_msg": "🚀 mubVPN — Быстрый и безопасный VPN!\n\nСкачай сейчас! 👇",
        "share_title": "🤝 <b>Поделиться:</b>", "btn_share_now": "📲 Поделиться",
        "btn_referral": "🎁 Бесплатный Premium (Рефералы)",
        "btn_my_vpn": "🔑 Моя ссылка",
        "my_vpn_text": "👤 <b>Ваша подписка</b>\n\n• Статус: {status}\n• Истекает: {expiry}\n\n🔑 <b>Ваша персональная ссылка:</b>\n<code>{vpn_link}</code>\n\n⚠️ <i>Эта ссылка только для одного устройства!</i>",
        "no_premium": "⚠️ <b>У вас нет Premium</b>",
        "ref_menu_text": "🎁 <b>Реферальная программа!</b>\n\nПриглашайте друзей и получайте <b>бесплатный Premium</b>!\n\n🔗 <b>Ваша ссылка:</b>\n<code>{ref_link}</code>",
        "plan_1m": "1 месяц", "plan_3m": "3 месяца", "plan_6m": "6 месяцев", "plan_1y": "1 год",
        "pay_info": "💳 <b>{name} Premium</b>\n\nЦена:\n🇷🇺 {rub} RUB\n🇰🇬 {kgs} KGS\n🌐 {usd} $\n\n⚠️ Для оплаты напишите оператору.\nАдмин: @kl_mub",
        "dl_title": "🚀 <b>Выберите устройство</b>",
        "dl_pc_desc": "💻 <b>Clash Verge Rev (v2.5.1)</b>",
        "dl_mobile_desc": "📱 <b>Мобильные приложения</b>",
        "btn_legal": "📄 Юридическая информация",
        "legal_text": "📄 <b>Юридические документы</b>\n\nОзнакомьтесь с официальными документами нашего сервиса:",
        "policy": "Политика конфиденциальности", "terms": "Пользовательское соглашение"
    },
    "uz": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nEng tezkor va xavfsiz internetga ega bo'ling. To'lov qilish yoki ilovani yuklab olish uchun quyidagi tugmalardan foydalaning:",
        "btn_pay": "💳 Sotib olish", "btn_how": "📖 Qanday to'lash kerak?",
        "btn_download": "🚀 Ilovani yuklab olish",
        "btn_support": "👨‍💻 Qo'llab-quvvatlash", "btn_share": "🤝 Ulashish",
        "pay_text": "💳 <b>Tarifni tanlang</b>\n\nTo'lov uchun operatorga yozing:",
        "pay_btn_link": "💳 Operatorga yozish", "back": "⬅️ Orqaga", "next": "Keyingi ➡️",
        "check_btn": "✅ To'ladim (Tekshirish)",
        "checking": "⏳ To'lov tekshirilmoqda...",
        "success": "🎉 <b>Premium faollashdi!</b>\n\nIlovani oching va VPN-dan foydalaning!",
        "not_found": "⚠️ To'lov topilmadi. Operatorga chek yuborganingizni tekshiring.",
        "how_step_1": "🚀 <b>1-QADAM: Tarifni tanlash</b>",
        "how_step_2": "💬 <b>2-QADAM: Operatorga yozish</b>",
        "how_step_3": "✅ <b>3-QADAM: Faollashtirish</b>",
        "menu_back": "Asosiy menyu:",
        "share_msg": "🚀 mubVPN — Android uchun eng tezkor va xavfsiz VPN!\n\nHozir yuklab ol! 👇",
        "share_title": "🤝 <b>Ulashish:</b>", "btn_share_now": "📲 Ulashish",
        "btn_referral": "🎁 Bepul Premium (Referal)",
        "btn_my_vpn": "🔑 Mening havolam",
        "my_vpn_text": "👤 <b>Sizning obunangiz</b>\n\n• Holat: {status}\n• Muddati: {expiry}\n\n🔑 <b>Sizning shaxsiy havolangiz:</b>\n<code>{vpn_link}</code>",
        "no_premium": "⚠️ <b>Sizda Premium yo'q</b>",
        "ref_menu_text": "🎁 <b>Referal dasturi!</b>\n\nDo'tslaringizni taklif qiling va <b>bepul Premium</b> oling!\n\n🔗 <b>Sizning havolangiz:</b>\n<code>{ref_link}</code>",
        "plan_1m": "1 oy", "plan_3m": "3 oy", "plan_6m": "6 oy", "plan_1y": "1 yil",
        "pay_info": "💳 <b>{name} Premium</b>\n\nNarxi:\n🇷🇺 {rub} RUB\n🇰🇬 {kgs} KGS\n🌐 {usd} $\n\n⚠️ To'lov uchun operatorga yozing.\nTo'lovdan so'ng chek yuboring.\n\nAdmin: @kl_mub",
        "dl_title": "🚀 <b>Qurilmangizni tanlang</b>",
        "dl_pc_desc": "💻 <b>Clash Verge Rev (v2.5.1)</b>",
        "dl_mobile_desc": "📱 <b>Mobil ilovalar</b>",
        "btn_legal": "📄 Yuridik ma'lumotlar",
        "legal_text": "📄 <b>Yuridik hujjatlar</b>",
        "policy": "Maxfiylik siyosati", "terms": "Foydalanuvchi shartnomasi"
    },
    "tg": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nБа интернети зудтарин ва бехатар дастрасӣ пайдо кунед. Барои пардохт ё боргирии барнома аз тугмаҳои зерин истифода баред:",
        "btn_pay": "💳 Харидан", "btn_how": "📖 Чӣ тавр бояд пардохт кард?",
        "btn_download": "🚀 Боргирии барнома",
        "btn_support": "👨‍💻 Дастгирӣ", "btn_share": "🤝 Ирсол",
        "pay_text": "💳 <b>Тарифро интихоб кунед</b>\n\nБарои пардохт ба оператор нависед:",
        "pay_btn_link": "💳 Навиштан ба оператор", "back": "⬅️ Ба ақиб", "next": "Оянда ➡️",
        "check_btn": "✅ Ман пардохт кардам (Санҷиш)",
        "checking": "⏳ Санҷиши пардохт...",
        "success": "🎉 <b>Premium фаъол шуд!</b>\n\nБарномаро кушоед ва аз VPN лаззат баред!",
        "not_found": "⚠️ Пардохт ёфт нашуд. Чекро ба оператор фиристед.",
        "how_step_1": "🚀 <b>ҚАДАМИ 1: Интихоби тариф</b>",
        "how_step_2": "💬 <b>ҚАДАМИ 2: Навиштан ба оператор</b>",
        "how_step_3": "✅ <b>ҚАДАМИ 3: Фаъолсозӣ</b>",
        "menu_back": "Менюи асосӣ:",
        "share_msg": "🚀 mubVPN — VPN-и зудтарин ва бехатар барои Android!\n\nHоло боргирӣ кун! 👇",
        "share_title": "🤝 <b>Ирсол:</b>", "btn_share_now": "📲 Ирсол",
        "btn_referral": "🎁 Premium-и ройгон (Реферал)",
        "btn_my_vpn": "🔑 Истиноди ман",
        "my_vpn_text": "👤 <b>Обунаи шумо</b>\n\n• Статус: {status}\n• Мӯҳлат: {expiry}\n\n🔑 <b>Истиноди шахсии шумо:</b>\n<code>{vpn_link}</code>",
        "no_premium": "⚠️ <b>Шумо Premium надоред</b>",
        "ref_menu_text": "🎁 <b>Барномаи рефералӣ!</b>\n\nДӯстони худро даъват кунед ва <b>Premium-и ройгон</b> гиред!\n\n🔗 <b>Истиноди шумо:</b>\n<code>{ref_link}</code>",
        "plan_1m": "1 моҳ", "plan_3m": "3 моҳ", "plan_6m": "6 моҳ", "plan_1y": "1 сол",
        "pay_info": "💳 <b>{name} Premium</b>\n\nНарх:\n🇷🇺 {rub} RUB\n🇰🇬 {kgs} KGS\n🌐 {usd} $\n\n⚠️ Барои пардохт ба оператор нависед.\nБаъди пардохт чекы фиристед.\n\nАдмин: @kl_mub",
        "dl_title": "🚀 <b>Дастгоҳи худро интихоб кунед</b>",
        "dl_pc_desc": "💻 <b>Clash Verge Rev (v2.5.1)</b>",
        "dl_mobile_desc": "📱 <b>Барномаҳои мобилӣ</b>",
        "btn_legal": "📄 Маълумоти ҳуқуқӣ",
        "legal_text": "📄 <b>Ҳуҷҷатҳои ҳуқуқӣ</b>",
        "policy": "Сиёсати махфият", "terms": "Шартномаи корбар"
    },
    "kk": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nЕң жылдам және қауіпсіз интернетке жол ашыңыз. Төлөм жасау немесе қосымшаны жүктеу үчүн төмендегі батырмаларды қолданыңыз:",
        "btn_pay": "💳 Сатып алу", "btn_how": "📖 Қалай төлеу керек?",
        "btn_download": "🚀 Қосымшаны жүктеу",
        "btn_support": "👨‍💻 Қолдау", "btn_share": "🤝 Бөлісу",
        "pay_text": "💳 <b>Тарифті таңдаңыз</b>\n\nТөлем жасау үшін операторға жазыңыз:",
        "pay_btn_link": "💳 Операторға жазу", "back": "⬅️ Артқа", "next": "Келесі ➡️",
        "check_btn": "✅ Төледім (Тексеру)",
        "checking": "⏳ Төлем тексерілуде...",
        "success": "🎉 <b>Premium белсендірілді!</b>\n\nҚосымшаны ашып, VPN-ді қолдана беріңиз!",
        "not_found": "⚠️ Төлем табылмады. Операторға чекті жібергеніңізді тексеріңіз.",
        "how_step_1": "🚀 <b>1-ҚАДАМ: Тариф таңдау</b>",
        "how_step_2": "💬 <b>2-ҚАДАМ: Операторға жазу</b>",
        "how_step_3": "✅ <b>3-ҚАДАМ: Белсендіру</b>",
        "menu_back": "Басты мәзір:",
        "share_msg": "🚀 mubVPN — Android үшін ең жылдам және қауіпсіз VPN!\n\nҚазір жүктеп ал! 👇",
        "share_title": "🤝 <b>Бөлісу:</b>", "btn_share_now": "📲 Бөлісу",
        "btn_referral": "🎁 Тегін Premium (Реферал)",
        "btn_my_vpn": "🔑 Менің сілтемем",
        "my_vpn_text": "👤 <b>Сіздің жазылымыңыз</b>\n\n• Статус: {status}\n• Мерзімі: {expiry}\n\n🔑 <b>Жеке сілтемеңіз:</b>\n<code>{vpn_link}</code>",
        "no_premium": "⚠️ <b>Сізде Premium жоқ</b>",
        "ref_menu_text": "🎁 <b>Рефералды бағдарлама!</b>\n\nДостарыңызды шақырып, <b>тегін Premium</b> алыңыз!\n\n🔗 <b>Сіздің сілтемеңіз:</b>\n<code>{ref_link}</code>",
        "plan_1m": "1 ай", "plan_3m": "3 ай", "plan_6m": "6 ай", "plan_1y": "1 жыл",
        "pay_info": "💳 <b>{name} Premium</b>\n\nБағасы:\n🇷🇺 {rub} RUB\n🇰🇬 {kgs} KGS\n🌐 {usd} $\n\n⚠️ Төлем үшін операторға жазыңыз.\nТөлемнен кейін чекті жіберіңіз.\n\nАдмин: @kl_mub",
        "dl_title": "🚀 <b>Құрылғыңызды таңдаңыз</b>",
        "dl_pc_desc": "💻 <b>Clash Verge Rev (v2.5.1)</b>",
        "dl_mobile_desc": "📱 <b>Мобильді қосымшалар</b>",
        "btn_legal": "📄 Құқықтық ақпарат",
        "legal_text": "📄 <b>Құқықтық құжаттар</b>",
        "policy": "Құпиялылық саясаты", "terms": "Пайдаланушы келісімі"
    },
    "tr": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nEn hızlı ve en güvenli internetin keyfini çıkarın. Ödeme yapmak veya uygulamayı indirmek için aşağıdaki butonları kullanın:",
        "btn_pay": "💳 Satın Al", "btn_how": "📖 Nasıl ödenir?",
        "btn_download": "🚀 Uygulamayı İndir",
        "btn_support": "👨‍💻 Destek", "btn_share": "🤝 Paylaş",
        "pay_text": "💳 <b>Plan seçin</b>\n\nÖdeme için operatöre yazın:",
        "pay_btn_link": "💳 Operatöre yaz", "back": "⬅️ Geri", "next": "İleri ➡️",
        "check_btn": "✅ Ödedim (Kontrol Et)",
        "checking": "⏳ Ödeme kontrol ediliyor...",
        "success": "🎉 <b>Premium Aktif Edildi!</b>\n\nUygulamayı açın ve VPN'in tadını çıkarın!",
        "not_found": "⚠️ Ödeme bulunamadı. Operatöre makbuzu gönderdiğinizden emin olun.",
        "how_step_1": "🚀 <b>ADIM 1: Plan seçimi</b>",
        "how_step_2": "💬 <b>ADIM 2: Operatöre yazın</b>",
        "how_step_3": "✅ <b>ADIM 3: Aktivasyon</b>",
        "menu_back": "Ana Menü:",
        "share_msg": "🚀 mubVPN — Android için en hızlı ve güvenli VPN!\n\nHemen indir! 👇",
        "share_title": "🤝 <b>Paylaş:</b>", "btn_share_now": "📲 Paylaş",
        "btn_referral": "🎁 Ücretsiz Premium (Referans)",
        "btn_my_vpn": "🔑 Benim linkim",
        "my_vpn_text": "👤 <b>Aboneliğiniz</b>\n\n• Durum: {status}\n• Bitiş Tarihi: {expiry}\n\n🔑 <b>Kişisel linkiniz:</b>\n<code>{vpn_link}</code>",
        "no_premium": "⚠️ <b>Premium aboneliğiniz yok</b>",
        "ref_menu_text": "🎁 <b>Referans Programı!</b>\n\nArkadaşlarınızı davet edin ve <b>ücretsiz Premium</b> kazanın!\n\n🔗 <b>Referans linkiniz:</b>\n<code>{ref_link}</code>",
        "plan_1m": "1 Ay", "plan_3m": "3 Ay", "plan_6m": "6 Ay", "plan_1y": "1 Yıl",
        "pay_info": "💳 <b>{name} Premium</b>\n\nFiyat:\n🇷🇺 {rub} RUB\n🇰🇬 {kgs} KGS\n🌐 {usd} $\n\n⚠️ Ödeme için operatöre yazın.\nÖdemeden sonra makbuz gönderin.\n\nAdmin: @kl_mub",
        "dl_title": "🚀 <b>Cihazınızı seçin</b>",
        "dl_pc_desc": "💻 <b>Clash Verge Rev (v2.5.1)</b>",
        "dl_mobile_desc": "📱 <b>Mobil uygulamalar</b>",
        "btn_legal": "📄 Yasal Bilgiler",
        "legal_text": "📄 <b>Yasal belgeler</b>",
        "policy": "Gizlilik Politikası", "terms": "Kullanıcı Sözleşmesi"
    },
    "en": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nUnlock the fastest and most secure internet access. Use the buttons below to pay or download the application:",
        "btn_pay": "💳 Buy", "btn_how": "📖 How to pay?",
        "btn_download": "🚀 Download App",
        "btn_support": "👨‍💻 Support", "btn_share": "🤝 Share",
        "pay_text": "💳 <b>Choose a plan</b>\n\nWrite to our operator for payment:",
        "pay_btn_link": "💳 Write to operator", "back": "⬅️ Back", "next": "Next ➡️",
        "check_btn": "✅ I have paid (Check)",
        "checking": "⏳ Checking payment...",
        "success": "🎉 <b>Premium activated!</b>\n\nOpen the app and enjoy your VPN!",
        "not_found": "⚠️ Payment not found. Make sure you sent the receipt to the operator.",
        "how_step_1": "🚀 <b>STEP 1: Choose plan</b>",
        "how_step_2": "💬 <b>STEP 2: Write to operator</b>",
        "how_step_3": "✅ <b>STEP 3: Activation</b>",
        "menu_back": "Main Menu:",
        "share_msg": "🚀 mubVPN — The fastest and safest VPN for Android!\n\nDownload now! 👇",
        "share_title": "🤝 <b>Share:</b>", "btn_share_now": "📲 Share",
        "btn_referral": "🎁 Free Premium (Referral)",
        "btn_my_vpn": "🔑 My Link",
        "my_vpn_text": "👤 <b>Your Subscription</b>\n\n• Status: {status}\n• Expiry: {expiry}\n\n🔑 <b>Your personal link:</b>\n<code>{vpn_link}</code>",
        "no_premium": "⚠️ <b>You don't have Premium</b>",
        "ref_menu_text": "🎁 <b>Referral Program!</b>\n\nInvite friends and get <b>free Premium</b>!\n\n🔗 <b>Your referral link:</b>\n<code>{ref_link}</code>",
        "plan_1m": "1 Month", "plan_3m": "3 Months", "plan_6m": "6 Months", "plan_1y": "1 Year",
        "pay_info": "💳 <b>{name} Premium</b>\n\nPrice:\n🇷🇺 {rub} RUB\n🇰🇬 {kgs} KGS\n🌐 {usd} $\n\n⚠️ Write to operator for payment.\nSend the receipt after payment.\n\nAdmin: @kl_mub",
        "dl_title": "🚀 <b>Choose your device</b>",
        "dl_pc_desc": "💻 <b>Clash Verge Rev (v2.5.1)</b>",
        "dl_mobile_desc": "📱 <b>Mobile apps</b>",
        "btn_legal": "📄 Legal Information",
        "legal_text": "📄 <b>Legal documents</b>",
        "policy": "Privacy Policy", "terms": "User Agreement"
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

    L = STRINGS.get(lang, STRINGS['ru'])

    return InlineKeyboardMarkup([

        [InlineKeyboardButton(L["btn_download"], callback_data='dl_platforms')],

        [InlineKeyboardButton(L["btn_pay"], callback_data='pay_menu')], 

        [InlineKeyboardButton(L["btn_my_vpn"], callback_data='my_vpn')],

        [InlineKeyboardButton(L["btn_referral"], callback_data='referral_menu')], 

        [InlineKeyboardButton(L["btn_how"], callback_data='how_1')], 

        [InlineKeyboardButton(L["btn_legal"], callback_data='legal_menu')],

        [InlineKeyboardButton(L["btn_support"], url=SUPPORT_URL)]

    ])



# --- КОМАНДАЛАР ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if context.args:

        arg = context.args[0]

        if arg.startswith('ref_'):

            inviter_id = arg.replace('ref_', '')

            new_user_tg_id = update.effective_user.id

            success, status = register_referral(new_user_tg_id, inviter_id)

            if success:

                try:

                    inviter_tg_id = None

                    if len(str(inviter_id)) != 28:

                        inviter_tg_id = int(inviter_id)

                    else:

                        inv_url = f"{FIREBASE_DB_URL}/users/{inviter_id}/telegram_id.json?auth={FIREBASE_DB_SECRET}"

                        resp_inv = requests.get(inv_url)

                        if resp_inv.status_code == 200 and resp_inv.json():

                            inviter_tg_id = int(resp_inv.json())

                    if inviter_tg_id:

                        msg = "🎁 Досуңуз чакырууну кабыл алды! Сизге **+10 күн акысыз Premium** берилди! 🎉"

                        await context.bot.send_message(chat_id=inviter_tg_id, text=msg, parse_mode=ParseMode.MARKDOWN)

                except Exception as ex:

                    log.error(f"Error sending referral notification: {ex}")

        else:

            context.user_data['uid'] = arg

            tg_id = update.effective_user.id

            try:

                url_user = f"{FIREBASE_DB_URL}/users/{arg}.json?auth={FIREBASE_DB_SECRET}"

                requests.patch(url_user, json={"telegram_id": tg_id})

                url_map = f"{FIREBASE_DB_URL}/telegram_to_uid/{tg_id}.json?auth={FIREBASE_DB_SECRET}"

                requests.put(url_map, json=arg)

            except Exception as ex:

                log.error(f"Error saving telegram_id mapping: {ex}")

    text = "🌐 Choose language / Тилди тандаңыз / Выберите язык:"

    if update.message: await update.message.reply_text(text, reply_markup=get_lang_keyboard())

    else: await update.callback_query.message.edit_text(text, reply_markup=get_lang_keyboard())



async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query; await query.answer()

    data = query.data; lang = context.user_data.get('lang', 'ru')



    if data.startswith('set_lang_'):

        lang = data.split('_')[2]; context.user_data['lang'] = lang

        await query.message.edit_text(STRINGS.get(lang, STRINGS['ru'])["welcome"], reply_markup=get_main_keyboard(lang), parse_mode=ParseMode.HTML)



    elif data == 'pay_menu':
        L = STRINGS.get(lang, STRINGS['ru']); uid = context.user_data.get('uid', query.from_user.id)

        keyboard = [
            [InlineKeyboardButton(f"{STRINGS[lang][PLANS['1m']['name_key']]}  — {PLANS['1m']['rub']} RUB", callback_data=f"plan:1m:{uid}")],
            [InlineKeyboardButton(f"{STRINGS[lang][PLANS['3m']['name_key']]}  — {PLANS['3m']['rub']} RUB", callback_data=f"plan:3m:{uid}")],
            [InlineKeyboardButton(f"{STRINGS[lang][PLANS['6m']['name_key']]}  — {PLANS['6m']['rub']} RUB", callback_data=f"plan:6m:{uid}")],
            [InlineKeyboardButton(f"{STRINGS[lang][PLANS['1y']['name_key']]} — {PLANS['1y']['rub']} RUB", callback_data=f"plan:1y:{uid}")],
            [InlineKeyboardButton(L["back"], callback_data='main_menu')]
        ]
        await query.message.edit_text(L["pay_text"], reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

    elif data.startswith('plan:'):
        L = STRINGS.get(lang, STRINGS['ru']); uid = context.user_data.get('uid', query.from_user.id)
        plan_id = data.split(':')[1]
        plan = PLANS.get(plan_id)

        if plan:
            plan_name = STRINGS[lang][plan['name_key']]
            text = L["pay_info"].format(name=plan_name, rub=plan['rub'], kgs=plan['kgs'], usd=plan['usd'])
            keyboard = [
                [InlineKeyboardButton(L["pay_btn_link"], url=SUPPORT_URL)],
                [InlineKeyboardButton(L["back"], callback_data='pay_menu')]
            ]
            await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

    elif data == 'check_payment':
        L = STRINGS.get(lang, STRINGS['ru']); uid = context.user_data.get('uid', query.from_user.id)
        await query.message.edit_text("Төлөм текшерилүүдө. Операторго чек жибергениңизди текшериңиз.", reply_markup=get_main_keyboard(lang))

    elif data == 'main_menu':
        await query.message.edit_text(STRINGS.get(lang, STRINGS['ru'])["welcome"], reply_markup=get_main_keyboard(lang), parse_mode=ParseMode.HTML)

    elif data == 'dl_platforms':
        L = STRINGS.get(lang, STRINGS['ky'])
        text = L.get("dl_title", STRINGS['ky']["dl_title"])
        kb = [
            [InlineKeyboardButton("📱 Android (APK)", url="https://github.com/Ulanbekmahmaraimov/mubvpn-bot/releases/download/v1.0.10/app-release.apk")],
            [InlineKeyboardButton("🤖 Google Play", url="https://play.google.com/store/apps/details?id=com.happproxy"),
             InlineKeyboardButton("🍎 App Store", url="https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973")],
            [InlineKeyboardButton("💻 Windows", callback_data="dl_win"), InlineKeyboardButton("🖥 macOS", callback_data="dl_mac")],
            [InlineKeyboardButton("🐧 Linux", callback_data="dl_linux")],
            [InlineKeyboardButton(L["back"], callback_data='main_menu')]
        ]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif data == 'dl_win':
        L = STRINGS.get(lang, STRINGS['ky'])
        text = L.get("dl_pc_desc", STRINGS['ky']["dl_pc_desc"])
        kb = [
            [InlineKeyboardButton("🪟 Windows x64 (EXE)", url="https://github.com/clash-verge-rev/clash-verge-rev/releases/download/v2.5.1/Clash.Verge_2.5.1_x64-setup.exe")],
            [InlineKeyboardButton("🪟 Windows ARM64", url="https://github.com/clash-verge-rev/clash-verge-rev/releases/download/v2.5.1/Clash.Verge_2.5.1_arm64-setup.exe")],
            [InlineKeyboardButton(L["back"], callback_data='dl_platforms')]
        ]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif data == 'dl_mac':
        L = STRINGS.get(lang, STRINGS['ky'])
        text = L.get("dl_pc_desc", STRINGS['ky']["dl_pc_desc"])
        kb = [
            [InlineKeyboardButton("🍎 Mac M-series (M1/M2/M3)", url="https://github.com/clash-verge-rev/clash-verge-rev/releases/download/v2.5.1/Clash.Verge_2.5.1_aarch64.dmg")],
            [InlineKeyboardButton("🍎 Mac Intel Chip", url="https://github.com/clash-verge-rev/clash-verge-rev/releases/download/v2.5.1/Clash.Verge_2.5.1_x64.dmg")],
            [InlineKeyboardButton(L["back"], callback_data='dl_platforms')]
        ]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif data == 'dl_linux':
        L = STRINGS.get(lang, STRINGS['ky'])
        text = "🐧 <b>Linux үчүн Clash Verge</b>\n\nОрнотуу буйругу:\n<code>sudo apt install ./Clash.Verge_2.5.1_amd64.deb</code>"
        kb = [
            [InlineKeyboardButton("🐧 Linux x64 (DEB)", url="https://github.com/clash-verge-rev/clash-verge-rev/releases/download/v2.5.1/Clash.Verge_2.5.1_amd64.deb")],
            [InlineKeyboardButton("🐧 Linux ARM64 (DEB)", url="https://github.com/clash-verge-rev/clash-verge-rev/releases/download/v2.5.1/Clash.Verge_2.5.1_arm64.deb")],
            [InlineKeyboardButton(L["back"], callback_data='dl_platforms')]
        ]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif data == 'legal_menu':
        L = STRINGS.get(lang, STRINGS['ru'])
        kb = [
            [InlineKeyboardButton(L["policy"], url="https://telegra.ph/Politika-konfidencialnosti-06-21-31")],
            [InlineKeyboardButton(L["terms"], url="https://telegra.ph/Polzovatelskoe-soglashenie-04-01-19")],
            [InlineKeyboardButton(L["back"], callback_data='main_menu')]
        ]
        await query.message.edit_text(L["legal_text"], reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)



    elif data == 'my_vpn':
        L = STRINGS.get(lang, STRINGS['ru']); uid = context.user_data.get('uid', query.from_user.id)
        try:
            url_user = f"{FIREBASE_DB_URL}/users/{uid}.json?auth={FIREBASE_DB_SECRET}"
            resp = requests.get(url_user)
            user_data = resp.json() if resp.status_code == 200 else None

            if user_data and user_data.get("isPremium"):
                expiry = user_data.get("premium_expiry", "---")
                # Уникалдуу шилтеме генерациялоо (Мисалы, сиздин сервердин базалык шилтемесине UID кошуу)
                # Бул жерге өзүңүздүн негизги сервериңиздин шилтемесин койсоңуз болот
                personal_link = f"vless://25ebd509-9479-483e-a1aa-8bc996424cea@46.33.10.134:8443?encryption=none&flow=xtls-rprx-vision&type=tcp&security=reality&sni=auto.quattro-tech.ru&fp=qq&pbk=10rVZPoOUP1TlQviIAsQ_jAROX0fRQxH0C92nq_zGQc&sid=43dcff53849b81e6#mubVPN_{uid}"

                text = L["my_vpn_text"].format(
                    status="✅ Активдүү",
                    expiry=expiry.split('T')[0],
                    vpn_link=personal_link
                )
            else:
                text = L["no_premium"]

            kb = [[InlineKeyboardButton(L["back"], callback_data='main_menu')]]
            await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
        except Exception as e:
            log.error(f"Error in my_vpn: {e}")
            await query.message.edit_text("Error loading data.", reply_markup=get_main_keyboard(lang))

    elif data == 'referral_menu':

        L = STRINGS.get(lang, STRINGS['ru']); uid = context.user_data.get('uid', query.from_user.id)

        bot_info = await context.bot.get_me()

        bot_username = bot_info.username

        ref_link = f"https://t.me/{bot_username}?start=ref_{uid}"

        referral_count = 0

        referral_days_granted = 0

        try:

            inviter_uid = uid

            if len(str(uid)) != 28:

                map_url = f"{FIREBASE_DB_URL}/telegram_to_uid/{uid}.json?auth={FIREBASE_DB_SECRET}"

                resp_map = requests.get(map_url)

                if resp_map.status_code == 200 and resp_map.json():

                    inviter_uid = resp_map.json()

            user_url = f"{FIREBASE_DB_URL}/users/{inviter_uid}.json?auth={FIREBASE_DB_SECRET}"

            resp_user = requests.get(user_url)

            if resp_user.status_code == 200 and resp_user.json():

                inviter_data = resp_user.json()

                referral_count = inviter_data.get("referral_count", 0)

                referral_days_granted = inviter_data.get("referral_days_granted", 0)

        except Exception as ex:

            log.error(f"Error fetching referral data: {ex}")

        text = L["ref_menu_text"].format(ref_link=ref_link)

        kb = [[InlineKeyboardButton(L["back"], callback_data='main_menu')]]

        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)



    elif data.startswith('how_'):

        step = data.split('_')[1]; L = STRINGS.get(lang, STRINGS['ru'])

        texts = {"1": L["how_step_1"], "2": L["how_step_2"], "3": L["how_step_3"], "4": L["how_step_4"]}

        nxt = str(int(step)+1) if int(step) < 4 else "menu"

        prv = str(int(step)-1) if int(step) > 1 else "main"

        row = [InlineKeyboardButton(L["back"], callback_data='main_menu' if prv=="main" else f'how_{prv}')]

        if nxt != "menu": row.append(InlineKeyboardButton(L["next"], callback_data=f'how_{nxt}'))

        await query.message.edit_text(texts.get(step, "Error"), reply_markup=InlineKeyboardMarkup([row]), parse_mode=ParseMode.HTML)



# --- WEB SERVER (DASHBOARD) ---

def get_dashboard_html(lang):

    texts = {

        'ky': {

            'h1': 'mubVPN — Android үчүн тез жана коопсуз VPN',

            'sub': '🚀 mubVPN — чектөөсүз интернетке коопсуз жол!\n\n✅ Маалыматтарди ишенимдүү шифрлейт\n✅ Бир таптоо менен туташуу\n✅ Жогорку ылдамдык\n\nАзыр жүктөп алып, эркиндиктен ырахат алыңыз! 👇',

            'btn_dl': 'Android үчүн жүктөө',

        },

        'ru': {

            'h1': 'mubVPN — Быстрый и безопасный VPN для Android',

            'sub': '🚀 mubVPN — ваш безопасный доступ к любимым сервисам без ограничений!\n\n✅ Надежно защищает ваши данные\n✅ Подключение в один тап\n✅ Высокая и стабильная скорость\n\nСкачай и пользуйся без ограничений уже сейчас! 👇',

            'btn_dl': 'Скачать для Android',

        }

    }

    t = texts.get(lang, texts['ru'])

    

    return f"""<!DOCTYPE html>

<html lang="{lang}">

<head>

<meta charset="UTF-8">

<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>{t['h1']}</title>

<style>

  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{ font-family: 'Inter', sans-serif; background-color: #03060a; color: #fff; text-align: center; }}

  .container {{ max-width: 800px; margin: 0 auto; padding: 40px 20px; }}

  .logo {{ font-weight: 900; font-size: 32px; background: linear-gradient(135deg, #fff 30%, #00E5A0); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 40px; }}

  .hero {{ background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); backdrop-filter: blur(40px); border-radius: 32px; padding: 60px 20px; }}

  .btn-download {{ display: inline-flex; align-items: center; gap: 16px; background: linear-gradient(135deg, #00E5A0, #00C58A); color: #03060a; padding: 20px 40px; border-radius: 16px; font-weight: 900; text-decoration: none; font-size: 20px; }}

</style>

</head>

<body>

  <div class="container">

    <div class="logo">mubVPN</div>

    <section class="hero">

      <h1>{t['h1']}</h1>

      <p style="margin: 20px 0 40px;">{t['sub']}</p>

      <a href="/download" class="btn-download">{t['btn_dl']}</a>

    </section>

  </div>

</body>

</html>"""


class BotHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path == '/download':

            apk_url = 'https://github.com/Ulanbekmahmaraimov/mubvpn-bot/releases/download/v1.0.10/app-release.apk'

            self.send_response(302); self.send_header('Location', apk_url); self.end_headers(); return



        self.send_response(200)

        self.send_header('Content-Type', 'text/html; charset=utf-8')

        self.end_headers()

        self.wfile.write(get_dashboard_html('ky').encode('utf-8'))



def run_server():

    port = int(os.environ.get('PORT', 8080))

    HTTPServer(('0.0.0.0', port), BotHandler).serve_forever()



def self_ping():
    """Ботту өчүрбөш үчүн ар 10 мүнөт сайын өзүнө сурам жөнөтөт."""
    # Render же Heroku'до APP_URL деген өзгөрмөгө боттун дарегин жазып коюңуз
    app_url = os.environ.get('APP_URL') or os.environ.get('RENDER_EXTERNAL_URL')
    if not app_url:
        log.warning("APP_URL өзгөрмөсү коюлган эмес. Өзүн-өзү ping кылуу иштебейт.")
        return

    while True:
        try:
            # Боттун өзүнүн веб-серверине сурам жөнөтөбүз
            response = requests.get(app_url)
            log.info(f"Self-ping ийгиликтүү: {response.status_code}")
        except Exception as e:
            log.error(f"Self-ping катасы: {e}")
        time.sleep(600)  # 600 секунд = 10 мүнөт


def main():
    # Веб-серверди иштетүү
    threading.Thread(target=run_server, daemon=True).start()
    # Өзүн-өзү ойготуп туруучу функцияны иштетүү
    threading.Thread(target=self_ping, daemon=True).start()

    from telegram.request import HTTPXRequest
    request = HTTPXRequest(connect_timeout=20, read_timeout=20)

    app = Application.builder().token(BOT_TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(CallbackQueryHЖandler(handle_callback))

    log.info("🤖 Bot is running...")

    app.run_polling(drop_pending_updates=True)



if __name__ == "__main__":
    main()
