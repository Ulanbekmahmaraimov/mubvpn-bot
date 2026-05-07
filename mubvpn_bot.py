import logging
import os
import requests
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, InputMediaPhoto
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import html

# Логдорду жөндөө
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.StreamHandler(), logging.FileHandler('bot.log', encoding='utf-8')]
)
log = logging.getLogger(__name__)

# ─── ЖӨНДӨӨЛӨР ───
BOT_TOKEN    = "8400265569:AAHQ21_zNVS3XPDlMoE9I8TW0JwaIaUuA1s"
LAVA_API     = "O4xJ2dC5ZxrtZPREDAm1vcUxYKke2RF8QSspy4vZPk4VKx1pbZt9KLfWfvRgHTWm"
SUPPORT_URL  = "https://t.me/kl_mub"

# Азырынча баарына бирдей шилтеме. Lava.top'тон өзүнчө товарларды ачып, ушул жердеги шилтемелерди алмаштырасыз.
LAVA_URLS = {
    "1m": "https://app.lava.top/products/db3d18c8-01e5-40f2-bf0a-e01842697312/8a98aa1a-78d0-4291-bf1e-6c143668cf15",
    "3m": "https://app.lava.top/products/db3d18c8-01e5-40f2-bf0a-e01842697312/8a98aa1a-78d0-4291-bf1e-6c143668cf15",
    "6m": "https://app.lava.top/products/db3d18c8-01e5-40f2-bf0a-e01842697312/8a98aa1a-78d0-4291-bf1e-6c143668cf15",
    "1y": "https://app.lava.top/products/db3d18c8-01e5-40f2-bf0a-e01842697312/8a98aa1a-78d0-4291-bf1e-6c143668cf15",
}

# Пландар
PLANS = {
    "1m":  {"name": "1 ай",   "months": 1},
    "3m":  {"name": "3 ай",   "months": 3},
    "6m":  {"name": "6 ай",   "months": 6},
    "1y":  {"name": "1 жыл",  "months": 12},
}

# ─── FIREBASE REST API (service account JSON керек эмес!) ────────────────────
FIREBASE_API_KEY = "AIzaSyA0vh26XTvzO-BZ1bBuRUU_ZcKr5mC7nsk"
FIREBASE_DB_URL  = "https://mubvpn-8b892-default-rtdb.firebaseio.com"

# Сиздин Firebase аккаунтуңуздун маалыматы (Google менен эмес, Email/Password кирүүгө)
# ⚠️  Firebase Console → Authentication → Add provider → Email/Password АКТИВДЕШТИРИҢИЗ
# Анан төмөнкүдөй бот аккаунт жасаңыз:
FIREBASE_BOT_EMAIL    = "ulanmahmaraimov@gmail.com"  # ← бар аккаунттун emailи
FIREBASE_BOT_PASSWORD = ""  # ← Google аккаунт үчүн бош калтырыңыз

# Google аккаунту болсо, database secret колдонобуз
# Firebase Console → Project Settings → Service Accounts → Database secrets → Show
FIREBASE_DB_SECRET = "NgRNzmtQYdgUcFWXiDRPAHAsSURVni2WaIKTw9Re"

_id_token: str | None = None
_token_expiry = datetime.min


def _get_firebase_token() -> str | None:
    """Firebase токен алат — Database Secret же Email/Password аркылуу."""
    # 1. Database Secret бар болсо — аны колдонобуз (эң жөнөкөй)
    if FIREBASE_DB_SECRET:
        return FIREBASE_DB_SECRET  # Secret'ти auth= параметри катары колдонсо болот

    # 2. Email/Password аркылуу кирүү
    global _id_token, _token_expiry
    if _id_token and datetime.now() < _token_expiry:
        return _id_token
    if not FIREBASE_BOT_PASSWORD:
        log.warning("⚠️ Firebase Secret же Password жок — Firebase'ге жазылбайт")
        return None
    try:
        resp = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}",
            json={"email": FIREBASE_BOT_EMAIL, "password": FIREBASE_BOT_PASSWORD, "returnSecureToken": True},
            timeout=10
        )
        data = resp.json()
        if "idToken" in data:
            _id_token = data["idToken"]
            _token_expiry = datetime.now() + timedelta(minutes=55)
            log.info("✅ Firebase токен алынды")
            return _id_token
        else:
            log.error(f"Firebase токен катасы: {data.get('error', data)}")
            return None
    except Exception as e:
        log.error(f"Firebase кирүү катасы: {e}")
        return None


