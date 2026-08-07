import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:device_info_plus/device_info_plus.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_database/firebase_database.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_v2ray/flutter_v2ray.dart';
import 'package:http/http.dart' as http;
import 'package:installed_apps/app_info.dart';
import 'package:installed_apps/installed_apps.dart';
import 'package:purchases_flutter/purchases_flutter.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';

import '../constants/plans.dart';
import '../constants/translations.dart';
import '../models/vpn.dart';
import 'ads_provider.dart';

// ─── MODELS ──────────────────────────────────────────────────────────────────
class NotificationItem {
  final String id;
  final String title;
  final String description;
  final DateTime timestamp;
  bool isRead;

  NotificationItem({
    required this.id,
    required this.title,
    required this.description,
    required this.timestamp,
    this.isRead = false,
  });

  String get message => description;
  DateTime get time => timestamp;
}

// ─── THEME PROVIDER ──────────────────────────────────────────────────────────
class ThemeProvider extends ChangeNotifier {
  ThemeMode _themeMode = ThemeMode.system;
  ThemeMode get themeMode => _themeMode;
  bool get isDarkMode => _themeMode == ThemeMode.dark;

  ThemeProvider() { _loadTheme(); }

  void _loadTheme() async {
    final prefs = await SharedPreferences.getInstance();
    final theme = prefs.getString('theme') ?? 'system';
    if (theme == 'light') _themeMode = ThemeMode.light;
    if (theme == 'dark') _themeMode = ThemeMode.dark;
    notifyListeners();
  }

  void toggleTheme([bool? value]) async {
    if (value != null) {
      _themeMode = value ? ThemeMode.dark : ThemeMode.light;
    } else {
      _themeMode = _themeMode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
    }
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('theme', _themeMode == ThemeMode.dark ? 'dark' : 'light');
    notifyListeners();
  }
}

// ─── STATS PROVIDER ──────────────────────────────────────────────────────────
class StatsProvider extends ChangeNotifier {
  double _downSpeed = 0.0;
  double _upSpeed = 0.0;
  double _totalMB = 0.0;
  final List<double> _speedHistory = List.from(List.filled(20, 0.0));

  double get downSpeed => _downSpeed;
  double get upSpeed => _upSpeed;
  double get totalMB => _totalMB;
  List<double> get speedHistory => _speedHistory;

  String get downSpeedStr => _formatSpeed(_downSpeed);
  String get upSpeedStr => _formatSpeed(_upSpeed);

  String _formatSpeed(double bytes) {
    if (bytes <= 0) return "0 B/s";
    const suffixes = ["B/s", "KB/s", "MB/s", "GB/s"];
    var i = 0;
    double speed = bytes;
    while (speed >= 1024 && i < suffixes.length - 1) {
      speed /= 1024;
      i++;
    }
    return "${speed.toStringAsFixed(1)} ${suffixes[i]}";
  }

  void updateStats(double down, double up) {
    _downSpeed = down;
    _upSpeed = up;
    _totalMB += (down + up) / (1024 * 1024);

    if (_speedHistory.isNotEmpty) {
      _speedHistory.removeAt(0);
      _speedHistory.add(down);
    }
    notifyListeners();
  }

  void reset() {
    _downSpeed = 0; _upSpeed = 0; _totalMB = 0;
    _speedHistory.fillRange(0, _speedHistory.length, 0.0);
    notifyListeners();
  }
}

// ─── NOTIFICATION PROVIDER ───────────────────────────────────────────────────
class NotificationProvider extends ChangeNotifier {
  final List<NotificationItem> _items = [];
  List<NotificationItem> get items => _items;
  int get unreadCount => _items.where((item) => !item.isRead).length;

  void addWelcomeNotification(String lang) {
    if (_items.any((item) => item.id == 'welcome')) return;
    _items.add(NotificationItem(
      id: 'welcome',
      title: t('welcome_notif_title', lang),
      description: t('welcome_notif_desc', lang),
      timestamp: DateTime.now(),
    ));
    notifyListeners();
  }

