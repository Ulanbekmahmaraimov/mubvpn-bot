import os

def rebuild_strings():
    new_strings = """STRINGS = {
    "ky": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\\n\\nЭң тез жана коопсуз интернетке жол ачыңыз. Төлөм жүргүзүү же тиркемени жүктөө үчүн төмөнкү баскычтарды колдонуңуз:",
        "btn_pay": "💳 Сатып алуу", "btn_how": "📖 Кантип төлөйм?",
        "btn_download": "🚀 Тиркемени жүктөө",
        "btn_support": "👨‍💻 Колдоо", "btn_share": "🤝 Бөлүшүү",
        "pay_text": "💳 <b>Төлөөгө өтүү</b>\\n\\nТөлөм Telegram ичинде коопсуз өтөт:",
        "pay_btn_link": "💳 Telegram", "back": "⬅️ Артка", "next": "Кийинки ➡️",
        "check_btn": "✅ Төлөдүм (Текшерүү)",
        "checking": "⏳ Төлөм текшерилүүдө...",
        "success": "🎉 <b>Premium активдешти!</b>\\n\\nТиркемени ачып, VPN'ди колдоно бериңиз!",
        "not_found": "⚠️ Төлөм табылган жок. Төлөп бүтсөңүз, 1-2 мүнөт күтүп кайра басыңыз.",
        "how_step_1": "🚀 <b>1-КАДАМ: План тандоо</b>\\n\\n'Сатып алуу' баскычын басып, мөөнөттү тандаңыз. 1 жылдык план эң пайдалуу! ✅",
        "how_step_2": "📧 <b>2-КАДАМ: Почтаны жазуу</b>\\n\\nТөлөм барагында Email-ди жазыңыз. 📩",
        "how_step_3": "💵 <b>3-КАДАМ: Валюта тандоо</b>\\n\\nКомиссия аз болушу үчүн <b>RUB</b> же <b>KGS</b> тандаңыз. 💰",
        "how_step_4": "📱 <b>4-КАДАМ: Карта маалыматы</b>\\n\\nКарта номерин жана CVC-кодун жазыңыз. 💳",
        "how_step_5": "✅ <b>5-КАДАМ: Төлөмдү бүтүрүү</b>\\n\\n'Оплатить' баскычын басып, SMS кодду киргизиңиз. 🎉",
        "how_step_6": "🛠 <b>6-КАДАМ: Текшерүү</b>\\n\\nЭгер Premium иштебесе, боттогу 'Текшерүү' баскычын басыңыз. @kl_mub дайыма жардамга даяр! 👨‍💻",
        "menu_back": "Башкы меню:", "share_msg": "🚀 mubVPN — Android үчүн эң тез жана коопсуз VPN!\\n\\n✅ Блоктоолорду айланып өтөт\\n✅ Маалыматтарды коргойт\\n✅ Чектөөсүз интернет\\n\\nАзыр жүктөп ал! 👇",
        "share_title": "🤝 <b>Бөлүшүү:</b>", "btn_share_now": "📲 Бөлүшүү"
    },
    "ru": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\\n\\nОткройте доступ к самому быстрому и безопасному интернету. Используйте кнопки ниже для оплаты или загрузки приложения:",
        "btn_pay": "💳 Купить", "btn_how": "📖 Как оплатить?",
        "btn_download": "🚀 Скачать приложение",
        "btn_support": "👨‍💻 Поддержка", "btn_share": "🤝 Поделиться",
        "pay_text": "💳 <b>Переход к оплате</b>\\n\\nОплата проходит безопасно внутри Telegram:",
        "pay_btn_link": "💳 Telegram", "back": "⬅️ Назад", "next": "Далее ➡️",
        "check_btn": "✅ Я оплатил (Проверять)",
        "checking": "⏳ Проверка платежа...",
        "success": "🎉 <b>Premium активирован!</b>\\n\\nОткройте приложение и наслаждайтесь VPN!",
        "not_found": "⚠️ Платеж не найден. Если вы оплатили, подождите 1-2 минуты и нажмите снова.",
        "how_step_1": "🚀 <b>ШАГ 1: Выбор тарифа</b>\\n\\nНажмите 'Купить' и выберите период. Годовой план самый выгодный! ✅",
        "how_step_2": "📧 <b>ШАГ 2: Ввод почты</b>\\n\\nУкажите Email для получения чека. 📩",
        "how_step_3": "💵 <b>ШАГ 3: Выбор валюты</b>\\n\\nВыбирайте <b>RUB</b> или <b>KGS</b> для минимальной комиссии. 💰",
        "how_step_4": "📱 <b>ШАГ 4: Данные карты</b>\\n\\nВведите номер карты и CVC-код. 💳",
        "how_step_5": "✅ <b>ШАГ 5: Завершение</b>\\n\\nНажмите 'Оплатить' и введите код из СМС. 🎉",
        "how_step_6": "🛠 <b>ШАГ 6: Проверка</b>\\n\\nЕсли Premium не активен, нажмите 'Проверить' в боте. @kl_mub на связи! 👨‍💻",
        "menu_back": "Главное меню:", "share_msg": "🚀 mubVPN — Самый быстрый и безопасный VPN для Android!\\n\\n✅ Обходит любые блокировки\\n✅ Надежно защищает данные\\n✅ Интернет без границ\\n\\nСкачай сейчас! 👇",
        "share_title": "🤝 <b>Поделиться:</b>", "btn_share_now": "📲 Поделиться"
    },
    "uz": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\\n\\nEng tezkor va xavfsiz internetga ega bo'ling. To'lov qilish yoki ilovani yuklab olish uchun quyidagi tugmalardan foydalaning:",
        "btn_pay": "💳 Sotib olish", "btn_how": "📖 Qanday to'lash kerak?",
        "btn_download": "🚀 Ilovani yuklab olish",
        "btn_support": "👨‍💻 Qo'llab-quvvatlash", "btn_share": "🤝 Ulashish",
        "pay_text": "💳 <b>To'lovga o'tish</b>\\n\\nTo'lov Telegram ichida xavfsiz amalga oshiriladi:",
        "pay_btn_link": "💳 Telegram", "back": "⬅️ Orqaga", "next": "Keyingi ➡️",
        "check_btn": "✅ To'ladim (Tekshirish)",
        "checking": "⏳ To'lov tekshirilmoqda...",
        "success": "🎉 <b>Premium faollashdi!</b>\\n\\nIlovani oching va VPN-dan foydalaning!",
        "not_found": "⚠️ To'lov topilmadi. Agar to'lagan bo'lsangiz, 1-2 daqiqa kutib qayta bosing.",
        "how_step_1": "🚀 <b>1-QADAM: Tarifni tanlash</b>\\n\\n'Sotib olish' tugmasini bosing va muddatni tanlang. 1 yillik plan eng foydali! ✅",
        "how_step_2": "📧 <b>2-QADAM: Pochta kiritish</b>\\n\\nTo'lov sahifasida Email-ingizni yozing. 📩",
        "how_step_3": "💵 <b>3-QADAM: Valyuta tanlash</b>\\n\\nKomissiya kam bo'lishi uchun <b>RUB</b> yoki <b>KGS</b> tanlang. 💰",
        "how_step_4": "📱 <b>4-QADAM: Karta ma'lumotlari</b>\\n\\nKarta raqami va CVC-kodni yozing. 💳",
        "how_step_5": "✅ <b>5-QADAM: Yakunlash</b>\\n\\n'To'lash' tugmasini bosing va SMS kodni kiriting. 🎉",
        "how_step_6": "🛠 <b>6-QADAM: Tekshirish</b>\\n\\nAgar Premium ishlamasa, ботdagi 'Tekshirish' tugmasini bosing. @kl_mub yordamga tayyor! 👨‍💻",
        "menu_back": "Asosiy menyu:", "share_msg": "🚀 mubVPN — Android uchun eng tezkor va xavfsiz VPN!\\n\\n✅ Blokirovkalarni aylanib o'tadi\\n✅ Ma'lumotlarni himoya qiladi\\n✅ Cheksiz internet\\n\\nHozir yuklab ol! 👇",
        "share_title": "🤝 <b>Ulashish:</b>", "btn_share_now": "📲 Ulashish"
    },
    "tg": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\\n\\nБа интернети зудтарин ва бехатар дастрасӣ пайдо кунед. Барои пардохт ё боргирии барнома аз тугмаҳои зерин истифода баред:",
        "btn_pay": "💳 Харидан", "btn_how": "📖 Чӣ тавр бояд пардохт кард?",
        "btn_download": "🚀 Боргирии барнома",
        "btn_support": "👨‍💻 Дастгирӣ", "btn_share": "🤝 Ирсол",
        "pay_text": "💳 <b>Гузаштан ба пардохт</b>\\n\\nПардохт дар дохили Telegram бехатар мегузарад:",
        "pay_btn_link": "💳 Telegram", "back": "⬅️ Ба ақиб", "next": "Оянда ➡️",
        "check_btn": "✅ Ман пардохт кардам (Санҷиш)",
        "checking": "⏳ Санҷиши пардохт...",
        "success": "🎉 <b>Premium фаъол шуд!</b>\\n\\nБарномаро кушоед ва аз VPN лаззат баред!",
        "not_found": "⚠️ Пардохт ёфт нашуд. Агар пардохт карда бошед, 1-2 дақиқа интизор шавед.",
        "how_step_1": "🚀 <b>ҚАДАМИ 1: Интихоби тариф</b>\\n\\n'Харидан'-ро пахш кунед. Нақшаи солона беҳтарин аст! ✅",
        "how_step_2": "📧 <b>ҚАДАМИ 2: Ворид кардани почта</b>\\n\\nEmail-и худро ворид кунед. 📩",
        "how_step_3": "💵 <b>ҚАДАМИ 3: Интихоби асъор</b>\\n\\n<b>RUB</b> ё <b>KGS</b>-ро интихоб кунед. 💰",
        "how_step_4": "📱 <b>ҚАДАМИ 4: Маълумоти корт</b>\\n\\nРақами корт ва рамзи CVC-ро ворид кунед. 💳",
        "how_step_5": "✅ <b>ҚАДАМИ 5: Анҷоми пардохт</b>\\n\\n'Пардохт кардан'-ро пахш кунед ва рамзи СМС-ро ворид кунед. 🎉",
        "how_step_6": "🛠 <b>ҚАДАМИ 6: Санҷиш</b>\\n\\nАгар Premium фаъол нашуда бошад, тугмаи 'Санҷиш'-ро пахш кунед. @kl_mub ҳамеша тайёр аст! 👨‍💻",
        "menu_back": "Менюи асосӣ:", "share_msg": "🚀 mubVPN — VPN-и зудтарин ва бехатар барои Android!\\n\\n✅ Маҳдудиятҳоро давр мезанад\\n✅ Маълумотро ҳифз мекунад\\n✅ Интернети бемаҳдуд\\n\\nHоло боргирӣ кун! 👇",
        "share_title": "🤝 <b>Ирсол:</b>", "btn_share_now": "📲 Ирсол"
    },
    "kk": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\\n\\nЕң жылдам және қауіпсіз интернетке жол ашыңыз. Төлөм жасау немесе қосымшаны жүктеу үчүн төмендегі батырмаларды қолданыңыз:",
        "btn_pay": "💳 Сатып алу", "btn_how": "📖 Қалай төлеу керек?",
        "btn_download": "🚀 Қосымшаны жүктеу",
        "btn_support": "👨‍💻 Қолдау", "btn_share": "🤝 Бөлісу",
        "pay_text": "💳 <b>Төлемге өту</b>\\n\\nТөлем Telegram ішінде қауіпсіз өтеді:",
        "pay_btn_link": "💳 Telegram", "back": "⬅️ Артқа", "next": "Келесі ➡️",
        "check_btn": "✅ Төледім (Тексеру)",
        "checking": "⏳ Төлем тексерілуде...",
        "success": "🎉 <b>Premium белсендірілді!</b>\\n\\nҚосымшаны ашып, VPN-ді қолдана беріңіз!",
        "not_found": "⚠️ Төлем табылмады. Егер төлеген болсаңыз, 1-2 минут күтіңіз.",
        "how_step_1": "🚀 <b>1-ҚАДАМ: Тариф таңдау</b>\\n\\n'Сатып алу' батырмасын басыңыз. 1 жылдық жоспар ең тиімді! ✅",
        "how_step_2": "📧 <b>2-ҚАДАМ: Поштаны енгізу</b>\\n\\nEmail-іңізді жазыңыз. 📩",
        "how_step_3": "💵 <b>3-ҚАДАМ: Валютаны таңдау</b>\\n\\nКомиссия аз болуы үчүн <b>RUB</b> немесе <b>KGS</b> таңдаңыз. 💰",
        "how_step_4": "📱 <b>4-ҚАДАМ: Карта мәліметтері</b>\\n\\nКарта нөмірін жана CVC-кодты енгізіңіз. 💳",
        "how_step_5": "✅ <b>5-ҚАДАМ: Аяқтау</b>\\n\\n'Төлеу' батырмасын басып, СМС кодты енгізіңіз. 🎉",
        "how_step_6": "🛠 <b>6-ҚАДАМ: Тексеру</b>\\n\\nЕгер жұмыс істемесе, боттағы 'Тексеру' батырмасын басыңыз. @kl_mub көмектеседі! 👨‍💻",
        "menu_back": "Басты мәзір:", "share_msg": "🚀 mubVPN — Android үшін ең жылдам және қауіпсіз VPN!\\n\\n✅ Блоктауларды айналып өтеді\\n✅ Деректерді қорғайды\\n✅ Шектеусіз интернет\\n\\nҚазір жүктеп ал! 👇",
        "share_title": "🤝 <b>Бөлісу:</b>", "btn_share_now": "📲 Бөлісу"
    },
    "tr": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\\n\\nEn hızlı ve en güvenli internetin keyfini çıkarın. Ödeme yapmak veya uygulamayı indirmek için aşağıdaki butonları kullanın:",
        "btn_pay": "💳 Satın Al", "btn_how": "📖 Nasıl ödenir?",
        "btn_download": "🚀 Uygulamayı İndir",
        "btn_support": "👨‍💻 Destek", "btn_share": "🤝 Paylaş",
        "pay_text": "💳 <b>Ödemeye Geç</b>\\n\\nÖdeme Telegram içinde güvenli bir şekilde yapılır:",
        "pay_btn_link": "💳 Telegram", "back": "⬅️ Geri", "next": "İleri ➡️",
        "check_btn": "✅ Ödedim (Kontrol Et)",
        "checking": "⏳ Ödeme kontrol ediliyor...",
        "success": "🎉 <b>Premium Aktif Edildi!</b>\\n\\nUygulamayı açın ve VPN'in tadını çıkarın!",
        "not_found": "⚠️ Ödeme bulunamadı. Ödeme yaptıysanız 1-2 dakika bekleyin.",
        "how_step_1": "🚀 <b>ADIM 1: Plan seçimi</b>\\n\\n'Satın Al'а tıklayın. Yıllık plan en karlı olanıdır! ✅",
        "how_step_2": "📧 <b>ADIM 2: E-posta girin</b>\\n\\nÖdeme sayfasında Email adresinizi girin. 📩",
        "how_step_3": "💵 <b>ADIM 3: Para birimi seçin</b>\\n\\n<b>RUB</b> veya <b>KGS</b> seçin. 💰",
        "how_step_4": "📱 <b>ADIM 4: Kart bilgileri</b>\\n\\nKart numaranızı ve CVC kodunuzu girin. 💳",
        "how_step_5": "✅ <b>ADIM 5: Ödemeyi tamamla</b>\\n\\n'Öde'ye tıklayın ve SMS kodunu girin. 🎉",
        "how_step_6": "🛠 <b>ADIM 6: Doğrulama</b>\\n\\nAktif değilse ботта 'Kontrol Et'e tıklayın. @kl_mub yardıma hazır! 👨‍💻",
        "menu_back": "Ana Menü:", "share_msg": "🚀 mubVPN — Android үчүн en hızlı ve güvenli VPN!\\n\\n✅ Tüm engelleri aşar\\n✅ Verileri korur\\n✅ Sınırsız İnternet\\n\\nHemen indir! 👇",
        "share_title": "🤝 <b>Paylaş:</b>", "btn_share_now": "📲 Paylaş"
    },
    "en": {
        "welcome": "💎 <b>mubVPN Premium Core</b>\\n\\nUnlock the fastest and most secure internet access. Use the buttons below to pay or download the application:",
        "btn_pay": "💳 Buy", "btn_how": "📖 How to pay?",
        "btn_download": "🚀 Download App",
        "btn_support": "👨‍💻 Support", "btn_share": "🤝 Share",
        "pay_text": "💳 <b>Proceed to Payment</b>\\n\\nThe payment is secure within Telegram:",
        "pay_btn_link": "💳 Telegram", "back": "⬅️ Back", "next": "Next ➡️",
        "check_btn": "✅ I have paid (Check)",
        "checking": "⏳ Checking payment...",
        "success": "🎉 <b>Premium activated!</b>\\n\\nOpen the app and enjoy your VPN!",
        "not_found": "⚠️ Payment not found. If you have paid, wait 1-2 minutes.",
        "how_step_1": "🚀 <b>STEP 1: Choose plan</b>\\n\\nClick 'Buy'. Yearly plan is the best value! ✅",
        "how_step_2": "📧 <b>STEP 2: Enter Email</b>\\n\\nEnter your Email on the payment page. 📩",
        "how_step_3": "💵 <b>STEP 3: Choose currency</b>\\n\\nChoose <b>RUB</b> or <b>KGS</b> for minimum commission. 💰",
        "how_step_4": "📱 <b>STEP 4: Card details</b>\\n\\nEnter card number and CVC code. 💳",
        "how_step_5": "✅ <b>STEP 5: Complete</b>\\n\\nClick 'Pay' and enter the SMS code. 🎉",
        "how_step_6": "🛠 <b>STEP 6: Verification</b>\\n\\nCheck the app. If not active, click 'Check' in the bot. @kl_mub is here to help! 👨‍💻",
        "menu_back": "Main Menu:", "share_msg": "🚀 mubVPN — The fastest and safest VPN for Android!\\n\\n✅ Bypasses all blocks\\n✅ Protects your data\\n✅ Unlimited Internet\\n\\nDownload now! 👇",
        "share_title": "🤝 <b>Share:</b>", "btn_share_now": "📲 Share"
    }
}"""

    with open('mubvpn_bot.py', 'rb') as f:
        content = f.read().decode('utf-8', errors='ignore')
    
    # Find start and end of STRINGS block
    start_marker = 'STRINGS = {'
    end_marker = '# --- КЛАВИАТУРАЛАР ---'
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx != -1 and end_idx != -1:
        new_content = content[:start_idx] + new_strings + "\n\n" + content[end_idx:]
        with open('mubvpn_bot.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✅ Rebuilt STRINGS dictionary successfully")
    else:
        print(f"❌ Could not find markers. Start: {start_idx}, End: {end_idx}")

if __name__ == "__main__":
    rebuild_strings()
