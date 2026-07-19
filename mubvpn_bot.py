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
import yaml
import secrets
from datetime import datetime, timedelta

from http.server import HTTPServer, BaseHTTPRequestHandler

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
from telegram.request import HTTPXRequest

# --- ЖӨНДӨӨЛӨР ---
BOT_TOKEN    = "8400265569:AAHQ21_zNVS3XPDlMoE9I8TW0JwaIaUuA1s"
SUPPORT_URL  = "https://t.me/kl_mub"
FIREBASE_DB_URL    = "https://mubvpn-8b892-default-rtdb.firebaseio.com"
FIREBASE_DB_SECRET = "NgRNzmtQYdgUcFWXiDRPAHAsSURVni2WaIKTw9Re"

PLATEGA_MERCHANT_ID = "7daa1458-3248-4106-bc81-bfe7f33b742f"
PLATEGA_API_KEY     = "Ia6n9MgN172IKWWOGAzkfQveSZ4ZIq2ktTpkt5hiBNpCfbtrX4V4XLozuKarEB2OzkNEEfHDsaTZadGJhZUJ6He7AtQFGS0U6Lud"

SERVERS = [
    {
        "name": "Германия 🇩🇪",
        "host": "167.235.22.54",
        "uuid": "2e922e6a-65db-4767-8216-a4b6b501b3b8",
        "pbk": "0CIqFJJXUoImvhH9fBIBBsW0G798Q9WpwWDdhbdw93M",
        "sid": "7682624ec01fe9",
        "sni": "www.sony.com",
        "spx": "/YQV0cMA4bZQ77uu"
    },
    {"name": "Нидерланды 🇳🇱", "host": "45.143.93.125"},
    {"name": "Финляндия 🇫🇮", "host": "95.216.148.163"},
    {"name": "Казахстан 🇰🇿", "host": "185.120.77.203"},
    {"name": "Польша 🇵🇱", "host": "144.31.2.98"},
    {"name": "АКШ 🇺🇸", "host": "46.8.209.180"},
    {"name": "Латвия 🇱🇻", "host": "46.183.223.210"}
]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
log = logging.getLogger(__name__)

PLANS = {
    "1m":  {"name_key": "plan_1m", "months": 1,  "rub": 109.99},
    "3m":  {"name_key": "plan_3m", "months": 3,  "rub": 309.99},
    "6m":  {"name_key": "plan_6m", "months": 6,  "rub": 599.99},
    "1y":  {"name_key": "plan_1y", "months": 12, "rub": 1099.99},
}

# --- ФУНКЦИЯЛАР ---

def firebase_set_premium(uid: str, months: int) -> str:
    try:
        url_old = f"{FIREBASE_DB_URL}/users/{uid}.json?auth={FIREBASE_DB_SECRET}"
        resp = requests.get(url_old, timeout=10)
        if resp.status_code != 200 or not resp.json(): return None
        user_data = resp.json()
        start_date = datetime.now()
        cur_exp = user_data.get("premium_expiry")
        if cur_exp:
            try:
                dt_exp = datetime.fromisoformat(cur_exp)
                if dt_exp > start_date: start_date = dt_exp
            except: pass
        expiry = (start_date + timedelta(days=months * 30)).isoformat()
        new_uid = secrets.token_urlsafe(12).replace('-', '').replace('_', '')[:16]
        user_data.update({"premium_expiry": expiry, "is_paid": True, "isPremium": True, "vpn_uuid": "2e922e6a-65db-4767-8216-a4b6b501b3b8", "last_payment_date": datetime.now().isoformat()})
        requests.put(f"{FIREBASE_DB_URL}/users/{new_uid}.json?auth={FIREBASE_DB_SECRET}", json=user_data, timeout=10)
        tg_id = user_data.get("telegram_id")
        if tg_id: requests.put(f"{FIREBASE_DB_URL}/telegram_to_uid/{tg_id}.json?auth={FIREBASE_DB_SECRET}", json=new_uid, timeout=10)
        requests.delete(url_old, timeout=10)
        return new_uid
    except Exception as e:
        log.error(f"Error in firebase_set_premium: {e}")
        return None

