import re

def update_strings():
    with open('mubvpn_bot.py', 'rb') as f:
        content = f.read().decode('utf-8', errors='ignore')
    
    # Define new share messages for each language
    replacements = {
        '"ky": {': '🚀 mubVPN — Android үчүн эң тез жана коопсуз VPN!\n\n✅ Блоктоолорду айланып өтөт\n✅ Маалыматтарды коргойт\n✅ Чектөөсүз интернет\n\nАзыр жүктөп ал! 👇',
        '"ru": {': '🚀 mubVPN — Самый быстрый и безопасный VPN для Android!\n\n✅ Обходит любые блокировки\n✅ Надежно защищает данные\n✅ Интернет без границ\n\nСкачай сейчас! 👇',
        '"uz": {': '🚀 mubVPN — Android uchun eng tezkor va xavfsiz VPN!\n\n✅ Blokirovkalarni aylanib o\'tadi\n✅ Ma\'lumotlarni himoya qiladi\n✅ Cheksiz internet\n\nHozir yuklab ol! 👇',
        '"tg": {': '🚀 mubVPN — VPN-и зудтарин ва бехатар барои Android!\n\n✅ Маҳдудиятҳоро давр мезанад\n✅ Маълумотро ҳифз мекунад\n✅ Интернети бемаҳдуд\n\nHоло боргирӣ кун! 👇',
        '"kk": {': '🚀 mubVPN — Android үшін ең жылдам және қауіпсіз VPN!\n\n✅ Блоктауларды айналып өтеді\n✅ Деректерді қорғайды\n✅ Шектеусіз интернет\n\nҚазір жүктеп ал! 👇',
        '"tr": {': '🚀 mubVPN — Android için en hızlı ve güvenli VPN!\n\n✅ Tüm engelleri aşar\n✅ Verileri korur\n✅ Sınırsız İnternet\n\nHemen indir! 👇',
        '"en": {': '🚀 mubVPN — The fastest and safest VPN for Android!\n\n✅ Bypasses all blocks\n✅ Protects your data\n✅ Unlimited Internet\n\nDownload now! 👇'
    }

    for lang_key, new_msg in replacements.items():
        # This regex looks for share_msg within the language block
        pattern = rf'({re.escape(lang_key)}.*?share_msg":\s*")(.*?)(")'
        content = re.sub(pattern, rf'\1{new_msg}\3', content, flags=re.DOTALL)

    with open('mubvpn_bot.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Successfully updated share messages in all languages")

if __name__ == "__main__":
    update_strings()