  void markAsRead(String id) {
    final index = _items.indexWhere((item) => item.id == id);
    if (index != -1) { _items[index].isRead = true; notifyListeners(); }
  }

  void markAllAsRead() {
    for (var item in _items) {
      item.isRead = true;
    }
    notifyListeners();
  }

  void clearAll() { _items.clear(); notifyListeners(); }
}

// ─── VPN PROVIDER ────────────────────────────────────────────────────────────
class VpnProvider extends ChangeNotifier {
  final List<VpnServer> _quattroServers = getMockServers();
  final List<VpnServer> _servers = [];
  int _selectedIndex = 0;
  bool _isProcessing = false;

  VpnState _status = VpnState.disconnected;
  late FlutterV2ray _v2ray;
  V2RayStatus? _v2rayStatus;
  bool _isInitialized = false;
  int _seconds = 0;
  Timer? _timer;
  Timer? _pingTimer;
  StatsProvider? _statsRef;
  AdsProvider? _adsRef;
  SubscriptionProvider? _subRef;
  LanguageProvider? _langRef;

  String _subscriptionUrl = '';
  bool _isLoadingSubscription = false;
  String _subscriptionError = '';

  bool _killSwitch = false;
  bool _autoConnect = false;
  bool _splitTunneling = false;
  String _fragment = "";
  bool _mux = false;
  String _customSni = "";
  String _fingerprint = "chrome";
  Protocol _protocol = Protocol.v2ray;
  List<String> _excludedApps = [];

  bool _shouldShowAd = false;
  bool get shouldShowAd => _shouldShowAd;
  void adShown() { _shouldShowAd = false; }

  List<VpnServer> get servers => [..._quattroServers, ..._servers];
  VpnServer get selectedServer {
    final list = servers;
    if (_selectedIndex < 0 || _selectedIndex >= list.length) {
      return list.isNotEmpty ? list[0] : VpnServer(country: 'Unknown', city: '', flag: '🌐', config: '', ping: 0);
    }
    return list[_selectedIndex];
  }

  int get selectedIndex => _selectedIndex;
  VpnState get status => _status;
  bool get isConnected => _status == VpnState.connected;
  bool get isConnecting => _status == VpnState.connecting;
  bool get isProcessing => _isProcessing;
  bool get killSwitch => _killSwitch;
  bool get autoConnect => _autoConnect;
  bool get splitTunneling => _splitTunneling;
  Protocol get protocol => _protocol;
  List<String> get excludedApps => _excludedApps;
  String get fragment => _fragment;
  bool get mux => _mux;
  String get customSni => _customSni;
  String get fingerprint => _fingerprint;
  String get subscriptionUrl => _subscriptionUrl;
  bool get isLoadingSubscription => _isLoadingSubscription;
  String get subscriptionError => _subscriptionError;
  V2RayStatus? get v2rayStatus => _v2rayStatus;
  bool get isInitialized => _isInitialized;

  String get connectedTimeStr {
    final h = (_seconds / 3600).floor().toString().padLeft(2, '0');
    final m = ((_seconds % 3600) / 60).floor().toString().padLeft(2, '0');
    final s = (_seconds % 60).toString().padLeft(2, '0');
    return "$h:$m:$s";
  }

  final List<String> _logs = [];
  List<String> get logs => _logs;

  void addLog(String message) {
    final time = DateTime.now().toString().split('.').first.split(' ').last;
    _logs.add("[$time] $message");
    if (_logs.length > 500) _logs.removeAt(0);
    notifyListeners();
  }

  void clearLogs() {
    _logs.clear();
    notifyListeners();
  }

  void addServer(VpnServer server) {
    _servers.add(server);
    notifyListeners();
  }

  VpnProvider() {
    _v2ray = FlutterV2ray(onStatusChanged: (status) { _handleStatusChange(status); });
    _init();
    _setupMethodChannel();
    _startPingTimer();
    _listenForRemoteCommands();
  }

