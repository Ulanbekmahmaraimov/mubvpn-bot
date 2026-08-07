import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../constants/colors.dart';
import '../constants/translations.dart';
import '../models/vpn.dart';
import '../providers/providers.dart';

class AddServerScreen extends StatefulWidget {
  const AddServerScreen({super.key});

  @override
  State<AddServerScreen> createState() => _AddServerScreenState();
}

class _AddServerScreenState extends State<AddServerScreen> {
  final _countryCtrl = TextEditingController();
  final _cityCtrl = TextEditingController();
  final _configCtrl = TextEditingController();
  bool _isPremium = false;

  @override
  void dispose() {
    _countryCtrl.dispose();
    _cityCtrl.dispose();
    _configCtrl.dispose();
    super.dispose();
  }

  void _addServer(VpnProvider vpn, String lang) {
    if (_countryCtrl.text.isEmpty || _cityCtrl.text.isEmpty || _configCtrl.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(t('fill_all_error', lang)), 
          backgroundColor: AppColors.red.withValues(alpha: 0.8),
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
        )
      );
      return;
    }

    vpn.addServer(VpnServer(
      country: _countryCtrl.text.trim(),
      city: _cityCtrl.text.trim(),
      flag: '🌐',
      config: _configCtrl.text.trim(),
      isPremium: _isPremium,
    ));

    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(t('server_added_success', lang)), 
        backgroundColor: AppColors.accent.withValues(alpha: 0.8),
        behavior: SnackBarBehavior.floating,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15)),
      )
    );
    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    final vpn = context.watch<VpnProvider>();
    final lang = context.watch<LanguageProvider>().lang;

    return Scaffold(
      backgroundColor: const Color(0xFF030303),
      body: Stack(
        children: [
          Positioned(
            top: -100,
            right: -50,
            child: _BlurredBlob(color: AppColors.accent.withValues(alpha: 0.12), size: 300),
          ),
          Positioned(
            bottom: 50,
            left: -100,
            child: _BlurredBlob(color: AppColors.blue.withValues(alpha: 0.08), size: 400),
          ),
          
          SafeArea(
            child: Column(
              children: [
                _buildHeader(context, lang),
                Expanded(
                  child: SingleChildScrollView(
                    physics: const BouncingScrollPhysics(),
                    padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _GlassCard(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                t('new_server_details', lang),
                                style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                              ),
                              const SizedBox(height: 24),
                              _buildField(
                                controller: _countryCtrl, 
                                icon: Icons.public_rounded, 
                                label: t('country_label', lang), 
                                hint: 'e.g. Germany'
                              ),
                              const SizedBox(height: 24),
                              _buildField(
                                controller: _cityCtrl, 
                                icon: Icons.location_city_rounded, 
                                label: t('city_label', lang), 
                                hint: 'e.g. Frankfurt'
                              ),
                              const SizedBox(height: 24),
                              _buildField(
                                controller: _configCtrl, 
                                icon: Icons.vpn_key_rounded, 
                                label: t('config_label', lang), 
                                hint: 'vless://...', 
                                maxLines: 4
                              ),
                              const SizedBox(height: 24),
                              _buildPremiumSwitch(lang),
                            ],
                          ),
                        ),
                        const SizedBox(height: 40),
                        _buildDeployButton(vpn, lang),
                        const SizedBox(height: 40),
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

  Widget _buildHeader(BuildContext context, String lang) {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Row(
        children: [
          GestureDetector(
            onTap: () => Navigator.pop(context),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: BackdropFilter(
                filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
                child: Container(
                  padding: const EdgeInsets.all(10), 
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.05), 
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.white.withValues(alpha: 0.1))
                  ), 
                  child: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white, size: 18)
                ),
              ),
            ),
          ),
          const SizedBox(width: 20),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(t('add_server', lang), style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.w900, letterSpacing: -0.5)),
              const Text('Elite Protocol Setup', style: TextStyle(color: Colors.white38, fontSize: 11, fontWeight: FontWeight.bold, letterSpacing: 1.0)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildField({
    required TextEditingController controller, 
    required IconData icon, 
    required String label, 
    required String hint, 
    int maxLines = 1
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: 4, bottom: 8),
          child: Text(label.toUpperCase(), style: const TextStyle(color: AppColors.accent, fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1.2)),
        ),
        Container(
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.02),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.white.withValues(alpha: 0.05)),
          ),
          child: TextField(
            controller: controller,
            maxLines: maxLines,
            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 15),
            decoration: InputDecoration(
              prefixIcon: Icon(icon, color: Colors.white24, size: 20),
              hintText: hint,
              hintStyle: const TextStyle(color: Colors.white10, fontSize: 14),
              border: InputBorder.none,
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildPremiumSwitch(String lang) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.02),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Row(
            children: [
              const Icon(Icons.stars_rounded, color: AppColors.gold, size: 20),
              const SizedBox(width: 12),
              Text(t('premium_server_toggle', lang), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 15)),
            ],
          ),
          Switch.adaptive(
            value: _isPremium, 
            onChanged: (v) => setState(() => _isPremium = v), 
            activeTrackColor: AppColors.gold.withValues(alpha: 0.3), 
            activeThumbColor: AppColors.gold
          ),
        ],
      ),
    );
  }

  Widget _buildDeployButton(VpnProvider vpn, String lang) {
    return Container(
      width: double.infinity,
      height: 60,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(20), 
        gradient: const LinearGradient(
          colors: [AppColors.accent, AppColors.blue],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ), 
        boxShadow: [
          BoxShadow(color: AppColors.accent.withValues(alpha: 0.3), blurRadius: 20, offset: const Offset(0, 10))
        ]
      ),
      child: ElevatedButton(
        onPressed: () => _addServer(vpn, lang),
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.transparent, 
          shadowColor: Colors.transparent, 
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20))
        ),
        child: Text(t('deploy_server_btn', lang).toUpperCase(), style: const TextStyle(color: Colors.black, fontWeight: FontWeight.w900, fontSize: 16, letterSpacing: 1.5)),
      ),
    );
  }
}

class _GlassCard extends StatelessWidget {
  final Widget child;
  const _GlassCard({required this.child});

  @override
  Widget build(BuildContext context) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(32),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 15, sigmaY: 15),
        child: Container(
          padding: const EdgeInsets.all(24),
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.03),
            borderRadius: BorderRadius.circular(32),
            border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
          ),
          child: child,
        ),
      ),
    );
  }
}

class _BlurredBlob extends StatelessWidget {
  final Color color;
  final double size;
  const _BlurredBlob({required this.color, required this.size});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: color,
        boxShadow: [BoxShadow(color: color, blurRadius: 100, spreadRadius: 40)],
      ),
    );
  }
}
