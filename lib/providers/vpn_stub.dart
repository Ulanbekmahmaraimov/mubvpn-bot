import 'dart:async';
import '../constants/translations.dart';

// ky: Бул браузер (Web) үчүн жасалма класс
// ru: Это фейковый класс для браузера (Web)
// en: This is a stub class for browser (Web)
// uz: Bu brauzer (Web) uchun soxta класс
// tj: Ин синфи сохта барои браузер (Web) аст
// kz: Бұл браузер (Web) үшін жасанды класс
// tr: Bu tarayıcı (Web) için sahte bir sınıftır

class OpenVPN {
  Future<void> initialize({
    String? groupIdentifier,
    String? providerBundleIdentifier,
    String? localizedDescription,
    dynamic lastStatus,
    dynamic lastStage,
  }) async {}

  Future<void> connect(String config, String name,
      {String? username,
      String? password,
      List<String>? bypassPackages,
      bool certIsRequired = false}) async {}

  void disconnect() {}

  static Future<String?> filteredConfig(String? config) async {
    return config;
  }

  OpenVPN({dynamic onVpnStatusChanged, dynamic onVpnStageChanged});
}

enum VPNStage {
  prepare,
  authenticating,
  connecting,
  authentication,
  connected,
  disconnected,
  disconnecting,
  denied,
  error,
  waitConnection,
  vpnGenerateConfig,
  getConfig,
  tcpConnect,
  udpConnect,
  assignIp,
  resolve,
  exiting,
  unknown;

  // Тилдерге которуу функциясы / Функция перевода / Translation function
  String localizedName(String lang) {
    return t('vpn_stage_$name', lang);
  }
}