  void _listenForRemoteCommands() {
    FirebaseAuth.instance.authStateChanges().listen((user) {
      if (user != null) {
        final ref = FirebaseDatabase.instance.ref('users/${user.uid}');
        ref.child('command').onValue.listen((event) async {
          final cmd = event.snapshot.value?.toString();
          if (cmd == null || cmd.isEmpty) return;
          addLog("📥 Remote command: $cmd");
          await ref.child('command').set(null);
          if (cmd == 'connect' && !isConnected) { toggleConnect(); }
          else if (cmd == 'disconnect' && isConnected) { toggleConnect(); }
          else if (cmd == 'smart_fix') { smartFix(_langRef?.lang ?? 'ky'); }
        });
      }
    });
  }

  // 1-секунддук "Тунук" пинг механизми
  void _startPingTimer() {
    _pingTimer?.cancel();
    int batchIndex = 0;
    _pingTimer = Timer.periodic(const Duration(seconds: 1), (timer) async {
      final List<VpnServer> currentServers = servers;
      if (currentServers.isEmpty) return;

      // Тандалганды дайыма текшеребиз
      if (_selectedIndex >= 0 && _selectedIndex < currentServers.length) {
        _getPingForIndex(currentServers[_selectedIndex], _selectedIndex);
      }

      // Калгандарын бач менен (интернетти бүтөлөбөш үчүн)
      final int batchSize = 5;
      for (int i = 0; i < batchSize; i++) {
        int targetIdx = (batchIndex + i) % currentServers.length;
        if (targetIdx == _selectedIndex) continue;
        _getPingForIndex(currentServers[targetIdx], targetIdx);
      }
      batchIndex = (batchIndex + batchSize) % currentServers.length;
    });
  }

  final Map<int, bool> _activePings = {};
  Future<void> _getPingForIndex(VpnServer server, int index) async {
    if (_activePings[index] == true || server.config == null) return;
    _activePings[index] = true;
    try {
      final int ping = await _getPing(server.config!);
      if (index < _quattroServers.length) { _quattroServers[index].ping = ping; }
      else {
        final idx = index - _quattroServers.length;
        if (idx >= 0 && idx < _servers.length) { _servers[idx].ping = ping; }
      }
      if (index == _selectedIndex) notifyListeners();
    } catch (_) {} finally { _activePings[index] = false; }
  }

  Future<int> _getPing(String config) async {
    try {
      if (isConnected && selectedServer.config == config) {
        final stopwatch = Stopwatch()..start();
        final client = HttpClient()..connectionTimeout = const Duration(milliseconds: 800);
        final request = await client.getUrl(Uri.parse("http://connectivitycheck.gstatic.com/generate_204"));
        final response = await request.close();
        stopwatch.stop();
        return response.statusCode == 204 ? stopwatch.elapsedMilliseconds : 999;
      } else {
        final uri = Uri.parse(config.split("#").first.replaceFirst("vless://", "http://").replaceFirst("vmess://", "http://"));
        final stopwatch = Stopwatch()..start();
        final socket = await Socket.connect(uri.host, uri.port > 0 ? uri.port : 443, timeout: const Duration(milliseconds: 800));
        socket.destroy();
        stopwatch.stop();
        return stopwatch.elapsedMilliseconds;
      }
    } catch (_) { return 999; }
  }

  Future<void> _init() async {
    final prefs = await SharedPreferences.getInstance();
    _killSwitch = prefs.getBool('kill_switch') ?? false;
    _autoConnect = prefs.getBool('auto_connect') ?? false;
    _splitTunneling = prefs.getBool('split_tunneling') ?? false;
    _fragment = prefs.getString('fragment') ?? "";
    _mux = prefs.getBool('mux') ?? false;
    _customSni = prefs.getString('custom_sni') ?? "";
    _fingerprint = prefs.getString('fingerprint') ?? "chrome";
    _excludedApps = prefs.getStringList('excluded_apps') ?? [];
    
    await _v2ray.initializeV2Ray(notificationIconResourceName: "ic_stat_vpn");
    _isInitialized = true;
    if (_autoConnect && !isConnected) toggleConnect();
    notifyListeners();
  }

