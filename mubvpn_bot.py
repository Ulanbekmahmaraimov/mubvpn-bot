import logging
import os
import json
import requests
import threading
import time
import html
import asyncio
import hashlib
import urllib.parse
import base64
import uuid
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


# Platega Орнотуулары (ТАКТАЛГАН ID)
PLATEGA_MERCHANT_ID = "7daa1458-3248-4106-bc81-bfe7f33b742f"
PLATEGA_API_KEY     = "Ia6n9MgN172IKWWOGAzkfQveSZ4ZIq2ktTpkt5hiBNpCfbtrX4V4XLozuKarEB2OzkNEEfHDsaTZadGJhZUJ6He7AtQFGS0U6Lud"

# --- СЕРВЕРЛЕР ---
SERVERS = [
    {"name": "Германия 🇩🇪", "host": "46.33.10.134"},
    {"name": "Нидерланды 🇳🇱", "host": "45.143.93.125"},
    {"name": "Финляндия 🇫🇮", "host": "95.216.148.163"},
    {"name": "Казахстан 🇰🇿", "host": "185.120.77.203"}
]



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

        # Ар бир сатып алууда жаңы уникалдуу номер (UUID) түзөбүз
        new_vpn_uuid = str(uuid.uuid4())

        resp_patch = requests.patch(url, json={
            "premium_expiry": expiry,
            "is_paid": True,
            "isPremium": True,
            "vpn_uuid": new_vpn_uuid
        })

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



def firebase_give_trial(uid: str, days: int = 3) -> bool:
    """Жаңы колдонуучуга сыноо мөөнөтүн (Trial) берет."""
    try:
        url = f"{FIREBASE_DB_URL}/users/{uid}.json?auth={FIREBASE_DB_SECRET}"
        resp = requests.get(url)
        if resp.status_code == 200:
            user_data = resp.json() or {}
            # Эгер мурда сыноо мөөнөтү берилген болсо же Premium болсо, кайра бербейбиз
            if user_data.get("trial_given") or user_data.get("isPremium"):
                return False

            expiry = (datetime.now() + timedelta(days=days)).isoformat()
            new_vpn_uuid = str(uuid.uuid4())

            requests.patch(url, json={
                "premium_expiry": expiry,
                "isPremium": True,
                "is_paid": False,
                "vpn_uuid": new_vpn_uuid,
                "trial_given": True
            })
            return True
    except Exception as e:
        log.error(f"Error giving trial: {e}")
    return False



# --- PLATEGA API ---