def register_referral(new_tg_id: int, inviter_id: str) -> tuple[bool, str]:
    try:
        ref_url = f"{FIREBASE_DB_URL}/referrals/{new_tg_id}.json?auth={FIREBASE_DB_SECRET}"
        if requests.get(ref_url, timeout=10).json(): return False, "already"
        inv_uid = inviter_id if (len(str(inviter_id)) == 16 or len(str(inviter_id)) == 28) else requests.get(f"{FIREBASE_DB_URL}/telegram_to_uid/{inviter_id}.json?auth={FIREBASE_DB_SECRET}", timeout=10).json()
        if not inv_uid: return False, "not_found"
        inv_url = f"{FIREBASE_DB_URL}/users/{inv_uid}.json?auth={FIREBASE_DB_SECRET}"
        inv_data = requests.get(inv_url, timeout=10).json()
        if not inv_data or str(inv_data.get("telegram_id")) == str(new_tg_id): return False, "invalid"
        start_dt = datetime.now()
        cur_exp = inv_data.get("premium_expiry")
        if cur_exp:
            try:
                dt_exp = datetime.fromisoformat(cur_exp)
                if dt_exp > start_dt: start_dt = dt_exp
            except: pass
        new_exp = (start_dt + timedelta(days=10)).isoformat()
        requests.patch(inv_url, json={"premium_expiry": new_exp, "referral_count": inv_data.get("referral_count", 0) + 1, "isPremium": True}, timeout=10)
        requests.put(ref_url, json={"inviter_uid": inv_uid, "timestamp": datetime.now().isoformat()}, timeout=10)
        return True, "success"
    except Exception as e:
        log.error(f"Error in register_referral: {e}")
        return False, "error"

def firebase_give_trial(uid: str) -> bool:
    try:
        url = f"{FIREBASE_DB_URL}/users/{uid}.json?auth={FIREBASE_DB_SECRET}"
        user_data = requests.get(url, timeout=10).json() or {}
        if user_data.get("trial_given") or user_data.get("isPremium"): return False
        expiry = (datetime.now() + timedelta(days=3)).isoformat()
        requests.patch(url, json={"premium_expiry": expiry, "isPremium": True, "trial_given": True, "vpn_uuid": "2e922e6a-65db-4767-8216-a4b6b501b3b8"}, timeout=10)
        return True
    except Exception as e:
        log.error(f"Error in firebase_give_trial: {e}")
        return False

def create_platega_invoice(uid, plan_id, amount) -> tuple[str, str]:
    try:
        url = "https://app.platega.io/v2/transaction/process"
        headers = {"X-MerchantId": PLATEGA_MERCHANT_ID, "X-Secret": PLATEGA_API_KEY, "Content-Type": "application/json"}
        data = {"paymentMethod": 2, "paymentDetails": {"amount": float(amount), "currency": "RUB"}, "description": f"mubVPN - {plan_id}", "payload": f"{uid}:{plan_id}"}
        resp = requests.post(url, json=data, headers=headers, timeout=15)
        return resp.json().get("url"), None if resp.status_code == 200 else f"Error {resp.status_code}"
    except Exception as e: return None, str(e)

