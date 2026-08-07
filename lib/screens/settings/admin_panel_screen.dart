import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:firebase_database/firebase_database.dart';
import '../../constants/colors.dart';
import '../../providers/providers.dart';
import 'admin_terminal_screen.dart';
import '../../services/ai_service.dart';

const Map<String, Map<String, String>> _adminTranslations = {
  'turbo_admin': {'ky': 'Turbo Админ', 'ru': 'Turbo Админ', 'en': 'Turbo Admin', 'kk': 'Turbo Админ', 'uz': 'Turbo Admin', 'tg': 'Turbo Админ', 'tr': 'Turbo Yönetici'},
  'total_users': {'ky': 'Колдонуучулар', 'ru': 'Пользователи', 'en': 'Total Users', 'kk': 'Пайдаланушылар', 'uz': 'Foydalanuvchilar', 'tg': 'Корбарон', 'tr': 'Kullanıcılar'},
  'turbo_vip': {'ky': 'Премиум', 'ru': 'Премиум', 'en': 'Turbo VIP', 'kk': 'Премиум', 'uz': 'Premium', 'tg': 'Премиум', 'tr': 'Premium VIP'},
  'turbo_search': {'ky': 'Издөө', 'ru': 'Поиск', 'en': 'Turbo Search', 'kk': 'Іздеу', 'uz': 'Qidirish', 'tg': 'Ҷустуҷӯ', 'tr': 'Arama'},
  'enter_email': {'ky': 'Колдонуучунун email дарегин жазыңыз...', 'ru': 'Введите email пользователя...', 'en': 'Enter user email...', 'kk': 'Пайдаланушының email енгізіңіз...', 'uz': 'Foydalanuvchi emailini kiriting...', 'tg': 'Email-и корбарро ворид кунед...', 'tr': 'Kullanıcı email girin...'},
  'device': {'ky': 'Түзмөк', 'ru': 'Устройство', 'en': 'Device', 'kk': 'Құрылғы', 'uz': 'Qurilma', 'tg': 'Дастгоҳ', 'tr': 'Cihaz'},
  'network_latency': {'ky': 'Тармак Пинги', 'ru': 'Сетевой Пинг', 'en': 'Network Latency', 'kk': 'Желі Пингі', 'uz': 'Tarmoq Pingi', 'tg': 'Пинг-и Шабака', 'tr': 'Ağ Gecikmesi'},
  'turbo_bypass_engine': {'ky': 'Turbo Орнотуулар', 'ru': 'Turbo Настройки', 'en': 'Turbo Bypass Engine', 'kk': 'Turbo Параметрлер', 'uz': 'Turbo Sozlamalar', 'tg': 'Танзимоти Turbo', 'tr': 'Turbo Ayarları'},
  'bandwidth_limit': {'ky': 'ЫЛДАМДЫК ЧЕКТӨӨСҮ', 'ru': 'ЛИМИТ СКОРОСТИ', 'en': 'BANDWIDTH LIMIT', 'kk': 'ЖЫЛДАМДЫҚ ШЕГІ', 'uz': 'TEZLIK CHEKLOVI', 'tg': 'МАҲДУДИЯТИ СУРЪАТ', 'tr': 'HIZ SINIRI'},
  'remote_app_banner': {'ky': 'ТҮЗ ЭСКЕРТҮҮ БИЛДИРҮҮСҮ', 'ru': 'ПРЯМОЕ УВЕДОМЛЕНИЕ', 'en': 'REMOTE APP BANNER NOTICE', 'kk': 'ТІКЕЛЕЙ ЕСКЕРТУ', 'uz': 'TO\'G\'RIDAN-TO\'G\'RI XABAR', 'tg': 'ОГОҲИИ МУСТАҚИМ', 'tr': 'DOĞRUDAN BİLDİRİM'},
  'broadcast_hint': {'ky': 'Телефонуна билдирүү жөнөтүү...', 'ru': 'Отправить сообщение на телефон...', 'en': 'Broadcast a custom alert on client phone...', 'kk': 'Телефонға хабарлама жіберу...', 'uz': 'Telefonga xabar yuborish...', 'tg': 'Фиристодани паём ба телефон...', 'tr': 'Telefona mesaj gönder...'},
  'turbo_command_center': {'ky': 'Буйрук Борбору', 'ru': 'Командный Центр', 'en': 'Turbo Command Center', 'kk': 'Бұйрық Орталығы', 'uz': 'Buyruq Markazi', 'tg': 'Маркази Фармон', 'tr': 'Komuta Merkezi'},
  'turbo_boost': {'ky': 'TURBO ТЕЗДЕТҮҮ', 'ru': 'TURBO УСКОРЕНИЕ', 'en': 'TURBO BOOST', 'kk': 'TURBO ЖЫЛДАМДАТУ', 'uz': 'TURBO TEZLASHTIRISH', 'tg': 'СУРЪАТИ TURBO', 'tr': 'TURBO HIZLANDIR'},
  'deep_scan': {'ky': 'ТЕРЕҢ ТЕКШЕРҮҮ', 'ru': 'ГЛУБОКИЙ СКАН', 'en': 'DEEP SCAN', 'kk': 'ТЕРЕҢ ТЕКСЕРУ', 'uz': 'CHUQUR TEKSHIRUV', 'tg': 'СКАНИ ЧУҚУР', 'tr': 'DERİN TARAMA'},
  'view_config_key': {'ky': '🔑 КЛЮЧТУ КӨРҮҮ ЖАНА БАШКАРУУ', 'ru': '🔑 ПРОСМОТР КЛЮЧА И УПРАВЛЕНИЕ', 'en': '🔑 VIEW CONFIG KEY & CONTROL', 'kk': '🔑 КІЛТТІ КӨРУ ЖӘНЕ БАСҚАРУ', 'uz': '🔑 KALITNI KO\'RISH VA BOSHQARISH', 'tg': '🔑 ДИДАНИ КАЛИД ВА ИДОРА', 'tr': '🔑 ANAHTARI GÖR VE YÖNET'},
  'admin_authorization': {'ky': 'Админ Уруксаттары', 'ru': 'Авторизация Админа', 'en': 'Admin Authorization', 'kk': 'Админ Рұқсаттары', 'uz': 'Admin Huquqlari', 'tg': 'Иҷозатномаи Админ', 'tr': 'Yönetici Yetkileri'},
  'subscription_expiry': {'ky': 'ЖАЗЫЛУУ МӨӨНӨТҮ', 'ru': 'СРОК ПОДПИСКИ', 'en': 'SUBSCRIPTION EXPIRY', 'kk': 'ЖАЗЫЛУ МЕРЗІМІ', 'uz': 'OBUNA MUDDATI', 'tg': 'МӮҲЛАТИ ОБУНА', 'tr': 'ABONELİK SÜRESİ'},
  'change_expiry': {'ky': 'Мөөнөттү Өзгөртүү', 'ru': 'Изменить срок', 'en': 'Change Expiry', 'kk': 'Мерзімді Өзгерту', 'uz': 'Muddatni O\'zgartirish', 'tg': 'Тағйири Мӯҳлат', 'tr': 'Süreyi Değiştir'},
  'vip_premium': {'ky': 'VIP Премиум', 'ru': 'VIP Премиум', 'en': 'VIP Premium', 'kk': 'VIP Премиум', 'uz': 'VIP Premium', 'tg': 'VIP Премиум', 'tr': 'VIP Premium'},
  'manager_access': {'ky': 'Менеджер Укугу', 'ru': 'Доступ Менеджера', 'en': 'Manager Access', 'kk': 'Менеджер Құқығы', 'uz': 'Menejer Huquqi', 'tg': 'Ҳуқуқи Менеҷер', 'tr': 'Yönetici Erişimi'},
  'support_tickets': {'ky': 'Жардам Сурамдары', 'ru': 'Запросы Поддержки', 'en': 'Support Tickets', 'kk': 'Қолдау Сұраулары', 'uz': 'Yordam So\'rovlari', 'tg': 'Дархостҳои Кумак', 'tr': 'Destek Talepleri'},
  'zero_tickets': {'ky': 'Сурамдар жок', 'ru': 'Нет запросов', 'en': 'Zero tickets', 'kk': 'Сұраулар жоқ', 'uz': 'So\'rovlar yo\'q', 'tg': 'Дархост нест', 'tr': 'Talep yok'},
  'user_connected_live': {'ky': 'КОЛДОНУУЧУ ТУТАШТЫ (LIVE)', 'ru': 'ПОЛЬЗОВАТЕЛЬ ПОДКЛЮЧЕН (LIVE)', 'en': 'USER CONNECTED (LIVE)', 'kk': 'ПАЙДАЛАНУШЫ ҚОСЫЛҒАН (LIVE)', 'uz': 'FOYDALANUVCHI ULANISHDA (LIVE)', 'tg': 'КОРБАР ПАЙВАСТА АСТ (LIVE)', 'tr': 'KULLANICI BAĞLI (LIVE)'},
  'user_disconnected': {'ky': 'КОЛДОНУУЧУ ӨЧҮП ТУРАТ', 'ru': 'ПОЛЬЗОВАТЕЛЬ ОТКЛЮЧЕН', 'en': 'USER DISCONNECTED', 'kk': 'ПАЙДАЛАНУШЫ АЖЫРАТЫЛҒАН', 'uz': 'FOYDALANUVCHI UZILGAN', 'tg': 'КОРБАР ҚАТЪ ШУД', 'tr': 'KULLANICI ÇEVRİMDIŞI'},
  'decrypted_key': {'ky': 'ШИФРДЕН ЧЫГАРЫЛГАН V2RAY КЛЮЧУ', 'ru': 'РАСШИФРОВАННЫЙ КЛЮЧ V2RAY', 'en': 'DECRYPTED V2RAY CONFIGURATION KEY', 'kk': 'ШИФРДЕН ШЫҒАРЫЛҒАН V2RAY КІЛТІ', 'uz': 'SHIFRDAN YECHILGAN V2RAY KALITI', 'tg': 'КАЛИДИ РАМЗКУШОДАИ V2RAY', 'tr': 'ŞİFRESİ ÇÖZÜLMÜŞ V2RAY ANAHTARI'},
  'copy_key': {'ky': 'КӨЧҮРҮҮ', 'ru': 'СКОПИРОВАТЬ', 'en': 'COPY KEY', 'kk': 'КӨШІРУ', 'uz': 'NUSXA OLISH', 'tg': 'НУСХА', 'tr': 'KOPYALA'},
  'connect': {'ky': 'ТУТАШТЫРУУ', 'ru': 'ПОДКЛЮЧИТЬ', 'en': 'CONNECT', 'kk': 'ҚОСУ', 'uz': 'ULASH', 'tg': 'ПАЙВАСТАН', 'tr': 'BAĞLAN'},
  'disconnect': {'ky': 'ӨЧҮРҮҮ', 'ru': 'ОТКЛЮЧИТЬ', 'en': 'DISCONNECT', 'kk': 'ӨШІРУ', 'uz': 'UZISH', 'tg': 'ҚАТЪ КАРДАН', 'tr': 'BAĞLANTIYI KES'},
  'offline': {'ky': 'Офлайн', 'ru': 'Офлайн', 'en': 'Offline', 'kk': 'Офлайн', 'uz': 'Oflayn', 'tg': 'Офлайн', 'tr': 'Çevrimdışı'},
  'global_throughput': {'ky': 'ГЛОБАЛДЫК ТАРМАК КҮЧҮ', 'ru': 'ГЛОБАЛЬНАЯ НАГРУЗКА', 'en': 'GLOBAL CORE THROUGHPUT', 'kk': 'ЖАҺАНДЫҚ ЖЕЛІ КҮШІ', 'uz': 'GLOBAL TARMOQ KUCHI', 'tg': 'БОРГИРИИ ГЛОБАЛӢ', 'tr': 'KÜRESEL AĞ GÜCÜ'},
  'turbo_boost_sent': {'ky': 'Turbo Boost жөнөтүлдү! 100x оптималдаштыруулар колдонулууда...', 'ru': 'Turbo Boost отправлен! Применяются 100x оптимизации...', 'en': 'Turbo Boost Sent! Applying 100x optimizations...', 'kk': 'Turbo Boost жіберілді! 100x оңтайландыру қолданылуда...', 'uz': 'Turbo Boost yuborildi! 100x optimizatsiya qo\'llanilmoqda...', 'tg': 'Turbo Boost фиристода шуд! Оптимизатсияи 100x...', 'tr': 'Turbo Boost Gönderildi! 100x optimizasyonlar uygulanıyor...'},
  'connect_sent': {'ky': 'Түзмөккө туташуу сигналы жөнөтүлдү!', 'ru': 'Сигнал подключения отправлен на устройство!', 'en': 'Sent remote Connect signal to device!', 'kk': 'Құрылғыға қосылу сигналы жіберілді!', 'uz': 'Qurilmaga ulanish signali yuborildi!', 'tg': 'Сигнали пайвастшавӣ ба дастгоҳ фиристода шуд!', 'tr': 'Cihaza bağlanma sinyali gönderildi!'},
  'disconnect_sent': {'ky': 'Түзмөккө өчүрүү сигналы жөнөтүлдү!', 'ru': 'Сигнал отключения отправлен на устройство!', 'en': 'Sent remote Disconnect signal to device!', 'kk': 'Құрылғыға өшіру сигналы жіберілді!', 'uz': 'Qurilmaga uzish signali yuborildi!', 'tg': 'Сигнали қатъ кардан ба дастгоҳ фиристода шуд!', 'tr': 'Cihaza bağlantı kesme sinyali gönderildi!'},
  'copied': {'ky': 'V2Ray ключу алмашуу буферине көчүрүлдү!', 'ru': 'Ключ V2Ray скопирован в буфер обмена!', 'en': 'V2Ray config key copied to clipboard!', 'kk': 'V2Ray кілті алмасу буферіне көшірілді!', 'uz': 'V2Ray kaliti clipboardga nusxalandi!', 'tg': 'Калиди V2Ray ба буфери мубодила нусхабардорӣ шуд!', 'tr': 'V2Ray anahtarı panoya kopyalandı!'},
  'tls_fingerprint': {'ky': 'TLS ФИНГЕРПРИНТ', 'ru': 'TLS ОТПЕЧАТОК', 'en': 'TLS FINGERPRINT', 'kk': 'TLS ФИНГЕРПРИНТ', 'uz': 'TLS FINGERPRINT', 'tg': 'TLS ФИНГЕРПРИНТ', 'tr': 'TLS PARMAK İZİ'},
};

