import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../constants/colors.dart';
import '../constants/translations.dart';
import '../models/vpn.dart';
import '../providers/providers.dart';
import 'settings/admin_terminal_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with SingleTickerProviderStateMixin {
  late AnimationController _pulseController;

  @override
  void initState() {
    super.initState();
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _pulseController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final vpn = context.watch<VpnProvider>();
    final sub = context.watch<SubscriptionProvider>();
    final lang = context.watch<LanguageProvider>().lang;

    return Scaffold(
      backgroundColor: const Color(0xFF030303),
      body: Stack(
        children: [
          // Animated Mesh Gradient Background
          _AnimatedBackground(status: vpn.status),
          
          SafeArea(
            child: Column(
              children: [
                _buildAppBar(context, sub, lang),
                if (!sub.isPremium) _buildPremiumBanner(context, lang),
                const Spacer(),
                _buildMainButton(vpn, lang),
                const Spacer(),
                _buildServerSelector(context, vpn, lang),
                const SizedBox(height: 30),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAppBar(BuildContext context, SubscriptionProvider sub, String lang) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      child: Row(
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: Container(
              decoration: BoxDecoration(
                boxShadow: [
                  BoxShadow(color: AppColors.accent.withValues(alpha: 0.3), blurRadius: 15, spreadRadius: 2)
                ],
              ),
              child: Image.asset(
                'assets/logo.jpg',
                width: 44,
                height: 42,
                fit: BoxFit.cover,
                errorBuilder: (context, error, stackTrace) => Container(
                  width: 44,
                  height: 42,
                  color: AppColors.accent,
                  child: const Icon(Icons.security, color: Colors.black),
                ),
              ),
            ),
          ),
          const SizedBox(width: 15),
          Expanded(
            child: GestureDetector(
              onTap: () => Navigator.pushNamed(context, '/paywall'),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('mubVPN', style: TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.w900, letterSpacing: -1)),
                  Row(
                    children: [
                      Text(sub.isPremium ? 'PREMIUM ACCESS' : 'FREE PLAN', 
                          style: TextStyle(color: sub.isPremium ? AppColors.accent : Colors.white54, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1.5)),
                      if (!sub.isPremium) ...[
                        const SizedBox(width: 4),
                        const Icon(Icons.stars_rounded, color: AppColors.gold, size: 12),
                      ]
                    ],
                  ),
                ],
              ),
            ),
          ),
          _buildIconButton(Icons.notifications_none_rounded, () => Navigator.pushNamed(context, '/notifications')),
          const SizedBox(width: 12),
          // AI Агент баскычы
          GestureDetector(
            onTap: () {
              HapticFeedback.heavyImpact();
              Navigator.push(context, MaterialPageRoute(builder: (context) => const AdminTerminalScreen()));
            },
            child: AnimatedBuilder(
              animation: _pulseController,
              builder: (context, child) => Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: const Color(0xFF00FFCC).withValues(alpha: 0.05 + (_pulseController.value * 0.1)),
                  shape: BoxShape.circle,
                  border: Border.all(color: const Color(0xFF00FFCC).withValues(alpha: 0.2 * _pulseController.value)),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFF00FFCC).withValues(alpha: 0.1 * _pulseController.value),
                      blurRadius: 10,
                      spreadRadius: 2,
                    )
                  ],
                ),
                child: const Icon(Icons.auto_awesome, color: Color(0xFF00FFCC), size: 22),
              ),
            ),
          ),
          const SizedBox(width: 12),
          _buildIconButton(Icons.settings_suggest_rounded, () => Navigator.pushNamed(context, '/settings')),
        ],
      ),
    );
  }

  Widget _buildPremiumBanner(BuildContext context, String lang) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24),
      child: GestureDetector(
        onTap: () => Navigator.pushNamed(context, '/paywall'),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(20),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
              decoration: BoxDecoration(
                color: AppColors.gold.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: AppColors.gold.withValues(alpha: 0.2)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.stars_rounded, color: AppColors.gold, size: 24),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(t('premium_upgrade', lang), style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold)),
                        Text(t('premium_subtitle', lang), style: const TextStyle(color: Colors.white54, fontSize: 11)),
                      ],
                    ),
                  ),
                  const Icon(Icons.arrow_forward_ios_rounded, color: Colors.white38, size: 14),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildIconButton(IconData icon, VoidCallback onTap) {
    return GestureDetector(
      onTap: onTap,
      child: ClipRRect(
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
          child: Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.white.withValues(alpha: 0.05),
              shape: BoxShape.circle,
              border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
            ),
            child: Icon(icon, color: Colors.white, size: 22),
          ),
        ),
      ),
    );
  }

  Widget _buildMainButton(VpnProvider vpn, String lang) {
    bool isConnected = vpn.status == VpnState.connected;
    bool isConnecting = vpn.status == VpnState.connecting;

    return GestureDetector(
      onTap: () async {
        final error = await vpn.toggleConnect();
        if (error != null && mounted) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(error), backgroundColor: Colors.redAccent));
        }
      },
      child: AnimatedBuilder(
        animation: _pulseController,
        builder: (context, child) {
          return Center(
            child: Stack(
              alignment: Alignment.center,
              children: [
                // Pulse Rings
                if (isConnected || isConnecting)
                  for (var i = 1; i <= 3; i++)
                    Transform.scale(
                      scale: 1 + (_pulseController.value * 0.5 * i),
                      child: Container(
                        width: 200,
                        height: 200,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          border: Border.all(color: (isConnected ? AppColors.accent : AppColors.blue).withValues(alpha: 0.2 - (i * 0.05))),
                        ),
                      ),
                    ),
                
                // Main Glass Button
                Container(
                  width: 220,
                  height: 220,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: (isConnected ? AppColors.accent : AppColors.blue).withValues(alpha: 0.2),
                        blurRadius: 60,
                        spreadRadius: 10,
                      )
                    ],
                  ),
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(110),
                    child: BackdropFilter(
                      filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
                      child: Container(
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: Colors.white.withValues(alpha: 0.03),
                          border: Border.all(color: (isConnected ? AppColors.accent : Colors.white).withValues(alpha: 0.2), width: 2),
                          gradient: LinearGradient(
                            begin: Alignment.topLeft,
                            end: Alignment.bottomRight,
                            colors: [
                              Colors.white.withValues(alpha: 0.1),
                              Colors.transparent,
                            ],
                          ),
                        ),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.power_settings_new_rounded,
                              size: 80,
                              color: isConnected ? AppColors.accent : Colors.white,
                            ),
                            const SizedBox(height: 10),
                            Text(
                              isConnecting 
                                ? t('connecting', lang).toUpperCase() 
                                : (isConnected ? t('connected', lang).toUpperCase() : t('press_to_connect', lang).toUpperCase()),
                              style: TextStyle(
                                color: isConnected ? AppColors.accent : Colors.white54,
                                fontSize: 12,
                                fontWeight: FontWeight.w900,
                                letterSpacing: 1,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildServerSelector(BuildContext context, VpnProvider vpn, String lang) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 30),
      child: GestureDetector(
        onTap: () => Navigator.pushNamed(context, '/servers'),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(24),
          child: BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 15, sigmaY: 15),
            child: Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.05),
                borderRadius: BorderRadius.circular(24),
                border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
              ),
              child: Row(
                children: [
                  Container(
                    width: 45,
                    height: 45,
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.05),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    alignment: Alignment.center,
                    child: Text(vpn.selectedServer.flag, style: const TextStyle(fontSize: 24)),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(t('select_server', lang).toUpperCase(), style: const TextStyle(color: Colors.white54, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1)),
                        const SizedBox(height: 2),
                        Text(
                          vpn.selectedServer.localizedCity(lang),
                          style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)
                        ),
                      ],
                    ),
                  ),
                  const Icon(Icons.keyboard_arrow_right_rounded, color: Colors.white54),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _AnimatedBackground extends StatelessWidget {
  final VpnState status;
  const _AnimatedBackground({required this.status});

  @override
  Widget build(BuildContext context) {
    final isConnected = status == VpnState.connected;
    return Stack(
      children: [
        Positioned(
          top: -100,
          right: -50,
          child: _Blob(color: (isConnected ? AppColors.accent : AppColors.blue).withValues(alpha: 0.15), size: 400),
        ),
        Positioned(
          bottom: 100,
          left: -100,
          child: _Blob(color: (isConnected ? AppColors.accent : Colors.purple).withValues(alpha: 0.1), size: 300),
        ),
      ],
    );
  }
}

class _Blob extends StatelessWidget {
  final Color color;
  final double size;
  const _Blob({required this.color, required this.size});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: color,
      ),
      child: BackdropFilter(filter: ImageFilter.blur(sigmaX: 100, sigmaY: 100), child: Container(color: Colors.transparent)),
    );
  }
}