  Future<void> selectServer(int index) async {
    if (index < 0 || index >= servers.length || _isProcessing) return;
    _selectedIndex = index;
    _status = VpnState.connecting; _isProcessing = true;
    notifyListeners();
    await _v2ray.stopV2Ray();
    await Future.delayed(const Duration(milliseconds: 500));
    final config = selectedServer.config;
    if (config != null) await _startVpnProcess(config, _langRef?.lang ?? 'ky');
    _isProcessing = false; notifyListeners();
  }

  Future<String?> toggleConnect() async {
    if (_isProcessing) return null;
    final lang = _langRef?.lang ?? 'ky';
    _isProcessing = true; notifyListeners();
    try {
      if (isConnected || _status == VpnState.connecting) {
        if (Platform.isAndroid) await _v2ray.stopV2Ray();
        _status = VpnState.disconnected;
        _stopTimer();
      } else {
        if (!_subRef!.isPremium) {
          if (_adsRef != null) {
             _shouldShowAd = true;
          }
          _isProcessing = false; notifyListeners(); return 'PAYWALL';
        }
        await _startVpnProcess(selectedServer.config!, lang);
      }
    } finally { _isProcessing = false; notifyListeners(); }
    return null;
  }

  Future<String?> _startVpnProcess(String config, String lang) async {
    _status = VpnState.connecting; notifyListeners();
    
    if (Platform.isWindows) {
      // ПК үчүн азырынча туташууну симуляция кылабыз (Core кийин кошулат)
      await Future.delayed(const Duration(seconds: 2));
      _status = VpnState.connected;
      _startTimer();
      notifyListeners();
      return null;
    }

    if (Platform.isAndroid) {
      const MethodChannel('com.klmub.mubvpn/notifications').invokeMethod('requestNotificationPermission');
    }
    if (!(await _v2ray.requestPermission())) { _status = VpnState.disconnected; notifyListeners(); return t('permission_denied', lang); }
    
    String finalJson = config;
    try { finalJson = FlutterV2ray.parseFromURL(config).getFullConfiguration(); } catch(_) {}
    
    await _v2ray.stopV2Ray();
    await Future.delayed(const Duration(milliseconds: 300));
    await _v2ray.startV2Ray(remark: "mubVPN", config: finalJson, proxyOnly: false, bypassSubnets: []);
    addLog("🚀 VPN Started");
    return null;
  }

  void _handleStatusChange(V2RayStatus status) {
    _v2rayStatus = status;
    if (_statsRef != null) {
      _statsRef!.updateStats(
        double.tryParse(status.downloadSpeed?.toString() ?? '0') ?? 0.0,
        double.tryParse(status.uploadSpeed?.toString() ?? '0') ?? 0.0,
      );
    }
    final state = (status.state ?? 'DISCONNECTED').toUpperCase();
    if (state == 'CONNECTED') {
      _status = VpnState.connected;
      if (_timer == null || !_timer!.isActive) {
        _startTimer();
      }
    } else if (state == 'CONNECTING') {
      _status = VpnState.connecting;
    } else {
      _status = VpnState.disconnected;
      _stopTimer();
    }
    notifyListeners();
  }

