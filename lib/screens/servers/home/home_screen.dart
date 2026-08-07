
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../../../constants/translations.dart';
import '../../../providers/providers.dart';
import '../../../providers/ads_provider.dart';
import 'package:flutter/services.dart';
import '../../../models/vpn.dart';
import 'dart:io';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with TickerProviderStateMixin {
  AnimationController? _pulseCtrl;
  AnimationController? _bgCtrl;

  bool _isUpdateDialogShowing = false;

  @override
  void initState() {
    super.initState();
    _pulseCtrl = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);

    _bgCtrl = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 10),
    )..repeat(reverse: true);

    // Жаңыртууну бир жолу гана текшерүү
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final system = Provider.of<SystemProvider>(context, listen: false);
      final lang = Provider.of<LanguageProvider>(context, listen: false).lang;
      if (system.shouldUpdate) {
        _showUpdateDialog(context, system, lang);
      }
    });
  }

  void _showUpdateDialog(BuildContext context, SystemProvider system, String lang) {
    if (_isUpdateDialogShowing) return;
    _isUpdateDialogShowing = true;

    showDialog(
      context: context,
      barrierDismissible: !system.isForced,
      builder: (context) => PopScope(
        canPop: !system.isForced,
        child: AlertDialog(
          backgroundColor: const Color(0xFF131B24),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
          title: Text(
            t('update_available_title', lang),
            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.system_update_rounded, size: 64, color: Color(0xFF00FF94)),
              const SizedBox(height: 16),
              Text(
                t('update_available_desc', lang),
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.white.withValues(alpha: 0.8), fontSize: 16),
              ),
              const SizedBox(height: 8),
              Text(
                "${t('version', lang)}: ${system.latestVersion}",
                style: const TextStyle(color: Color(0xFF00FF94), fontWeight: FontWeight.bold),
              ),
            ],
          ),
          actions: [
            if (!system.isForced)
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: Text(t('later_btn', lang), style: TextStyle(color: Colors.white.withValues(alpha: 0.6))),
              ),
            ElevatedButton(
              onPressed: () => system.launchUpdateUrl(),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF00FF94),
                foregroundColor: Colors.black,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
              child: Text(t('update_btn', lang), style: const TextStyle(fontWeight: FontWeight.bold)),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _pulseCtrl?.dispose();
    _bgCtrl?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final vpn = context.watch<VpnProvider>();
    final stats = context.watch<StatsProvider>();
    final sub = context.watch<SubscriptionProvider>();
    final lang = context.watch<LanguageProvider>().lang;
    final isConnected = vpn.status == VpnState.connected;
    final isConnecting = vpn.status == VpnState.connecting;

    // Жарнама көрсөтүү (ар бир 30 мүнөт сайын)
    if (vpn.shouldShowAd && sub.isTrial) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        context.read<AdsProvider>().showAdBeforeConnect(onFinished: () {
           vpn.adShown();
        });
      });
    }

    final size = MediaQuery.of(context).size;

    return Scaffold(
      backgroundColor: const Color(0xFF060A0E),
      body: Stack(
        clipBehavior: Clip.none,
        children: [
          Container(color: const Color(0xFF06090D)),
          AnimatedBuilder(
            animation: _bgCtrl ?? const AlwaysStoppedAnimation(0.0),
            builder: (_, __) {
              final t = _bgCtrl?.value ?? 0.0;
              return Stack(
                clipBehavior: Clip.none,
                children: [
                  Positioned(
                    top: -size.height * 0.08 + 30 * t,
                    right: -size.width * 0.25 + 20 * t,
                    child: Container(
                      width: size.width * 0.95,
                      height: size.width * 0.95,
                      decoration: const BoxDecoration(
                        shape: BoxShape.circle,
                        gradient: LinearGradient(
                          begin: Alignment.topRight,
                          end: Alignment.bottomLeft,
                          colors: [Color(0xFF165B40), Color(0xFF09291C)],
                        ),
                      ),
                    ),
                  ),
                ],
              );
            },
          ),
          SafeArea(
            child: Column(
              children: [
                _buildAppBar(context, sub),
                if (!sub.isPremium) _buildPremiumUpgradeBanner(context, lang),
                Expanded(
                  child: SingleChildScrollView(
                    physics: const BouncingScrollPhysics(),
                    padding: const EdgeInsets.symmetric(horizontal: 24),
                    child: Column(
                      children: [
                        const SizedBox(height: 16),
                        _buildStatusBadge(context, vpn, isConnected, lang, vpn.connectedTimeStr),
                        const SizedBox(height: 40),
                        _buildPowerButton(vpn, isConnected, isConnecting),
                        const SizedBox(height: 52),
                        _buildSpeedCard(stats, lang),
                        const SizedBox(height: 16),
                        _buildServerCard(context, vpn),
                        const SizedBox(height: 120),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // ────────────────────────── APP BAR ──────────────────────────
  Widget _buildAppBar(BuildContext context, SubscriptionProvider sub) {
    final notif = context.watch<NotificationProvider>();
    final lang = context.watch<LanguageProvider>().lang;
    return Padding(
      padding: const EdgeInsets.fromLTRB(22, 14, 22, 8),
      child: Row(
        children: [
          Container(
            width: 44, height: 44,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(13),
              gradient: const LinearGradient(
                colors: [Color(0xFF00E5A0), Color(0xFF00896A)],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF00C896).withValues(alpha: 0.35),
                  blurRadius: 14,
                  offset: const Offset(0, 5),
                ),
              ],
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(13),
              child: Image.asset(
                'assets/logo.jpg',
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => const Icon(
                  Icons.shield_rounded, color: Colors.white, size: 26),
              ),
            ),
          ),
          const SizedBox(width: 13),
          Expanded(
            child: GestureDetector(
              onTap: () {
                final user = FirebaseAuth.instance.currentUser;
                if (user != null) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text(t('syncing_status', lang)), duration: const Duration(seconds: 1)),
                  );
                  context.read<SubscriptionProvider>().syncWithFirebase(user.uid);
                } else {
                  Navigator.pushNamed(context, '/paywall');
                }
              },
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('mubVPN',
                      style: TextStyle(
                        color: Colors.white, fontSize: 21,
                        fontWeight: FontWeight.w800, letterSpacing: 0.3,
                      ),
                      overflow: TextOverflow.ellipsis),
                  Text(sub.isPremium ? 'PREMIUM • ${sub.remainingTime}' : 'FREE PLAN • Tap to sync',
                      style: TextStyle(
                        color: sub.isPremium ? const Color(0xFF00E5A0) : const Color(0xFF4A7A65), 
                        fontSize: 11,
                        fontWeight: sub.isPremium ? FontWeight.bold : FontWeight.normal
                      ),
                      overflow: TextOverflow.ellipsis),
                ],
              ),
            ),
          ),
          const SizedBox(width: 8),
          GestureDetector(
            onTap: () => Navigator.pushNamed(context, '/notifications'),
            child: Stack(
              children: [
                Container(
                  width: 44, height: 44,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: Colors.white.withValues(alpha: 0.07),
                    border: Border.all(
                      color: Colors.white.withValues(alpha: 0.12), width: 1),
                  ),
                  child: const Icon(Icons.notifications_none_rounded,
                      color: Colors.white, size: 22),
                ),
                if (notif.unreadCount > 0)
                  Positioned(
                    right: 0, top: 0,
                    child: Container(
                      width: 16, height: 16,
                      decoration: BoxDecoration(
                        color: const Color(0xFFFF3B30),
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: const Color(0xFF060A0E), width: 2),
                      ),
                      child: Center(
                        child: Text('${notif.unreadCount}',
                            style: const TextStyle(
                              color: Colors.white, fontSize: 9,
                              fontWeight: FontWeight.bold)),
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPremiumUpgradeBanner(BuildContext context, String lang) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
      child: GestureDetector(
        onTap: () => Navigator.pushNamed(context, '/paywall'),
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              colors: [Color(0xFFFFD700), Color(0xFFB8860B)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            borderRadius: BorderRadius.circular(20),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.2),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          child: Row(
            children: [
              const Icon(Icons.stars_rounded, color: Colors.black, size: 28),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      t('premium_upgrade', lang),
                      style: const TextStyle(color: Colors.black, fontWeight: FontWeight.w900, fontSize: 14),
                    ),
                    Text(
                      t('premium_subtitle', lang),
                      style: const TextStyle(color: Colors.black54, fontSize: 11, fontWeight: FontWeight.w600),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.arrow_forward_ios_rounded, color: Colors.black54, size: 14),
            ],
          ),
        ),
      ),
    );
  }

  // ────────────────────────── СТАТУС ──────────────────────────
  Widget _buildStatusBadge(BuildContext context, VpnProvider vpn, bool isConnected, String lang, String? timeStr) {
    final color = isConnected ? const Color(0xFF00E5A0) : const Color(0xFFFF3B30);
    
    String statusText = isConnected 
        ? t('protected', lang).toUpperCase() 
        : t('not_protected', lang).toUpperCase();
        
    String text = isConnected ? '$statusText • ${timeStr ?? "00:00:00"}' : statusText;
    
    final sub = context.read<SubscriptionProvider>();
    if (isConnected && sub.isTrial) {
      text += ' (TRIAL)';
    }

    return GestureDetector(
      onTap: () => _showDiagnosticsSheet(context, vpn),
      child: AnimatedBuilder(
        animation: _pulseCtrl ?? const AlwaysStoppedAnimation(0.0),
        builder: (_, __) => Container(
          padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.08),
            borderRadius: BorderRadius.circular(30),
            border: Border.all(color: color.withValues(alpha: 0.25), width: 1.2),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                width: 8, height: 8,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: color,
                  boxShadow: [
                    BoxShadow(
                      color: color.withValues(alpha: 0.7 * (_pulseCtrl?.value ?? 0.0)),
                      blurRadius: 10 * (_pulseCtrl?.value ?? 0.0),
                      spreadRadius: 2 * (_pulseCtrl?.value ?? 0.0),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 10),
              Flexible(
                child: Text(
                  text,
                  style: TextStyle(
                    color: color, fontSize: 12,
                    fontWeight: FontWeight.w700, letterSpacing: 1.8,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showDiagnosticsSheet(BuildContext context, VpnProvider vpn) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (context) {
        return StatefulBuilder(
          builder: (context, setModalState) {
            return Container(
              height: MediaQuery.of(context).size.height * 0.7,
              decoration: const BoxDecoration(
                color: Color(0xFF0B1219),
                borderRadius: BorderRadius.vertical(top: Radius.circular(32)),
                border: Border(top: BorderSide(color: Colors.white10, width: 1.5)),
              ),
              child: Column(
                children: [
                  const SizedBox(height: 12),
                  Container(width: 48, height: 5, decoration: BoxDecoration(color: Colors.white24, borderRadius: BorderRadius.circular(10))),
                  const SizedBox(height: 16),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 24),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('MubVPN Diagnostics', style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
                        Row(
                          children: [
                            IconButton(
                              icon: const Icon(Icons.copy_all, color: Color(0xFF00E5A0)),
                              onPressed: () {
                                Clipboard.setData(ClipboardData(text: vpn.logs.join('\n')));
                                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Logs copied!')));
                              },
                            ),
                            IconButton(icon: const Icon(Icons.refresh, color: Colors.white), onPressed: () => setModalState(() {})),
                          ],
                        ),
                      ],
                    ),
                  ),
                  const Divider(color: Colors.white10, height: 24),
                  Expanded(
                    child: ListView.builder(
                      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
                      itemCount: vpn.logs.length,
                      itemBuilder: (context, idx) {
                        final log = vpn.logs[idx];
                        Color color = Colors.white70;
                        if (log.contains('🟢')) color = const Color(0xFF00E5A0);
                        else if (log.contains('❌')) color = const Color(0xFFFF3B30);
                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          child: Text(log, style: TextStyle(color: color, fontSize: 12, fontFamily: 'monospace')),
                        );
                      },
                    ),
                  ),
                  Padding(
                    padding: const EdgeInsets.all(24),
                    child: ElevatedButton.icon(
                      onPressed: () async {
                        await vpn.smartFix(context.read<LanguageProvider>().lang);
                        setModalState(() {});
                      },
                      icon: const Icon(Icons.build_circle_outlined, color: Colors.black),
                      label: const Text('Smart Fix', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.black)),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF00E5A0),
                        minimumSize: const Size(double.infinity, 56),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                      ),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }

  Widget _buildPowerButton(VpnProvider vpn, bool isConnected, bool isConnecting) {
    const accent = Color(0xFF00E5A0);
    return GestureDetector(
      onTap: vpn.isProcessing ? null : () async {
        final error = await vpn.toggleConnect();
        if (error == 'PAYWALL' && mounted) Navigator.pushNamed(context, '/paywall');
        else if (error != null && mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(error), backgroundColor: Colors.redAccent));
      },
      child: AnimatedBuilder(
        animation: _pulseCtrl ?? const AlwaysStoppedAnimation(0.0),
        builder: (_, __) => SizedBox(
          width: 210, height: 210,
          child: Stack(
            alignment: Alignment.center,
            children: [
              if (isConnected)
                Container(
                  width: 210 * (1 + 0.04 * (_pulseCtrl?.value ?? 0.0)),
                  height: 210 * (1 + 0.04 * (_pulseCtrl?.value ?? 0.0)),
                  decoration: BoxDecoration(shape: BoxShape.circle, boxShadow: [BoxShadow(color: accent.withValues(alpha: 0.25 * (_pulseCtrl?.value ?? 0.0)), blurRadius: 60, spreadRadius: 15)]),
                ),
              Container(width: 210, height: 210, decoration: BoxDecoration(shape: BoxShape.circle, border: Border.all(color: Colors.white.withValues(alpha: 0.06)))),
              Container(width: 185, height: 185, decoration: BoxDecoration(shape: BoxShape.circle, border: Border.all(color: Colors.white.withValues(alpha: 0.04)))),
              Container(
                width: 158, height: 158,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: RadialGradient(center: const Alignment(-0.3, -0.3), colors: isConnected ? [const Color(0xFF0F2018), const Color(0xFF060A0E)] : [const Color(0xFF14202C), const Color(0xFF060A0E)]),
                  border: Border.all(color: isConnected ? accent.withValues(alpha: 0.55) : Colors.white.withValues(alpha: 0.10), width: 1.8),
                  boxShadow: [BoxShadow(color: Colors.black.withValues(alpha: 0.6), blurRadius: 25, spreadRadius: 4), if (isConnected) BoxShadow(color: accent.withValues(alpha: 0.25), blurRadius: 40, spreadRadius: 8)],
                ),
                child: Center(
                  child: (isConnecting || vpn.isProcessing)
                      ? const SizedBox(width: 55, height: 55, child: CircularProgressIndicator(color: accent, strokeWidth: 2.5))
                      : Icon(Icons.power_settings_new_rounded, size: 70, color: isConnected ? accent : Colors.white.withValues(alpha: 0.18)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatSpeed(double bytes) {
    if (bytes < 1024) return "${bytes.toInt()} B/s";
    if (bytes < 1024 * 1024) return "${(bytes / 1024).toStringAsFixed(1)} KB/s";
    return "${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB/s";
  }

  Widget _buildSpeedCard(StatsProvider stats, String lang) {
    return _glassCard(child: Row(
      children: [
        Expanded(child: _speedCol(Icons.arrow_downward_rounded, t('download', lang).toUpperCase(), _formatSpeed(stats.downSpeed), const Color(0xFF00E5A0))),
        Container(width: 1, height: 44, decoration: BoxDecoration(gradient: LinearGradient(begin: Alignment.topCenter, end: Alignment.bottomCenter, colors: [Colors.transparent, Colors.white.withValues(alpha: 0.10), Colors.transparent]))),
        Expanded(child: _speedCol(Icons.arrow_upward_rounded, t('upload', lang).toUpperCase(), _formatSpeed(stats.upSpeed), const Color(0xFF5CB8FF))),
      ],
    ));
  }

  Widget _speedCol(IconData icon, String label, String val, Color color) {
    return Column(children: [
      Row(mainAxisAlignment: MainAxisAlignment.center, children: [
        Icon(icon, color: color, size: 12),
        const SizedBox(width: 4),
        Flexible(child: Text(label, style: TextStyle(color: Colors.white.withValues(alpha: 0.38), fontSize: 9, fontWeight: FontWeight.w700, letterSpacing: 0.5), overflow: TextOverflow.ellipsis))
      ]),
      const SizedBox(height: 6),
      FittedBox(
        fit: BoxFit.scaleDown,
        child: Text(val, style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.w800)),
      ),
    ]);
  }

  Widget _buildServerCard(BuildContext context, VpnProvider vpn) {
    final server = vpn.selectedServer;
    final lang = context.watch<LanguageProvider>().lang;
    return GestureDetector(
      onTap: () => Navigator.pushNamed(context, '/servers'),
      child: _glassCard(child: Row(children: [
        Container(
          width: 48, height: 48,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            color: Colors.white.withValues(alpha: 0.06),
            border: Border.all(color: Colors.white.withValues(alpha: 0.09))
          ),
          child: Center(child: Text(server.flag, style: const TextStyle(fontSize: 24)))
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                server.localizedCity(lang),
                style: const TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.w700),
                overflow: TextOverflow.ellipsis,
                maxLines: 1,
              ),
              const SizedBox(height: 2),
              Row(
                children: [
                  Flexible(
                    child: Text(
                      server.localizedCountry(lang),
                      style: TextStyle(color: Colors.white.withValues(alpha: 0.38), fontSize: 11),
                      overflow: TextOverflow.ellipsis,
                      maxLines: 1,
                    ),
                  ),
                  const SizedBox(width: 6),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                    decoration: BoxDecoration(
                      color: server.loadColor.withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      server.ping > 0 ? "${server.ping} ms" : "--",
                      style: TextStyle(color: server.loadColor, fontSize: 8, fontWeight: FontWeight.bold),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(width: 8),
        Icon(Icons.unfold_more_rounded, color: Colors.white.withValues(alpha: 0.3), size: 18),
      ])),
    );
  }

  Widget _glassCard({required Widget child}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
      decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.03), borderRadius: BorderRadius.circular(26), border: Border.all(color: Colors.white.withValues(alpha: 0.06))),
      child: child,
    );
  }
}