String _t(String key, String lang) {
  return _adminTranslations[key]?[lang] ?? _adminTranslations[key]?['en'] ?? key;
}
class AdminPanelScreen extends StatefulWidget {
  const AdminPanelScreen({super.key});

  @override
  State<AdminPanelScreen> createState() => _AdminPanelScreenState();
}

class _AdminPanelScreenState extends State<AdminPanelScreen> with SingleTickerProviderStateMixin {
  final TextEditingController _searchController = TextEditingController();
  final TextEditingController _fragmentController = TextEditingController();
  final TextEditingController _sniController = TextEditingController();
  final TextEditingController _noticeController = TextEditingController();
  
  Map<String, dynamic>? _foundUser;
  bool _isSearching = false;
  bool _isLoadingTickets = true;
  List<Map<String, dynamic>> _tickets = [];
  
  int _totalUsers = 0;
  int _premiumUsers = 0;

  late AnimationController _pulseController;

  @override
  void initState() {
    super.initState();
    _loadData();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _searchController.dispose();
    _fragmentController.dispose();
    _sniController.dispose();
    _noticeController.dispose();
    super.dispose();
  }

  Future<void> _loadData() async {
    await Future.wait([
      _loadTickets(),
      _loadStats(),
    ]);
  }

  Future<void> _loadStats() async {
    final snapshot = await FirebaseDatabase.instance.ref('users').get();
    if (snapshot.exists) {
      final data = snapshot.value as Map;
      int total = data.length;
      int premium = 0;
      data.forEach((k, v) {
        if (v is Map && (v['isPremium'] == true || v['is_paid'] == true)) premium++;
      });
      if (mounted) {
        setState(() {
          _totalUsers = total;
          _premiumUsers = premium;
        });
      }
    }
  }