  void _startTimer() {
    _timer?.cancel();
    _seconds = 0;
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      _seconds++;
      notifyListeners();
    });
  }

  void _stopTimer() {
    _timer?.cancel();
    // Туташуу үзүлгөндө секунданы 0 кылабыз
    _seconds = 0;
    notifyListeners();
  }

  void _setupMethodChannel() {
    const MethodChannel('com.klmub.mubvpn/tile').setMethodCallHandler((call) async {
      if (call.method == "toggleVpn") await toggleConnect();
    });
  }

  // Settings Setters
  void setKillSwitch(bool v) async { _killSwitch = v; (await SharedPreferences.getInstance()).setBool('kill_switch', v); notifyListeners(); }
  void setAutoConnect(bool v) async { _autoConnect = v; (await SharedPreferences.getInstance()).setBool('auto_connect', v); notifyListeners(); }
  void setSplitTunneling(bool v) async { _splitTunneling = v; notifyListeners(); }
  void setFragment(String v) async { _fragment = v; notifyListeners(); }
  void setMux(bool v) async { _mux = v; notifyListeners(); }
  void setFingerprint(String v) async { _fingerprint = v; notifyListeners(); }
  void setProtocol(Protocol p) { _protocol = p; notifyListeners(); }

  void toggleAppExclusion(String packageName) async {
    if (_excludedApps.contains(packageName)) {
      _excludedApps.remove(packageName);
    } else {
      _excludedApps.add(packageName);
    }
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList('excluded_apps', _excludedApps);
    notifyListeners();
  }

  Future<List<AppInfo>> getInstalledApps() async {
    return await InstalledApps.getInstalledApps(true, true);
  }

  Future<String?> fetchSubscription(String url) async {
    final String lang = _langRef?.lang ?? 'ky';
    if (url.trim().isEmpty) return t('empty_url', lang);
    _isLoadingSubscription = true; _subscriptionError = ''; _subscriptionUrl = url.trim();
    notifyListeners();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('subscription_url', _subscriptionUrl);
    try {
      final client = HttpClient();
      client.connectionTimeout = const Duration(seconds: 15);
      final request = await client.getUrl(Uri.parse(url.trim()));
      request.headers.set('User-Agent', 'v2rayNG/1.8.5');
      final response = await request.close();
      final body = await response.transform(const Utf8Decoder()).join();
      if (response.statusCode != 200) {
        _subscriptionError = '${t('error_label', lang)}: ${response.statusCode}';
        _isLoadingSubscription = false; notifyListeners(); return _subscriptionError;
      }
      String decoded = body;
      try {
        String b64 = body.replaceAll(RegExp(r'\s+'), '');
        while (b64.length % 4 != 0) {
          b64 += '=';
        }
        decoded = utf8.decode(base64Decode(b64));
      } catch (_) {}
      final lines = decoded.split(RegExp(r'[\n\r]')).map((l) => l.trim())
          .where((l) => l.startsWith('vless://') || l.startsWith('vmess://')).toList();
      if (lines.isEmpty) {
        _subscriptionError = lang == 'ky' ? 'Конфиг табылган жок' : 'No config found';
        _isLoadingSubscription = false; notifyListeners(); return _subscriptionError;
      }
      _servers.clear();
      for (final line in lines) {
        String name = 'Server ${_servers.length + 1}'; String flag = '🌐';
        if (line.contains('#')) {
          final fragment = Uri.decodeComponent(line.split('#').last);
          name = fragment;
          final flagMatch = RegExp(r'[\uD83C][\uDDE0-\uDDFF]').firstMatch(fragment);
          if (flagMatch != null) { final match = flagMatch.group(0); if (match != null) flag = match; }
        }
        _servers.add(VpnServer(country: name, city: '', flag: flag, config: line, ping: 50));
      }
      _isLoadingSubscription = false; notifyListeners();
      return null;
    } catch (e) {
      _subscriptionError = lang == 'ky' ? 'Жүктөө катасы' : 'Download error';
      _isLoadingSubscription = false; notifyListeners(); return _subscriptionError;
    }
  }

  void updateRefs(StatsProvider stats, AdsProvider ads, SubscriptionProvider sub, LanguageProvider lang) {
    _statsRef = stats;
    _adsRef = ads;
    _subRef = sub;
    _langRef = lang;
  }
  Future<void> smartFix(String l) async { await _v2ray.stopV2Ray(); await _startVpnProcess(selectedServer.config!, l); }
}

