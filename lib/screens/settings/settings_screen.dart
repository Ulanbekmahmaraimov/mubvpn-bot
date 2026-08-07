import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../../constants/colors.dart';
import '../../constants/translations.dart';
import '../../models/vpn.dart';
import '../../providers/providers.dart';
import 'package:url_launcher/url_launcher.dart';
import 'split_tunneling_screen.dart';
import 'debug_logs_screen.dart';
import 'admin_panel_screen.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late TextEditingController _subController;

  @override
  void initState() {
    super.initState();
    final vpn = context.read<VpnProvider>();
    _subController = TextEditingController(text: vpn.subscriptionUrl);
  }

  @override
  void dispose() {
    _subController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final vpn = context.watch<VpnProvider>();
    final theme = context.watch<ThemeProvider>();
    final sub = context.watch<SubscriptionProvider>();
    final lang = context.watch<LanguageProvider>().lang;
    
    // Эгер серверден шилтеме өзгөрсө, контроллерди жаңылайбыз
    if (_subController.text != vpn.subscriptionUrl && !vpn.isLoadingSubscription) {
      _subController.text = vpn.subscriptionUrl;
    }

    return Scaffold(
      backgroundColor: const Color(0xFF060A0E),
      body: Stack(
        children: [
          Positioned(
            top: -100,
            left: -50,
            child: _BlurredBlob(
              color: AppColors.accent.withValues(alpha: 0.08),
              size: 300,
            ),
          ),
          SafeArea(
            child: SingleChildScrollView(
              padding: const EdgeInsets.only(bottom: 100),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildHeader(lang),
                  const SizedBox(height: 24),
                  _buildUserProfile(context, lang),
                  if (sub.isPremium) ...[
                    const SizedBox(height: 16),
                    _buildPremiumStatusCard(sub, lang),
                  ],
                  const SizedBox(height: 28),
                  _buildSectionLabel(t('connection_section', lang)),
                  _buildCard([
                    _buildToggleItem(
                      icon: Icons.shield_outlined,
                      title: t('kill_switch', lang),
                      description: t('kill_switch_desc', lang),
                      value: vpn.killSwitch,
                      onChanged: (v) => vpn.setKillSwitch(v),
                    ),
                    _buildDivider(),
                    _buildToggleItem(
                      icon: Icons.bolt_rounded,
                      title: t('auto_connect', lang),
                      description: t('auto_connect_desc', lang),
                      value: vpn.autoConnect,
                      onChanged: (v) => vpn.setAutoConnect(v),
                    ),
                  ]),
                  const SizedBox(height: 28),
                  _buildSectionLabel(t('advanced_section', lang)),
                  _buildCard([
                    _buildToggleItem(
                      icon: Icons.alt_route_rounded,
                      title: t('split_tunneling', lang),
                      description: t('split_tunneling_desc', lang),
                      value: vpn.splitTunneling,
                      onChanged: (v) {
                        vpn.setSplitTunneling(v);
                        if (v) {
                          Navigator.push(
                            context,
                            MaterialPageRoute(builder: (context) => const SplitTunnelingScreen()),
                          );
                        }
                      },
                    ),
                    _buildDivider(),
                    _buildClickItem(
                      icon: Icons.history_rounded,
                      title: t('protocol', lang),
                      value: _protocolName(vpn.protocol),
                      onTap: () => _showProtocolDialog(context, vpn, lang),
                    ),
                  ]),
                  const SizedBox(height: 28),
                  _buildSectionLabel(t('appearance_section', lang)),
                  _buildCard([
                    _buildToggleItem(
                      icon: Icons.nightlight_round_outlined,
                      title: theme.isDarkMode ? t('dark_mode', lang) : t('light_mode', lang),
                      description: t('change_appearance', lang),
                      value: theme.isDarkMode,
                      onChanged: (v) => theme.toggleTheme(v),
                    ),
                    _buildDivider(),
                    _buildClickItem(
                      icon: Icons.language_rounded,
                      title: t('language', lang),
                      value: kLanguages.firstWhere((l) => l['code'] == lang)['name']!,
                      onTap: () => _showLanguageDialog(context, context.read<LanguageProvider>(), lang),
                    ),
                  ]),
                  const SizedBox(height: 28),
                  _buildSectionLabel(t('support_section', lang)),
                  _buildCard([
                    _buildClickItem(
                      icon: Icons.headset_mic_outlined,
                      title: t('contact_support', lang),
                      value: '',
                      onTap: () async {
                        final url = Uri.parse("https://t.me/kl_mub");
                        if (await canLaunchUrl(url)) {
                          await launchUrl(url, mode: LaunchMode.externalApplication);
                        }
                      },
                    ),
                    _buildDivider(),
                    _buildClickItem(
                      icon: Icons.feedback_outlined,
                      title: t('report_problem', lang),
                      value: '',
                      onTap: () => _showSupportDialog(context, sub, vpn, lang),
                    ),
                  ]),
                  const SizedBox(height: 28),
                  _buildSectionLabel(t('troubleshooting_section', lang)),
                  _buildCard([
                    if (sub.isAdmin || sub.isManager) ...[
                      _buildClickItem(
                        icon: Icons.admin_panel_settings_outlined,
                        iconColor: AppColors.accent,
                        title: t('admin_panel', lang),
                        value: sub.role.toUpperCase(),
                        onTap: () => Navigator.push(
                          context,
                          MaterialPageRoute(builder: (context) => const AdminPanelScreen()),
                        ),
                      ),
                      _buildDivider(),
                    ],
                    _buildClickItem(
                      icon: Icons.bug_report_outlined,
                      title: t('debug_logs', lang),
                      value: '',
                      onTap: () => Navigator.push(
                        context,
                        MaterialPageRoute(builder: (context) => const DebugLogsScreen()),
                      ),
                    ),
                    _buildDivider(),
                    _buildClickItem(
                      icon: Icons.build_circle_outlined,
                      title: t('smart_fix', lang),
                      value: vpn.isProcessing ? '...' : '',
                      onTap: () async {
                        await vpn.smartFix(lang);
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text(t('fix_completed', lang)),
                              backgroundColor: AppColors.accent,
                            ),
                          );
                        }
                      },
                    ),
                  ]),
                  const SizedBox(height: 28),
                  _buildSectionLabel(t('servers_section', lang)),
                  _buildSubscriptionCard(context, vpn, lang),
                  const SizedBox(height: 28),
                  _buildSectionLabel(t('account_section', lang)),
                  _buildCard([
                    _buildClickItem(
                      icon: Icons.logout_rounded,
                      title: t('logout', lang),
                      value: '',
                      onTap: () async {
                        await FirebaseAuth.instance.signOut();
                        if (context.mounted) {
                          Navigator.pushNamedAndRemoveUntil(context, '/login', (route) => false);
                        }
                      },
                    ),
                  ]),

                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildUserProfile(BuildContext context, String lang) {
    final user = FirebaseAuth.instance.currentUser;
    if (user == null) return const SizedBox.shrink();

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(22),
          border: Border.all(color: Colors.white.withValues(alpha: 0.06)),
        ),
        child: Row(
          children: [
            Container(
              width: 50,
              height: 50,
              decoration: BoxDecoration(
                color: AppColors.accent.withValues(alpha: 0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.person_rounded, color: AppColors.accent, size: 28),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    user.displayName ?? t('user_label', lang),
                    style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  Text(
                    user.email ?? '',
                    style: TextStyle(color: Colors.white.withValues(alpha: 0.4), fontSize: 13),
                  ),
                  const SizedBox(height: 8),
                  GestureDetector(
                    onTap: () {
                      Clipboard.setData(ClipboardData(text: user.uid));
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text(t('uid_copied', lang)), duration: const Duration(seconds: 1)),
                      );
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.05),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Flexible(
                            child: Text(
                              "UID: ${user.uid}",
                              style: TextStyle(color: AppColors.accent.withValues(alpha: 0.7), fontSize: 10, fontFamily: 'monospace'),
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                          const SizedBox(width: 4),
                          const Icon(Icons.copy_rounded, size: 12, color: Colors.white24),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPremiumStatusCard(SubscriptionProvider sub, String lang) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [
              AppColors.accent.withValues(alpha: 0.15),
              AppColors.accent.withValues(alpha: 0.05),
            ],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(22),
          border: Border.all(color: AppColors.accent.withValues(alpha: 0.3)),
        ),
        child: Row(
          children: [
            Container(
              width: 44,
              height: 44,
              decoration: const BoxDecoration(
                color: AppColors.accent,
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.star_rounded, color: Colors.black, size: 26),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    t('premium_access', lang).toUpperCase(),
                    style: const TextStyle(
                      color: AppColors.accent,
                      fontSize: 12,
                      fontWeight: FontWeight.w900,
                      letterSpacing: 1.2,
                    ),
                    overflow: TextOverflow.ellipsis,
                    maxLines: 1,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    sub.remainingTime,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                    overflow: TextOverflow.ellipsis,
                    maxLines: 1,
                  ),
                  Text(
                    "${t('expires_on', lang)}: ${sub.expiryDateStr}",
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.5),
                      fontSize: 12,
                    ),
                    overflow: TextOverflow.ellipsis,
                    maxLines: 1,
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSubscriptionCard(BuildContext context, VpnProvider vpn, String lang) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white.withValues(alpha: 0.05),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
        ),
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.link_rounded, color: AppColors.accent, size: 20),
                    const SizedBox(width: 8),
                    Text(
                      t('subscription_url', lang),
                      style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 15),
                    ),
                    const Spacer(),
                    if (vpn.isLoadingSubscription)
                      const SizedBox(
                        width: 20, height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.accent),
                      ),
                  ],
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: _subController,
                  style: const TextStyle(color: Colors.white, fontSize: 13),
                  decoration: InputDecoration(
                    hintText: 'https://...',
                    hintStyle: TextStyle(color: Colors.white.withValues(alpha: 0.3), fontSize: 13),
                    filled: true,
                    fillColor: Colors.white.withValues(alpha: 0.06),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide.none,
                    ),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  ),
                ),
                if (vpn.subscriptionError.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text(vpn.subscriptionError, style: const TextStyle(color: Colors.redAccent, fontSize: 12)),
                ],
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        '${vpn.servers.length} ${t('servers_loaded', lang)}',
                        style: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontSize: 12),
                        overflow: TextOverflow.ellipsis,
                        maxLines: 1,
                      ),
                    ),
                    const SizedBox(width: 8),
                    GestureDetector(
                      onTap: vpn.isLoadingSubscription
                          ? null
                          : () async {
                              final url = _subController.text.trim();
                              if (url.isEmpty) return;
                              final err = await vpn.fetchSubscription(url);
                              if (err == null && context.mounted) {
                                ScaffoldMessenger.of(context).showSnackBar(
                                  SnackBar(
                                    content: Text('✅ ${vpn.servers.length} ${t('servers_loaded', lang)}!'),
                                    backgroundColor: AppColors.accent,
                                  ),
                                );
                              }
                            },
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        decoration: const BoxDecoration(
                          gradient: LinearGradient(colors: [AppColors.accent, AppColors.accentDark]),
                          borderRadius: BorderRadius.all(Radius.circular(10)),
                        ),
                        child: Text(
                          t('download_btn', lang),
                          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 13),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
      ),
    );
  }


  Widget _buildHeader(String lang) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 20, 20, 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            t('settings_title', lang),
            style: const TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.w900),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionLabel(String label) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      child: Text(
        label,
        style: TextStyle(
          color: Colors.white.withValues(alpha: 0.35),
          fontSize: 12,
          fontWeight: FontWeight.w900,
          letterSpacing: 1.5,
        ),
      ),
    );
  }

  Widget _buildCard(List<Widget> children) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      child: Container(
        decoration: BoxDecoration(
          color: AppColors.surface,
          borderRadius: BorderRadius.circular(22),
          border: Border.all(color: Colors.white.withValues(alpha: 0.06)),
        ),
        child: Column(children: children),
      ),
    );
  }

  Widget _buildToggleItem({
    required IconData icon,
    required String title,
    required String description,
    required bool value,
    required ValueChanged<bool> onChanged,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
      child: Row(
        children: [
          Icon(icon, color: AppColors.accent, size: 24),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(title, style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w600)),
                const SizedBox(height: 3),
                Text(description, style: const TextStyle(color: AppColors.textSecondary, fontSize: 12)),
              ],
            ),
          ),
          Switch(
            value: value,
            onChanged: onChanged,
            activeTrackColor: AppColors.accent.withValues(alpha: 0.4),
            activeThumbColor: AppColors.accent,
            inactiveTrackColor: Colors.white.withValues(alpha: 0.08),
            inactiveThumbColor: Colors.white.withValues(alpha: 0.3),
          ),
        ],
      ),
    );
  }

  Widget _buildClickItem({
    required IconData icon,
    required String title,
    required String value,
    required VoidCallback onTap,
    Color? iconColor,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(22),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
        child: Row(
          children: [
            Icon(icon, color: iconColor ?? AppColors.accent, size: 24),
            const SizedBox(width: 16),
            Expanded(child: Text(title, style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w600))),
            Text(value, style: const TextStyle(color: AppColors.textSecondary, fontSize: 14)),
            const SizedBox(width: 6),
            Icon(Icons.chevron_right_rounded, color: Colors.white.withValues(alpha: 0.2), size: 20),
          ],
        ),
      ),
    );
  }

  Widget _buildDivider() {
    return Divider(height: 1, thickness: 1, color: Colors.white.withValues(alpha: 0.05), indent: 58);
  }

  String _protocolName(Protocol p) {
    switch (p) {
      case Protocol.v2ray: return 'V2RAY';
      case Protocol.wireguard: return 'WIREGUARD';
      case Protocol.openvpn: return 'OPENVPN';
      case Protocol.auto: return 'AUTO';
    }
  }

  void _showProtocolDialog(BuildContext context, VpnProvider vpn, String lang) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          padding: const EdgeInsets.fromLTRB(24, 20, 24, 40),
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
            border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(2))),
              const SizedBox(height: 20),
              Text(t('select_protocol', lang),
                  style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),
              Flexible(
                child: ListView(
                  shrinkWrap: true,
                  children: Protocol.values.map((p) => ListTile(
                    contentPadding: const EdgeInsets.symmetric(horizontal: 8),
                    title: Text(_protocolName(p), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
                    trailing: vpn.protocol == p ? const Icon(Icons.check_circle_rounded, color: AppColors.accent) : null,
                    onTap: () {
                      vpn.setProtocol(p);
                      Navigator.pop(context);
                    },
                  )).toList(),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showLanguageDialog(BuildContext context, LanguageProvider provider, String lang) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (context) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          padding: const EdgeInsets.fromLTRB(24, 20, 24, 40),
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
            border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(2))),
              const SizedBox(height: 20),
              Text(t('select_language', lang),
                  style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),
              Flexible(
                child: ListView(
                  shrinkWrap: true,
                  children: kLanguages.map((l) => ListTile(
                    contentPadding: const EdgeInsets.symmetric(horizontal: 8),
                    leading: Text(l['flag']!, style: const TextStyle(fontSize: 24)),
                    title: Text(l['name']!, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
                    trailing: provider.lang == l['code'] ? const Icon(Icons.check_circle_rounded, color: AppColors.accent) : null,
                    onTap: () {
                      provider.setLang(l['code']!);
                      Navigator.pop(context);
                    },
                  )).toList(),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showSupportDialog(BuildContext context, SubscriptionProvider sub, VpnProvider vpn, String lang) {
    final controller = TextEditingController();
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
        child: Container(
          padding: EdgeInsets.fromLTRB(24, 20, 24, MediaQuery.of(context).viewInsets.bottom + 40),
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(28)),
            border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(width: 40, height: 4, decoration: BoxDecoration(color: Colors.white.withValues(alpha: 0.15), borderRadius: BorderRadius.circular(2))),
              const SizedBox(height: 20),
              Text(t('send_ticket_title', lang), style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 20),
              TextField(
                controller: controller,
                maxLines: 5,
                style: const TextStyle(color: Colors.white),
                decoration: InputDecoration(
                  hintText: t('message_hint', lang),
                  hintStyle: TextStyle(color: Colors.white.withValues(alpha: 0.3)),
                  filled: true,
                  fillColor: Colors.white.withValues(alpha: 0.05),
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(16), borderSide: BorderSide.none),
                ),
              ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.accent,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                  ),
                  onPressed: () async {
                    if (controller.text.trim().isEmpty) return;
                    await sub.sendSupportTicket(controller.text.trim(), vpn.logs);
                    if (context.mounted) {
                      Navigator.pop(context);
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text(t('ticket_sent', lang)), backgroundColor: AppColors.accent),
                      );
                    }
                  },
                  child: Text(t('send_btn', lang), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                ),
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
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: color,
        boxShadow: [
          BoxShadow(
            color: color,
            blurRadius: 100,
            spreadRadius: 40,
          )
        ],
      ),
    );
  }
}
