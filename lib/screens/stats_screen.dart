import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../constants/colors.dart';
import '../constants/translations.dart';
import '../providers/providers.dart';

class StatsScreen extends StatefulWidget {
  const StatsScreen({super.key});

  @override
  State<StatsScreen> createState() => _StatsScreenState();
}

class _StatsScreenState extends State<StatsScreen> with TickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(seconds: 10),
      vsync: this,
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final stats = context.watch<StatsProvider>();
    final vpn = context.watch<VpnProvider>();
    final lang = context.watch<LanguageProvider>().lang;

    return Scaffold(
      backgroundColor: const Color(0xFF030303), // OLED Black
      body: Stack(
        children: [
          // Animated Mesh Gradient
          AnimatedBuilder(
            animation: _controller,
            builder: (context, child) {
              return Stack(
                children: [
                  Positioned(
                    top: -150 + (50 * _controller.value),
                    right: -100 + (100 * _controller.value),
                    child: _buildGlow(AppColors.accent.withValues(alpha: 0.15), 500),
                  ),
                  Positioned(
                    bottom: 50 - (80 * _controller.value),
                    left: -120 + (60 * _controller.value),
                    child: _buildGlow(AppColors.blue.withValues(alpha: 0.12), 450),
                  ),
                ],
              );
            },
          ),

          // Backdrop Blur Layer
          BackdropFilter(
            filter: ImageFilter.blur(sigmaX: 80, sigmaY: 80),
            child: Container(color: Colors.transparent),
          ),

          SafeArea(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildHeader(context, lang),
                  const SizedBox(height: 25),
                  _buildSessionInfo(vpn, lang),
                  const SizedBox(height: 20),
                  _buildStatsGrid(stats, lang),
                  const SizedBox(height: 20),
                  _buildChartCard(stats, lang),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGlow(Color color, double size) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: RadialGradient(colors: [color, color.withValues(alpha: 0)]),
      ),
    );
  }

  Widget _buildHeader(BuildContext context, String lang) {
    return Padding(
      padding: const EdgeInsets.only(top: 10),
      child: Row(
        children: [
          GestureDetector(
            onTap: () => Navigator.pop(context),
            child: _buildGlassContainer(
              padding: const EdgeInsets.all(12),
              borderRadius: 50,
              child: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white, size: 18),
            ),
          ),
          const SizedBox(width: 20),
          Text(
            t('statistics', lang),
            style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  Widget _buildSessionInfo(VpnProvider vpn, String lang) {
    return _buildGlassContainer(
      padding: const EdgeInsets.all(22),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.accent.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(15),
            ),
            child: const Icon(Icons.timer_outlined, color: AppColors.accent, size: 28),
          ),
          const SizedBox(width: 15),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                t('connected_time', lang),
                style: TextStyle(color: Colors.white.withValues(alpha: 0.4), fontSize: 12),
              ),
              const SizedBox(height: 4),
              Text(
                vpn.connectedTimeStr,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 26,
                  fontWeight: FontWeight.w900,
                  fontFamily: 'monospace',
                ),
              ),
            ],
          ),
          const Spacer(),
          _buildStatusBadge(vpn.isConnected, lang),
        ],
      ),
    );
  }

  Widget _buildStatusBadge(bool isConnected, String lang) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: isConnected ? AppColors.accent.withValues(alpha: 0.1) : AppColors.red.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: isConnected ? AppColors.accent.withValues(alpha: 0.2) : AppColors.red.withValues(alpha: 0.2)),
      ),
      child: Text(
        isConnected ? t('active', lang) : t('off', lang),
        style: TextStyle(
          color: isConnected ? AppColors.accent : AppColors.red,
          fontSize: 10,
          fontWeight: FontWeight.bold,
          letterSpacing: 0.5,
        ),
      ),
    );
  }

  Widget _buildStatsGrid(StatsProvider stats, String lang) {
    return Row(
      children: [
        Expanded(child: _buildStatCard(Icons.download_rounded, t('download', lang), stats.downSpeedStr, AppColors.accent)),
        const SizedBox(width: 15),
        Expanded(child: _buildStatCard(Icons.upload_rounded, t('upload', lang), stats.upSpeedStr, const Color(0xFF4DA8FF))),
      ],
    );
  }

  Widget _buildStatCard(IconData icon, String label, String value, Color color) {
    return _buildGlassContainer(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: color, size: 24),
          const SizedBox(height: 15),
          Text(
            value,
            style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(color: Colors.white.withValues(alpha: 0.4), fontSize: 12),
          ),
        ],
      ),
    );
  }

  Widget _buildChartCard(StatsProvider stats, String lang) {
    final maxSpeed = stats.speedHistory.isEmpty ? 1.0 : stats.speedHistory.reduce((a, b) => a > b ? a : b).clamp(1.0, double.infinity);

    return _buildGlassContainer(
      padding: const EdgeInsets.all(22),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                t('speed_history', lang),
                style: const TextStyle(color: Colors.white54, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1.2),
              ),
              Text(
                '${stats.totalMB.toStringAsFixed(1)} MB ${t('used', lang)}',
                style: const TextStyle(color: AppColors.accent, fontSize: 11),
              ),
            ],
          ),
          const SizedBox(height: 25),
          SizedBox(
            height: 100,
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: stats.speedHistory.map((s) {
                final h = (s / maxSpeed * 100).clamp(5.0, 100.0);
                return Flexible(
                  child: Container(
                    margin: const EdgeInsets.symmetric(horizontal: 2),
                    width: 8,
                    height: h,
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [
                          AppColors.accent.withValues(alpha: s > 0 ? 0.8 : 0.1),
                          AppColors.accent.withValues(alpha: 0.05),
                        ],
                      ),
                      borderRadius: BorderRadius.circular(4),
                    ),
                  ),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGlassContainer({required Widget child, required EdgeInsets padding, double borderRadius = 25}) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(borderRadius),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 15, sigmaY: 15),
        child: Container(
          padding: padding,
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.03),
            borderRadius: BorderRadius.circular(borderRadius),
            border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
          ),
          child: child,
        ),
      ),
    );
  }
}
