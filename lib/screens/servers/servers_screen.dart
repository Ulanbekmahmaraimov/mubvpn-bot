import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../constants/translations.dart';
import '../../providers/providers.dart';
import '../../models/vpn.dart';

class ServersScreen extends StatefulWidget {
  const ServersScreen({super.key});

  @override
  State<ServersScreen> createState() => _ServersScreenState();
}

class _ServersScreenState extends State<ServersScreen> {
  String _searchQuery = '';

  @override
  Widget build(BuildContext context) {
    final vpnProvider = context.watch<VpnProvider>();
    final lang = context.watch<LanguageProvider>().lang;
    
    final servers = vpnProvider.servers.where((s) {
      final searchLower = _searchQuery.toLowerCase();
      return s.localizedCountry(lang).toLowerCase().contains(searchLower) || 
             s.localizedCity(lang).toLowerCase().contains(searchLower);
    }).toList();

    return Scaffold(
      backgroundColor: const Color(0xFF05070A),
      body: Stack(
        children: [
          // Арткы фондогу жашыл эффект
          Positioned(
            top: -100,
            right: -50,
            child: Container(
              width: 400,
              height: 400,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: const Color(0xFF00C896).withValues(alpha: 0.1),
              ),
            ),
          ),
          
          SafeArea(
            child: Column(
              children: [
                _buildAppBar(context, lang),
                _buildSearchBar(lang),
                Expanded(
                  child: ListView.separated(
                    padding: const EdgeInsets.fromLTRB(24, 10, 24, 100),
                    itemCount: servers.length,
                    physics: const BouncingScrollPhysics(),
                    separatorBuilder: (_, __) => const SizedBox(height: 12),
                    itemBuilder: (context, index) {
                      final server = servers[index];
                      // Provider'деги чыныгы индексти табабыз
                      final actualIndex = vpnProvider.servers.indexWhere((s) => s.config == server.config);
                      final isSelected = vpnProvider.selectedIndex == actualIndex;
                      return _buildServerItem(server, isSelected, actualIndex, vpnProvider, lang);
                    },
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAppBar(BuildContext context, String lang) {
    final canPop = Navigator.canPop(context);
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Row(
        children: [
          if (canPop) ...[
            GestureDetector(
              onTap: () => Navigator.pop(context),
              child: Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.05),
                  shape: BoxShape.circle,
                  border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
                ),
                child: const Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white, size: 20),
              ),
            ),
            const SizedBox(width: 20),
          ],
          Text(
            t('locations', lang),
            style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  Widget _buildSearchBar(String lang) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 8),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(20),
        child: Container(
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.05),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: Colors.white.withValues(alpha: 0.1)),
          ),
          child: TextField(
            onChanged: (v) => setState(() => _searchQuery = v),
            style: const TextStyle(color: Colors.white),
            decoration: InputDecoration(
              hintText: t('search_servers', lang),
              hintStyle: TextStyle(color: Colors.white.withValues(alpha: 0.3)),
              prefixIcon: Icon(Icons.search_rounded, color: Colors.white.withValues(alpha: 0.3)),
              border: InputBorder.none,
              contentPadding: const EdgeInsets.symmetric(vertical: 15),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildServerItem(VpnServer server, bool isSelected, int index, VpnProvider vpn, String lang) {
    final sub = context.read<SubscriptionProvider>();
    return Padding(
      padding: const EdgeInsets.only(bottom: 2),
      child: GestureDetector(
        onTap: () {
          if (server.isPremium && !sub.isPremium) {
            Navigator.pushNamed(context, '/paywall');
            return;
          }

          // Серверди тандайбыз
          vpn.selectServer(index);

          // Эгерде баракча атайын ачылган болсо (canPop), анда аны жабабыз.
          // Эгер төмөнкү менюдан (BottomNav) ачылган болсо, жаппайбыз.
          if (Navigator.canPop(context)) {
            Navigator.pop(context);
          }
        },
        child: Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: isSelected ? const Color(0xFF00C896).withValues(alpha: 0.15) : Colors.white.withValues(alpha: 0.04),
            borderRadius: BorderRadius.circular(24),
            border: Border.all(
              color: isSelected ? const Color(0xFF00C896).withValues(alpha: 0.4) : Colors.white.withValues(alpha: 0.08),
            ),
          ),
          child: Row(
              children: [
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: Colors.white.withValues(alpha: 0.05),
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: Center(child: Text(server.flag, style: const TextStyle(fontSize: 24))),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        server.localizedCity(lang),
                        style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                      Text(
                        server.localizedCountry(lang),
                        style: TextStyle(color: Colors.white.withValues(alpha: 0.4), fontSize: 12),
                      ),
                    ],
                  ),
                ),
                _buildLoadIndicator(server),
                const SizedBox(width: 12),
                if (server.isPremium)
                  Icon(Icons.workspace_premium_rounded, 
                    color: sub.isPremium ? const Color(0xFFFFD700) : Colors.white24, 
                    size: 20)
                else
                  Icon(
                    isSelected ? Icons.check_circle_rounded : Icons.radio_button_unchecked_rounded,
                    color: isSelected ? const Color(0xFF00C896) : Colors.white.withValues(alpha: 0.1),
                  ),
              ],
            ),
          ),
        ),
    );
  }

  Widget _buildLoadIndicator(VpnServer server) {
    return Column(
      children: [
        Icon(Icons.bar_chart_rounded, color: server.loadColor, size: 18),
        Text(
          '${server.ping}ms',
          style: TextStyle(color: server.loadColor, fontSize: 10, fontWeight: FontWeight.bold),
        ),
      ],
    );
  }
}