def firebase_set_premium(uid: str, months: int) -> bool:
    """Firebase REST API аркылуу Premium орнотуу."""
    token = _get_firebase_token()
    if not token:
        log.error("Firebase токен жок — Premium орнотулбады")
        return False
    try:
        expiry = (datetime.now() + timedelta(days=months * 30)).isoformat()
        url = f"{FIREBASE_DB_URL}/users/{uid}.json?auth={token}"
        resp = requests.patch(url, json={
            "premium_expiry": expiry,
            "is_paid": True,
        }, timeout=10)
        if resp.status_code == 200:
            log.info(f"✅ Premium орнотулду: uid={uid}, {months} ай")
            return True
        else:
            log.error(f"Firebase жазуу катасы: {resp.status_code} {resp.text}")
            return False
    except Exception as e:
        log.error(f"Firebase сактоо катасы: {e}")
        return False


def firebase_save_telegram(uid: str, telegram_id: int):
    """Колдонуучунун Telegram ID'ин Firebase'ге сактоо."""
    if not uid:
        return
    token = _get_firebase_token()
    if not token:
        return
    try:
        url = f"{FIREBASE_DB_URL}/users/{uid}.json?auth={token}"
        requests.patch(url, json={"telegram_id": telegram_id}, timeout=10)
    except Exception as e:
        log.error(f"Telegram ID сактоо катасы: {e}")


def lava_check_payment(uid: str) -> dict | None:
    """Lava.top'тан UID боюнча акыркы төлөнгөн инвойсту текшерет."""
    try:
        resp = requests.get(
            'https://gate.lava.top/api/v2/invoices',
            headers={'X-Api-Key': LAVA_API, 'Accept': 'application/json'},
            timeout=10
        )
        if resp.status_code == 200:
            for inv in resp.json().get('items', []):  # X-Api-Key менен 'items' келет
                info = inv.get('additionalFields', inv.get('additional_info', ''))
                info_str = str(info)
                
                # Биз additional_info'го "uid|plan_id" деп жөнөтөбүз (мисалы: "123456789|3m")
                if "|" in info_str:
                    inv_uid, inv_plan = info_str.split("|", 1)
                else:
                    inv_uid = info_str
                    inv_plan = "1m"
                    
                if inv_uid == uid and inv.get('status') in ('success', 'paid'):
                    # API аркылуу сумманы окуп, ошого жараша планды тактоо:
                    amount = float(inv.get('amount', 0))
                    
                    if amount >= 1000: 
                        inv_plan = "1y"
                    elif amount >= 600: 
                        inv_plan = "6m"
                    elif amount >= 350: 
                        inv_plan = "3m"
                    elif amount >= 150: 
                        inv_plan = "1m"
                    # Эгер amount 0 болсо (же окулбай калса), эски inv_plan кала берет.

                    return {"invoice": inv, "plan": inv_plan}
    except Exception as e:
        log.error(f'Lava текшерүү катасы: {e}')
    return None

# ЖАҢЫ СҮРӨТТӨР (Инструкция үчүн)
PHOTO_1 = "bot_images/step1.jpg"  # Валюта тандоо
PHOTO_2 = "bot_images/step2.jpg"  # План тандоо
PHOTO_3 = "bot_images/step3.jpg"  # Почтаны жазуу
PHOTO_4 = "bot_images/step4.jpg"  # Өтүүнү ырастоо
PHOTO_5 = "bot_images/step5.jpg"  # Төлөм формасы
PHOTO_6 = "bot_images/step6.jpg"  # Банк тиркемеси (Карта)

