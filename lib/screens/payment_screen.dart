import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../constants/colors.dart';
import '../constants/translations.dart';
import '../providers/providers.dart';

class PaymentScreen extends StatefulWidget {
  const PaymentScreen({super.key});

  @override
  State<PaymentScreen> createState() => _PaymentScreenState();
}

class _PaymentScreenState extends State<PaymentScreen> {
  bool _isProcessing = false;

  @override
  Widget build(BuildContext context) {
    final sub = context.watch<SubscriptionProvider>();
    final lang = context.watch<LanguageProvider>().lang;

    return Scaffold(
      backgroundColor: const Color(0xFF030303),
      body: Stack(
        children: [
          Positioned(
            top: -100,
            left: -50,
            child: _BlurredBlob(color: AppColors.accent.withValues(alpha: 0.1), size: 300),
          ),
          Positioned(
            bottom: -50,
            right: -50,
            child: _BlurredBlob(color: AppColors.blue.withValues(alpha: 0.05), size: 350),
          ),

          SafeArea(
            child: Column(
              children: [
                _buildHeader(context, lang),
                Expanded(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(24),
                    physics: const BouncingScrollPhysics(),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _buildSummaryCard(sub, lang),
                        const SizedBox(height: 32),
                        _buildLabel('PAYMENT METHOD'),
                        _buildGlassCard([
                          _buildPaymentMethodTile(Icons.credit_card_rounded, 'Credit Card', true),
                          _buildDivider(),
                          _buildPaymentMethodTile(Icons.account_balance_wallet_rounded, 'Google Pay', false),
                          _buildDivider(),
                          _buildPaymentMethodTile(Icons.apple_rounded, 'Apple Pay', false),
                        ]),
                        const SizedBox(height: 40),
                        _buildPayButton(context, sub, lang),
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
            child: Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.05),
                shape: BoxShape.circle,
                border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
              ),
              child: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white, size: 18),
            ),
          ),
          const SizedBox(width: 20),
          Text(t('payment', lang),
              style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.w900, letterSpacing: -0.5)),
        ],
      ),
    );
  }

  Widget _buildSummaryCard(SubscriptionProvider sub, String lang) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [AppColors.accent.withValues(alpha: 0.2), Colors.transparent],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(30),
        border: Border.all(color: AppColors.accent.withValues(alpha: 0.2)),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(sub.selectedPlanId == '1y' ? t('yearly', lang) : t('monthly', lang),
                  style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
              Text(sub.selectedPlanId == '1y' ? '\$59.99' : '\$9.99',
                  style: const TextStyle(color: AppColors.accent, fontSize: 22, fontWeight: FontWeight.w900)),
            ],
          ),
          const SizedBox(height: 12),
          Divider(color: Colors.white.withValues(alpha: 0.05)),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(t('total_data', lang), style: TextStyle(color: Colors.white.withValues(alpha: 0.4), fontSize: 14)),
              Text(sub.selectedPlanId == '1y' ? '\$59.99' : '\$9.99',
                  style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildLabel(String text) {
    return Padding(
      padding: const EdgeInsets.only(left: 8, bottom: 12),
      child: Text(text, style: const TextStyle(color: AppColors.accent, fontSize: 11, fontWeight: FontWeight.w900, letterSpacing: 1.5)),
    );
  }

  Widget _buildGlassCard(List<Widget> children) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(28),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 15, sigmaY: 15),
        child: Container(
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.03),
            borderRadius: BorderRadius.circular(28),
            border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
          ),
          child: Column(children: children),
        ),
      ),
    );
  }

  Widget _buildPaymentMethodTile(IconData icon, String title, bool isSelected) {
    return Padding(
      padding: const EdgeInsets.all(20),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: (isSelected ? AppColors.accent : Colors.white).withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: isSelected ? AppColors.accent : Colors.white38, size: 22),
          ),
          const SizedBox(width: 16),
          Expanded(child: Text(title, style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold))),
          if (isSelected) const Icon(Icons.check_circle_rounded, color: AppColors.accent, size: 24),
        ],
      ),
    );
  }

  Widget _buildDivider() => Divider(height: 1, color: Colors.white.withValues(alpha: 0.05), indent: 70);

  Widget _buildPayButton(BuildContext context, SubscriptionProvider sub, String lang) {
    return Container(
      width: double.infinity,
      height: 60,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(20),
        gradient: LinearGradient(
          colors: _isProcessing 
              ? [Colors.grey, Colors.grey.withValues(alpha: 0.5)] 
              : [AppColors.accent, AppColors.blue]
        ),
        boxShadow: [
          if (!_isProcessing)
            BoxShadow(color: AppColors.accent.withValues(alpha: 0.3), blurRadius: 20, offset: const Offset(0, 10))
        ],
      ),
      child: ElevatedButton(
        onPressed: _isProcessing ? null : () async {
          setState(() => _isProcessing = true);
          
          // Simulation for direct payment
          await Future.delayed(const Duration(seconds: 2));
          
          if (mounted) {
            await sub.activatePlan(sub.selectedPlanId);
            _showSuccessDialog(context, lang);
            setState(() => _isProcessing = false);
          }
        },
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.transparent,
          shadowColor: Colors.transparent,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        ),
        child: _isProcessing
          ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(color: Colors.black, strokeWidth: 3))
          : Text(t('pay_now', lang).toUpperCase(), style: const TextStyle(color: Colors.black, fontWeight: FontWeight.w900, fontSize: 16)),
      ),
    );
  }

  void _showSuccessDialog(BuildContext context, String lang) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: AlertDialog(
          backgroundColor: const Color(0xFF121212),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(30), 
            side: BorderSide(color: AppColors.accent.withValues(alpha: 0.3))
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.check_circle_outline_rounded, color: AppColors.accent, size: 80),
              const SizedBox(height: 20),
              const Text('PREMIUM АКТИВДҮҮ!', style: TextStyle(color: Colors.white, fontSize: 20, fontWeight: FontWeight.bold)),
              const SizedBox(height: 10),
              const Text('Эми сиз бардык серверлерди чектөөсүз колдоно аласыз.', textAlign: TextAlign.center, style: TextStyle(color: Colors.white70)),
              const SizedBox(height: 30),
              ElevatedButton(
                onPressed: () => Navigator.popUntil(context, (route) => route.isFirst),
                style: ElevatedButton.styleFrom(backgroundColor: AppColors.accent, foregroundColor: Colors.black, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(15))),
                child: const Text('БАШТОО', style: TextStyle(fontWeight: FontWeight.bold)),
              ),
            ],
          ),
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
      decoration: BoxDecoration(shape: BoxShape.circle, color: color, boxShadow: [BoxShadow(color: color, blurRadius: 100, spreadRadius: 40)]),
    );
  }
}