def create_platega_invoice(uid: str, plan_id: str, amount_rub: float) -> tuple[str, str]:
    """Platega аркылуу төлөм шилтемесин түзөт. Кайтарат: (URL, ErrorMessage)"""
    try:
        # Негизги API дареги (Түзүлгөн: api.platega.io -> app.platega.io)
        url = "https://app.platega.io/v2/transaction/process"
        headers = {
            "X-MerchantId": PLATEGA_MERCHANT_ID,
            "X-Secret": PLATEGA_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        data = {
            "paymentMethod": 2,  # SBP (Система быстрых платежей)
            "paymentDetails": {
                "amount": float(amount_rub),
                "currency": "RUB"
            },
            "description": f"mubVPN Premium - {plan_id}",
            "return": "https://t.me/mubvpn_pay_bot",
            "failedUrl": "https://t.me/mubvpn_pay_bot",
            "payload": f"{uid}:{plan_id}"
        }

        log.info(f"Platega'га сурам жөнөтүлүүдө: {url}")
        resp = requests.post(url, json=data, headers=headers, timeout=15)

        if resp.status_code == 200:
            return resp.json().get("url"), None
        else:
            # Толук ката маалыматын алуу
            try:
                err_data = resp.json()
                err_msg = f"API Катасы {resp.status_code}: {json.dumps(err_data, ensure_ascii=False)}"
            except:
                err_msg = f"API Катасы {resp.status_code}: {resp.text[:200]}"

            log.error(f"Platega API катасы: {err_msg}")
            return None, err_msg

    except requests.exceptions.ConnectionError as ce:
        log.error(f"Platega туташуу катасы (DNS маселеси болушу мүмкүн): {ce}")
        return None, "Серверге туташуу мүмкүн эмес (DNS Error). Бир аздан кийин кайра аракет кылыңыз."
    except Exception as e:
        log.error(f"Platega күтүлбөгөн ката: {e}")
        return None, str(e)



# --- БОТТУН ТЕКСТТЕРИ ---

STRINGS = {
    "ky": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nЭң тез жана коопсуз интернетке жол ачыңыз. Төлөм жүргүзүү же тиркемени жүктөө үчүн төмөнкү баскычтарды колдонуңуз:",
        "btn_pay": "💳 Сатып алуу", "btn_how": "📖 Кантип төлөйм?",
        "btn_download": "🚀 Жүктөп алуу", "btn_support": "👨‍💻 Колдоо", "btn_share": "🤝 Бөлүшүү",
        "pay_text": "💳 <b>Планды тандаңыз</b>\n\nТөлөмдөр SBP жана Крипто аркылуу автоматтык түрдө кабыл алынат:",
        "pay_btn_link": "💳 Төлөм шилтемеси", "back": "⬅️ Артка", "next": "Кийинки ➡️",
        "check_btn": "✅ Төлөдүм (Текшерүү)", "checking": "⏳ Төлөм текшерилүүдө...",
        "success": "🎉 <b>Premium активдешти!</b>\n\nТиркемени ачып, VPN'ди колдоно бериңиз!",
        "not_found": "⚠️ Төлөм табылган жок. Төлөгөндөн кийин 1-2 мүнөт күтө туруңуз.",
        "how_step_1": "🚀 <b>1-КАДАМ: План тандоо</b>\n\n'Сатып алуу' баскычын басып, мөөнөттү тандаңыз.",
        "how_step_2": "💳 <b>2-КАДАМ: Төлөө</b>\n\nТөлөм шилтемесине өтүп, SBP же Крипто менен төлөңүз.",
        "how_step_3": "✅ <b>3-КАДАМ: Активдештирүү</b>\n\nТөлөмдөн кийин Premium автоматтык түрдө иштеп баштайт.",
        "menu_back": "Башкы меню:",
        "share_msg": "🚀 mubVPN — Android үчүн эң тез жана коопсуз VPN!\n\nАзыр жүктөп ал! 👇",
        "share_title": "🤝 <b>Бөлүшүү:</b>", "btn_share_now": "📲 Sharing link",
        "btn_referral": "🎁 Акысыз Premium (Рефералы)",
        "btn_my_vpn": "🔑 Менин шилтемем",
        "my_vpn_text": "👤 <b>Сиздин жазылууңуз</b>\n\n• Статус: {status}\n• Мөөнөтү: {expiry}\n\n🔑 <b>Сиздин жеке шилтемеңиз:</b>\n<code>{vpn_link}</code>\n\n⚠️ <i>Бул шилтеме бир гана түзүлүш үчүн! Башкаларга бербеңиз.</i>",
        "no_premium": "⚠️ <b>Сизде Premium жок</b>",
        "ref_menu_text": "🎁 <b>Рефераалдык программа!</b>\n\nДосторуңузду чакырып, <b>бекер Premium</b> алыңыз!\n\n• Ар бир чакырылган дос үчүн: <b>+10 күн акысыз Premium</b>.\n\n🔗 <b>Сиздин шилтемеңиз:</b>\n<code>{ref_link}</code>",
        "plan_1m": "1 ай", "plan_3m": "3 ай", "plan_6m": "6 ай", "plan_1y": "1 жыл",
        "pay_info": "💳 <b>{name} Premium</b>\n\nБаасы: {rub} RUB\n\nТөлөө үчүн төмөнкү баскычты басыңыз. Төлөмдөн кийин Premium автоматтык түрдө берилет.",
        "dl_title": "🚀 <b>Түзмөгүңүздү тандаңыз</b>",
        "dl_pc_desc": "💻 <b>Clash Verge Rev (v2.5.1)</b>",
        "dl_mobile_desc": "📱 <b>Мобилдик тиркемелер</b>",
        "btn_legal": "📄 Юридикалык маалымат",
        "legal_text": "📄 <b>Юридикалык документтер</b>",
        "policy": "Купуялык саясаты", "terms": "Колдонуучу келишими",
        "trial_msg": "🎁 <b>Сизге 3 күндүк акысыз Premium берилди!</b>\n\nБул биздин VPN'ди сынап көрүү үчүн белек. Төмөндө сиздин шилтемеңиз:"
    },
    "ru": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nОткройте доступ к быстрому и безопасному интернету. Используйте кнопки ниже для оплаты или загрузки приложения:",
        "btn_pay": "💳 Купить", "btn_how": "📖 Как оплатить?",
        "btn_download": "🚀 Скачать приложение", "btn_support": "👨‍💻 Поддержка", "btn_share": "🤝 Поделиться",
        "pay_text": "💳 <b>Выберите тариф</b>\n\nОплата принимается через СБП и Крипто автоматически:",
        "pay_btn_link": "💳 Ссылка на оплату", "back": "⬅️ Назад", "next": "Далее ➡️",
        "check_btn": "✅ Я оплатил (Проверить)", "checking": "⏳ Проверка платежа...",
        "success": "🎉 <b>Premium активирован!</b>\n\nОткройте приложение и наслаждайтесь VPN!",
        "not_found": "⚠️ Платеж не найден. Подождите 1-2 минуты после оплаты.",
        "how_step_1": "🚀 <b>ШАГ 1: Выбор тарифа</b>\n\nНажмите 'Купить' и выберите срок подписки.",
        "how_step_2": "💳 <b>ШАГ 2: Оплата</b>\n\nПерейдите по ссылке и оплатите через СБП или Крипто.",
        "how_step_3": "✅ <b>ШАГ 3: Активация</b>\n\nПосле оплаты Premium активируется автоматически.",
        "menu_back": "Главное меню:",
        "share_msg": "🚀 mubVPN — Самый быстрый и безопасный VPN для Android!\n\nСкачай сейчас! 👇",
        "share_title": "🤝 <b>Поделиться:</b>", "btn_share_now": "📲 Sharing link",
        "btn_referral": "🎁 Бесплатный Premium (Рефералы)",
        "btn_my_vpn": "🔑 Моя ссылка",
        "my_vpn_text": "👤 <b>Ваша подписка</b>\n\n• Статус: {status}\n• Истекает: {expiry}\n\n🔑 <b>Ваша персональная ссылка:</b>\n<code>{vpn_link}</code>\n\n⚠️ <i>Эта ссылка только для одного устройства!</i>",
        "no_premium": "⚠️ <b>У вас нет Premium</b>",
        "ref_menu_text": "🎁 <b>Реферальная программа!</b>\n\nПриглашайте друзей и получайте <b>бесплатный Premium</b>!\n\n• За каждого друга: <b>+10 дней бесплатного Premium</b>.\n\n🔗 <b>Ваша ссылка:</b>\n<code>{ref_link}</code>",
        "plan_1m": "1 месяц", "plan_3m": "3 месяца", "plan_6m": "6 месяцев", "plan_1y": "1 год",
        "pay_info": "💳 <b>{name} Premium</b>\n\nЦена: {rub} RUB\n\nНажмите кнопку ниже для оплаты. Premium активируется автоматически.",
        "dl_title": "🚀 <b>Выберите устройство</b>",
        "dl_pc_desc": "💻 <b>Clash Verge Rev (v2.5.1)</b>",
        "dl_mobile_desc": "📱 <b>Мобильные приложения</b>",
        "btn_legal": "📄 Юридическая информация",
        "legal_text": "📄 <b>Юридические документы</b>",
        "policy": "Политика конфиденциальности", "terms": "Пользовательское соглашение",
        "trial_msg": "🎁 <b>Вам начислено 3 дня бесплатного Premium!</b>\n\nЭто подарок, чтобы вы могли попробовать наш VPN. Ниже ваша ссылка:"
    },
    "en": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nUnlock fast and secure internet. Use the buttons below to pay or download the app:",
        "btn_pay": "💳 Buy Premium", "btn_how": "📖 How to pay?",
        "btn_download": "🚀 Download App", "btn_support": "👨‍💻 Support", "btn_share": "🤝 Share",
        "pay_text": "💳 <b>Choose a plan</b>\n\nPayments are accepted via Crypto and local methods automatically:",
        "pay_btn_link": "💳 Payment Link", "back": "⬅️ Back", "next": "Next ➡️",
        "check_btn": "✅ I have paid (Check)", "checking": "⏳ Checking payment...",
        "success": "🎉 <b>Premium activated!</b>\n\nOpen the app and enjoy your VPN!",
        "not_found": "⚠️ Payment not found. Wait 1-2 minutes after payment.",
        "how_step_1": "🚀 <b>STEP 1: Choose plan</b>\n\nClick 'Buy' and select the duration.",
        "how_step_2": "💳 <b>STEP 2: Payment</b>\n\nFollow the link and complete the payment.",
        "how_step_3": "✅ <b>STEP 3: Activation</b>\n\nPremium will be activated automatically after payment.",
        "menu_back": "Main Menu:",
        "share_msg": "🚀 mubVPN — The fastest and safest VPN for Android!\n\nDownload now! 👇",
        "share_title": "🤝 <b>Share:</b>", "btn_share_now": "📲 Sharing link",
        "btn_referral": "🎁 Free Premium (Referral)",
        "btn_my_vpn": "🔑 My Link",
        "my_vpn_text": "👤 <b>Your Subscription</b>\n\n• Status: {status}\n• Expiry: {expiry}\n\n🔑 <b>Your personal link:</b>\n<code>{vpn_link}</code>\n\n⚠️ <i>This link is for one device only!</i>",
        "no_premium": "⚠️ <b>No active Premium</b>",
        "ref_menu_text": "🎁 <b>Referral Program!</b>\n\nInvite friends and get <b>free Premium</b>!\n\n• For each friend: <b>+10 days of free Premium</b>.\n\n🔗 <b>Your link:</b>\n<code>{ref_link}</code>",
        "plan_1m": "1 month", "plan_3m": "3 months", "plan_6m": "6 months", "plan_1y": "1 year",
        "pay_info": "💳 <b>{name} Premium</b>\n\nPrice: {rub} RUB\n\nClick the button below to pay. Premium is granted automatically.",
        "dl_title": "🚀 <b>Choose your device</b>",
        "dl_pc_desc": "💻 <b>Clash Verge Rev (v2.5.1)</b>",
        "dl_mobile_desc": "📱 <b>Mobile Apps</b>",
        "btn_legal": "📄 Legal Info",
        "legal_text": "📄 <b>Legal Documents</b>",
        "policy": "Privacy Policy", "terms": "Terms of Service",
        "trial_msg": "🎁 <b>You've been granted 3 days of free Premium!</b>\n\nTry our VPN for free. Here is your link:"
    },
    "uz": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nTezkor va xavfsiz internetga yo'l oching. To'lov qilish yoki ilovani yuklab olish uchun quyidagi tugmalardan foydalaning:",
        "btn_pay": "💳 Sotib olish", "btn_how": "📖 Qanday to'layman?",
        "btn_download": "🚀 Yuklab olish", "btn_support": "👨‍💻 Qo'llab-quvvatlash", "btn_share": "🤝 Ulashish",
        "pay_text": "💳 <b>Tarifni tanlang</b>\n\nTo'lovlar avtomatik ravishda qabul qilinadi:",
        "pay_btn_link": "💳 To'lov havolasi", "back": "⬅️ Orqaga", "next": "Keyingi ➡️",
        "check_btn": "✅ To'ladim (Tekshirish)", "checking": "⏳ To'lov tekshirilmoqda...",
        "success": "🎉 <b>Premium faollashdi!</b>\n\nIlovani oching va VPN-dan foydalaning!",
        "not_found": "⚠️ To'lov topilmadi. To'lovdan so'ng 1-2 daqiqa kuting.",
        "how_step_1": "🚀 <b>1-QADAM: Tarifni tanlash</b>",
        "how_step_2": "💳 <b>2-QADAM: To'lov</b>",
        "how_step_3": "✅ <b>3-QADAM: Faollashtirish</b>",
        "menu_back": "Asosiy menyu:",
        "share_msg": "🚀 mubVPN — Android uchun eng tezkor va xavfsiz VPN!\n\nHozir yuklab ol! 👇",
        "share_title": "🤝 <b>Ulashish:</b>", "btn_share_now": "📲 Sharing link",
        "btn_referral": "🎁 Bepul Premium (Referal)",
        "btn_my_vpn": "🔑 Mening havolam",
        "my_vpn_text": "👤 <b>Sizning obunangiz</b>\n\n• Holat: {status}\n• Muddati: {expiry}\n\n🔑 <b>Sizning shaxsiy havolangiz:</b>\n<code>{vpn_link}</code>",
        "no_premium": "⚠️ <b>Sizda Premium yo'q</b>",
        "ref_menu_text": "🎁 <b>Referal dasturi!</b>\n\nDo'stlarni taklif qiling va <b>bepul Premium</b> oling!\n\n• Har bir do'st uchun: <b>+10 kun bepul Premium</b>.\n\n🔗 <b>Sizning havolangiz:</b>\n<code>{ref_link}</code>",
        "plan_1m": "1 oy", "plan_3m": "3 oy", "plan_6m": "6 oy", "plan_1y": "1 yil",
        "pay_info": "💳 <b>{name} Premium</b>\n\nNarxi: {rub} RUB\n\nTo'lov uchun tugmani bosing. Premium avtomatik faollashadi.",
        "dl_title": "🚀 <b>Qurilmangizni tanlang</b>",
        "dl_pc_desc": "💻 <b>Clash Verge Rev (v2.5.1)</b>",
        "dl_mobile_desc": "📱 <b>Mobil ilovalar</b>",
        "btn_legal": "📄 Yuridik ma'lumotlar",
        "legal_text": "📄 <b>Yuridik hujjatlar</b>",
        "policy": "Maxfiylik siyosati", "terms": "Foydalanuvchi shartnomasi",
        "trial_msg": "🎁 <b>Sizga 3 kunlik bepul Premium berildi!</b>\n\nVPN-ni sinab ko'ring. Mana sizning havolangiz:"
    },
    "kk": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nЕң жылдам және қауіпсіз интернетке жол ашыңыз. Төлем жасау немесе қолданбаны жүктеу үшін төмендегі батырмаларды қолданыңыз:",
        "btn_pay": "💳 Сатып алу", "btn_how": "📖 Қалай төлеймін?",
        "btn_download": "🚀 Жүктеу", "btn_support": "👨‍💻 Қолдау", "btn_share": "🤝 Бөлісу",
        "pay_text": "💳 <b>Тарифті таңдаңыз</b>\n\nТөлемдер автоматты түрде қабылданады:",
        "pay_btn_link": "💳 Төлем сілтемесі", "back": "⬅️ Артқа", "next": "Келесі ➡️",
        "check_btn": "✅ Төледім (Тексеру)", "checking": "⏳ Төлем тексерілуде...",
        "success": "🎉 <b>Premium белсендірілді!</b>\n\nҚолданбаны ашып, VPN-ді қолдана беріңіз!",
        "not_found": "⚠️ Төлем табылмады. Төлегеннен кейін 1-2 минут күте тұрыңыз.",
        "how_step_1": "🚀 <b>1-ҚАДАМ: Тариф таңдау</b>",
        "how_step_2": "💳 <b>2-ҚАДАМ: Төлеу</b>",
        "how_step_3": "✅ <b>3-ҚАДАМ: Белсендіру</b>",
        "menu_back": "Басты мәзір:",
        "share_msg": "🚀 mubVPN — Android үшін ең жылдам және қауіпсіз VPN!\n\nҚазір жүктеп ал! 👇",
        "share_title": "🤝 <b>Бөлісу:</b>", "btn_share_now": "📲 Бөлісу",
        "btn_referral": "🎁 Тегін Premium (Реферал)",
        "btn_my_vpn": "🔑 Менің сілтемем",
        "my_vpn_text": "👤 <b>Сіздің жазылымыңыз</b>\n\n• Статус: {status}\n• Мерзімі: {expiry}\n\n🔑 <b>Жеке сілтемеңіз:</b>\n<code>{vpn_link}</code>",
        "no_premium": "⚠️ <b>Сізде Premium жоқ</b>",
        "ref_menu_text": "🎁 <b>Рефералды бағдарлама!</b>\n\nДостарды шақырып, <b>тегін Premium</b> алыңыз!\n\n• Әр дос үшін: <b>+10 күн тегін Premium</b>.\n\n🔗 <b>Сіздің сілтемеңіз:</b>\n<code>{ref_link}</code>",
        "plan_1m": "1 ай", "plan_3m": "3 ай", "plan_6m": "6 ай", "plan_1y": "1 жыл",
        "pay_info": "💳 <b>{name} Premium</b>\n\nБағасы: {rub} RUB\n\nТөлеу үшін батырманы басыңыз. Premium автоматты түрде қосылады.",
        "dl_title": "🚀 <b>Құрылғыңызды таңдаңыз</b>",
        "dl_pc_desc": "💻 <b>Clash Verge Rev (v2.5.1)</b>",
        "dl_mobile_desc": "📱 <b>Мобильді қолданбалар</b>",
        "btn_legal": "📄 Құқықтық ақпарат",
        "legal_text": "📄 <b>Құқықтық құжаттар</b>",
        "policy": "Құпиялылық саясаты", "terms": "Пайдаланушы келісімі",
        "trial_msg": "🎁 <b>Сізге 3 күндік тегін Premium берілді!</b>\n\nБұл біздің VPN-ді сынап көруге арналған сыйлық. Сіздің сілтемеңіз:"
    },
    "tg": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nБа интернети зудтарин ва бехатар дастрасӣ пайдо кунед. Барои пардохт ё боргирии барнома аз тугмаҳои зерин истифода баред:",
        "btn_pay": "💳 Харидан", "btn_how": "📖 Чӣ тавр пардохт кунам?",
        "btn_download": "🚀 Боргирӣ", "btn_support": "👨‍💻 Дастгирӣ", "btn_share": "🤝 Фиристодан",
        "pay_text": "💳 <b>Тарифро интихоб кунед</b>\n\nПардохтҳо ба таври худкор қабул мешаванд:",
        "pay_btn_link": "💳 Истиноди пардохт", "back": "⬅️ Ба ақиб", "next": "Оянда ➡️",
        "check_btn": "✅ Ман пардохт кардам", "checking": "⏳ Санҷиши пардохт...",
        "success": "🎉 <b>Premium фаъол шуд!</b>\n\nБарномаро кушоед ва аз VPN лаззат баред!",
        "not_found": "⚠️ Пардохт ёфт нашуд. Баъди пардохт 1-2 дақиқа интизор шавед.",
        "how_step_1": "🚀 <b>ҚАДАМИ 1: Интихоби тариф</b>",
        "how_step_2": "💳 <b>ҚАДАМИ 2: Пардохт</b>",
        "how_step_3": "✅ <b>ҚАДАМИ 3: Фаъолсозӣ</b>",
        "menu_back": "Менюи асосӣ:",
        "share_msg": "🚀 mubVPN — VPN-и зудтарин ва бехатар барои Android!\n\nHоло боргирӣ кун! 👇",
        "share_title": "🤝 <b>Ирсол:</b>", "btn_share_now": "📲 Sharing link",
        "btn_referral": "🎁 Premium-и ройгон (Реферал)",
        "btn_my_vpn": "🔑 Истиноди ман",
        "my_vpn_text": "👤 <b>Обунаи шумо</b>\n\n• Статус: {status}\n• Мӯҳлат: {expiry}\n\n🔑 <b>Истиноди шахсии шумо:</b>\n<code>{vpn_link}</code>",
        "no_premium": "⚠️ <b>Шумо Premium надоред</b>",
        "ref_menu_text": "🎁 <b>Барномаи рефералӣ!</b>\n\nДӯстонро даъват кунед ва <b>Premium-и ройгон</b> гиред!\n\n• Барои ҳар як дӯст: <b>+10 рӯз Premium-и ройгон</b>.\n\n🔗 <b>Истиноди шумо:</b>\n<code>{ref_link}</code>",
        "plan_1m": "1 моҳ", "plan_3m": "3 моҳ", "plan_6m": "6 моҳ", "plan_1y": "1 сол",
        "pay_info": "💳 <b>{name} Premium</b>\n\nНарх: {rub} RUB\n\nБарои пардохт тугмаро пахш кунед. Premium ба таври худкор фаъол мешавад.",
        "dl_title": "🚀 <b>Дастгоҳи худро интихоб кунед</b>",
        "dl_pc_desc": "💻 <b>Clash Verge Rev (v2.5.1)</b>",
        "dl_mobile_desc": "📱 <b>Барномаҳои мобилӣ</b>",
        "btn_legal": "📄 Маълумоти ҳуқуқӣ",
        "legal_text": "📄 <b>Ҳуҷҷатҳои ҳуқуқӣ</b>",
        "policy": "Сиёсати махфият", "terms": "Шартномаи корбар",
        "trial_msg": "🎁 <b>Ба шумо 3 рӯз Premium-и ройгон дода шуд!</b>\n\nИн туҳфа барои санҷиши VPN-и мост. Истиноди шумо:"
    },
    "tr": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\n\nEn hızlı ve en güvenli internetin keyfini çıkarın. Ödeme yapmak veya uygulamayı indirmek için aşağıdaki butonları kullanın:",
        "btn_pay": "💳 Satın Al", "btn_how": "📖 Nasıl ödenir?",
        "btn_download": "🚀 İndir", "btn_support": "👨‍💻 Destek", "btn_share": "🤝 Paylaş",
        "pay_text": "💳 <b>Plan seçin</b>\n\nÖdemeler otomatik olarak alınır:",
        "pay_btn_link": "💳 Ödeme Linki", "back": "⬅️ Geri", "next": "İleri ➡️",
        "check_btn": "✅ Ödedim (Kontrol Et)", "checking": "⏳ Ödeme kontrol ediliyor...",
        "success": "🎉 <b>Premium Aktif Edildi!</b>\n\nUygulamayı açın ve VPN'in tadını çıkarın!",
        "not_found": "⚠️ Ödeme bulunamadı. Ödemeden sonra 1-2 dakika bekleyin.",
        "how_step_1": "🚀 <b>ADIM 1: Plan seçimi</b>",
        "how_step_2": "💳 <b>ADIM 2: Ödeme</b>",
        "how_step_3": "✅ <b>ADIM 3: Aktivasyon</b>",
        "menu_back": "Ana Menü:",
        "share_msg": "🚀 mubVPN — Android için en hızlı ve güvenli VPN!\n\nHemen indir! 👇",
        "share_title": "🤝 <b>Paylaş:</b>", "btn_share_now": "📲 Sharing link",
        "btn_referral": "🎁 Ücretsiz Premium (Referans)",
        "btn_my_vpn": "🔑 Benim linkim",
        "my_vpn_text": "👤 <b>Aboneliğiniz</b>\n\n• Durum: {status}\n• Bitiş Tarihi: {expiry}\n\n🔑 <b>Kişisel linkiniz:</b>\n<code>{vpn_link}</code>",
        "no_premium": "⚠️ <b>Premium aboneliğiniz yok</b>",
        "ref_menu_text": "🎁 <b>Referans Programı!</b>\n\nArkadaşlarınızı davet edin ve <b>ücretsiz Premium</b> kazanın!\n\n• Her arkadaş için: <b>+10 gün ücretsiz Premium</b>.\n\n🔗 <b>Referans linkiniz:</b>\n<code>{ref_link}</code>",
        "plan_1m": "1 Ay", "plan_3m": "3 Ay", "plan_6m": "6 Ay", "plan_1y": "1 Yıl",
        "pay_info": "💳 <b>{name} Premium</b>\n\nFiyat: {rub} RUB\n\nÖdemek için butona tıklayın. Premium otomatik olarak aktif edilir.",
        "dl_title": "🚀 <b>Cihazınızı seçin</b>",
        "dl_pc_desc": "💻 <b>Clash Verge Rev (v2.5.1)</b>",
        "dl_mobile_desc": "📱 <b>Mobil uygulamalar</b>",
        "btn_legal": "📄 Yasal Bilgiler",
        "legal_text": "📄 <b>Yasal belgeler</b>",
        "policy": "Gizlilik Politikası", "terms": "Kullanıcı Sözleşmesi",
        "trial_msg": "🎁 <b>Size 3 günlük ücretsiz Premium verildi!</b>\n\nVPN'imizi denemeniz için bir hediye. İşte linkiniz:"
    }
}

