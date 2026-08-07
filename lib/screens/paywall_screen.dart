import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../constants/colors.dart';
import '../constants/translations.dart';
import '../constants/plans.dart';
import '../providers/providers.dart';

class PaywallScreen extends StatefulWidget {
  const PaywallScreen({super.key});

  @override
  State<PaywallScreen> createState() => _PaywallScreenState();
}

class _PaywallScreenState extends State<PaywallScreen> with WidgetsBindingObserver {
  
  @override
  void initState() {
    super.initState();
    // Тиркеменин абалын (ачык/жабык) көзөмөлдөө үчүн кошулду
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    // Колдонуучу браузерден төлөп бүтүп, тиркемеге кайтып келген учур
    if (state == AppLifecycleState.resumed) {
      _autoCheckPayment();
    }
  }

  Future<void> _autoCheckPayment() async {
    final sub = context.read<SubscriptionProvider>();
    final lang = context.read<LanguageProvider>().lang;

    final success = await sub.checkLavaPaymentStatus();
    if (success && mounted) {
      _showSuccessSnackBar(context, t('payment_success_msg', lang));
      // Эгер ийгиликтүү болсо, экранды жабабыз
      Navigator.pop(context);
    }
  }

  @override
  Widget build(BuildContext context) {
    final sub = context.watch<SubscriptionProvider>();
    final lang = context.watch<LanguageProvider>().lang;
    final systemProv = context.watch<SystemProvider>();

    return Scaffold(
      backgroundColor: const Color(0xFF030303),
      body: Stack(
        children: [
          Positioned(
            top: -100,
            right: -50,
            child: _BlurredBlob(color: AppColors.gold.withValues(alpha: 0.1), size: 300),
          ),
          Positioned(
            bottom: -100,
            left: -50,
            child: _BlurredBlob(color: AppColors.accent.withValues(alpha: 0.05), size: 400),
          ),

          SafeArea(
            child: Column(
              children: [
                _buildHeader(context),
                Expanded(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(24),
                    physics: const BouncingScrollPhysics(),
                    child: Column(
                      children: [
                        const Icon(Icons.stars_rounded, size: 80, color: AppColors.gold),
                        const SizedBox(height: 20),
                        Text(t('premium_title', lang),
                            style: const TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.w900, letterSpacing: -0.5),
                            textAlign: TextAlign.center),
                        const SizedBox(height: 20),
                        
                        _buildCurrencySelector(sub),
                        
                        const SizedBox(height: 30),
                        _buildFeatureItem(Icons.bolt_rounded, t('feat_speed', lang), AppColors.accent),
                        _buildFeatureItem(Icons.public_rounded, t('feat_servers', lang), AppColors.blue),
                        _buildFeatureItem(Icons.security_rounded, t('advanced_encryption', lang), Colors.purpleAccent),
                        const SizedBox(height: 40),
                        
                        ...kPlans.values.map((plan) {
                          final price = plan['prices'][sub.currency];
                          final symbol = kCurrencies[sub.currency]?['symbol'] ?? '';
                          return Padding(
                            padding: const EdgeInsets.only(bottom: 16),
                            child: _buildPlanCard(
                              plan['id'], 
                              t(plan['labelKey'], lang), 
                              '$symbol$price', 
                              sub,
                              lang,
                              discount: plan['discountKey'] != null ? t(plan['discountKey'], lang) : null,
                              isPopular: plan['popular'] ?? false,
                            ),
                          );
                        }),

                        const SizedBox(height: 24),
                        _buildSubscribeButton(context, sub, lang),

                        if (systemProv.showExternalPayments) ...[
                          const SizedBox(height: 16),
                          _buildOtherPaymentMethods(context, sub, lang),
                        ],

                        const SizedBox(height: 12),
                        TextButton(
                          onPressed: () => _showCodeEntryDialog(context, sub, lang),
                          child: Text(t('have_code', lang), style: const TextStyle(color: Colors.white38, fontSize: 13)),
                        ),
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

  void _showCodeEntryDialog(BuildContext context, SubscriptionProvider sub, String lang) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1A1A1A),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24), side: const BorderSide(color: Colors.white10)),
        title: Text(t('enter_code', lang), style: const TextStyle(color: Colors.white)),
        content: TextField(
          controller: controller,
          style: const TextStyle(color: Colors.white),
          decoration: InputDecoration(
            hintText: 'XXXX-XXXX-XXXX',
            hintStyle: const TextStyle(color: Colors.white24),
            filled: true,
            fillColor: Colors.white.withValues(alpha: 0.05),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(15), borderSide: BorderSide.none),
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: Text(t('cancel', lang), style: const TextStyle(color: Colors.white38))),
          ElevatedButton(
            onPressed: () async {
              final code = controller.text.trim();
              if (code.isEmpty) return;
              final success = await sub.verifyActivationCode(code);
              if (context.mounted) {
                Navigator.pop(context);
                if (success) {
                  _showSuccessSnackBar(context, t('code_success', lang));
                } else {
                  _showErrorSnackBar(context, t('code_error', lang));
                }
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.accent, foregroundColor: Colors.black),
            child: Text(t('activate', lang)),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader(BuildContext context) {
    return Align(
      alignment: Alignment.topLeft,
      child: IconButton(
        padding: const EdgeInsets.all(24),
        icon: const Icon(Icons.close_rounded, color: Colors.white24, size: 28),
        onPressed: () => Navigator.pop(context),
      ),
    );
  }

  Widget _buildCurrencySelector(SubscriptionProvider sub) {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: kCurrencies.keys.map((c) {
          final isSelected = sub.currency == c;
          return GestureDetector(
            onTap: () => sub.setCurrency(c),
            child: Container(
              margin: const EdgeInsets.symmetric(horizontal: 4),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: isSelected ? AppColors.accent : Colors.white.withValues(alpha: 0.05),
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: isSelected ? AppColors.accent : Colors.white10),
              ),
              child: Text(
                c,
                style: TextStyle(
                  color: isSelected ? Colors.black : Colors.white,
                  fontWeight: FontWeight.bold,
                  fontSize: 12,
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildFeatureItem(IconData icon, String text, Color color) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 20),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(color: color.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(12)),
            child: Icon(icon, color: color, size: 22),
          ),
          const SizedBox(width: 16),
          Text(text, style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }

  Widget _buildPlanCard(String id, String title, String price, SubscriptionProvider sub, String lang, {String? discount, bool isPopular = false}) {
    final isSelected = sub.selectedPlanId == id;
    return GestureDetector(
      onTap: () => sub.setPlan(id),
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: isSelected ? AppColors.accent.withValues(alpha: 0.1) : Colors.white.withValues(alpha: 0.02),
              borderRadius: BorderRadius.circular(24),
              border: Border.all(color: isSelected ? AppColors.accent.withValues(alpha: 0.4) : Colors.white.withValues(alpha: 0.08), width: 1.5),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(title, style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                      if (discount != null)
                        Text(discount, style: const TextStyle(color: AppColors.accent, fontSize: 11, fontWeight: FontWeight.w900, letterSpacing: 0.5)),
                    ],
                  ),
                ),
                Text(price, style: const TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.w900)),
              ],
            ),
          ),
          if (isPopular)
            Positioned(
              top: -10,
              right: 20,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                decoration: BoxDecoration(
                  color: AppColors.gold,
                  borderRadius: BorderRadius.circular(10),
                ),
                child: Text(t('popular', lang).toUpperCase(), style: const TextStyle(color: Colors.black, fontSize: 10, fontWeight: FontWeight.w900)),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildSubscribeButton(BuildContext context, SubscriptionProvider sub, String lang) {
    return Container(
      width: double.infinity,
      height: 60,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(20),
        gradient: const LinearGradient(colors: [AppColors.accent, AppColors.blue]),
        boxShadow: [BoxShadow(color: AppColors.accent.withValues(alpha: 0.3), blurRadius: 20, offset: const Offset(0, 10))],
      ),
      child: ElevatedButton(
        onPressed: () async {
          if (sub.isFetchingOfferings) return;
          if (sub.availablePackages.isEmpty) {
            await sub.retryFetchOfferings();
            if (sub.availablePackages.isEmpty && context.mounted) {
              _showErrorSnackBar(context, t('no_plans_error', lang));
              return;
            }
          }
          
          try {
            if (sub.availablePackages.isNotEmpty) {
              final package = sub.availablePackages.firstWhere(
                (p) => p.packageType.name.toLowerCase().contains(sub.selectedPlanId),
                orElse: () => sub.availablePackages.first,
              );
              final success = await sub.purchasePackage(package);
              if (success && context.mounted) {
                 Navigator.pop(context);
                 _showSuccessSnackBar(context, t('payment_success_msg', lang));
              }
            }
          } catch (e) {
            _showErrorSnackBar(context, "${t('error_auth_failed', lang)}: $e");
          }
        },
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.transparent,
          shadowColor: Colors.transparent,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        ),
        child: sub.isFetchingOfferings 
          ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(color: Colors.black, strokeWidth: 2))
          : Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.shopping_bag_rounded, color: Colors.black, size: 20),
                const SizedBox(width: 10),
                Text(t('subscribe_now', lang).toUpperCase(), style: const TextStyle(color: Colors.black, fontWeight: FontWeight.w900, fontSize: 16)),
              ],
            ),
      ),
    );
  }

  Widget _buildOtherPaymentMethods(BuildContext context, SubscriptionProvider sub, String lang) {
    return Column(
      children: [
        Text(t('other_payment_methods', lang), style: const TextStyle(color: Colors.white24, fontSize: 10, fontWeight: FontWeight.bold, letterSpacing: 1.5)),
        const SizedBox(height: 12),
        _buildPaymentMethodTile(
          icon: Icons.send_rounded,
          title: t('pay_via_telegram', lang),
          subtitle: t('telegram_bot_desc', lang),
          color: Colors.blueAccent,
          onTap: () async {
            await sub.payViaExternalLink();
          },
        ),
      ],
    );
  }

  Widget _buildPaymentMethodTile({required IconData icon, required String title, required String subtitle, required Color color, required VoidCallback onTap}) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.03),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: Colors.white.withValues(alpha: 0.05)),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(color: color.withValues(alpha: 0.1), borderRadius: BorderRadius.circular(12)),
              child: Icon(icon, color: color, size: 22),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold)),
                  Text(subtitle, style: const TextStyle(color: Colors.white38, fontSize: 11)),
                ],
              ),
            ),
            const Icon(Icons.chevron_right_rounded, color: Colors.white24),
          ],
        ),
      ),
    );
  }

  void _showSuccessSnackBar(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: AppColors.accent),
    );
  }

  void _showErrorSnackBar(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.redAccent),
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