STRINGS = {
    "ky": {
        "welcome": "🛡 <b>mubVPN Premium</b>\n\nТөлөм жүргүзүү үчүн төмөнкү баскычтарды колдонуңуз:",
        "btn_pay": "💳 Сатып алуу",
        "btn_how": "📖 Төлөөнү үйрөнүү",
        "btn_support": "👨‍💻 Колдоо",
        "btn_share": "🤝 Достор менен бөлүшүү",
        "btn_1m": "1 Ай",
        "btn_3m": "3 Ай (Үнөмдөө)",
        "btn_6m": "6 Ай (Пайдалуу)",
        "btn_1y": "1 Жыл (-44% Супер баа)",
        "pay_text": "💳 <b>Төлөөгө өтүү</b>\n\nТөлөм Telegram ичинде коопсуз өтөт:",
        "pay_btn_link": "💳 Оплатить через Lava.top",
        "back": "⬅️ Артка",
        "next": "Кийинки ➡️",
        "how_step_1": "🚀 <b>Инструкция: mubVPN Premium кантип сатып алса болот</b>\n\n🌍 <b>1-КАДАМ: Валюта тандоо</b>\n\nТөлөм барагына өткөндө, биринчи кезекте валютаны <b>RUB</b> кылып тандаңыз. Бул сизге МИР карталары аркылуу ашыкча комиссиясыз төлөөгө мүмкүнчүлүк берет.",
        "how_step_2": "📅 <b>2-КАДАМ: План тандоо</b>\n\nЫлайыктуу жазылуу мөөнөтүн тандаңыз: 1, 3, 6 ай же 1 жыл. Эсиңизде болсун, бир жылдык жазылуу эң пайдалуу — 44% чейин үнөмдөйсүз!",
        "how_step_3": "📧 <b>3-КАДАМ: Email жазуу</b>\n\nӨзүңүздүн иштеп жаткан электрондук почтаңызды жазыңыз. Ага төлөм чеги келет жана система Premium'ду иштетүү үчүн сиздин төлөмүңүздү каттайт.",
        "how_step_4": "💳 <b>4-КАДАМ: Өтүүнү ырастоо</b>\n\nЖалпы сумманы текшерип, «Оплатить» баскычын басыңыз. Сиз корголгон төлөм барагына багытталасыз.",
        "how_step_5": "✅ <b>5-КАДАМ: Карта маалыматтарын толтуруу</b>\n\nТөлөм барагында кийинки кадамда даярдаган маалыматтарды киргизиңиз. Картанын номерин, жарактуулук мөөнөтүн жана CVC-кодун толтуруңуз.",
        "how_step_6": (
            "📱 <b>6-КАДАМ: Картанын маалыматын кайдан алса болот?</b>\n\n"
            "Эгерде жаныңызда карта жок болсо, маалыматтарды банк тиркемеңизден алыңыз (мисалы, Сбербанк же Т-Банк):\n\n"
            "<b>Маалыматтарды көрүү:</b> МИР картаңызды басып, «Показать реквизиты» тандаңыз. Сиз картанын номерин, мөөнөтүн жана жашыруун кодду көрөсүз.\n\n"
            "<b>Маалыматтарды көчүрүү:</b> Жөн гана 16 орундуу номерди жана мөөнөттү көчүрүп алып, 5-кадамдагы төлөм формасына чаптаңыз.\n\n"
            "✨ Бул кадамдарды аткаргандан кийин, сиздин Premium автоматтык түрдө иштетилет!\n\n"
            "Эгерде суроолоруңуз болсо, биз ар дайым байланыштабыз: @kl_mub"
        ),
        "menu_back": "Башкы меню:",
        "share_msg": "🛡 mubVPN - Эң тез жана коопсуз VPN! Premium'ду ушул жерден алсаң болот."
    },
    "ru": {
        "welcome": "🛡 <b>mubVPN Premium</b>\n\nВыберите действие:",
        "btn_pay": "💳 Купить",
        "btn_how": "📖 Как оплатить?",
        "btn_support": "👨‍💻 Поддержка",
        "btn_share": "🤝 Поделиться с друзьями",
        "btn_1m": "1 Месяц",
        "btn_3m": "3 Месяца (Экономия)",
        "btn_6m": "6 Месяцев (Выгодно)",
        "btn_1y": "1 Год (-44% Супер цена)",
        "pay_text": "💳 <b>Переход к оплате</b>\n\nОплата проходит внутри Telegram:",
        "pay_btn_link": "💳 Оплатить через Lava.top",
        "back": "⬅️ Назад",
        "next": "Далее ➡️",
        "how_step_1": "🚀 <b>Инструкция: Как купить MubVPN Premium</b>\n\n🌍 <b>ШАГ 1: Выбор валюты</b>\n\nПри переходе на страницу оплаты первым делом выберите валюту <b>RUB</b>. Это позволит вам оплачивать через карты МИР без лишних комиссий.",
        "how_step_2": "📅 <b>ШАГ 2: Выбор тарифа</b>\n\nВыберите подходящий период подписки: 1, 3, 6 месяцев или 1 год. Помните, что годовая подписка самая выгодная — экономия до 44%!",
        "how_step_3": "📧 <b>ШАГ 3: Ввод Email</b>\n\nВведите вашу рабочую электронную почту. На неё придёт чек об оплате, а система зафиксирует ваш платеж для активации Премиума.",
        "how_step_4": "💳 <b>ШАГ 4: Подтверждение перехода</b>\n\nПроверьте итоговую сумму и нажмите кнопку «Оплатить». Вас перенаправит на защищенную платежную страницу.",
        "how_step_5": "✅ <b>ШАГ 5: Заполнение данных карты</b>\n\nНа странице оплаты введите данные, которые вы подготовили на следующем шаге. Заполните номер карты, срок действия и CVC-код.",
        "how_step_6": (
            "📱 <b>ШАГ 6: Где взять данные карты?</b>\n\n"
            "Если у вас нет карты под рукой, возьмите данные из приложения вашего банка (например, Сбербанк или Т-Банк):\n\n"
            "<b>Посмотреть данные:</b> Нажмите на карту МИР и выберите «Показать реквизиты». Вы увидите номер карты, срок и секретный код.\n\n"
            "<b>Скопировать реквизиты:</b> Просто скопируйте 16-значный номер и срок действия, чтобы вставить их в форму оплаты из Шага 5.\n\n"
            "✨ После выполнения этих шагов ваш Премиум активируется автоматически!\n\n"
            "Если у вас возникли вопросы, мы всегда на связи: @kl_mub"
        ),
        "menu_back": "Главное меню:",
        "share_msg": "🛡 mubVPN - Самый быстрый и безопасный VPN! Premium можно купить здесь."
    },
    "en": {
        "welcome": "🛡 <b>mubVPN Premium</b>\n\nPlease choose an option:",
        "btn_pay": "💳 Buy",
        "btn_how": "📖 How to pay?",
        "btn_support": "👨‍💻 Support",
        "btn_share": "🤝 Share with friends",
        "btn_1m": "1 Month",
        "btn_3m": "3 Months (Save)",
        "btn_6m": "6 Months (Best Value)",
        "btn_1y": "1 Year (-44% Super Deal)",
        "pay_text": "💳 <b>Proceed to Payment</b>\n\nThe payment is secure within Telegram:",
        "pay_btn_link": "💳 Оплатить через Lava.top",
        "back": "⬅️ Back",
        "next": "Next ➡️",
        "how_step_1": "🚀 <b>Instruction: How to buy MubVPN Premium</b>\n\n🌍 <b>STEP 1: Choose currency</b>\n\nWhen you go to the payment page, first choose <b>RUB</b> currency. This allows you to pay with MIR cards without extra fees.",
        "how_step_2": "📅 <b>STEP 2: Choose a plan</b>\n\nChoose a suitable subscription period: 1, 3, 6 months or 1 year. Remember, an annual subscription is the most profitable - savings up to 44%!",
        "how_step_3": "📧 <b>STEP 3: Enter Email</b>\n\nEnter your working email. A receipt will be sent there, and the system will record your payment to activate Premium.",
        "how_step_4": "💳 <b>STEP 4: Confirm transition</b>\n\nCheck the total amount and click the «Pay» button. You will be redirected to a secure payment page.",
        "how_step_5": "✅ <b>STEP 5: Fill in card details</b>\n\nOn the payment page, enter the details you prepared in the next step. Fill in the card number, expiration date, and CVC code.",
        "how_step_6": (
            "📱 <b>STEP 6: Where to get card details?</b>\n\n"
            "If you don't have a physical card, get the details from your bank app (e.g. Sberbank or T-Bank):\n\n"
            "<b>View details:</b> Click on your MIR card and choose «Show details». You will see the card number, expiration date, and secret code.\n\n"
            "<b>Copy details:</b> Simply copy the 16-digit number and expiration date to paste them into the payment form from Step 5.\n\n"
            "✨ After completing these steps, your Premium will be activated automatically!\n\n"
            "If you have any questions, we are always in touch: @kl_mub"
        ),
        "menu_back": "Main Menu:",
        "share_msg": "🛡 mubVPN - The fastest and safest VPN! Get Premium here."
    }
}

