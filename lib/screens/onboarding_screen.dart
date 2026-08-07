import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../constants/colors.dart';
import '../constants/translations.dart';
import '../providers/providers.dart';

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key});

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _pageController = PageController();
  int _currentPage = 0;

  @override
  Widget build(BuildContext context) {
    final lang = context.watch<LanguageProvider>().lang;
    final List<Map<String, String>> pages = [
      {
        'title': t('onboarding_title_1', lang),
        'desc': t('onboarding_desc_1', lang),
        'image': '🚀',
      },
      {
        'title': t('onboarding_title_2', lang),
        'desc': t('onboarding_desc_2', lang),
        'image': '🛡️',
      },
      {
        'title': t('onboarding_title_3', lang),
        'desc': t('onboarding_desc_3', lang),
        'image': '🌍',
      },
    ];

    return Scaffold(
      backgroundColor: const Color(0xFF030303),
      body: Stack(
        children: [
          // Background Blobs
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
                Expanded(
                  child: PageView.builder(
                    controller: _pageController,
                    onPageChanged: (i) => setState(() => _currentPage = i),
                    itemCount: pages.length,
                    itemBuilder: (context, i) => _buildPage(pages[i]),
                  ),
                ),
                _buildBottomControls(pages.length, lang),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPage(Map<String, String> page) {
    return Padding(
      padding: const EdgeInsets.all(40),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(page['image']!, style: const TextStyle(fontSize: 100)),
          const SizedBox(height: 60),
          Text(page['title']!,
              style: const TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.w900, letterSpacing: -1),
              textAlign: TextAlign.center),
          const SizedBox(height: 20),
          Text(page['desc']!,
              textAlign: TextAlign.center,
              style: TextStyle(color: Colors.white.withValues(alpha: 0.4), fontSize: 16, height: 1.5)),
        ],
      ),
    );
  }

  Widget _buildBottomControls(int totalPages, String lang) {
    return Padding(
      padding: const EdgeInsets.all(40),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(totalPages, (i) => _buildIndicator(i == _currentPage)),
          ),
          const SizedBox(height: 40),
          _buildNextButton(totalPages, lang),
        ],
      ),
    );
  }

  Widget _buildIndicator(bool isActive) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      margin: const EdgeInsets.symmetric(horizontal: 4),
      height: 6,
      width: isActive ? 24 : 6,
      decoration: BoxDecoration(color: isActive ? AppColors.accent : Colors.white10, borderRadius: BorderRadius.circular(3)),
    );
  }

  Widget _buildNextButton(int totalPages, String lang) {
    return Container(
      width: double.infinity,
      height: 60,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(20),
        gradient: const LinearGradient(colors: [AppColors.accent, AppColors.blue]),
        boxShadow: [BoxShadow(color: AppColors.accent.withValues(alpha: 0.3), blurRadius: 20, offset: const Offset(0, 10))],
      ),
      child: ElevatedButton(
        onPressed: () {
          if (_currentPage < totalPages - 1) {
            _pageController.nextPage(duration: const Duration(milliseconds: 500), curve: Curves.easeOutCubic);
          } else {
            Navigator.pushReplacementNamed(context, '/main');
          }
        },
        style: ElevatedButton.styleFrom(
          backgroundColor: Colors.transparent,
          shadowColor: Colors.transparent,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        ),
        child: Text(_currentPage == totalPages - 1 ? t('get_started', lang).toUpperCase() : t('next', lang).toUpperCase(),
            style: const TextStyle(color: Colors.black, fontWeight: FontWeight.w900, fontSize: 16, letterSpacing: 1)),
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