# --- КЛАВИАТУРАЛАР ---

def get_firebase_config():
    """Firebase'ден жөндөөлөрдү алат."""
    try:
        url_sys = f"{FIREBASE_DB_URL}/system_config.json?auth={FIREBASE_DB_SECRET}"
        url_set = f"{FIREBASE_DB_URL}/settings.json?auth={FIREBASE_DB_SECRET}"

        sys_resp = requests.get(url_sys, timeout=5)
        set_resp = requests.get(url_set, timeout=5)

        sys_config = sys_resp.json() if sys_resp.status_code == 200 else {}
        settings = set_resp.json() if set_resp.status_code == 200 else {}

        # Эгер маалымат жок болсо (None), бош сөздүк колдонуу
        if sys_config is None: sys_config = {}
        if settings is None: settings = {}

        show_pay = sys_config.get("show_external_payments", True)
        show_tg = settings.get("show_telegram", True)

        # Консолдон маалыматты текшерүү үчүн
        log.info(f"Firebase Config - Payments: {show_pay}, Telegram: {show_tg}")

        return {
            "show_external_payments": show_pay,
            "show_telegram": show_tg
        }
    except Exception as e:
        log.error(f"Error fetching firebase config: {e}")
        # Ката болсо баскычтарды жашырбайбыз
        return {"show_external_payments": True, "show_telegram": True}

