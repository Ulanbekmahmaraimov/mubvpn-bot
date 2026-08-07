import 'package:flutter/foundation.dart';
import 'package:google_mobile_ads/google_mobile_ads.dart';

class AdsProvider extends ChangeNotifier {
  InterstitialAd? _interstitialAd;
  RewardedAd? _rewardedAd;
  bool _isAdLoaded = false;
  int _loadAttempts = 0;

  bool get isAdLoaded => _isAdLoaded;

  // ТЕСТТИК ID-лер (AdMob тараптан берилген расмий тесттик бирдиктер)
  final String interstitialAdUnitId = kDebugMode 
      ? 'ca-app-pub-3940256099942544/1033173712' 
      : 'ca-app-pub-XXXXXXXXXXXXXXXX/XXXXXXXXXX';
      
  final String rewardedAdUnitId = kDebugMode 
      ? 'ca-app-pub-3940256099942544/5224354917' 
      : 'ca-app-pub-XXXXXXXXXXXXXXXX/XXXXXXXXXX';

  void loadAds() {
    _loadInterstitial();
    _loadRewarded();
  }

  void _loadInterstitial() {
    InterstitialAd.load(
      adUnitId: interstitialAdUnitId,
      request: const AdRequest(),
      adLoadCallback: InterstitialAdLoadCallback(
        onAdLoaded: (ad) {
          debugPrint('Interstitial жарнама жүктөлдү ✅');
          _interstitialAd = ad;
          _isAdLoaded = true;
          notifyListeners();
        },
        onAdFailedToLoad: (error) {
          debugPrint('Interstitial катасы ❌: $error');
          _interstitialAd = null;
          _checkAdStatus();
        },
      ),
    );
  }

  void _loadRewarded() {
    RewardedAd.load(
      adUnitId: rewardedAdUnitId,
      request: const AdRequest(),
      rewardedAdLoadCallback: RewardedAdLoadCallback(
        onAdLoaded: (ad) {
          debugPrint('Rewarded жарнама жүктөлдү ✅');
          _rewardedAd = ad;
          _isAdLoaded = true;
          notifyListeners();
        },
        onAdFailedToLoad: (error) {
          debugPrint('Rewarded катасы ❌: $error');
          _rewardedAd = null;
          _checkAdStatus();
        },
      ),
    );
  }

  void _checkAdStatus() {
    _isAdLoaded = _interstitialAd != null || _rewardedAd != null;
    if (!_isAdLoaded) {
      _loadAttempts++;
      if (_loadAttempts < 5) {
        Future.delayed(const Duration(seconds: 30), () => loadAds());
      }
    }
    notifyListeners();
  }

  void showAdBeforeConnect({required Function onFinished}) {
    // 1. Адегенде Interstitial текшеребиз
    if (_interstitialAd != null) {
      debugPrint('Interstitial көрсөтүлүүдө...');
      _interstitialAd!.fullScreenContentCallback = FullScreenContentCallback(
        onAdDismissedFullScreenContent: (ad) {
          ad.dispose();
          _interstitialAd = null;
          _isAdLoaded = _rewardedAd != null;
          loadAds();
          onFinished();
        },
        onAdFailedToShowFullScreenContent: (ad, error) {
          ad.dispose();
          _interstitialAd = null;
          onFinished();
        },
      );
      _interstitialAd!.show();
      return;
    }

    // 2. Эгер ал жок болсо, Rewarded текшеребиз
    if (_rewardedAd != null) {
      debugPrint('Rewarded көрсөтүлүүдө...');
      _rewardedAd!.fullScreenContentCallback = FullScreenContentCallback(
        onAdDismissedFullScreenContent: (ad) {
          ad.dispose();
          _rewardedAd = null;
          _isAdLoaded = _interstitialAd != null;
          loadAds();
          onFinished();
        },
        onAdFailedToShowFullScreenContent: (ad, error) {
          ad.dispose();
          _rewardedAd = null;
          onFinished();
        },
      );
      _rewardedAd!.show(onUserEarnedReward: (_, __) {});
      return;
    }

    // 3. Эч бири жок болсо, күттүрбөйбүз
    debugPrint('Жарнамалар даяр эмес, өткөрүлүүдө...');
    loadAds();
    onFinished();
  }
}
