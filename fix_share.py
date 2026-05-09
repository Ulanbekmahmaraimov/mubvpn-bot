import html

def fix_share():
    with open('mubvpn_bot.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        if "share_url = f\"https://t.me/share/url?url=https://t.me/{bot.username}" in line:
            new_line = '        share_url = f"https://t.me/share/url?url=https://mubvpn-bot.onrender.com/?lang={lang}&text={html.escape(L[\'share_msg\'])}"\n'
            new_lines.append(new_line)
        else:
            new_lines.append(line)
            
    with open('mubvpn_bot.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

if __name__ == "__main__":
    fix_share()