def get_lang_keyboard():

    return InlineKeyboardMarkup([

        [InlineKeyboardButton("🇰🇬 Кыргызча", callback_data='set_lang_ky'), InlineKeyboardButton("🇷🇺 Русский", callback_data='set_lang_ru')],

        [InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data='set_lang_uz'), InlineKeyboardButton("🇹🇯 Тоҷикӣ", callback_data='set_lang_tg')],

        [InlineKeyboardButton("🇰🇿 Қазақша", callback_data='set_lang_kk'), InlineKeyboardButton("🇹🇷 Türkçe", callback_data='set_lang_tr')],

        [InlineKeyboardButton("🇺🇸 English", callback_data='set_lang_en')]

    ])



def get_main_keyboard(lang):
    L = STRINGS.get(lang, STRINGS['ru'])

    # Текшерүү үчүн Firebase жөндөөлөрүн убактылуу эске албай,
    # баскычтарды ар дайым көрсөтөбүз.
    keyboard = [
        [InlineKeyboardButton(L["btn_download"], callback_data='dl_platforms')],
        [InlineKeyboardButton(L["btn_pay"], callback_data='pay_menu')],
        [InlineKeyboardButton(L["btn_referral"], callback_data='referral_menu')],
        [InlineKeyboardButton(L["btn_how"], callback_data='how_1')],
        [InlineKeyboardButton(L["btn_legal"], callback_data='legal_menu')],
        [InlineKeyboardButton(L["btn_support"], url=SUPPORT_URL)]
    ]

    return InlineKeyboardMarkup(keyboard)