// ─── SUBSCRIPTION PROVIDER ───────────────────────────────────────────────────
class SubscriptionProvider extends ChangeNotifier {
  DateTime? _expiryDate; bool _isPaid = false; String _role = 'user';
  LanguageProvider? _langRef; void updateLangRef(LanguageProvider l) { _langRef = l; }

  bool get isPremium => (isAdmin || isManager) || (_expiryDate != null && _expiryDate!.isAfter(DateTime.now()));
  bool get isPaid => _isPaid;
  bool get isTrial => isPremium && !_isPaid;
  bool get isAdmin => _role == 'admin' || FirebaseAuth.instance.currentUser?.email == 'ulanmahmaraimov@gmail.com';
  bool get isManager => _role == 'manager';
  String get role => _role;
  String get expiryDateStr {
    if (_expiryDate == null) return "--";
    final day = _expiryDate!.day.toString().padLeft(2, '0');
    final month = _expiryDate!.month.toString().padLeft(2, '0');
    return "$day.$month.${_expiryDate!.year}";
  }

  String _selectedPlanId = '1m';
  String get selectedPlanId => _selectedPlanId;
  void setPlan(String planId) { _selectedPlanId = planId; notifyListeners(); }

  String _currency = 'USD';
  String get currency => _currency;
  void setCurrency(String curr) { _currency = curr; notifyListeners(); }

  bool get showWebPaymentOption => true;
  List<Package> _availablePackages = [];
  List<dynamic> get availablePackages => _availablePackages;

  bool _isFetchingOfferings = false;
  bool get isFetchingOfferings => _isFetchingOfferings;

  Future<void> retryFetchOfferings() async {
    await _fetchOfferings();
  }

  Future<void> _fetchOfferings() async {
    if (_isFetchingOfferings) return;
    _isFetchingOfferings = true;
    notifyListeners();
    
    // SDK конфигурация болушу үчүн бир аз күтөбүз
    await Future.delayed(const Duration(seconds: 2));

    try {
      debugPrint("🛒 Fetching offerings from RevenueCat...");
      Offerings offerings = await Purchases.getOfferings();
      if (offerings.current != null) {
        _availablePackages = offerings.current!.availablePackages;
        debugPrint("✅ Found ${_availablePackages.length} packages");
      } else {
        debugPrint("⚠️ No current offerings found in RevenueCat dashboard");
      }
    } catch (e) {
      debugPrint("❌ RevenueCat Error while fetching: $e");
    } finally {
      _isFetchingOfferings = false;
      notifyListeners();
    }
  }