  Future<void> _loadTickets() async {
    setState(() => _isLoadingTickets = true);
    final tickets = await context.read<SubscriptionProvider>().fetchSupportTickets();
    if (mounted) {
      setState(() {
        _tickets = tickets;
        _isLoadingTickets = false;
      });
    }
  }

  Future<void> _searchUser() async {
    if (_searchController.text.isEmpty) return;
    HapticFeedback.mediumImpact();
    setState(() => _isSearching = true);
    final user = await context.read<SubscriptionProvider>().findUserByEmail(_searchController.text.trim());
    if (mounted) {
      setState(() {
        _foundUser = user;
        _isSearching = false;
        if (user != null) {
          _fragmentController.text = user['settings']['fragment'] ?? "";
          _sniController.text = user['settings']['custom_sni'] ?? "";
          _noticeController.text = user['settings']['remote_notice'] ?? "";
        }
      });
    }
  }

  Future<void> _resolveTicket(String ticketId) async {
    HapticFeedback.lightImpact();
    await FirebaseDatabase.instance.ref('support_tickets/$ticketId').remove();
    _loadTickets();
  }

  Widget _buildGlobalTrafficVisualizer(String lang) {
    return AnimatedBuilder(
      animation: _pulseController,
      builder: (context, child) => Container(
        height: 65,
        margin: const EdgeInsets.only(top: 16),
        padding: const EdgeInsets.symmetric(horizontal: 20),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.015),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: Colors.white.withOpacity(0.04)),
        ),
        child: Row(
          children: [
            Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(_t('global_throughput', lang), style: const TextStyle(color: Colors.white38, fontSize: 8, fontWeight: FontWeight.bold, letterSpacing: 1.5)),
                const SizedBox(height: 4),
                const Text("⚡ 1.48 Gbps", style: TextStyle(color: Colors.greenAccent, fontSize: 14, fontWeight: FontWeight.w900, fontFamily: 'monospace')),
              ],
            ),
            const SizedBox(width: 24),
            Expanded(
              child: CustomPaint(
                painter: TrafficWavePainter(_pulseController.value),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final sub = context.watch<SubscriptionProvider>();
    final lang = context.watch<LanguageProvider>().lang;

    return Scaffold(
      backgroundColor: const Color(0xFF060A0E),
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        flexibleSpace: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [Colors.black.withOpacity(0.8), Colors.transparent],
            ),
          ),
        ),
        title: Text(
          _t('turbo_admin', lang),
          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, letterSpacing: 2, fontSize: 18),
        ),
        actions: [
          RepaintBoundary(
            child: IconButton(
              icon: AnimatedBuilder(
                animation: _pulseController,
                builder: (context, child) => Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.greenAccent.withOpacity(0.1 + (_pulseController.value * 0.1)),
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(color: Colors.greenAccent.withOpacity(0.2 * _pulseController.value), blurRadius: 10, spreadRadius: 2)
                    ],
                  ),
                  child: const Icon(Icons.terminal_rounded, color: Colors.greenAccent, size: 20),
                ),
              ),
              onPressed: () {
                HapticFeedback.heavyImpact();
                Navigator.push(context, MaterialPageRoute(builder: (context) => const AdminTerminalScreen()));
              },
            ),
          ),
          const SizedBox(width: 12),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadData,
        color: AppColors.accent,
        edgeOffset: 100,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 120, 16, 40),
          children: [
            _buildDashboardStats(lang),
            _buildGlobalTrafficVisualizer(lang),
            const SizedBox(height: 32),
            _buildSearchSection(lang),
            if (_foundUser != null) _buildUserEliteCard(sub, lang),
            const SizedBox(height: 32),
            _buildSectionHeader(_t('support_tickets', lang), Icons.auto_awesome_motion_rounded),
            const SizedBox(height: 12),
            _buildTicketsSection(lang),
          ],
        ),
      ),
    );
  }

  Widget _buildDashboardStats(String lang) {
    return Row(
      children: [
        _buildStatCard(_t('total_users', lang), _totalUsers.toString(), Icons.people_rounded, Colors.blueAccent),
        const SizedBox(width: 16),
        _buildStatCard(_t('turbo_vip', lang), _premiumUsers.toString(), Icons.bolt_rounded, AppColors.accent),
      ],
    );
  }

  Widget _buildStatCard(String label, String value, IconData icon, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [color.withOpacity(0.15), color.withOpacity(0.05)],
          ),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: color.withOpacity(0.2)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(12)),
              child: Icon(icon, color: color, size: 22),
            ),
            const SizedBox(height: 16),
            Text(value, style: const TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.w900, letterSpacing: -1)),
            Text(label, style: TextStyle(color: Colors.white.withOpacity(0.4), fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1)),
          ],
        ),
      ),
    );
  }

  Widget _buildSearchSection(String lang) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildSectionHeader(_t('turbo_search', lang), Icons.radar_rounded),
        const SizedBox(height: 12),
        Container(
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(0.03),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: Colors.white.withOpacity(0.05)),
          ),
          child: TextField(
            controller: _searchController,
            style: const TextStyle(color: Colors.white),
            decoration: InputDecoration(
              hintText: _t('enter_email', lang),
              hintStyle: const TextStyle(color: Colors.white24, fontSize: 14),
              contentPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 18),
              border: InputBorder.none,
              suffixIcon: Padding(
                padding: const EdgeInsets.only(right: 8),
                child: IconButton(
                  icon: const Icon(Icons.search_rounded, color: AppColors.accent),
                  onPressed: _searchUser,
                ),
              ),
            ),
            onSubmitted: (_) => _searchUser(),
          ),
        ),
        if (_isSearching) const Center(child: Padding(padding: EdgeInsets.all(20), child: CircularProgressIndicator(color: AppColors.accent))),
      ],
    );
  }

  Widget _buildUserEliteCard(SubscriptionProvider sub, String lang) {
    final uid = _foundUser!['uid'];
    final role = _foundUser!['role'];
    final isPremium = _foundUser!['isPremium'];
    final Map<String, dynamic> settings = {};
    if (_foundUser!['settings'] is Map) {
      (_foundUser!['settings'] as Map).forEach((k, v) {
        settings[k.toString()] = v;
      });
    }

    return AnimatedContainer(
      duration: const Duration(milliseconds: 500),
      margin: const EdgeInsets.only(top: 24),
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: const Color(0xFF11161D),
        borderRadius: BorderRadius.circular(32),
        border: Border.all(color: Colors.white.withOpacity(0.08)),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.5), blurRadius: 40, offset: const Offset(0, 20))],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 50,
                height: 50,
                decoration: BoxDecoration(
                  gradient: LinearGradient(colors: [AppColors.accent, AppColors.accent.withOpacity(0.5)]),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Center(child: Text(_foundUser!['email'][0].toUpperCase(), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 20))),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(_foundUser!['email'], style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900, fontSize: 16)),
                    Text('UID: $uid', style: const TextStyle(color: Colors.white24, fontSize: 10, fontFamily: 'monospace')),
                  ],
                ),
              ),
              _buildRoleBadge(role),
            ],
          ),
          const SizedBox(height: 24),
          _buildInfoRow(Icons.phone_android_rounded, _t('device', lang), _foundUser!['device'] ?? 'Unknown'),
          const SizedBox(height: 8),
          _buildInfoRow(
            Icons.network_ping_rounded,
            _t('network_latency', lang),
            (settings['current_ping'] == 'Offline' || settings['current_ping'] == null) ? _t('offline', lang) : settings['current_ping'],
            valueColor: (settings['current_ping'] == null || settings['current_ping'] == 'Offline')
                ? Colors.white30
                : Colors.greenAccent,
          ),
          const Padding(padding: EdgeInsets.symmetric(vertical: 20), child: Divider(color: Colors.white10)),
          
          _buildEliteSectionTitle(_t('turbo_bypass_engine', lang)),
          const SizedBox(height: 16),
          _buildModernField('Fragmentation', _fragmentController, 'e.g. 1-100,2', (v) => _updateSetting(uid, 'fragment', v)),
          const SizedBox(height: 16),
          _buildModernField('Custom SNI', _sniController, 'e.g. google.com', (v) => _updateSetting(uid, 'custom_sni', v)),
          const SizedBox(height: 16),
          _buildFingerprintDropdown(uid, settings['fingerprint'] ?? 'chrome', lang),
          _buildSpeedLimitDropdown(uid, settings['speed_limit'] ?? 'no_limit', lang),
          _buildNoticeField(uid, settings, lang),
          
          _buildCoolToggle('Multi-Stream (Mux 16x)', settings['mux'] ?? true, (v) => _updateSetting(uid, 'mux', v)),

          const Padding(padding: EdgeInsets.symmetric(vertical: 20), child: Divider(color: Colors.white10)),
          _buildEliteSectionTitle(lang == 'ky' ? 'Turbo Command Center' : 'Turbo Command Center'),
          const SizedBox(height: 16),
          _buildCommandGrid(uid, sub),
          
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.orangeAccent.withOpacity(0.1),
                    side: const BorderSide(color: Colors.orangeAccent),
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  ),
                  icon: const Icon(Icons.bolt_rounded, color: Colors.orangeAccent),
                  label: Text(_t('turbo_boost', lang), style: const TextStyle(color: Colors.orangeAccent, fontWeight: FontWeight.w900)),
                  onPressed: () {
                    HapticFeedback.heavyImpact();
                    sub.sendCommand(uid, 'turbo_boost');
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_t('turbo_boost_sent', lang)), backgroundColor: Colors.orangeAccent));
                    _searchUser();
                  },
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.purpleAccent.withOpacity(0.1),
                    side: const BorderSide(color: Colors.purpleAccent),
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  ),
                  icon: const Icon(Icons.biotech_rounded, color: Colors.purpleAccent),
                  label: Text(_t('deep_scan', lang), style: const TextStyle(color: Colors.purpleAccent, fontWeight: FontWeight.w900)),
                  onPressed: () {
                    HapticFeedback.heavyImpact();
                    _runDeepDiagnosis(uid, _foundUser!);
                  },
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.accent.withOpacity(0.1),
                side: const BorderSide(color: AppColors.accent),
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              ),
              icon: const Icon(Icons.vpn_key_rounded, color: AppColors.accent),
              label: Text(_t('view_config_key', lang), style: const TextStyle(color: AppColors.accent, fontWeight: FontWeight.w900)),
              onPressed: () {
                HapticFeedback.heavyImpact();
                _showKeyConfigPopup(context, uid, _foundUser!, settings, lang);
              },
            ),
          ),
          
          if (sub.isAdmin) ...[
            const Padding(padding: EdgeInsets.symmetric(vertical: 20), child: Divider(color: Colors.white10)),
            _buildEliteSectionTitle(_t('admin_auth', lang)),
            const SizedBox(height: 12),
            _buildDatePickerRow(uid, sub, _foundUser!['expiryDate'], lang),
            const SizedBox(height: 12),
            _buildCoolToggle(_t('vip_premium', lang), isPremium, (v) async {
              HapticFeedback.heavyImpact();
              await sub.updateUserStatus(uid, isPremium: v, expiryDate: v ? DateTime.now().add(const Duration(days: 30)).toIso8601String() : null);
              _searchUser();
            }),
            _buildCoolToggle(_t('manager_access', lang), role == 'manager', (v) async {
              HapticFeedback.vibrate();
              await sub.updateUserStatus(uid, role: v ? 'manager' : 'user');
              _searchUser();
            }),
          ],
        ],
      ),
    );
  }

  Widget _buildDatePickerRow(String uid, SubscriptionProvider sub, String? currentExpiry, String lang) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildEliteSectionTitle(_t('subscription_expiry', lang)),
            const SizedBox(height: 4),
            Text(
              currentExpiry != null ? currentExpiry.split('T').first : 'No Expiry Set',
              style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold, fontFamily: 'monospace'),
            ),
          ],
        ),
        TextButton.icon(
          style: TextButton.styleFrom(
            foregroundColor: AppColors.accent,
            backgroundColor: AppColors.accent.withOpacity(0.08),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          ),
          icon: const Icon(Icons.calendar_today_rounded, size: 14),
          label: Text(_t('change_expiry', lang), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
          onPressed: () async {
            HapticFeedback.heavyImpact();
            final DateTime? picked = await showDatePicker(
              context: context,
              initialDate: DateTime.now().add(const Duration(days: 30)),
              firstDate: DateTime.now(),
              lastDate: DateTime.now().add(const Duration(days: 3650)),
              builder: (context, child) {
                return Theme(
                  data: Theme.of(context).copyWith(
                    colorScheme: const ColorScheme.dark(
                      primary: AppColors.accent,
                      onPrimary: Colors.white,
                      surface: Color(0xFF0F1419),
                      onSurface: Colors.white,
                    ), dialogTheme: const DialogThemeData(backgroundColor: Color(0xFF0F1419)),
                  ),
                  child: child!,
                );
              },
            );
            if (picked != null) {
              await sub.updateUserStatus(uid, isPremium: true, expiryDate: picked.toIso8601String());
              _searchUser();
            }
          },
        ),
      ],
    );
  }

  Widget _buildSpeedLimitDropdown(String uid, String current, String lang) {
    final options = ['no_limit', '100_mbps', '50_mbps', '10_mbps', '5_mbps', '2_mbps'];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 16),
        _buildEliteSectionTitle(_t('bandwidth_limit', lang)),
        const SizedBox(height: 8),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          decoration: BoxDecoration(color: Colors.black26, borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.white.withOpacity(0.05))),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<String>(
              value: options.contains(current) ? current : 'no_limit',
              dropdownColor: const Color(0xFF1A1F24),
              isExpanded: true,
              style: const TextStyle(color: Colors.white, fontSize: 14),
              items: options.map((e) => DropdownMenuItem(value: e, child: Text(e.replaceAll('_', ' ').toUpperCase()))).toList(),
              onChanged: (v) {
                if (v != null) {
                  HapticFeedback.selectionClick();
                  _updateSetting(uid, 'speed_limit', v);
                }
              },
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildNoticeField(String uid, Map<String, dynamic> settings, String lang) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 16),
        _buildEliteSectionTitle(_t('remote_app_banner', lang)),
        const SizedBox(height: 8),
        Container(
          height: 48,
          decoration: BoxDecoration(color: Colors.black26, borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.white.withOpacity(0.05))),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _noticeController,
                  style: const TextStyle(color: Colors.white, fontSize: 14),
                  decoration: InputDecoration(
                    hintText: _t('broadcast_hint', lang),
                    hintStyle: const TextStyle(color: Colors.white12, fontSize: 12),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 16),
                    border: InputBorder.none,
                  ),
                ),
              ),
              IconButton(
                icon: const Icon(Icons.send_rounded, color: Colors.purpleAccent, size: 20),
                onPressed: () {
                  HapticFeedback.heavyImpact();
                  _updateSetting(uid, 'remote_notice', _noticeController.text.trim());
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(
                      content: Text('Notice broadcasted to client phone!'),
                      backgroundColor: Colors.purpleAccent,
                    ),
                  );
                },
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildRoleBadge(String role) {
    Color c = role == 'admin' ? Colors.redAccent : (role == 'manager' ? Colors.blueAccent : AppColors.accent);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(color: c.withOpacity(0.1), borderRadius: BorderRadius.circular(10), border: Border.all(color: c.withOpacity(0.3))),
      child: Text(role.toUpperCase(), style: TextStyle(color: c, fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1)),
    );
  }

  Widget _buildModernField(String label, TextEditingController controller, String hint, ValueChanged<String> onSave) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label, style: const TextStyle(color: Colors.white38, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1)),
        const SizedBox(height: 8),
        Container(
          height: 48,
          decoration: BoxDecoration(color: Colors.black26, borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.white.withOpacity(0.05))),
          child: Row(
            children: [
              Expanded(
                child: TextField(
                  controller: controller,
                  style: const TextStyle(color: Colors.white, fontSize: 14),
                  decoration: InputDecoration(hintText: hint, hintStyle: const TextStyle(color: Colors.white10), contentPadding: const EdgeInsets.symmetric(horizontal: 16), border: InputBorder.none),
                ),
              ),
              IconButton(icon: const Icon(Icons.bolt_rounded, color: AppColors.accent, size: 20), onPressed: () {
                HapticFeedback.lightImpact();
                onSave(controller.text.trim());
              }),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildFingerprintDropdown(String uid, String current, String lang) {
    final options = ['chrome', 'firefox', 'safari', 'edge', 'ios', 'android', 'random'];
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildEliteSectionTitle(_t('tls_fingerprint', lang)),
        const SizedBox(height: 8),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          decoration: BoxDecoration(color: Colors.black26, borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.white.withOpacity(0.05))),
          child: DropdownButtonHideUnderline(
            child: DropdownButton<String>(
              value: options.contains(current) ? current : 'chrome',
              dropdownColor: const Color(0xFF1A1F24),
              isExpanded: true,
              style: const TextStyle(color: Colors.white, fontSize: 14),
              items: options.map((e) => DropdownMenuItem(value: e, child: Text(e.toUpperCase()))).toList(),
              onChanged: (v) {
                if (v != null) {
                  HapticFeedback.selectionClick();
                  _updateSetting(uid, 'fingerprint', v);
                }
              },
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildCommandGrid(String uid, SubscriptionProvider sub) {
    return GridView.count(
      crossAxisCount: 4,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 12,
      crossAxisSpacing: 12,
      childAspectRatio: 0.9,
      children: [
        _buildCommandBtn(Icons.assignment_rounded, 'LOGS', Colors.orangeAccent, () => sub.sendCommand(uid, 'upload_logs')),
        _buildCommandBtn(Icons.auto_fix_high_rounded, 'FIX', Colors.blueAccent, () => sub.sendCommand(uid, 'smart_fix')),
        _buildCommandBtn(Icons.power_settings_new_rounded, 'VPN', Colors.greenAccent, () => sub.sendCommand(uid, 'connect')),
        _buildCommandBtn(Icons.dns_rounded, 'NODE', Colors.purpleAccent, () => _showServerDialog(uid)),
      ],
    );
  }

  Widget _buildCommandBtn(IconData icon, String label, Color color, VoidCallback onTap) {
    return InkWell(
      onTap: () {
        HapticFeedback.mediumImpact();
        onTap();
      },
      borderRadius: BorderRadius.circular(16),
      child: Container(
        decoration: BoxDecoration(color: color.withOpacity(0.05), borderRadius: BorderRadius.circular(16), border: Border.all(color: color.withOpacity(0.1))),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: color, size: 22),
            const SizedBox(height: 6),
            Text(label, style: TextStyle(color: color, fontSize: 9, fontWeight: FontWeight.w900)),
          ],
        ),
      ),
    );
  }

  Widget _buildCoolToggle(String title, bool value, ValueChanged<bool> onChanged) {
    return Padding(
      padding: const EdgeInsets.only(top: 12),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(title, style: const TextStyle(color: Colors.white70, fontSize: 14, fontWeight: FontWeight.w500)),
          Switch(value: value, activeThumbColor: AppColors.accent, activeTrackColor: AppColors.accent.withOpacity(0.3), onChanged: (v) {
            HapticFeedback.selectionClick();
            onChanged(v);
          }),
        ],
      ),
    );
  }

  Widget _buildTicketsSection(String lang) {
    if (_isLoadingTickets) return const Center(child: CircularProgressIndicator(color: AppColors.accent));
    if (_tickets.isEmpty) return Center(child: Padding(padding: const EdgeInsets.all(40), child: Text(_t('zero_tickets', lang), style: const TextStyle(color: Colors.white24))));
    
    return Column(children: _tickets.map((t) => _buildEliteTicketCard(t, lang)).toList());
  }

  Widget _buildEliteTicketCard(Map<String, dynamic> ticket, String lang) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(color: Colors.white.withOpacity(0.02), borderRadius: BorderRadius.circular(24), border: Border.all(color: Colors.white.withOpacity(0.05))),
      child: Theme(
        data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
        child: ExpansionTile(
          iconColor: AppColors.accent,
          title: Text(ticket['email'] ?? 'System', style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.w700)),
          subtitle: Text(ticket['message'] ?? 'Analyze required', style: const TextStyle(color: AppColors.accent, fontSize: 12)),
          trailing: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              IconButton(icon: const Icon(Icons.auto_awesome, color: Colors.purpleAccent, size: 20), onPressed: () {
                HapticFeedback.heavyImpact();
                _analyzeWithAI(ticket);
              }),
              IconButton(icon: const Icon(Icons.done_all_rounded, color: Colors.greenAccent, size: 20), onPressed: () => _resolveTicket(ticket['id'])),
            ],
          ),
          children: [
            Container(
              height: 200,
              margin: const EdgeInsets.all(16),
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: Colors.black45, borderRadius: BorderRadius.circular(16)),
              child: ListView.builder(
                itemCount: (ticket['logs'] as List? ?? []).length,
                itemBuilder: (context, i) => Text(ticket['logs'][i], style: const TextStyle(color: Colors.white54, fontSize: 8, fontFamily: 'monospace')),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionHeader(String title, IconData icon) {
    return Row(
      children: [
        Icon(icon, color: AppColors.accent, size: 18),
        const SizedBox(width: 8),
        Text(title.toUpperCase(), style: const TextStyle(color: Colors.white38, fontSize: 11, fontWeight: FontWeight.w900, letterSpacing: 2)),
      ],
    );
  }

  Widget _buildEliteSectionTitle(String title) {
    return Text(title.toUpperCase(), style: const TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 2));
  }

  Widget _buildInfoRow(IconData icon, String label, String value, {Color? valueColor}) {
    return Row(
      children: [
        Icon(icon, color: Colors.white24, size: 16),
        const SizedBox(width: 8),
        Text(label, style: const TextStyle(color: Colors.white38, fontSize: 13)),
        const Spacer(),
        Text(
          value,
          style: TextStyle(
            color: valueColor ?? Colors.white70,
            fontSize: 13,
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }

  void _showKeyConfigPopup(BuildContext context, String uid, Map<String, dynamic> user, Map<String, dynamic> settings, String lang) {
    final sub = context.read<SubscriptionProvider>();
    final vpn = context.read<VpnProvider>();
    
    final serverIndex = settings['selected_server_index'] ?? 0;
    String rawConfig = "vless://mubvpn-reality-node@127.0.0.1:443?security=reality&sni=google.com&fp=chrome#MubVPN-Reality";
    if (serverIndex >= 0 && serverIndex < vpn.servers.length) {
      rawConfig = vpn.servers[serverIndex].config ?? rawConfig;
    }

    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF0A0E12),
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(36))),
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setPopupState) {
            final isOnline = settings['current_ping'] != null && settings['current_ping'] != 'Offline';
            return Container(
              padding: const EdgeInsets.all(28),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        width: 12,
                        height: 12,
                        decoration: BoxDecoration(
                          color: isOnline ? Colors.greenAccent : Colors.redAccent,
                          shape: BoxShape.circle,
                          boxShadow: [
                            BoxShadow(
                              color: (isOnline ? Colors.greenAccent : Colors.redAccent).withOpacity(0.5),
                              blurRadius: 8,
                              spreadRadius: 2,
                            )
                          ],
                        ),
                      ),
                      const SizedBox(width: 12),
                      Text(
                        isOnline ? _t('user_connected_live', lang) : _t('user_disconnected', lang),
                        style: TextStyle(
                          color: isOnline ? Colors.greenAccent : Colors.white38,
                          fontSize: 11,
                          fontWeight: FontWeight.w900,
                          letterSpacing: 2,
                        ),
                      ),
                      const Spacer(),
                      IconButton(
                        icon: const Icon(Icons.close_rounded, color: Colors.white30),
                        onPressed: () => Navigator.pop(context),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  
                  Text(
                    _t('decrypted_key', lang),
                    style: const TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 2),
                  ),
                  const SizedBox(height: 12),

                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: Colors.black38,
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: Colors.white.withOpacity(0.04)),
                    ),
                    child: SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: SelectableText(
                        rawConfig,
                        style: const TextStyle(
                          color: Colors.greenAccent,
                          fontFamily: 'monospace',
                          fontSize: 12,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),

                  _buildPopupMetaRow("Protocol", "Reality / VLESS"),
                  _buildPopupMetaRow("Fingerprint", settings['fingerprint'] ?? "Chrome"),
                  _buildPopupMetaRow("Custom SNI", settings['custom_sni'] ?? "Bypassed"),
                  _buildPopupMetaRow("Fragmentation", settings['fragment'] ?? "Disabled"),
                  
                  const SizedBox(height: 28),

                  GridView.count(
                    crossAxisCount: 3,
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    crossAxisSpacing: 12,
                    mainAxisSpacing: 12,
                    childAspectRatio: 1.1,
                    children: [
                      _buildPopupButton(
                        icon: Icons.copy_all_rounded,
                        label: _t('copy_key', lang),
                        color: Colors.blueAccent,
                        onTap: () {
                          Clipboard.setData(ClipboardData(text: rawConfig));
                          HapticFeedback.heavyImpact();
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text(_t('copied', lang)),
                              backgroundColor: Colors.blueAccent,
                            ),
                          );
                        },
                      ),
                      _buildPopupButton(
                        icon: Icons.play_arrow_rounded,
                        label: _t('connect', lang),
                        color: Colors.greenAccent,
                        onTap: () {
                          HapticFeedback.heavyImpact();
                          sub.sendCommand(uid, 'connect');
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text(_t('connect_sent', lang)),
                              backgroundColor: Colors.greenAccent,
                            ),
                          );
                        },
                      ),
                      _buildPopupButton(
                        icon: Icons.stop_rounded,
                        label: _t('disconnect', lang),
                        color: Colors.redAccent,
                        onTap: () {
                          HapticFeedback.heavyImpact();
                          sub.sendCommand(uid, 'disconnect');
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text(_t('disconnect_sent', lang)),
                              backgroundColor: Colors.redAccent,
                            ),
                          );
                        },
                      ),
                    ],
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  Widget _buildPopupMetaRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.white38, fontSize: 12)),
          Text(value, style: const TextStyle(color: Colors.white70, fontSize: 12, fontWeight: FontWeight.bold, fontFamily: 'monospace')),
        ],
      ),
    );
  }

  Widget _buildPopupButton({required IconData icon, required String label, required Color color, required VoidCallback onTap}) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        decoration: BoxDecoration(
          color: color.withOpacity(0.06),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: color.withOpacity(0.2)),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: color, size: 24),
            const SizedBox(height: 6),
            Text(
              label,
              style: TextStyle(color: color, fontSize: 9, fontWeight: FontWeight.w900, letterSpacing: 1),
            ),
          ],
        ),
      ),
    );
  }

  void _showServerDialog(String uid) {
    final vpn = context.read<VpnProvider>();
    final sub = context.read<SubscriptionProvider>();
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF0F1419),
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(30))),
      builder: (context) => Container(
        padding: const EdgeInsets.symmetric(vertical: 24),
        child: ListView.builder(
          shrinkWrap: true,
          itemCount: vpn.servers.length,
          itemBuilder: (context, i) => ListTile(
            leading: Text(vpn.servers[i].flag, style: const TextStyle(fontSize: 24)),
            title: Text(vpn.servers[i].country, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            subtitle: Text(vpn.servers[i].city, style: const TextStyle(color: Colors.white24, fontSize: 12)),
            onTap: () {
              HapticFeedback.mediumImpact();
              sub.sendCommand(uid, 'set_server:$i');
              Navigator.pop(context);
            },
          ),
        ),
      ),
    );
  }

  Future<void> _updateSetting(String uid, String key, dynamic value) async {
    await context.read<SubscriptionProvider>().updateRemoteSettings(uid, {key: value});
    _searchUser(); 
  }

  void _analyzeWithAI(Map<String, dynamic> ticket) async {
    final List logs = ticket['logs'] ?? [];
    showModalBottomSheet(
      context: context,
      isDismissible: false,
      backgroundColor: const Color(0xFF060A0E),
      builder: (context) => const SizedBox(height: 200, child: Center(child: CircularProgressIndicator(color: Colors.purpleAccent))),
    );

    final analysis = await AIService().analyzeLogs(logs.map((e) => e.toString()).toList());
    if (!mounted) return;
    Navigator.pop(context);

    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF0F1419),
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(30))),
      builder: (context) => Container(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.auto_awesome, color: Colors.purpleAccent),
                SizedBox(width: 12),
                Text('AI NEURAL ANALYSIS', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w900)),
              ],
            ),
            const SizedBox(height: 24),
            Text(analysis, style: const TextStyle(color: Colors.white70, fontSize: 15, height: 1.5)),
            const SizedBox(height: 32),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(backgroundColor: AppColors.accent, padding: const EdgeInsets.symmetric(vertical: 16), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16))),
                onPressed: () => Navigator.pop(context),
                child: const Text('CONFIRMED', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _runDeepDiagnosis(String uid, Map<String, dynamic> user) async {
    final sub = context.read<SubscriptionProvider>();
    // 1. Request fresh logs
    sub.sendCommand(uid, 'upload_logs');
    
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF060A0E),
      isDismissible: false,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(30))),
      builder: (context) => Container(
        height: 400,
        padding: const EdgeInsets.all(32),
        child: Column(
          children: [
            const CircularProgressIndicator(color: Colors.purpleAccent),
            const SizedBox(height: 24),
            const Text('RUNNING DEEP NEURAL SCAN...', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w900, letterSpacing: 2)),
            const SizedBox(height: 12),
            const Text('Fetching logs, checking ports, and analyzing protocol handshake...', style: TextStyle(color: Colors.white38, fontSize: 12), textAlign: TextAlign.center),
            const Spacer(),
            // Mocking the scan process for visualization
            TweenAnimationBuilder<double>(
              tween: Tween(begin: 0, end: 1),
              duration: const Duration(seconds: 3),
              builder: (context, value, child) => Column(
                children: [
                  LinearProgressIndicator(value: value, backgroundColor: Colors.white10, color: Colors.purpleAccent),
                  const SizedBox(height: 8),
                  Text('${(value * 100).toInt()}% COMPLETE', style: const TextStyle(color: Colors.purpleAccent, fontSize: 10, fontWeight: FontWeight.bold)),
                ],
              ),
            ),
          ],
        ),
      ),
    );

    // Wait for "scan" simulation
    await Future.delayed(const Duration(seconds: 3));
    if (!mounted) return;
    Navigator.pop(context);

    // Get the diagnostic report
    final List<String> logsToAnalyze = (user['logs'] as List?)?.map((e) => e.toString()).toList() ?? 
        ["DEEP_SCAN_REQUEST: Analyzing Port 443", "Handshake: Reality/VLESS", "Status: Blocked by DPI"];
    final analysis = await AIService().analyzeLogs(logsToAnalyze);
    
    if (!mounted) return;
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF0F1419),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30), side: BorderSide(color: Colors.purpleAccent.withOpacity(0.3))),
        title: const Row(
          children: [
            Icon(Icons.biotech_rounded, color: Colors.purpleAccent),
            SizedBox(width: 12),
            Text('DIAGNOSTIC REPORT', style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w900)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildDiagItem('SERVER PORT', '443 (TLS)', Colors.greenAccent),
            _buildDiagItem('CONFIG STATUS', 'VALID (VLESS)', Colors.greenAccent),
            _buildDiagItem('NETWORK BLOCK', 'HIGH PROBABILITY', Colors.redAccent),
            const Divider(color: Colors.white10, height: 32),
            Text(analysis, style: const TextStyle(color: Colors.white70, fontSize: 14, height: 1.4)),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('OK', style: TextStyle(color: AppColors.accent))),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: Colors.purpleAccent),
            onPressed: () {
              sub.sendCommand(uid, 'turbo_boost');
              Navigator.pop(context);
            },
            child: const Text('AUTO-FIX', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  Widget _buildDiagItem(String label, String value, Color color) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.white38, fontSize: 10, fontWeight: FontWeight.bold)),
          Text(value, style: TextStyle(color: color, fontSize: 10, fontWeight: FontWeight.w900)),
        ],
      ),
    );
  }
}

