
import 'dart:io';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';
import 'package:provider/provider.dart';
import 'package:window_manager/window_manager.dart';
import 'package:purchases_flutter/purchases_flutter.dart';

import 'constants/colors.dart';
import 'constants/translations.dart';
import 'providers/ads_provider.dart';
import 'providers/providers.dart';
import 'screens/add_server_screen.dart';
import 'screens/notifications_screen.dart';
import 'screens/onboarding_screen.dart';
import 'screens/payment_screen.dart';
import 'screens/paywall_screen.dart';
import 'screens/servers/home/home_screen.dart';
import 'screens/servers/servers_screen.dart';
import 'screens/settings/settings_screen.dart';

import 'screens/splash_screen.dart';
import 'screens/stats_screen.dart';
import 'screens/login_screen.dart';
import 'screens/registration_screen.dart';

/// The entry point for the mubVPN Flutter application.
/// Initializes Firebase, Mobile Ads, and sets the system UI style.
void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  if (Platform.isWindows) {
    await windowManager.ensureInitialized();
    WindowOptions windowOptions = const WindowOptions(
      size: Size(420, 800),
      minimumSize: Size(420, 800),
      center: true,
      backgroundColor: Colors.transparent,
      skipTaskbar: false,
      titleBarStyle: TitleBarStyle.normal,
      title: "mubVPN Desktop",
    );
    windowManager.waitUntilReadyToShow(windowOptions, () async {
      await windowManager.show();
      await windowManager.focus();
    });
  }

  try {
    await Firebase.initializeApp();
  } catch (e) {
    debugPrint("Firebase init error: $e");
  }

  if (Platform.isAndroid) {
    try {
      // REVENUECAT CONFIGURATION
      await Purchases.setLogLevel(LogLevel.debug);
      PurchasesConfiguration configuration = PurchasesConfiguration("test_MoNKbiToBirXEtXwJldOcoGOmkG");
      await Purchases.configure(configuration);
      debugPrint("✅ RevenueCat configured successfully");
    } catch (e) {
      debugPrint("❌ RevenueCat configuration error: $e");
    }
  }

  MobileAds.instance.initialize();
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.light,
  ));
  runApp(const MubVpnApp());
}

/// The root widget of the application.
/// Configures multi-provider for state management and handles global themes.
class MubVpnApp extends StatelessWidget {
  const MubVpnApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => ThemeProvider()),
        ChangeNotifierProvider(create: (_) => StatsProvider()),
        ChangeNotifierProvider(create: (_) => NotificationProvider()),
        ChangeNotifierProvider(create: (_) => LanguageProvider()),
        ChangeNotifierProvider(create: (_) => AdsProvider()..loadAds()),
        ChangeNotifierProvider(create: (_) => SubscriptionProvider()),
        ChangeNotifierProvider(create: (_) => SystemProvider()),
        // VpnProvider depends on other providers and is updated via ProxyProvider
        ChangeNotifierProxyProvider4<StatsProvider, AdsProvider, SubscriptionProvider, LanguageProvider, VpnProvider>(
          create: (_) => VpnProvider(),
          update: (_, stats, ads, sub, lang, vpn) {
            final provider = vpn ?? VpnProvider();
            return provider..updateRefs(stats, ads, sub, lang);
          },
        ),
      ],
      child: const _AppContent(),
    );
  }
}

/// internal widget to build the [MaterialApp] with theme and localization.
class _AppContent extends StatelessWidget {
  const _AppContent();

