import logging
import os
import json
import requests
import threading
import time
import html
import asyncio
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

        resp_patch = requests.patch(url, json={"premium_expiry": expiry, "is_paid": True})

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
        "welcome": "🚀 <b>mubVPN — Эң тез жана коопсуз VPN!</b>\n\n🌍 Чектөөсүз интернетке жол ачыңыз.\n⚡️ Жогорку ылдамдык (1 Гбит/с чейин).\n🛡 Коопсуздук жана толук купуялык.\n\nТөмөндөгү менюдан керектүү бөлүмдү тандаңыз:",
        "btn_profile": "👤 Мой профиль / Счёт",
        "btn_my_vpn": "🔑 Моя ссылка (VLESS)",
        "btn_pay": "💳 Купить / Продлить",
        "btn_referral": "🎁 Бесплатный Premium (+10...)",
        "btn_servers": "📡 Статус серверов",
        "btn_download": "🚀 Скачать приложение",
        "btn_guide": "📖 Инструкция",
        "btn_promo": "🎟 Ввести промокод",
        "btn_support": "👨‍💻 Служба поддержки",
        "pay_text": "💳 <b>Планды тандаңыз:</b>\n\nБардык пландар чексиз трафик жана 100% VLESS-Reality коопсуздук камтыйт.",
        "back": "⬅️ Назад",
        "main_menu": "🏠 Башкы меню",
        "pay_btn_link": "💳 Төлөө (Lava / Telegram)",
        "check_btn": "✅ Төлөдүм (Текшерүү)",
        "checking": "⏳ Төлөм текшерилүүдө...",
        "success": "🎉 <b>Premium активдешти!</b>\n\nТиркемени ачып, VPN'ди колдоно бериңиз!",
        "not_found": "⚠️ Төлөм табылган жок. Төлөп бүтсөңүз, 1-2 мүнөт күтүп кайра басыңыз.",
        "ref_menu_text": "🎁 <b>Рефераалдык программа!</b>\n\nДосторуңузду чакырып, <b>бекер Premium</b> алыңыз!\n\n• Ар бир чакырылган дос үчүн: <b>+10 күн акысыз Premium</b>.\n• Максималдуу бекер мөөнөт: <b>365 күнгө чейин (1 жыл)</b>.\n\n🔗 <b>Сиздин шилтемеңиз:</b>\n<code>{ref_link}</code>\n\n👥 Чакырылган достор: <b>{referral_count}</b> адам\n📅 Алынган бекер күндөр: <b>{referral_days_granted}</b> күн"
    },
    "ru": {
        "welcome": "🚀 <b>mubVPN — Самый быстрый и безопасный VPN!</b>\n\n🌍 Откройте доступ к свободному интернету.\n⚡️ Высокая скорость (до 1 Гбит/с).\n🛡 Полная приватность и защита.\n\nВыберите нужный раздел из меню ниже:",
        "btn_profile": "👤 Мой профиль / Счёт",
        "btn_my_vpn": "🔑 Моя ссылка (VLESS)",
        "btn_pay": "💳 Купить / Продлить",
        "btn_referral": "🎁 Бесплатный Premium (+10...)",
        "btn_servers": "📡 Статус серверов",
        "btn_download": "🚀 Скачать приложение",
        "btn_guide": "📖 Инструкция",
        "btn_promo": "🎟 Ввести промокод",
        "btn_support": "👨‍💻 Служба поддержки",
        "pay_text": "💳 <b>Выберите тарифный план:</b>\n\nВсе тарифы включают безлимитный трафик и максимальную защиту VLESS-Reality.",
        "back": "⬅️ Назад",
        "main_menu": "🏠 Главное меню",
        "pay_btn_link": "💳 Оплатить (Lava / Telegram)",
        "check_btn": "✅ Я оплатил (Проверить)",
        "checking": "⏳ Проверка платежа...",
        "success": "🎉 <b>Premium активирован!</b>\n\nОткройте приложение и наслаждайтесь VPN!",
        "not_found": "⚠️ Платеж не найден. Если вы оплатили, подождите 1-2 минуты и нажмите снова.",
        "ref_menu_text": "🎁 <b>Реферальная программа!</b>\n\nПриглашайте друзей и получайте <b>бесплатный Premium</b>!\n\n• За каждого приглашенного друга: <b>+10 дней бесплатного Premium</b>.\n• Максимальный лимит: <b>до 365 дней (1 год)</b>.\n\n🔗 <b>Ваша ссылка:</b>\n<code>{ref_link}</code>\n\n👥 Приглашено друзей: <b>{referral_count}</b>\n📅 Получено дней: <b>{referral_days_granted}</b>",
        "how_step_2": "📧 <b>ADIM 2: E-posta girin</b>\n\nÖdeme sayfasında Email adresinizi girin. 📩",
        "how_step_3": "💵 <b>ADIM 3: Para birimi seçin</b>\n\n<b>RUB</b> veya <b>KGS</b> seçin. 💰",
        "how_step_4": "📱 <b>ADIM 4: Kart bilgileri</b>\n\nKart numaranızı ve CVC kodunuzu girin. 💳",
        "how_step_5": "✅ <b>ADIM 5: Ödemeyi tamamla</b>\n\n'Öde'ye tıklayın ve SMS kodunu girin. 🎉",
        "how_step_6": "🛠 <b>ADIM 6: Doğrulama</b>\n\nAktif değilse ботта 'Kontrol Et'e tıklayın. @kl_mub yardıma hazır! 👨‍💻",
        "menu_back": "Ana Menü:",
        "share_msg": "🚀 mubVPN — Android için en hızlı ve güvenli VPN!\n\n✅ Tüm engelleri aşar\n✅ Verileri güvenle şifreler\n✅ Tek dokunuşla bağlantı\n✅ Yüksek ve kararlı hız\n\nHemen indir! 👇",
        "share_title": "🤝 <b>Paylaş:</b>", "btn_share_now": "📲 Paylaş",
        "btn_referral": "🎁 Ücretsiz Premium (Referans)",
        "ref_menu_text": "🎁 <b>Referans Programı!</b>\n\nArkadaşlarınızı davet edin ve <b>ücretsiz Premium</b> kazanın!\n\n• Her davet edilen arkadaş için: <b>+10 gün ücretsiz Premium</b>.\n• Maksimum ücretsiz limit: <b>365 güne kadar (1 yıl)</b>.\n\n🔗 <b>Referans linkiniz:</b>\n<code>{ref_link}</code>\n\n👥 Davet edilen arkadaşlar: <b>{referral_count}</b> kişi\n📅 Kazanılan ücretsiz günler: <b>{referral_days_granted}</b> gün"
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
        "menu_back": "Main Menu:",
        "share_msg": "🚀 mubVPN — The fastest and safest VPN for Android!\n\n✅ Bypasses all blocks\n✅ Securely encrypts your data\n✅ One-tap connection\n✅ High and stable speed\n\nDownload now! 👇",
        "share_title": "🤝 <b>Share:</b>", "btn_share_now": "📲 Share",
        "btn_referral": "🎁 Free Premium (Referral)",
        "ref_menu_text": "🎁 <b>Referral Program!</b>\n\nInvite friends and get <b>free Premium</b>!\n\n• For each invited friend: <b>+10 days of free Premium</b>.\n• Maximum free limit: <b>up to 365 days (1 year)</b>.\n\n🔗 <b>Your referral link:</b>\n<code>{ref_link}</code>\n\n👥 Invited friends: <b>{referral_count}</b>\n📅 Free days granted: <b>{referral_days_granted}</b>"
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

    # Түз жүктөө шилтемесин колдонобуз, колдонуучуга оңой болушу үчүн
    apk_direct_url = "https://github.com/Ulanbekmahmaraimov/mubvpn-bot/releases/download/v1.0.5/mubvpn.apk"

    return InlineKeyboardMarkup([

        [InlineKeyboardButton(L["btn_download"], url=apk_direct_url)],

        [InlineKeyboardButton(L["btn_pay"], callback_data='pay_menu')], 

        [InlineKeyboardButton(L["btn_referral"], callback_data='referral_menu')], 

        [InlineKeyboardButton(L["btn_how"], callback_data='how_1')], 

        [InlineKeyboardButton(L["btn_share"], callback_data='share_app')], 

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

                        # Чакырган адамга кубанычтуу кабарлама жөнөтөбүз

                        msg = "🎁 Досуңуз чакырууну кабыл алды! Сизге **+10 күн акысыз Premium** берилди! 🎉"

                        await context.bot.send_message(chat_id=inviter_tg_id, text=msg, parse_mode=ParseMode.MARKDOWN)

                except Exception as ex:

                    log.error(f"Error sending referral notification: {ex}")

        else:

            # Бул тиркемеден келген Firebase UID

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

async def promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("🎟 <b>Промокод киргизиңиз / Введите промокод:</b>\n\nМисалы / Пример: <code>/promo MUB2026</code>", parse_mode=ParseMode.HTML)
        return

    code = context.args[0].upper().strip()
    valid_codes = {
        "MUB2026": 7,
        "PREMIUM2026": 14,
        "VIP2026": 30
    }

    if code not in valid_codes:
        await update.message.reply_text("❌ <b>Ката промокод! / Неверный промокод!</b>\n\nКодду туура жазып кайра аракет кылыңыз.", parse_mode=ParseMode.HTML)
        return

    days = valid_codes[code]
    uid = context.user_data.get('uid', str(tg_id))
    try:
        url_map = f"{FIREBASE_DB_URL}/telegram_to_uid/{tg_id}.json?auth={FIREBASE_DB_SECRET}"
        r = requests.get(url_map, timeout=5)
        if r.status_code == 200 and r.json():
            uid = r.json()
    except: pass

    # Promo check
    promo_check_url = f"{FIREBASE_DB_URL}/used_promos/{tg_id}_{code}.json?auth={FIREBASE_DB_SECRET}"
    try:
        resp_check = requests.get(promo_check_url, timeout=5)
        if resp_check.status_code == 200 and resp_check.json() is not None:
            await update.message.reply_text("⚠️ <b>Сиз бул промокодду мурда колдонгонсуз!</b>\n\nВы уже использовали этот промокод!", parse_mode=ParseMode.HTML)
            return
    except: pass

    user_url = f"{FIREBASE_DB_URL}/users/{uid}.json?auth={FIREBASE_DB_SECRET}"
    start_date = datetime.now()
    try:
        resp_u = requests.get(user_url, timeout=5)
        if resp_u.status_code == 200 and resp_u.json():
            cur_exp = resp_u.json().get("premium_expiry")
            if cur_exp:
                try:
                    exp_dt = datetime.fromisoformat(cur_exp)
                    if exp_dt > start_date:
                        start_date = exp_dt
                except: pass
    except: pass

    new_exp = (start_date + timedelta(days=days)).isoformat()
    try:
        requests.patch(user_url, json={"premium_expiry": new_exp, "is_paid": True})
        requests.put(promo_check_url, json={"timestamp": datetime.now().isoformat(), "days": days})
        await update.message.reply_text(f"🎉 <b>Промокод активдешти! / Промокод активирован!</b>\n\nСизге <b>+{days} күн</b> акысыз Premium берилди! ✨", parse_mode=ParseMode.HTML)
    except Exception as ex:
        log.error(f"Promo error: {ex}")
        await update.message.reply_text("⚠️ Ката пайда болду. Кайра аракет кылыңыз.", parse_mode=ParseMode.HTML)


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
        kb = [
            [InlineKeyboardButton(L["pay_btn_link"], web_app=WebAppInfo(url=link))],
            [InlineKeyboardButton(L["check_btn"], callback_data='check_payment')],
            [InlineKeyboardButton(L["back"], callback_data='main_menu')]
        ]
        await query.message.edit_text(L["pay_text"], reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif data == 'check_payment':
        L = STRINGS[lang]; uid = context.user_data.get('uid', query.from_user.id)
        await query.message.edit_text(L["checking"], parse_mode=ParseMode.HTML)

        # 3 секунд күтөбүз (эффект үчүн)
        await asyncio.sleep(3)

        # Firebase'ден текшерүү
        url = f"{FIREBASE_DB_URL}/users/{uid}.json?auth={FIREBASE_DB_SECRET}"
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200 and resp.json():
                user_data = resp.json()
                is_paid = user_data.get("is_paid", False)
                expiry = user_data.get("premium_expiry")

                if is_paid and expiry:
                    # Эгер төлөнгөн болсо - куттуктайбыз
                    await query.message.edit_text(L["success"], reply_markup=get_main_keyboard(lang), parse_mode=ParseMode.HTML)
                    return

            # Төлөнө элек болсо - эскертүү
            kb = [[InlineKeyboardButton(L["check_btn"], callback_data='check_payment')], [InlineKeyboardButton(L["back"], callback_data='main_menu')]]
            await query.message.edit_text(L["not_found"], reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
        except Exception as e:
            log.error(f"Error checking payment: {e}")
            await query.message.edit_text("⚠️ Error connecting to server.", reply_markup=get_main_keyboard(lang))



    elif data == 'my_vpn':
        L = STRINGS[lang]; uid = context.user_data.get('uid', query.from_user.id)
        app_url = os.environ.get('RENDER_EXTERNAL_URL', "https://mubvpn-bot-vy55.onrender.com")
        vless_link = f"vless://2e922e6a-65db-4767-8216-a4b6b501b3b8@167.235.22.54:443?encryption=none&flow=xtls-rprx-vision&type=tcp&headerType=none&security=reality&sni=www.sony.com&fp=chrome&pbk=0CIqFJJXUoImvhH9fBIBBsW0G798Q9WpwWDdhbdw93M&sid=7682624ec01fe9#mubVPN-{uid}"
        txt = (
            f"🔑 <b>Сиздин жеке VLESS туташуу шилтемеңиз:</b>\n\n"
            f"<code>{vless_link}</code>\n\n"
            f"🌐 <b>Подписка шилтемеси (Auto-Sync):</b>\n"
            f"<code>{app_url}/s/{uid}</code>\n\n"
            f"💡 <i>Бул шилтемени көчүрүп, Happ Proxy же v2rayNG тиркемесине салыңыз.</i>"
        )
        kb = [[InlineKeyboardButton(L["back"], callback_data='main_menu')]]
        await query.message.edit_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif data == 'profile':
        L = STRINGS[lang]; uid = context.user_data.get('uid', query.from_user.id)
        url = f"{FIREBASE_DB_URL}/users/{uid}.json?auth={FIREBASE_DB_SECRET}"
        user_data = {}
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200 and resp.json():
                user_data = resp.json()
        except: pass

        is_prem = user_data.get("is_paid", False)
        exp_str = user_data.get("premium_expiry")
        ref_count = user_data.get("referral_count", 0)

        now = datetime.now()
        days_left = 0
        formatted_date = "Жок / Нет"

        if exp_str:
            try:
                exp_dt = datetime.fromisoformat(exp_str)
                if exp_dt > now:
                    is_prem = True
                    days_left = (exp_dt - now).days + 1
                    formatted_date = exp_dt.strftime("%Y-%m-%d %H:%M")
                else:
                    is_prem = False
                    formatted_date = "Мөөнөтү бүткөн"
            except: pass

        status_icon = "🟢 ACTIVE PREMIUM" if is_prem else "🔴 МӨӨНӨТҮ БҮТТҮ"

        txt = (
            f"👤 <b>mubVPN Жеке Эсеп / Профиль:</b>\n\n"
            f"🔹 <b>Статус:</b> {status_icon}\n"
            f"📅 <b>Премиум мөөнөтү:</b> {formatted_date}\n"
            f"⏳ <b>Калган убакыт:</b> {days_left} күн\n"
            f"🎁 <b>Чакырылган достор:</b> {ref_count} адам\n"
            f"🆔 <b>ID:</b> <code>{uid}</code>\n\n"
            f"🔒 <b>Протокол:</b> VLESS-Reality (1 Gbps)"
        )
        kb = [
            [InlineKeyboardButton("💳 Планды узартуу", callback_data='pay_menu')],
            [InlineKeyboardButton("🔑 Менин шилтемем", callback_data='my_vpn')],
            [InlineKeyboardButton(L["back"], callback_data='main_menu')]
        ]
        await query.message.edit_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif data == 'servers_status':
        L = STRINGS[lang]
        servers_text = (
            "📡 <b>mubVPN Серверлеринин абалы (7 жигердүү сервер):</b>\n\n"
            "🇩🇪 <b>Германия (Frankfurt - Main)</b> — 🟢 Active (1 Gbps) · Ping ~18ms\n"
            "🇵🇱 <b>Польша (Варшава)</b> — 🟢 Active (1 Gbps) · Ping ~24ms\n"
            "🇳🇱 <b>Нидерланды (Амстердам)</b> — 🟢 Active (1 Gbps) · Torrent ✅ · Ping ~20ms\n"
            "🇱🇻 <b>Латвия (Рига)</b> — 🟢 Active (1 Gbps) · Ping ~28ms\n"
            "🇺🇸 <b>АКШ / США (Денвер)</b> — 🟢 Active (1 Gbps) · Ping ~45ms\n"
            "🇮🇹 <b>Италия (Милан)</b> — 🟢 Active (1 Gbps) · Ping ~30ms\n"
            "🇳🇴 <b>Норвегия (Осло)</b> — 🟢 Active (1 Gbps) · Ping ~35ms\n\n"
            "🔒 <b>Протоколдор:</b> VLESS-Reality (1 Gbps)\n"
            "♾ <b>Трафик:</b> Чексиз (Unlimited)\n\n"
            "💡 <i>Бардык серверлер mubVPN тиркемесинде автоматтуу түрдө жүктөлөт!</i>"
        )
        kb = [[InlineKeyboardButton(L["back"], callback_data='main_menu')]]
        await query.message.edit_text(servers_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif data == 'dl_platforms':
        L = STRINGS[lang]
        apk_direct_url = "https://github.com/Ulanbekmahmaraimov/mubvpn-bot/releases/download/v1.0.6/mubvpn.apk"
        dl_text = (
            "🚀 <b>mubVPN тиркемелерин жүктөп алыңыз:</b>\n\n"
            "📱 <b>mubVPN Android APK:</b> <a href='" + apk_direct_url + "'>mubVPN Direct Download</a>\n"
            "🤖 <b>Happ Proxy (Play Store):</b> <a href='https://play.google.com/store/apps/details?id=com.happproxy'>Happ Proxy App</a>\n"
            "🍎 <b>Happ Proxy (iOS / App Store):</b> <a href='https://apps.apple.com/ru/app/happ-proxy-utility-plus/id6746188973'>Happ Proxy iOS</a>\n"
            "💻 <b>Windows / PC Client:</b> <a href='https://github.com/2dust/v2rayN/releases'>v2rayN Client</a>"
        )
        kb = [[InlineKeyboardButton(L["back"], callback_data='main_menu')]]
        await query.message.edit_text(dl_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif data == 'guide':
        L = STRINGS[lang]
        guide_text = (
            "📖 <b>mubVPN туташуу нускамасы (3 жөнөкөй кадам):</b>\n\n"
            "1️⃣ **mubVPN** же **Happ Proxy** колдонмосун телефонуңузга жүктөп алыңыз.\n"
            "2️⃣ Боттон <b>'🔑 Менин шилтемем'</b> кнопкасын басып, VLESS шилтемени көчүрүп алыңыз.\n"
            "3️⃣ Колдонмону ачып, **+** баскычын басып **Import from Clipboard** тандаңыз.\n\n"
            "🎉 Даяр! Эми туташуу баскычын басып, чексиз интернеттен ырахат алыңыз!"
        )
        kb = [[InlineKeyboardButton(L["back"], callback_data='main_menu')]]
        await query.message.edit_text(guide_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif data == 'promo_info':
        L = STRINGS[lang]
        promo_text = "🎟 <b>Промокодуңузду жазыңыз:</b>\n\nМисалы: <code>/promo MUB2026</code> буйругун жазып жөнөтүңүз."
        kb = [[InlineKeyboardButton(L["back"], callback_data='main_menu')]]
        await query.message.edit_text(promo_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

    elif data == 'share_app':

        L = STRINGS[lang]

        # Боттун шилтемесин эмес, Render сайтынын шилтемесин бөлүшөбүз (ал сүрөтү менен чыгат)

        share_url = f"https://t.me/share/url?url=https://mubvpn-bot.onrender.com/?lang={lang}&text={html.escape(L.get('share_msg', 'mubVPN'))}"

        kb = [[InlineKeyboardButton(L.get("btn_share_now", "📲 Бөлүшүү"), url=share_url)], [InlineKeyboardButton(L["back"], callback_data='main_menu')]]

        await query.message.edit_text(L.get("share_title", "🤝 Бөлүшүү"), reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)



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



    elif data == 'referral_menu':

        L = STRINGS[lang]; uid = context.user_data.get('uid', query.from_user.id)

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

        text = L["ref_menu_text"].format(ref_link=ref_link, referral_count=referral_count, referral_days_granted=referral_days_granted)

        kb = [[InlineKeyboardButton(L["back"], callback_data='main_menu')]]

        if query.message.photo: await query.message.delete()

        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)



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

            apk_url = 'https://github.com/Ulanbekmahmaraimov/mubvpn-bot/releases/download/v1.0.6/mubvpn.apk'

            self.send_response(302)

            self.send_header('Location', apk_url)

            self.end_headers()

            return

            

        # --- АВТО ТИЛ ТААНУУ (Browser Language Detection) ---
        query_params = urllib.parse.parse_qs(parsed_path.query)
        lang = query_params.get('lang', [None])[0]

        if not lang:
            accept_lang = self.headers.get('Accept-Language', '')
            if 'ru' in accept_lang: lang = 'ru'
            elif 'uz' in accept_lang: lang = 'uz'
            elif 'tg' in accept_lang: lang = 'tg'
            elif 'kk' in accept_lang: lang = 'kk'
            elif 'tr' in accept_lang: lang = 'tr'
            elif 'en' in accept_lang: lang = 'en'
            else: lang = 'ky'

        

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

                    # 1. Биринчи кезекте plan_id аркылуу айды аныктоого аракет кылабыз (эгер Telegram боттон төлөнсө)
                    months = None
                    additional = data.get('additionalFields')
                    if isinstance(additional, dict):
                        plan_id = additional.get('plan')
                        if plan_id == '1y': months = 12
                        elif plan_id == '6m': months = 6
                        elif plan_id == '3m': months = 3
                        elif plan_id == '1m': months = 1

                    # 2. Эгер план аныкталбаса, анда валютага жана суммага карап аныктайбыз (тиркемеден төлөнсө)
                    if months is None:
                        currency = data.get('currency', 'RUB')
                        if isinstance(currency, str):
                            currency = currency.upper()
                            
                        months = 1
                        if currency == 'USD':
                            if amount >= 30: months = 12
                            elif amount >= 18: months = 6
                            elif amount >= 10: months = 3
                        elif currency == 'KGS':
                            if amount >= 2500: months = 12
                            elif amount >= 1500: months = 6
                            elif amount >= 800: months = 3
                        else: # RUB жана башка валюталар
                            if amount >= 3000: months = 12
                            elif amount >= 1800: months = 6
                            elif amount >= 1000: months = 3

                    

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

    # Туташуу убактысын (Timeout) узартабыз
    from telegram.request import HTTPXRequest
    request = HTTPXRequest(connect_timeout=20, read_timeout=20)

    app = Application.builder().token(BOT_TOKEN).request(request).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("promo", promo))
    app.add_handler(CommandHandler("code", promo))

    app.add_handler(CallbackQueryHandler(handle_callback))

    log.info("🤖 Bot is running...")

    app.run_polling(drop_pending_updates=True)



if __name__ == "__main__":
    main()
