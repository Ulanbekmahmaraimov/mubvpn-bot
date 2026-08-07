import 'package:flutter/material.dart';
import '../constants/translations.dart';

enum VpnState { disconnected, connecting, connected, error }

enum Protocol { auto, v2ray, wireguard, openvpn }

class VpnServer {
  final String country;
  final String city;
  final String flag;
  final String? config;
  final bool isPremium;
  int ping;

  final int currentUsers;
  final int maxCapacity;

  final String countryKey;
  final String cityKey;

  VpnServer({
    required this.country,
    required this.city,
    required this.flag,
    this.config,
    this.isPremium = false,
    this.ping = 0,
    this.currentUsers = 0,
    this.maxCapacity = 500,
    this.countryKey = '',
    this.cityKey = '',
  });

  String localizedCountry(String lang) {
    if (countryKey.isNotEmpty) {
      final val = t(countryKey, lang);
      if (val != countryKey) return val;
    }
    return country;
  }

  String localizedCity(String lang) {
    if (cityKey.isNotEmpty) {
      final val = t(cityKey, lang);
      if (val != cityKey) return val;
    }
    return city;
  }

  double get loadPercentage => (currentUsers / maxCapacity) * 100;

  Color get loadColor {
    if (ping == 0) return Colors.white24;
    if (ping < 100) return Colors.green;
    if (ping < 200) return Colors.orange;
    return Colors.red;
  }
}

List<VpnServer> getMockServers() {
  return [
    VpnServer(
      country: "Germany", countryKey: "country_germany",
      city: "Frankfurt (Main Server)", cityKey: "city_frankfurt", flag: "🇩🇪", isPremium: false,
      config: "vless://2e922e6a-65db-4767-8216-a4b6b501b3b8@167.235.22.54:443?encryption=none&flow=xtls-rprx-vision&type=tcp&headerType=none&security=reality&sni=www.sony.com&fp=chrome&pbk=0CIqFJJXUoImvhH9fBIBBsW0G798Q9WpwWDdhbdw93M&sid=7682624ec01fe9#%F0%9F%87%A9%F0%9F%87%AA%20%D0%93%D0%B5%D1%80%D0%BC%D0%B0%D0%BD%D0%B8%D1%8F%20%7C%20Bot%20Main",
    ),
    VpnServer(
      country: "Poland", countryKey: "country_poland",
      city: "Warsaw", cityKey: "city_warsaw", flag: "🇵🇱", isPremium: false,
      config: "vless://7e9e22d7-826e-44b9-a1bd-f582153d80cc@144.31.2.184:443?encryption=none&flow=xtls-rprx-vision&type=tcp&headerType=none&security=reality&sni=pl.quattro-tech.ru&fp=qq&pbk=10rVZPoOUP1TlQviIAsQ_jAROX0fRQxH0C92nq_zGQc&sid=43dcff53849b81e6#%F0%9F%87%B5%F0%9F%87%B1%20%F0%9F%8E%AE%20%E2%AD%90%EF%B8%8F%20%D0%9F%D0%BE%D0%BB%D1%8C%D1%88%D0%B0",
    ),
    VpnServer(
      country: "Netherlands", countryKey: "country_netherlands",
      city: "Amsterdam", cityKey: "city_amsterdam", flag: "🇳🇱", isPremium: false,
      config: "vless://7e9e22d7-826e-44b9-a1bd-f582153d80cc@23.236.186.50:443?encryption=none&flow=xtls-rprx-vision&type=tcp&headerType=none&security=reality&sni=nl.quattro-tech.ru&fp=qq&pbk=10rVZPoOUP1TlQviIAsQ_jAROX0fRQxH0C92nq_zGQc&sid=43dcff53849b81e6#%F0%9F%87%B3%F0%9F%87%B1%20%E2%9A%A1%EF%B8%8F%20%D0%9D%D0%B8%D0%B4%D0%B5%D1%80%D0%BB%D0%B0%D0%BD%D0%B4%D1%8B%20%7C%20Torrent%20%E2%9C%85",
    ),
    VpnServer(
      country: "Latvia", countryKey: "country_latvia",
      city: "Riga", cityKey: "city_riga", flag: "🇱🇻", isPremium: false,
      config: "vless://7e9e22d7-826e-44b9-a1bd-f582153d80cc@46.183.223.211:443?encryption=none&flow=xtls-rprx-vision&type=tcp&headerType=none&security=reality&sni=lv.quattro-tech.ru&fp=edge&pbk=10rVZPoOUP1TlQviIAsQ_jAROX0fRQxH0C92nq_zGQc&sid=43dcff53849b81e6#%F0%9F%87%B1%F0%9F%87%BB%20%E2%9A%A1%EF%B8%8F%20%D0%9B%D0%B0%D1%82%D0%B2%D0%B8%D1%8F",
    ),
    VpnServer(
      country: "USA", countryKey: "country_usa",
      city: "Denver", cityKey: "city_denver", flag: "🇺🇸", isPremium: false,
      config: "vless://7e9e22d7-826e-44b9-a1bd-f582153d80cc@23.237.28.195:443?encryption=none&flow=xtls-rprx-vision&type=tcp&headerType=none&security=reality&sni=us2.quattro-tech.ru&fp=qq&pbk=10rVZPoOUP1TlQviIAsQ_jAROX0fRQxH0C92nq_zGQc&sid=43dcff53849b81e6#%F0%9F%87%BA%F0%9F%87%B8%20%E2%9A%A1%EF%B8%8F%20%D0%A1%D0%A8%D0%90%2C%20%D0%94%D0%B5%D0%BD%D0%B2%D0%B5%D1%80",
    ),
    VpnServer(
      country: "Italy", countryKey: "country_italy",
      city: "Milan", cityKey: "city_milan", flag: "🇮🇹", isPremium: false,
      config: "vless://7e9e22d7-826e-0007-a1bd-f582153d80cc@185.16.213.67:8443?encryption=none&flow=xtls-rprx-vision&type=tcp&headerType=none&security=reality&sni=auto.quattro-tech.ru&fp=qq&pbk=10rVZPoOUP1TlQviIAsQ_jAROX0fRQxH0C92nq_zGQc&sid=43dcff53849b81e6#%F0%9F%87%AE%F0%9F%87%B9%20%E2%AD%90%EF%B8%8F%20%D0%98%D1%82%D0%B0%D0%BB%D0%B8%D1%8F",
    ),
    VpnServer(
      country: "Norway", countryKey: "country_norway",
      city: "Oslo", cityKey: "city_oslo", flag: "🇳🇴", isPremium: false,
      config: "vless://7e9e22d7-826e-000c-a1bd-f582153d80cc@185.16.213.67:8443?encryption=none&flow=xtls-rprx-vision&type=tcp&headerType=none&security=reality&sni=auto.quattro-tech.ru&fp=qq&pbk=10rVZPoOUP1TlQviIAsQ_jAROX0fRQxH0C92nq_zGQc&sid=43dcff53849b81e6#%F0%9F%87%B3%F0%9F%87%B4%20%E2%9A%A1%EF%B8%8F%20%E2%AD%90%EF%B8%8F%20%D0%9D%D0%BE%D1%80%D0%B2%D0%B5%D0%B3%D0%B8%D1%8F",
    ),
  ];
}
