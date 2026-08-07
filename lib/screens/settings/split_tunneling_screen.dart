import 'package:flutter/material.dart';
import 'package:installed_apps/app_info.dart';
import 'package:provider/provider.dart';
import '../../constants/colors.dart';
import '../../constants/translations.dart';
import '../../providers/providers.dart';

class SplitTunnelingScreen extends StatefulWidget {
  const SplitTunnelingScreen({super.key});

  @override
  State<SplitTunnelingScreen> createState() => _SplitTunnelingScreenState();
}

class _SplitTunnelingScreenState extends State<SplitTunnelingScreen> {
  String _searchQuery = "";
  List<AppInfo>? _apps;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadApps();
  }

  Future<void> _loadApps() async {
    final vpn = context.read<VpnProvider>();
    try {
      final apps = await vpn.getInstalledApps();
      if (mounted) {
        setState(() {
          _apps = apps;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final vpn = context.watch<VpnProvider>();
    final lang = context.read<LanguageProvider>().lang;

    return Scaffold(
      backgroundColor: AppColors.bg,
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text(
          t('select_apps', lang),
          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        ),
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: TextField(
              onChanged: (v) => setState(() => _searchQuery = v.toLowerCase()),
              style: const TextStyle(color: Colors.white),
              decoration: InputDecoration(
                hintText: t('search_apps_hint', lang),
                hintStyle: TextStyle(color: Colors.white.withValues(alpha: 0.5)),
                prefixIcon: const Icon(Icons.search, color: AppColors.accent),
                filled: true,
                fillColor: Colors.white.withValues(alpha: 0.05),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(12),
                  borderSide: BorderSide.none,
                ),
              ),
            ),
          ),
          Expanded(
            child: _isLoading 
              ? const Center(child: CircularProgressIndicator(color: AppColors.accent))
              : (_apps == null || _apps!.isEmpty)
                ? Center(
                    child: Text(
                      t('no_apps_found', lang),
                      style: const TextStyle(color: Colors.white70),
                    ),
                  )
                : ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    itemCount: _apps!
                        .where((app) => app.name.toLowerCase().contains(_searchQuery))
                        .length,
                    itemBuilder: (context, index) {
                      final filteredApps = _apps!
                          .where((app) => app.name.toLowerCase().contains(_searchQuery))
                          .toList();
                      final app = filteredApps[index];
                      final isExcluded = vpn.excludedApps.contains(app.packageName);

                      return Container(
                        margin: const EdgeInsets.only(bottom: 8),
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.05),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: ListTile(
                          leading: SizedBox(
                            width: 40,
                            height: 40,
                            child: app.icon != null
                              ? Image.memory(
                                  app.icon!,
                                  errorBuilder: (context, error, stackTrace) =>
                                      const Icon(Icons.android, color: Colors.green),
                                )
                              : const Icon(Icons.android, color: Colors.green),
                          ),
                          title: Text(
                            app.name,
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w500),
                          ),
                          subtitle: Text(
                            app.packageName,
                            style: TextStyle(color: Colors.white.withValues(alpha: 0.5), fontSize: 12),
                          ),
                          trailing: Switch(
                            activeThumbColor: AppColors.accent,
                            value: isExcluded,
                            onChanged: (v) => vpn.toggleAppExclusion(app.packageName),
                          ),
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
