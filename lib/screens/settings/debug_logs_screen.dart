import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import '../../constants/colors.dart';
import '../../providers/providers.dart';

class DebugLogsScreen extends StatelessWidget {
  const DebugLogsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final vpn = context.watch<VpnProvider>();
    final lang = context.watch<LanguageProvider>().lang;

    return Scaffold(
      backgroundColor: const Color(0xFF060A0E),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        title: Text(
          lang == 'ky' ? 'Каталар журналы' : 'Debug Logs',
          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.cloud_upload_outlined, color: AppColors.blue),
            onPressed: () async {
              final sub = context.read<SubscriptionProvider>();
              await sub.uploadLogs(vpn.logs);
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text(lang == 'ky' ? 'Жөнөтүлдү!' : 'Logs sent!')),
                );
              }
            },
          ),
          IconButton(
            icon: const Icon(Icons.copy_rounded, color: AppColors.accent),
            onPressed: () {
              Clipboard.setData(ClipboardData(text: vpn.logs.join('\n')));
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text(lang == 'ky' ? 'Көчүрүлдү!' : 'Logs copied!')),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.delete_outline_rounded, color: Colors.redAccent),
            onPressed: () => vpn.clearLogs(),
          ),
        ],
      ),
      body: vpn.logs.isEmpty
          ? Center(
              child: Text(
                lang == 'ky' ? 'Логдор жок' : 'No logs found',
                style: const TextStyle(color: Colors.white24),
              ),
            )
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: vpn.logs.length,
              reverse: true,
              itemBuilder: (context, index) {
                final log = vpn.logs[vpn.logs.length - 1 - index];
                Color logColor = Colors.white70;
                if (log.contains('❌') || log.contains('error') || log.contains('failed')) {
                  logColor = Colors.redAccent;
                } else if (log.contains('✅') || log.contains('success') || log.contains('granted')) {
                  logColor = AppColors.accent;
                } else if (log.contains('🚀')) {
                  logColor = AppColors.blue;
                }

                return Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Text(
                    log,
                    style: TextStyle(
                      color: logColor,
                      fontSize: 12,
                      fontFamily: 'monospace',
                    ),
                  ),
                );
              },
            ),
    );
  }
}
