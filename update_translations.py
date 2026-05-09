import re
import os

file_path = r'c:\Users\admin\StudioProjects\mubvpn\lib\constants\translations.dart'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

translations = {
    'ky': "\n    'country_us': 'АКШ',\n    'city_new_york': 'Нью-Йорк',\n    'city_los_angeles': 'Лос-Анжелес',",
    'ru': "\n    'country_us': 'США',\n    'city_new_york': 'Нью-Йорк',\n    'city_los_angeles': 'Лос-Анджелес',",
    'en': "\n    'country_us': 'United States',\n    'city_new_york': 'New York',\n    'city_los_angeles': 'Los Angeles',",
    'kk': "\n    'country_us': 'АҚШ',\n    'city_new_york': 'Нью-Йорк',\n    'city_los_angeles': 'Лос-Анджелес',",
    'tr': "\n    'country_us': 'ABD',\n    'city_new_york': 'New York',\n    'city_los_angeles': 'Los Angeles',",
    'tg': "\n    'country_us': 'ИМА',\n    'city_new_york': 'Ню Йорк',\n    'city_los_angeles': 'Лос Анҷелес',",
    'uz': "\n    'country_us': 'AQSH',\n    'city_new_york': 'Nyu-York',\n    'city_los_angeles': 'Los-Anjeles',"
}

for lang, extra in translations.items():
    # Find the language dictionary start and insert new keys
    pattern = rf"('{lang}'\s*:\s*{{)"
    content = re.sub(pattern, r"\1" + extra, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Translations added successfully.")