# --- TEXTS ---
STRINGS = {
    "ky": {
        "welcome": "🚀 <b>mubVPN — Эң тез жана коопсуз!</b>\n\n🌍 Чектөөсүз интернетке жол ачыңыз.\n⚡️ Жогорку ылдамдык.\n🛡 Купуялык.",
        "btn_pay": "💳 Сатып алуу", "btn_how": "📖 Кантип?", "btn_download": "🚀 Жүктөө", "btn_support": "👨‍💻 Колдоо", "btn_share": "🤝 Бөлүшүү",
        "btn_my_vpn": "🔑 Менин шилтемем", "btn_referral": "🎁 Акысыз Premium", "back": "⬅️ Артка", "pay_text": "💳 Планды тандаңыз:",
        "trial_msg": "🎁 Сизге 3 күндүк акысыз Premium берилди!\nШилтемеңиз:", "no_premium": "⚠️ Premium жок",
        "my_vpn_text": "👤 Статус: {status}\n⌛ Мөөнөтү: {expiry}\n\n🔗 Шилтеме:\n<code>{vpn_link}</code>",
        "ref_menu_text": "🎁 Досторду чакырып, +10 күн алыңыз!\nШилтемеңиз:\n<code>{ref_link}</code>",
        "plan_1m": "1 ай", "plan_3m": "3 ай", "plan_6m": "6 ай", "plan_1y": "1 жыл", "pay_info": "💳 {name} — {rub} RUB", "pay_btn_link": "💳 Төлөм шилтемеси", "share_msg": "🚀 mubVPN — Эң тез жана коопсуз VPN!"
    },
    "ru": {
        "welcome": "🚀 <b>mubVPN — Самый быстрый и безопасный!</b>\n\n🌍 Свободный интернет.\n⚡️ Высокая скорость.\n🛡 Приватность.",
        "btn_pay": "💳 Купить", "btn_how": "📖 Как?", "btn_download": "🚀 Скачать", "btn_support": "👨‍💻 Поддержка", "btn_share": "🤝 Поделиться",
        "btn_my_vpn": "🔑 Моя ссылка", "btn_referral": "🎁 Бесплатный Premium", "back": "⬅️ Назад", "pay_text": "💳 Выберите тариф:",
        "trial_msg": "🎁 Вам начислено 3 дня бесплатного Premium!\nСсылка:", "no_premium": "⚠️ Нет Premium",
        "my_vpn_text": "👤 Статус: {status}\n⌛ Истекает: {expiry}\n\n🔗 Ссылка:\n<code>{vpn_link}</code>",
        "ref_menu_text": "🎁 Приглашайте друзей и получайте +10 дней!\nСсылка:\n<code>{ref_link}</code>",
        "plan_1m": "1 месяц", "plan_3m": "3 месяца", "plan_6m": "6 месяцев", "plan_1y": "1 год", "pay_info": "💳 {name} — {rub} RUB", "pay_btn_link": "💳 Ссылка на оплату", "share_msg": "🚀 mubVPN — Самый быстрый и безопасный VPN!"
    },
    "en": {
        "welcome": "🚀 <b>mubVPN — Fastest & Safest!</b>\n\n🌍 Unlock the open internet.\n⚡️ High speed.\n🛡 Privacy.",
        "btn_pay": "💳 Buy", "btn_how": "📖 How?", "btn_download": "🚀 Download", "btn_support": "👨‍💻 Support", "btn_share": "🤝 Share",
        "btn_my_vpn": "🔑 My Link", "btn_referral": "🎁 Free Premium", "back": "⬅️ Back", "pay_text": "💳 Choose a plan:",
        "trial_msg": "🎁 You've been granted 3 days of free Premium!\nYour link:", "no_premium": "⚠️ No Premium",
        "my_vpn_text": "👤 Status: {status}\n⌛ Expiry: {expiry}\n\n🔗 Link:\n<code>{vpn_link}</code>",
        "ref_menu_text": "🎁 Invite friends and get +10 days!\nYour link:\n<code>{ref_link}</code>",
        "plan_1m": "1 month", "plan_3m": "3 months", "plan_6m": "6 months", "plan_1y": "1 year", "pay_info": "💳 {name} — {rub} RUB", "pay_btn_link": "💳 Payment Link", "share_msg": "🚀 mubVPN — Fastest and Safest VPN!"
    },
    "uz": {
        "welcome": "🚀 <b>mubVPN — Eng tezkor va xavfsiz!</b>\n\n🌍 Cheksiz internetga yo'l oching.\n⚡️ Yuqori tezlik.\n🛡 Maxfiylik.",
        "btn_pay": "💳 Sotib olish", "btn_how": "📖 Qanday?", "btn_download": "🚀 Yuklab olish", "btn_support": "👨‍💻 Yordam", "btn_share": "🤝 Ulashish",
        "btn_my_vpn": "🔑 Mening havola", "btn_referral": "🎁 Bepul Premium", "back": "⬅️ Orqaga", "pay_text": "💳 Tarifni tanlang:",
        "trial_msg": "🎁 Sizga 3 kunlik bepul Premium berildi!\nSizning havolangiz:", "no_premium": "⚠️ Premium yo'q",
        "my_vpn_text": "👤 Holati: {status}\n⌛ Muddati: {expiry}\n\n🔗 Havola:\n<code>{vpn_link}</code>",
        "ref_menu_text": "🎁 Do'stlarni taklif qiling va +10 kun oling!\nSizning havolangiz:\n<code>{ref_link}</code>",
        "plan_1m": "1 oy", "plan_3m": "3 oy", "plan_6m": "6 oy", "plan_1y": "1 yil", "pay_info": "💳 {name} — {rub} RUB", "pay_btn_link": "💳 To'lov havolasi", "share_msg": "🚀 mubVPN — Eng tezkor va xavfsiz VPN!"
    },
    "kk": {
        "welcome": "🚀 <b>mubVPN — Ең жылдам және қауіпсіз!</b>\n\n🌍 Шектеусіз интернетке жол ашыңыз.\n⚡️ Жоғары жылдамдық.\n🛡 Құпиялылық.",
        "btn_pay": "💳 Сатып алу", "btn_how": "📖 Қалай?", "btn_download": "🚀 Жүктеу", "btn_support": "👨+💻 Қолдау", "btn_share": "🤝 Бөлісу",
        "btn_my_vpn": "🔑 Менің сілтемем", "btn_referral": "🎁 Тегін Premium", "back": "⬅️ Артқа", "pay_text": "💳 Тарифті таңдаңыз:",
        "trial_msg": "🎁 Сізге 3 күндік тегін Premium берілді!\nСілтемеңиз:", "no_premium": "⚠️ Premium жоқ",
        "my_vpn_text": "👤 Мәртебесі: {status}\n⌛ Мерзімі: {expiry}\n\n🔗 Сілтеме:\n<code>{vpn_link}</code>",
        "ref_menu_text": "🎁 Достарды шақырып, +10 күн алыңыз!\nСілтемеңіз:\n<code>{ref_link}</code>",
        "plan_1m": "1 ай", "plan_3m": "3 ай", "plan_6m": "6 ай", "plan_1y": "1 жыл", "pay_info": "💳 {name} — {rub} RUB", "pay_btn_link": "💳 Төлем сілтемесі", "share_msg": "🚀 mubVPN — Ең жылдам және қауіпсіз VPN!"
    },
    "tg": {
        "welcome": "🚀 <b>mubVPN — Зудтарин ва бехатарин!</b>\n\n🌍 Ба интернети озод дастрасӣ пайдо кунед.\n⚡️ Суръати баланд.\n🛡 Махфият.",
        "btn_pay": "💳 Харидан", "btn_how": "📖 Чӣ тавр?", "btn_download": "🚀 Боргирӣ", "btn_support": "👨‍💻 Дастгирӣ", "btn_share": "🤝 Фиристодан",
        "btn_my_vpn": "🔑 Истиноди ман", "btn_referral": "🎁 Premium-и ройгон", "back": "⬅️ Ба ақиб", "pay_text": "💳 Тарифро интихоб кунед:",
        "trial_msg": "🎁 Ба шумо 3 рӯз Premium-и ройгон дода шуд!\nИстиноди шумо:", "no_premium": "⚠️ Premium надоред",
        "my_vpn_text": "👤 Статус: {status}\n⌛ Мӯҳлат: {expiry}\n\n🔗 Истинод:\n<code>{vpn_link}</code>",
        "ref_menu_text": "🎁 Дӯстонро даъват кунед ва +10 рӯз гиред!\nИстиноди шумо:\n<code>{ref_link}</code>",
        "plan_1m": "1 моҳ", "plan_3m": "3 моҳ", "plan_6m": "6 моҳ", "plan_1y": "1 сол", "pay_info": "💳 {name} — {rub} RUB", "pay_btn_link": "💳 Истиноди пардохт", "share_msg": "🚀 mubVPN — VPN-и зудтарин ва бехатар!"
    },
    "tr": {
        "welcome": "🚀 <b>mubVPN — En Hızlı ve Güvenli!</b>\n\n🌍 Özgür internete kapı açın.\n⚡️ Yüksek hız.\n🛡 Gizlilik.",
        "btn_pay": "💳 Satın Al", "btn_how": "📖 Nasıl?", "btn_download": "🚀 İndir", "btn_support": "👨‍💻 Destek", "btn_share": "🤝 Paylaş",
        "btn_my_vpn": "🔑 Benim Linkim", "btn_referral": "🎁 Ücretsiz Premium", "back": "⬅️ Geri", "pay_text": "💳 Plan seçin:",
        "trial_msg": "🎁 Size 3 günlük ücretsiz Premium verildi!\nLinkiniz:", "no_premium": "⚠️ Premium yok",
        "my_vpn_text": "👤 Durum: {status}\n⌛ Bitiş: {expiry}\n\n🔗 Link:\n<code>{vpn_link}</code>",
        "ref_menu_text": "🎁 Arkadaşlarınızı davet edin ve +10 gün kazanın!\nLinkiniz:\n<code>{ref_link}</code>",
        "plan_1m": "1 ay", "plan_3m": "3 ay", "plan_6m": "6 ay", "plan_1y": "1 yıl", "pay_info": "💳 {name} — {rub} RUB", "pay_btn_link": "💳 Ödeme Linki", "share_msg": "🚀 mubVPN — En Hızlı ve Güvenli VPN!"
    }
}