  @override
  Widget build(BuildContext context) {
    final theme = context.watch<ThemeProvider>();
    final langProv = context.watch<LanguageProvider>();
    
    // Update language reference in SubscriptionProvider
    context.read<SubscriptionProvider>().updateLangRef(langProv);

    return MaterialApp(
      title: 'mubVPN',
      debugShowCheckedModeBanner: false,
      themeMode: theme.themeMode,
      theme: ThemeData(
        brightness: Brightness.light,
        scaffoldBackgroundColor: Colors.white,
        colorScheme: ColorScheme.fromSeed(
            seedColor: AppColors.accent, brightness: Brightness.light),
        fontFamily: 'SF Pro Display',
        useMaterial3: true,
      ),
      darkTheme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: AppColors.bg,
        colorScheme: ColorScheme.fromSeed(
            seedColor: AppColors.accent, brightness: Brightness.dark),
        fontFamily: 'SF Pro Display',
        useMaterial3: true,
      ),
      home: StreamBuilder<User?>(
        stream: FirebaseAuth.instance.authStateChanges(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const SplashScreen();
          }
          if (snapshot.hasData && snapshot.data != null) {
            return const MainShell();
          }
          return const LoginScreen();
        },
      ),
      routes: {
        '/onboarding': (_) => const OnboardingScreen(),
        '/login': (_) => const LoginScreen(),
        '/registration': (_) => const RegistrationScreen(),
        '/main': (_) => const MainShell(),
        '/paywall': (_) => const PaywallScreen(),
        '/payment': (_) => const PaymentScreen(),
        '/add-server': (_) => const AddServerScreen(),
        '/servers': (_) => const ServersScreen(),
        '/stats': (_) => const StatsScreen(),
        '/notifications': (_) => const NotificationsScreen(),
      },
    );
  }
}

/// The main shell of the app containing the bottom navigation bar and indexed stack of pages.
class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _currentIndex = 0;

  @override
  void initState() {
    super.initState();
    // Sync premium status with Firebase after the first frame
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final user = FirebaseAuth.instance.currentUser;
      if (user != null) {
        context.read<SubscriptionProvider>().syncWithFirebase(user.uid);
      }
      
      // Android 13+ үчүн Билдирмелерге уруксат суроо (КЛЮЧ ҮЧҮН ЭҢ МААНИЛҮҮ)
      if (Platform.isAndroid) {
        const MethodChannel('com.klmub.mubvpn/notifications')
            .invokeMethod('requestNotificationPermission')
            .then((granted) {
              debugPrint("Notification permission granted: $granted");
            })
            .catchError((e) => debugPrint("Notification permission error: $e"));
      }
    });
  }

  final _pages = const [
    HomeScreen(),
    ServersScreen(),
    SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    final lang = context.watch<LanguageProvider>().lang;

    return Scaffold(
      extendBody: true,
      backgroundColor: const Color(0xFF080C10),
      body: IndexedStack(
        index: _currentIndex,
        children: _pages,
      ),
      bottomNavigationBar: _buildBottomNav(lang),
    );
  }

  /// Builds the custom floating bottom navigation bar.
  Widget _buildBottomNav(String lang) {
    return Container(
      height: 82,
      margin: const EdgeInsets.fromLTRB(20, 0, 20, 28),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.03),
        borderRadius: BorderRadius.circular(34),
        border: Border.all(
          color: Colors.white.withValues(alpha: 0.06),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildNavItem(0, Icons.grid_view_rounded, t('home', lang)),
          _buildNavItem(1, Icons.language_rounded, t('servers', lang)),
          _buildNavItem(2, Icons.settings_outlined, t('settings', lang)),
        ],
      ),
    );
  }

  /// Builds an individual navigation item for the bottom bar.
  Widget _buildNavItem(int index, IconData icon, String label) {
    final bool sel = _currentIndex == index;
    return Expanded(
      child: GestureDetector(
        onTap: () => setState(() => _currentIndex = index),
        behavior: HitTestBehavior.opaque,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              color: sel
                  ? AppColors.accent
                  : Colors.white.withValues(alpha: 0.30),
              size: 26,
            ),
            const SizedBox(height: 5),
            Text(
              label,
              style: TextStyle(
                color: sel
                    ? AppColors.accent
                    : Colors.white.withValues(alpha: 0.30),
                fontSize: 10,
                fontWeight: sel ? FontWeight.w600 : FontWeight.w400,
                letterSpacing: 0.2,
              ),
            ),
            const SizedBox(height: 5),
            AnimatedContainer(
              duration: const Duration(milliseconds: 280),
              curve: Curves.easeInOut,
              width: sel ? 5 : 0,
              height: sel ? 5 : 0,
              decoration: BoxDecoration(
                color: sel ? AppColors.accent : Colors.transparent,
                shape: BoxShape.circle,
                boxShadow: sel
                    ? [
                        BoxShadow(
                          color: AppColors.accent.withValues(alpha: 0.7),
                          blurRadius: 8,
                          spreadRadius: 1,
                        )
                      ]
                    : null,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