class TrafficWavePainter extends CustomPainter {
  final double animationValue;
  TrafficWavePainter(this.animationValue);

  @override
  void paint(Canvas canvas, Size size) {
    final paint1 = Paint()
      ..color = Colors.greenAccent.withOpacity(0.15)
      ..strokeWidth = 2.0
      ..style = PaintingStyle.stroke;

    final paint2 = Paint()
      ..color = Colors.purpleAccent.withOpacity(0.15)
      ..strokeWidth = 1.5
      ..style = PaintingStyle.stroke;

    final path1 = Path();
    final path2 = Path();

    path1.moveTo(0, size.height / 2);
    path2.moveTo(0, size.height / 2);

    for (double x = 0; x < size.width; x++) {
      final y1 = size.height / 2 + 
          (15 * math.sin((x / size.width * 2 * math.pi * 2) + animationValue * 2 * math.pi));
      final y2 = size.height / 2 + 
          (10 * math.cos((x / size.width * 2 * math.pi * 3) - animationValue * 2 * math.pi));
      path1.lineTo(x, y1);
      path2.lineTo(x, y2);
    }

    canvas.drawPath(path1, paint1);
    canvas.drawPath(path2, paint2);
  }

  @override
  bool shouldRepaint(covariant TrafficWavePainter oldDelegate) => 
      oldDelegate.animationValue != animationValue;
}