def get_main_keyboard(lang):
    L = STRINGS.get(lang, STRINGS['ru'])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(L["btn_download"], callback_data='dl_platforms')],
        [InlineKeyboardButton(L["btn_my_vpn"], callback_data='my_vpn')],
        [InlineKeyboardButton(L["btn_pay"], callback_data='pay_menu')],
        [InlineKeyboardButton(L["btn_referral"], callback_data='referral_menu')],
        [InlineKeyboardButton(L["btn_support"], url=SUPPORT_URL)]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        tg_id = update.effective_user.id
        resp = requests.get(f"{FIREBASE_DB_URL}/telegram_to_uid/{tg_id}.json?auth={FIREBASE_DB_SECRET}", timeout=10)
        uid = resp.json() if resp.status_code == 200 else None

        if context.args and context.args[0].startswith('ref_'):
            success, _ = register_referral(tg_id, context.args[0].replace('ref_', ''))
            if success: await context.bot.send_message(chat_id=tg_id, text="🎁 Сиз чакырууну кабыл алдыңыз!")

        if not uid:
            uid = secrets.token_urlsafe(12).replace('-', '').replace('_', '')[:16]
            requests.put(f"{FIREBASE_DB_URL}/telegram_to_uid/{tg_id}.json?auth={FIREBASE_DB_SECRET}", json=uid, timeout=10)
            requests.patch(f"{FIREBASE_DB_URL}/users/{uid}.json?auth={FIREBASE_DB_SECRET}", json={"telegram_id": tg_id, "isPremium": False, "created_at": datetime.now().isoformat()}, timeout=10)

        context.user_data['uid'] = uid
        if firebase_give_trial(uid): context.user_data['just_registered'] = True

        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇰🇬 Кыргызча", callback_data='set_lang_ky'), InlineKeyboardButton("🇷🇺 Русский", callback_data='set_lang_ru')],
            [InlineKeyboardButton("🇺🇸 English", callback_data='set_lang_en'), InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data='set_lang_uz')],
            [InlineKeyboardButton("🇰🇿 Қазақша", callback_data='set_lang_kk'), InlineKeyboardButton("🇹🇯 Тоҷикӣ", callback_data='set_lang_tg')],
            [InlineKeyboardButton("🇹🇷 Türkçe", callback_data='set_lang_tr')]
        ])
        await update.message.reply_text("Выберите язык / Тилди тандаңыз / Choose language:", reply_markup=kb)
    except Exception as e:
        log.error(f"Error in start command: {e}")

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query; await query.answer(); data = query.data; lang = context.user_data.get('lang', 'ru')
    try:
        if data.startswith('set_lang_'):
            lang = data.split('_')[2]; context.user_data['lang'] = lang; L = STRINGS.get(lang, STRINGS['ru'])
            await query.message.edit_text(L["welcome"], reply_markup=get_main_keyboard(lang), parse_mode=ParseMode.HTML)
            if context.user_data.get('just_registered'):
                app_url = os.environ.get('RENDER_EXTERNAL_URL') or "https://mubvpn-bot-vy55.onrender.com"
                sub_link = f"{app_url}/s/{context.user_data['uid']}"
                await context.bot.send_message(chat_id=query.from_user.id, text=f"{L['trial_msg']}\n\n<code>{sub_link}</code>", parse_mode=ParseMode.HTML)
                context.user_data['just_registered'] = False
        elif data == 'pay_menu':
            L = STRINGS.get(lang, STRINGS['ru']); uid = context.user_data.get('uid')
            kb = [[InlineKeyboardButton(f"{STRINGS[lang]['plan_'+p]} — {PLANS[p]['rub']} RUB", callback_data=f"plan:{p}:{uid}")] for p in PLANS]
            await query.message.edit_text(L["pay_text"], reply_markup=InlineKeyboardMarkup(kb + [[InlineKeyboardButton(L["back"], callback_data='set_lang_'+lang)]]), parse_mode=ParseMode.HTML)
        elif data.startswith('plan:'):
            parts = data.split(':'); plan = PLANS.get(parts[1])
            pay_url, err = create_platega_invoice(parts[2], parts[1], plan['rub'])
            if pay_url: await query.message.edit_text(STRINGS[lang]["pay_info"].format(name=STRINGS[lang]["plan_"+parts[1]], rub=plan['rub']), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(STRINGS[lang]["pay_btn_link"], url=pay_url)], [InlineKeyboardButton(STRINGS[lang]["back"], callback_data='pay_menu')]]), parse_mode=ParseMode.HTML)
        elif data == 'my_vpn':
            uid = context.user_data.get('uid'); user = requests.get(f"{FIREBASE_DB_URL}/users/{uid}.json?auth={FIREBASE_DB_SECRET}", timeout=10).json()
            if user and user.get("isPremium"):
                app_url = os.environ.get('RENDER_EXTERNAL_URL') or "https://mubvpn-bot-vy55.onrender.com"
                sub_link = f"{app_url}/s/{uid}"
                await query.message.edit_text(STRINGS[lang]["my_vpn_text"].format(status="Active 💎", expiry=user.get("premium_expiry","").split('T')[0], vpn_link=sub_link), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🌐 Open", url=sub_link)], [InlineKeyboardButton(STRINGS[lang]["back"], callback_data='set_lang_'+lang)]]), parse_mode=ParseMode.HTML)
            else: await query.message.edit_text(STRINGS[lang]["no_premium"], reply_markup=get_main_keyboard(lang))
        elif data == 'referral_menu':
            uid = context.user_data.get('uid')
            bot_info = await context.bot.get_me()
            ref_link = f"https://t.me/{bot_info.username}?start=ref_{uid}"
            await query.message.edit_text(STRINGS[lang]["ref_menu_text"].format(ref_link=ref_link), reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(STRINGS[lang]["back"], callback_data='set_lang_'+lang)]]), parse_mode=ParseMode.HTML)
        elif data == 'dl_platforms':
            kb = [
                [InlineKeyboardButton("📱 Android (APK)", url="https://github.com/Ulanbekmahmaraimov/mubvpn-bot/releases/download/v1.0.10/app-release.apk")],
                [InlineKeyboardButton("🤖 Google Play", url="https://play.google.com/store/apps/details?id=com.happproxy"), InlineKeyboardButton("🍎 App Store", url="https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973")],
                [InlineKeyboardButton(STRINGS[lang]["back"], callback_data='set_lang_'+lang)]
            ]
            await query.message.edit_text("🚀 Download / Жүктөө / Скачать:", reply_markup=InlineKeyboardMarkup(kb))
    except Exception as e:
        log.error(f"Error in handle_callback: {e}")

class BotHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/webhook/platega':
            try:
                data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                if str(data.get("status")).upper() == "CONFIRMED":
                    uid, pid = data.get("payload", ":").split(':')
                    new_uid = firebase_set_premium(uid, PLANS.get(pid, {}).get("months", 1))
                    if new_uid: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": uid, "text": "💎 Premium Activated!", "parse_mode": "HTML"}, timeout=10)
                self.send_response(200); self.end_headers(); self.wfile.write(b"OK")
            except: self.send_response(400); self.end_headers()
    def do_GET(self):
        if self.path.startswith('/s/'):
            try:
                uid = self.path.split('/')[2].split('?')[0]; user = requests.get(f"{FIREBASE_DB_URL}/users/{uid}.json?auth={FIREBASE_DB_SECRET}", timeout=10).json()
                if not user or not user.get("isPremium"): self.send_response(403); self.end_headers(); return
                ua = self.headers.get('User-Agent', '').lower()
                is_vpn = any(x in ua for x in ['clash', 'v2ray', 'shadowrocket', 'happ', 'dart', 'okhttp'])
                if not is_vpn and 'mozilla' in ua:
                    sub = f"https://{self.headers.get('Host')}/s/{uid}"; qr = urllib.parse.quote(sub)
                    html = f"<html><body style='background:#000;color:white;font-family:sans-serif;text-align:center;padding:50px;'><h1>mubVPN Premium</h1><img src='https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={qr}'><br><br><code>{sub}</code><br><br><a href='v2rayng://install-config?url={sub}' style='display:block;padding:15px;background:#4facfe;color:black;text-decoration:none;border-radius:10px;font-weight:bold;'>Import to mubVPN</a></body></html>"
                    self.send_response(200); self.send_header('Content-Type', 'text/html'); self.end_headers(); self.wfile.write(html.encode()); return
                configs = []
                for srv in SERVERS:
                    uuid = srv.get("uuid", "2e922e6a-65db-4767-8216-a4b6b501b3b8")
                    pbk, sid, sni = srv.get("pbk", "0CIqFJJXUoImvhH9fBIBBsW0G798Q9WpwWDdhbdw93M"), srv.get("sid", "7682624ec01fe9"), srv.get("sni", "www.sony.com")
                    configs.append(f"vless://{uuid}@{srv['host']}:8443?encryption=none&flow=xtls-rprx-vision&type=tcp&security=reality&sni={sni}&fp=chrome&pbk={pbk}&sid={sid}#mubVPN_{srv['name']}")
                self.send_response(200); self.send_header('Content-Type', 'text/plain'); self.end_headers(); self.wfile.write(base64.b64encode("\n".join(configs).encode()).decode().encode())
            except: self.send_response(500); self.end_headers()
        else: self.send_response(200); self.end_headers(); self.wfile.write(b"Active")

def run_server(): HTTPServer(('0.0.0.0', int(os.environ.get('PORT', 8080))), BotHandler).serve_forever()

def keep_alive():
    app_url = os.environ.get('RENDER_EXTERNAL_URL')
    if not app_url:
        log.info("RENDER_EXTERNAL_URL not found, self-ping disabled.")
        return
    while True:
        try:
            requests.get(app_url, timeout=10)
            log.info("Self-ping successful.")
        except Exception as e:
            log.error(f"Self-ping failed: {e}")
        time.sleep(600) # Ар бир 10 мүнөттө

def main():
    threading.Thread(target=run_server, daemon=True).start()
    threading.Thread(target=keep_alive, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).request(HTTPXRequest(connect_timeout=20, read_timeout=20)).build()
    app.add_handler(CommandHandler("start", start)); app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()

if __name__ == "__main__": main()