# --- КОМАНДАЛАР ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    uid = None

    if context.args:
        arg = context.args[0]
        if arg.startswith('ref_'):
            inviter_id = arg.replace('ref_', '')
            success, status = register_referral(tg_id, inviter_id)
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

            # Реферал аркылуу келген колдонуучуну да каттайбыз
            uid = f"tg_{tg_id}"
        else:
            uid = arg
            context.user_data['uid'] = uid
            try:
                url_user = f"{FIREBASE_DB_URL}/users/{uid}.json?auth={FIREBASE_DB_SECRET}"
                requests.patch(url_user, json={"telegram_id": tg_id})
                url_map = f"{FIREBASE_DB_URL}/telegram_to_uid/{tg_id}.json?auth={FIREBASE_DB_SECRET}"
                requests.put(url_map, json=uid)
            except Exception as ex:
                log.error(f"Error saving telegram_id mapping: {ex}")

    # Эгер UID жок болсо (түз Телеграмдан кирсе)
    if not uid:
        map_url = f"{FIREBASE_DB_URL}/telegram_to_uid/{tg_id}.json?auth={FIREBASE_DB_SECRET}"
        resp_map = requests.get(map_url)
        if resp_map.status_code == 200 and resp_map.json():
            uid = resp_map.json()
        else:
            uid = f"tg_{tg_id}"
            try:
                requests.put(map_url, json=uid)
                requests.patch(f"{FIREBASE_DB_URL}/users/{uid}.json?auth={FIREBASE_DB_SECRET}", json={
                    "telegram_id": tg_id,
                    "is_paid": False,
                    "isPremium": False
                })
            except: pass

    if uid:
        context.user_data['uid'] = uid
        if firebase_give_trial(uid):
            context.user_data['just_registered'] = True

    text = "🌐 Choose language / Тилди тандаңыз / Выберите язык:"
    if update.message: await update.message.reply_text(text, reply_markup=get_lang_keyboard())
    else: await update.callback_query.message.edit_text(text, reply_markup=get_lang_keyboard())