def get_lang_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇰🇬 Кыргызча", callback_data='set_lang_ky')],
        [InlineKeyboardButton("🇷🇺 Русский", callback_data='set_lang_ru')],
        [InlineKeyboardButton("🇺🇸 English", callback_data='set_lang_en')]
    ])

def get_main_keyboard(lang):
    L = STRINGS[lang]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(L["btn_pay"], callback_data='pay_menu')],
        [InlineKeyboardButton(L["btn_how"], callback_data='how_1')],
        [InlineKeyboardButton(L["btn_share"], callback_data='share_app')],
        [InlineKeyboardButton(L["btn_support"], url=SUPPORT_URL)]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /start UID — тиркемеден жиберилген (Firebase UID)
    if context.args:
        uid = context.args[0]
        context.user_data['uid'] = uid
        firebase_save_telegram(uid, update.effective_user.id)
        log.info(f'▶️ /start uid={uid} tg={update.effective_user.id}')

    if update.message:
        await update.message.reply_text(
            "🌐 Choose language / Тилди тандаңыз / Выберите язык:",
            reply_markup=get_lang_keyboard()
        )
    else:
        await update.callback_query.message.edit_text(
            "🌐 Choose language / Тилди тандаңыз / Выберите язык:",
            reply_markup=get_lang_keyboard()
        )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    lang = context.user_data.get('lang', 'ru')

    async def send_how_step(photo_path, caption, keyboard):
        try:
            if query.message.photo:
                await query.message.edit_media(
                    media=InputMediaPhoto(open(photo_path, 'rb'), caption=caption, parse_mode=ParseMode.HTML), 
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await context.bot.send_photo(
                    chat_id=query.message.chat_id, 
                    photo=open(photo_path, 'rb'), 
                    caption=caption, 
                    reply_markup=InlineKeyboardMarkup(keyboard), 
                    parse_mode=ParseMode.HTML
                )
                await query.message.delete()
        except Exception as e:
            logging.error(f"Error sending photo {photo_path}: {e}")
            try:
                fallback_text = caption + "\n\n<i>(Сүрөт жеткиликсиз / Фото временно недоступно)</i>"
                if query.message.photo:
                    await query.message.delete()
                    await context.bot.send_message(
                        chat_id=query.message.chat_id, 
                        text=fallback_text, 
                        reply_markup=InlineKeyboardMarkup(keyboard), 
                        parse_mode=ParseMode.HTML
                    )
                else:
                    await query.message.edit_text(
                        text=fallback_text, 
                        reply_markup=InlineKeyboardMarkup(keyboard), 
                        parse_mode=ParseMode.HTML
                    )
            except Exception as inner_e:
                logging.error(f"Fallback error: {inner_e}")

    if data.startswith('set_lang_'):
        lang = data.split('_')[2]
        context.user_data['lang'] = lang
        await query.message.edit_text(STRINGS[lang]["welcome"], reply_markup=get_main_keyboard(lang), parse_mode=ParseMode.HTML)

    elif data == 'pay_menu':
        L = STRINGS[lang]
        keyboard = [
            [InlineKeyboardButton(L["btn_1m"], callback_data='pay_plan_1m')],
            [InlineKeyboardButton(L["btn_3m"], callback_data='pay_plan_3m')],
            [InlineKeyboardButton(L["btn_6m"], callback_data='pay_plan_6m')],
            [InlineKeyboardButton(L["btn_1y"], callback_data='pay_plan_1y')],
            [InlineKeyboardButton(L["back"], callback_data='main_menu')]
        ]
        title = "Канча убакытка аласыз? / Выберите период / Choose a plan:"
        await query.message.edit_text(title, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

    elif data.startswith('pay_plan_'):
        plan_id = data.split('_')[2]  # '1m', '3m', '6m', '1y'
        L = STRINGS[lang]
        uid = context.user_data.get('uid', str(query.from_user.id))
        
        # UID жана Планды бириктирип жөнөтөбүз: uid|plan_id (Бул Lava.top'тон текшерүү үчүн керек)
        additional_info = f"{uid}|{plan_id}"
        link = f"{LAVA_URLS[plan_id]}?additional_info={additional_info}"
        
        keyboard = [
            [InlineKeyboardButton(L["pay_btn_link"], web_app=WebAppInfo(url=link))],
            [InlineKeyboardButton("✅ Төлөдүм / Я оплатил", callback_data=f'check_pay')],
            [InlineKeyboardButton(L["back"], callback_data='pay_menu')]
        ]
        await query.message.edit_text(L["pay_text"], reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

    elif data == 'check_pay':
        uid = context.user_data.get('uid', str(query.from_user.id))
        await query.answer("⏳ Текшерилүүдө...")
        await query.message.edit_text("⏳ Төлөм текшерилүүдө...")

        result = lava_check_payment(uid)
        if result:
            plan_id = result.get('plan', '1m')
            months = PLANS.get(plan_id, {}).get('months', 1)
            plan_name = PLANS.get(plan_id, {}).get('name', '1 ай')
            
            ok = firebase_set_premium(uid, months)
            if ok:
                await query.message.edit_text(
                    f"🎉 <b>Premium {plan_name} мөөнөткө активдешти!</b>\n\n"
                    "✅ Тиркемени ачып, VPN'ге туташыңыз!",
                    parse_mode=ParseMode.HTML
                )
            else:
                await query.message.edit_text(
                    "⚠️ Төлөм табылды, бирок Firebase иштебей жатат.\n"
                    "@kl_mub менен байланышыңыз."
                )
        else:
            lang_curr = context.user_data.get('lang', 'ru')
            await query.message.edit_text(
                "⚠️ Төлөм табылган жок.\n\nТөлөп бүтсөңүз, 1-2 мүнөт күтүп кайра басыңыз.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Кайра текшерүү", callback_data='check_pay')],
                    [InlineKeyboardButton("⬅️ Артка", callback_data='main_menu')]
                ])
            )

    elif data == 'share_app':
        L = STRINGS[lang]
        bot_info = await context.bot.get_me()
        share_url = f"https://t.me/share/url?url=https://t.me/{bot_info.username}&text={html.escape(L['share_msg'])}"
        keyboard = [[InlineKeyboardButton("📲 Бөлүшүү / Поделиться", url=share_url)], [InlineKeyboardButton(L["back"], callback_data='main_menu')]]
        await query.message.edit_text(L["btn_share"], reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)



    elif data == 'how_1':
        L = STRINGS[lang]
        keyboard = [[InlineKeyboardButton(L["next"], callback_data='how_2')], [InlineKeyboardButton(L["back"], callback_data='main_menu')]]
        await send_how_step(PHOTO_1, L["how_step_1"], keyboard)


    elif data == 'how_2':
        L = STRINGS[lang]
        keyboard = [[InlineKeyboardButton(L["back"], callback_data='how_1')], [InlineKeyboardButton(L["next"], callback_data='how_3')]]
        await send_how_step(PHOTO_2, L["how_step_2"], keyboard)

    elif data == 'how_3':
        L = STRINGS[lang]
        keyboard = [[InlineKeyboardButton(L["back"], callback_data='how_2')], [InlineKeyboardButton(L["next"], callback_data='how_4')]]
        await send_how_step(PHOTO_3, L["how_step_3"], keyboard)

    elif data == 'how_4':
        L = STRINGS[lang]
        keyboard = [[InlineKeyboardButton(L["back"], callback_data='how_3')], [InlineKeyboardButton(L["next"], callback_data='how_5')]]
        await send_how_step(PHOTO_4, L["how_step_4"], keyboard)

    elif data == 'how_5':
        L = STRINGS[lang]
        keyboard = [[InlineKeyboardButton(L["back"], callback_data='how_4')], [InlineKeyboardButton(L["next"], callback_data='how_6')]]
        await send_how_step(PHOTO_5, L["how_step_5"], keyboard)

    elif data == 'how_6':
        L = STRINGS[lang]
        keyboard = [[InlineKeyboardButton(L["back"], callback_data='how_5')], [InlineKeyboardButton("🏠 Меню", callback_data='main_menu')]]
        await send_how_step(PHOTO_6, L["how_step_6"], keyboard)

    elif data == 'main_menu':
        L = STRINGS[lang]
        if query.message.photo:
            await query.message.delete()
        await context.bot.send_message(chat_id=query.message.chat_id, text=L["menu_back"], reply_markup=get_main_keyboard(lang), parse_mode=ParseMode.HTML)

def main():
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import os

    class DummyHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is running!")
        def do_HEAD(self):
            self.send_response(200)
            self.end_headers()

    def run_dummy_server():
        port = int(os.environ.get('PORT', 8080))
        server = HTTPServer(('0.0.0.0', port), DummyHandler)
        server.serve_forever()

    threading.Thread(target=run_dummy_server, daemon=True).start()

    # Self-ping to keep Render awake
    def keep_awake():
        import time
        import requests
        url = "https://mubvpn-bot.onrender.com"
        while True:
            try:
                requests.get(url)
            except:
                pass
            time.sleep(600) # Ping every 10 minutes

    threading.Thread(target=keep_awake, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.run_polling()

if __name__ == "__main__":
    main()