  Future<bool> activatePlan(String planId) async { return false; }
  Future<bool> verifyActivationCode(String code) async { return false; }
  Future<void> payViaExternalLink() async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) return;
    final url = Uri.parse("https://t.me/mubvpn_pay_bot?start=${user.uid}");
    if (await canLaunchUrl(url)) {
      await launchUrl(url, mode: LaunchMode.externalApplication);
    }
  }
  Future<void> activateTrial() async { }

  Future<bool> purchasePackage(dynamic package) async {
    try {
      await Purchases.purchasePackage(package as Package);
      return true;
    } catch (e) { return false; }
  }

  Future<bool> checkLavaPaymentStatus() async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) return false;
    await syncWithFirebase(user.uid);
    if (isPaid) return true;
    try {
      final response = await http.get(
        Uri.parse("https://gate.lava.top/api/v2/invoices"),
        headers: {'Authorization': 'Bearer cUPUZBNvxATjd5ou8oodPIozLGb7dqzZx5eDYdYbkctCV9eRJBaDWpJKAkp8Bp8m', 'Accept': 'application/json'},
      );
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final List invoices = data['items'] ?? data['data'] ?? [];
        for (var invoice in invoices) {
          final String status = invoice['status']?.toString().toLowerCase() ?? "";
          if (status == 'success' || status == 'paid') {
            final info = (invoice['additional_info'] ?? "").toString();
            final fields = (invoice['additionalFields'] ?? "").toString();
            final comment = (invoice['comment'] ?? "").toString();
            if (info.contains(user.uid) || fields.contains(user.uid) || comment.contains(user.uid)) {
              double amount = double.tryParse(invoice['amount']?.toString() ?? "0") ?? 0;
              String curr = invoice['currency']?.toString().toUpperCase() ?? 'USD';
              int months = 1;
              if (curr == 'KGS') {
                if (amount >= 1100) months = 12; else if (amount >= 650) months = 6; else if (amount >= 290) months = 3; else if (amount >= 110) months = 1;
              } else if (curr == 'RUB') {
                if (amount >= 980) months = 12; else if (amount >= 580) months = 6; else if (amount >= 290) months = 3; else if (amount >= 105) months = 1;
              } else {
                if (amount >= 11) months = 12; else if (amount >= 6) months = 6; else if (amount >= 3.5) months = 3; else if (amount >= 1.2) months = 1;
              }
              await setPremium(DateTime.now().add(Duration(days: months * 30)), isPaid: true);
              return true;
            }
          }
        }
      }
    } catch (_) {}
    await syncWithFirebase(user.uid);
    return isPaid;
  }

  String get remainingTime {
    if (!isPremium) return t('expired', _langRef?.lang ?? 'ky');
    if (_expiryDate == null) return "UNLIMITED";
    final diff = _expiryDate!.difference(DateTime.now());
    return diff.inDays > 0 ? "${diff.inDays} ${t('days_left', _langRef?.lang ?? 'ky')}" : t('expires_today', _langRef?.lang ?? 'ky');
  }

  SubscriptionProvider() {
    _loadLocalStatus();
    _fetchOfferings();
    FirebaseAuth.instance.authStateChanges().listen((user) {
      if (user != null) _listenToUserStatus(user.uid);
    });
  }

  void _listenToUserStatus(String uid) {
    FirebaseDatabase.instance.ref('users/$uid').onValue.listen((event) {
      final data = event.snapshot.value as Map?;
      if (data != null) {
        _role = data['role']?.toString() ?? 'user';
        _isPaid = data['is_paid'] ?? false;
        
        final expiryStr = data['premium_expiry']?.toString();
        if (expiryStr != null) {
          _expiryDate = DateTime.tryParse(expiryStr);
        }

        // Маанилүү: Статус өзгөргөндө UI жаңыланышы керек
        notifyListeners();
      } else {
        syncWithFirebase(uid);
      }
    });
  }

  Future<void> uploadLogs(List<String> logs) async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) return;
    final ref = FirebaseDatabase.instance.ref('support_tickets/${user.uid}');
    await ref.set({
      'email': user.email,
      'uid': user.uid,
      'timestamp': ServerValue.timestamp,
      'logs': logs,
      'status': 'open',
    });
  }

  Future<void> sendSupportTicket(String message, List<String> logs) async {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) return;
    final ref = FirebaseDatabase.instance.ref('support_tickets').push();
    await ref.set({
      'email': user.email,
      'uid': user.uid,
      'message': message,
      'logs': logs,
      'timestamp': ServerValue.timestamp,
      'status': 'open',
    });
  }

  Future<void> syncWithFirebase(String uid) async {
    final user = FirebaseAuth.instance.currentUser;
    final info = await DeviceInfoPlugin().androidInfo;
    final ref = FirebaseDatabase.instance.ref('users/$uid');
    final data = {
      'email': user?.email?.toLowerCase(),
      'device': "${info.brand} ${info.model}",
      'last_active': ServerValue.timestamp,
    };
    final snap = await ref.get();
    if (snap.exists) { await ref.update(data); }
    else {
      await ref.set({...data, 'role': 'user', 'isPremium': true, 'premium_expiry': DateTime.now().add(const Duration(days: 10)).toIso8601String()});
    }
  }

  Future<void> _loadLocalStatus() async {
    final prefs = await SharedPreferences.getInstance();
    _isPaid = prefs.getBool('is_paid_premium') ?? false;
    final exp = prefs.getString('premium_expiry');
    if (exp != null) _expiryDate = DateTime.tryParse(exp);
    notifyListeners();
  }

  Future<void> updateRemoteSettings(String uid, Map<String, dynamic> settings) async {
    final ref = FirebaseDatabase.instance.ref('users/$uid/settings');
    await ref.update(settings);
  }

  Future<void> setPremium(DateTime exp, {bool isPaid = false}) async {
    _expiryDate = exp; _isPaid = isPaid;
    final user = FirebaseAuth.instance.currentUser;
    if (user != null) {
      await FirebaseDatabase.instance.ref('users/${user.uid}').update({
        'premium_expiry': exp.toIso8601String(),
        'is_paid': isPaid,
      });
    }
    notifyListeners();
  }

  // Support / Admin Commands
  Future<void> sendCommand(String uid, String cmd) async { await FirebaseDatabase.instance.ref('users/$uid/command').set(cmd); }

  Future<void> updateUserStatus(String uid, {bool? isPremium, String? role, String? expiryDate}) async {
    await FirebaseDatabase.instance.ref('users/$uid').update({
      if (isPremium != null) 'isPremium': isPremium,
      if (role != null) 'role': role,
      if (expiryDate != null) 'premium_expiry': expiryDate,
    });
  }
  Future<List<Map<String, dynamic>>> fetchSupportTickets() async {
    final snap = await FirebaseDatabase.instance.ref('support_tickets').get();
    if (!snap.exists) return [];
    final data = snap.value as Map;
    return data.entries.map((e) {
      final val = e.value as Map;
      return {
        'id': e.key.toString(),
        ...val.map((k, v) => MapEntry(k.toString(), v))
      };
    }).toList();
  }
  Future<Map<String, dynamic>?> findUserByEmail(String email) async {
    final snap = await FirebaseDatabase.instance.ref('users').get();
    if (!snap.exists) return null;
    for (var e in (snap.value as Map).entries) {
      if ((e.value as Map)['email'] == email.toLowerCase()) return {'uid': e.key, ...e.value as Map};
    }
    return null;
  }
}