async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query; await query.answer()

    data = query.data; lang = context.user_data.get('lang', 'ru')



    if data.startswith('set_lang_'):

        lang = data.split('_')[2]; context.user_data['lang'] = lang
        L = STRINGS.get(lang, STRINGS['ru'])

        await query.message.edit_text(L["welcome"], reply_markup=get_main_keyboard(lang), parse_mode=ParseMode.HTML)

        # Эгер жаңы катталган болсо, сыноо билдирүүсүн жөнөтүү
        if context.user_data.get('just_registered'):
            uid = context.user_data.get('uid')
            app_url = os.environ.get('APP_URL') or os.environ.get('RENDER_EXTERNAL_URL') or "https://mubvpn-bot-vy55.onrender.com"
            sub_link = f"{app_url}/sub/{uid}"

            trial_text = L.get("trial_msg", "🎁 Trial activated!") + f"\n\n<code>{sub_link}</code>"
            await context.bot.send_message(chat_id=query.from_user.id, text=trial_text, parse_mode=ParseMode.HTML)
            context.user_data['just_registered'] = False



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
        try:
            L = STRINGS.get(lang, STRINGS['ru']);
            parts = data.split(':')
            plan_id = parts[1]
            uid = parts[2] if len(parts) > 2 else context.user_data.get('uid', query.from_user.id)
            plan = PLANS.get(plan_id)

            if plan:
                plan_name = STRINGS[lang][plan['name_key']]
                # Төлөм шилтемесин түзүү
                payment_url, error_info = create_platega_invoice(str(uid), plan_id, plan['rub'])

                if payment_url:
                    text = L["pay_info"].format(name=plan_name, rub=plan['rub'])
                    keyboard = [
                        [InlineKeyboardButton(L["pay_btn_link"], url=payment_url)],
                        [InlineKeyboardButton(L["back"], callback_data='pay_menu')]
                    ]
                    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
                else:
                    await query.message.edit_text(f"Төлөм шилтемесин түзүүдө ката кетти.\n\nКата маалыматы: {error_info}", reply_markup=get_main_keyboard(lang))
        except Exception as e:
            log.error(f"Error in handle_callback (plan): {e}")
            await query.message.edit_text(f"Кечиресиз, техникалык ката кетти: {e}", reply_markup=get_main_keyboard(lang))

    elif data == 'check_payment':
        L = STRINGS.get(lang, STRINGS['ru'])
        await query.message.edit_text(L["checking"], reply_markup=get_main_keyboard(lang))

    elif data == 'main_menu':
        await query.message.edit_text(STRINGS.get(lang, STRINGS['ru'])["welcome"], reply_markup=get_main_keyboard(lang), parse_mode=ParseMode.HTML)

    elif data == 'dl_platforms':
        L = STRINGS.get(lang, STRINGS['ky'])
        text = L.get("dl_title", "🚀 <b>Түзмөгүңүздү тандаңыз</b>")
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
        text = L.get("dl_pc_desc", "💻 <b>Clash Verge Rev (v2.5.1)</b>")
        kb = [
            [InlineKeyboardButton("🪟 Windows x64 (EXE)", url="https://github.com/clash-verge-rev/clash-verge-rev/releases/download/v2.5.1/Clash.Verge_2.5.1_x64-setup.exe")],
            [InlineKeyboardButton("🪟 Windows ARM64", url="https://github.com/clash-verge-rev/clash-verge-rev/releases/download/v2.5.1/Clash.Verge_2.5.1_arm64-setup.exe")],
            [InlineKeyboardButton(L["back"], callback_data='dl_platforms')]
        ]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif data == 'dl_mac':
        L = STRINGS.get(lang, STRINGS['ky'])
        text = L.get("dl_pc_desc", "💻 <b>Clash Verge Rev (v2.5.1)</b>")
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




    elif data == 'referral_menu' or data == 'share_menu':
        L = STRINGS.get(lang, STRINGS['ru']); uid = context.user_data.get('uid', query.from_user.id)
        bot_info = await context.bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start=ref_{uid}"

        app_url = os.environ.get('APP_URL') or os.environ.get('RENDER_EXTERNAL_URL') or "https://mubvpn-bot-vy55.onrender.com"
        share_page_url = f"{app_url}/share/{uid}?lang={lang}"

        text = L["ref_menu_text"].format(ref_link=ref_link)
        kb = [
            [InlineKeyboardButton(L["btn_share_now"], web_app=WebAppInfo(url=share_page_url))],
            [InlineKeyboardButton(L["back"], callback_data='main_menu')]
        ]
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)



# --- WEB SERVER (WEBHOOK) ---

class BotHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/webhook/platega':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data)
                log.info(f"Platega Webhook received: {data}")

                # Төлөм ийгиликтүү болсо
                status = str(data.get("status", "")).upper()
                if status == "CONFIRMED":
                    # UID жана Plan ID'ни payload'дон алуу
                    payload = data.get("payload", "")
                    uid = None
                    plan_id = None

                    if ":" in payload:
                        parts = payload.split(":")
                        uid = parts[0]
                        plan_id = parts[1]
                    else:
                        # Эски формат же ката болсо metadata'дан текшерүү
                        metadata = data.get("metadata", {})
                        uid = metadata.get("uid")
                        plan_id = metadata.get("plan_id")

                    if uid and plan_id:
                        months = PLANS.get(plan_id, {}).get("months", 1)
                        success = firebase_set_premium(uid, months)

                        if success:
                            # Колдонуучуга Telegram аркылуу билдирүү жөнөтүү
                            self.send_telegram_notification(uid)
                            log.info(f"Premium activated for user {uid} via payload {payload}")

                self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
            except Exception as e:
                log.error(f"Webhook error: {e}")
                self.send_response(400); self.end_headers()
        else:
            self.send_response(404); self.end_headers()

    def send_telegram_notification(self, uid):
        """Төлөмдөн кийин Telegram аркылуу кабар жөнөтөт."""
        try:
            # Түздөн-түз Telegram ID же UID экенин текшерүү
            tg_id = uid if str(uid).isdigit() else None

            if not tg_id:
                # Алгач UID'ден Telegram ID табуу керек
                url_map = f"{FIREBASE_DB_URL}/telegram_to_uid.json?auth={FIREBASE_DB_SECRET}"
                resp = requests.get(url_map)
                if resp.status_code == 200:
                    mapping = resp.json()
                    if mapping:
                        for tid, u in mapping.items():
                            if str(u) == str(uid):
                                tg_id = tid; break

            if tg_id:
                app_url = os.environ.get('APP_URL') or os.environ.get('RENDER_EXTERNAL_URL') or "https://mubvpn-bot-vy55.onrender.com"
                sub_link = f"{app_url}/sub/{uid}"

                # Серверлердин тизмесин билдирүүгө кошуу
                server_list = "\n".join([f"📍 {srv['name']}" for srv in SERVERS])

                msg = (
                    "🎉 <b>Төлөм кабыл алынды!</b>\n\n"
                    "Premium активдешти. Төмөндө сиздин жеке жазылуу шилтемеңиз (VLESS / TCP / REALITY | JSON):\n\n"
                    f"🌐 <b>Subscription Link:</b>\n<code>{sub_link}</code>\n\n"
                    f"<b>Жеткиликтүү серверлер:</b>\n{server_list}\n\n"
                    "<i>Бул шилтемени көчүрүп, тиркемеге (v2rayNG, Clash ж.б.) кошуңуз.</i>"
                )
                send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                log.info(f"Sending success notification to {tg_id}")
                requests.post(send_url, data={"chat_id": tg_id, "text": msg, "parse_mode": "HTML"})
            else:
                log.error(f"Could not find Telegram ID for UID: {uid}")
        except Exception as e:
            log.error(f"Error sending Telegram notification: {e}")

    def do_GET(self):
        if self.path == '/download':
            apk_url = 'https://github.com/Ulanbekmahmaraimov/mubvpn-bot/releases/download/v1.0.10/app-release.apk'
            self.send_response(302); self.send_header('Location', apk_url); self.end_headers(); return

        if self.path.startswith('/sub/'):
            uid = self.path.replace('/sub/', '')
            # Premium текшерүү
            url_user = f"{FIREBASE_DB_URL}/users/{uid}.json?auth={FIREBASE_DB_SECRET}"
            resp = requests.get(url_user)
            user_data = resp.json() if resp.status_code == 200 else None

            if user_data and user_data.get("isPremium"):
                configs = []
                v_uuid = user_data.get("vpn_uuid", "25ebd509-9479-483e-a1aa-8bc996424cea")
                expiry_date = user_data.get("premium_expiry", "---").split('T')[0]

                for srv in SERVERS:
                    # Шилтемеге мөөнөтүн жана сервердин атын кошобуз
                    link = f"vless://{v_uuid}@{srv['host']}:8443?encryption=none&flow=xtls-rprx-vision&type=tcp&security=reality&sni=auto.quattro-tech.ru&fp=qq&pbk=10rVZPoOUP1TlQviIAsQ_jAROX0fRQxH0C92nq_zGQc&sid=43dcff53849b81e6#mubVPN_{srv['name']}_{expiry_date}"
                    configs.append(link)

                content = "\n".join(configs)
                b64_content = base64.b64encode(content.encode()).decode()

                self.send_response(200)
                self.send_header('Content-Type', 'text/plain; charset=utf-8')
                self.end_headers()
                self.wfile.write(b64_content.encode())
                return
            else:
                self.send_response(403); self.end_headers(); self.wfile.write(b"No Premium")
                return

        if self.path.startswith('/share/'):
            # Универсалдуу бөлүшүү баракчасы
            try:
                parts = self.path.split('/')
                uid_part = parts[2].split('?')[0]

                # Боттун атын алуу үчүн API колдонобуз
                bot_username = "mubvpn_pay_bot"
                ref_link = f"https://t.me/{bot_username}?start=ref_{uid_part}"
                share_msg = "🚀 mubVPN — Android үчүн эң тез жана коопсуз VPN! Азыр жүктөп ал! 👇"

                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <title>Sharing link</title>
                    <script src="https://telegram.org/js/telegram-web-app.js"></script>
                    <style>
                        body {{ background-color: #000; color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; font-family: sans-serif; }}
                        .btn {{ background: linear-gradient(45deg, #00f2fe 0%, #4facfe 100%); border: none; padding: 15px 30px; border-radius: 10px; color: black; font-weight: bold; font-size: 18px; cursor: pointer; }}
                    </style>
                </head>
                <body>
                    <button class="btn" onclick="share()">📲 Sharing link</button>
                    <script>
                        const tg = window.Telegram.WebApp;
                        tg.ready();
                        tg.expand();
                        function share() {{
                            if (navigator.share) {{
                                navigator.share({{
                                    title: 'mubVPN',
                                    text: `{share_msg}`,
                                    url: '{ref_link}'
                                }}).then(() => tg.close())
                                  .catch((err) => {{
                                      if(err.name !== 'AbortError') tg.close();
                                  }});
                            }} else {{
                                // Fallback: көчүрүп алуу
                                const el = document.createElement('textarea');
                                el.value = '{ref_link}';
                                document.body.appendChild(el);
                                el.select();
                                document.execCommand('copy');
                                document.body.removeChild(el);
                                alert('Шилтеме көчүрүлдү!');
                                tg.close();
                            }}
                        }}
                        // Дароо чакырууга аракет кылабыз
                        setTimeout(share, 200);
                    </script>
                </body>
                </html>
                """
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html_content.encode())
                return
            except:
                self.send_response(500); self.end_headers(); return

        self.send_response(200); self.end_headers(); self.wfile.write(b"mubVPN Bot is active!")



def run_server():
    port = int(os.environ.get('PORT', 8080))
    HTTPServer(('0.0.0.0', port), BotHandler).serve_forever()



def self_ping():
    app_url = os.environ.get('APP_URL') or os.environ.get('RENDER_EXTERNAL_URL')
    if not app_url: return
    while True:
        try: requests.get(app_url)
        except: pass
        time.sleep(600)


def main():
    # Веб-серверди иштетүү
    threading.Thread(target=run_server, daemon=True).start()
    # Өзүн-өзү ойготуп туруучу функцияны иштетүү
    threading.Thread(target=self_ping, daemon=True).start()

    from telegram.request import HTTPXRequest
    request = HTTPXRequest(connect_timeout=20, read_timeout=20)

    app = Application.builder().token(BOT_TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(CallbackQueryHandler(handle_callback))

    log.info("🤖 Bot is running...")

    app.run_polling(drop_pending_updates=True)



if __name__ == "__main__":
    main()