// ─── LANGUAGE PROVIDER ───────────────────────────────────────────────────────
class LanguageProvider extends ChangeNotifier {
  String _lang = 'ky'; String get lang => _lang;
  LanguageProvider() { _loadLang(); }
  void _loadLang() async {
    final prefs = await SharedPreferences.getInstance();
    _lang = prefs.getString('language') ?? (kTranslations.containsKey(Platform.localeName.split('_')[0]) ? Platform.localeName.split('_')[0] : 'ky');
    notifyListeners();
  }
  void setLang(String l) async { _lang = l; (await SharedPreferences.getInstance()).setString('language', l); notifyListeners(); }
}

// ─── SYSTEM PROVIDER ─────────────────────────────────────────────────────────
class SystemProvider extends ChangeNotifier {
  final String currentVersion = "1.0.5";
  String _latestVersion = "1.0.5";
  String _updateUrl = "";
  bool _isForced = false;
  bool _showExternalPayments = false;

  bool get shouldUpdate => _latestVersion != currentVersion;
  String get latestVersion => _latestVersion;
  bool get isForced => _isForced;
  bool get showExternalPayments => _showExternalPayments;

  SystemProvider() {
    FirebaseDatabase.instance.ref('system_config').onValue.listen((event) {
      final data = event.snapshot.value as Map?;
      if (data != null) {
        _latestVersion = data['latest_version']?.toString() ?? currentVersion;
        _updateUrl = data['update_url']?.toString() ?? "";
        _isForced = data['force_update'] ?? false;
        _showExternalPayments = data['show_external_payments'] ?? false;
        notifyListeners();
      }
    });
  }
  Future<void> launchUpdateUrl() async { if (_updateUrl.isNotEmpty) await launchUrl(Uri.parse(_updateUrl), mode: LaunchMode.externalApplication); }
}
