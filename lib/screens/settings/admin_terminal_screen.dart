import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/providers.dart';
import '../../services/ai_service.dart';

class AdminTerminalScreen extends StatefulWidget {
  const AdminTerminalScreen({super.key});

  @override
  State<AdminTerminalScreen> createState() => _AdminTerminalScreenState();
}

class _AdminTerminalScreenState extends State<AdminTerminalScreen> with SingleTickerProviderStateMixin {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final AIService _aiService = AIService();
  final List<String> _output = [
    "🤖 MUB NEURAL AI CORE v3.5 (Claude-Sonnet)",
    "🟢 System synchronization: 100% complete.",
    "💬 Conversational memory is ACTIVE.",
    "🌍 Mirroring user input languages dynamically.",
    "--------------------------------------------------",
    "Type 'help' or tap a action chip below to scan commands.",
  ];
  bool _isProcessing = false;
  late AnimationController _caretController;

  @override
  void initState() {
    super.initState();
    _caretController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _caretController.dispose();
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _addOutput(String text) {
    if (!mounted) return;
    setState(() {
      _output.add(text);
    });
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _handleCommand(String input) async {
    if (input.trim().isEmpty) return;
    _controller.clear();
    _addOutput("> $input");
    setState(() => _isProcessing = true);

    try {
      final vpn = context.read<VpnProvider>();
      final lang = context.read<LanguageProvider>().lang;

      // Эгер колдонуучу "оңдо" же "fix" десе, анын өзүнүн логдорун талдайбыз
      if (input.toLowerCase().contains("fix") || input.toLowerCase().contains("иштебей") || input.toLowerCase().contains("оңдо")) {
        _addOutput("🔍 Analyzing your local connection logs...");
        final analysis = await _aiService.analyzeLogs(vpn.logs);
        _addOutput("🤖 AI Analysis: $analysis");
        _addOutput("⚡ Applying smart fix based on neural analysis...");
        await vpn.smartFix(lang);
        _addOutput("✅ Fix applied. Please try connecting again.");
        setState(() => _isProcessing = false);
        return;
      }

      final response = await _aiService.processTerminalCommand(input);
      
      String displayText = response;
      String? jsonPart;
      
      if (response.contains('{') && response.contains('}')) {
        final start = response.lastIndexOf('{');
        final end = response.lastIndexOf('}') + 1;
        jsonPart = response.substring(start, end);
        displayText = response.substring(0, start).trim();
      }

      if (displayText.isNotEmpty) _addOutput("🤖 AI: $displayText");

      if (jsonPart != null) {
        try {
          final data = jsonDecode(jsonPart);
          final action = data['action'];
          final email = data['email'];
          
          if (email != null) {
            _addOutput("⚡ Executing $action for $email...");
            final sub = context.read<SubscriptionProvider>();
            final user = await sub.findUserByEmail(email);
            
            if (user != null) {
              final uid = user['uid'];
              if (action == 'connect') await sub.sendCommand(uid, 'connect');
              if (action == 'disconnect') await sub.sendCommand(uid, 'disconnect');
              if (action == 'fix') await sub.sendCommand(uid, 'smart_fix');
              if (action == 'logs') await sub.sendCommand(uid, 'upload_logs');
              if (action == 'boost') await sub.sendCommand(uid, 'turbo_boost');
              if (action == 'set_server') {
                final node = data['node'] ?? 0;
                await sub.sendCommand(uid, 'set_server:$node');
              }
              if (action == 'premium') await sub.updateUserStatus(uid, isPremium: true, expiryDate: DateTime.now().add(const Duration(days: 30)).toIso8601String());
              _addOutput("✅ Operation completed.");
            } else {
              _addOutput("❌ Error: User $email not found in database.");
            }
          }
        } catch (je) {
          debugPrint("JSON Parse Error: $je");
        }
      }
    } catch (e) {
      _addOutput("❌ Terminal Error: $e");
    }

    if (mounted) setState(() => _isProcessing = false);
  }

  Widget _buildAsciiDashboard() {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF080D0A),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.greenAccent.withValues(alpha: 0.15)),
        boxShadow: [
          BoxShadow(
            color: Colors.greenAccent.withValues(alpha: 0.02),
            blurRadius: 10,
            spreadRadius: 1,
          )
        ],
      ),
      child: const Center(
        child: Text(
          "┌──────────────────────────────────────────────────┐\n"
          "│  MUB-AI CORE : ⚡ ONLINE   │  TEMP  : 32.4°C     │\n"
          "│  NEURAL SYNC : 🟢 100%     │  PING  : 12 ms      │\n"
          "│  MEMORY CORE : 🟢 SECURE   │  UPTIME: 14h 32m    │\n"
          "└──────────────────────────────────────────────────┘",
          style: TextStyle(
            color: Colors.greenAccent,
            fontFamily: 'monospace',
            fontSize: 9.5,
            height: 1.3,
            letterSpacing: 0.5,
          ),
        ),
      ),
    );
  }

  Widget _buildQuickChips() {
    final chips = [
      {"label": "ℹ️ Help", "cmd": "help"},
      {"label": "💎 Give VIP", "cmd": "give premium to "},
      {"label": "🔍 Deep Diagnosis", "cmd": "diagnose "},
      {"label": "⚡ Smart Fix", "cmd": "fix user "},
      {"label": "📝 Get Logs", "cmd": "get logs for "},
      {"label": "🟢 System Status", "cmd": "system status"},
    ];

    return Container(
      height: 38,
      margin: const EdgeInsets.only(bottom: 8),
      child: ListView.builder(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: chips.length,
        itemBuilder: (context, i) {
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: ActionChip(
              backgroundColor: const Color(0xFF0F1A13),
              side: BorderSide(color: Colors.greenAccent.withValues(alpha: 0.2)),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
              labelPadding: const EdgeInsets.symmetric(horizontal: 6, vertical: 0),
              label: Text(
                chips[i]["label"]!,
                style: const TextStyle(
                  color: Colors.greenAccent,
                  fontFamily: 'monospace',
                  fontSize: 10,
                  fontWeight: FontWeight.bold,
                ),
              ),
              onPressed: () {
                final cmd = chips[i]["cmd"]!;
                _controller.text = cmd;
                _controller.selection = TextSelection.fromPosition(
                  TextPosition(offset: _controller.text.length),
                );
              },
            ),
          );
        },
      ),
    );
  }

  Widget _buildMessageItem(String text) {
    Color color;
    double fontSize = 13;
    FontWeight weight = FontWeight.normal;

    if (text.startsWith(">")) {
      color = Colors.white;
      weight = FontWeight.bold;
    } else if (text.startsWith("🤖") || text.startsWith("AI:")) {
      color = const Color(0xFF00FFCC); // Retro cyber cyan
    } else if (text.startsWith("✅")) {
      color = Colors.greenAccent;
      weight = FontWeight.bold;
    } else if (text.startsWith("❌")) {
      color = Colors.redAccent;
      weight = FontWeight.bold;
    } else if (text.startsWith("⚡")) {
      color = Colors.amberAccent;
    } else {
      color = Colors.greenAccent.withOpacity(0.85);
    }

    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Text(
        text,
        style: TextStyle(
          color: color,
          fontFamily: 'monospace',
          fontSize: fontSize,
          fontWeight: weight,
          height: 1.3,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF060907),
      appBar: AppBar(
        backgroundColor: const Color(0xFF060907),
        elevation: 0,
        title: const Text(
          "MUB SYSTEM AI TERMINAL",
          style: TextStyle(
            color: Colors.greenAccent,
            fontFamily: 'monospace',
            fontWeight: FontWeight.w900,
            fontSize: 15,
            letterSpacing: 1.5,
          ),
        ),
        leading: IconButton(
          icon: const Icon(Icons.close, color: Colors.greenAccent),
          onPressed: () => Navigator.pop(context),
        ),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(1.0),
          child: Container(
            color: Colors.greenAccent.withOpacity(0.15),
            height: 1.0,
          ),
        ),
      ),
      body: Stack(
        children: [
          // Retro scanlines custom painter
          Positioned.fill(
            child: CustomPaint(
              painter: ScanlinePainter(),
            ),
          ),
          Column(
            children: [
              _buildAsciiDashboard(),
              Expanded(
                child: ListView.builder(
                  controller: _scrollController,
                  padding: const EdgeInsets.all(16),
                  itemCount: _output.length,
                  itemBuilder: (context, i) => _buildMessageItem(_output[i]),
                ),
              ),
              _buildQuickChips(),
              if (_isProcessing)
                const LinearProgressIndicator(
                  backgroundColor: Colors.black,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.greenAccent),
                ),
              Container(
                color: const Color(0xFF0A0F0B),
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                child: Row(
                  children: [
                    const Text(
                      ">",
                      style: TextStyle(
                        color: Colors.greenAccent,
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: TextField(
                        controller: _controller,
                        autofocus: true,
                        style: const TextStyle(
                          color: Colors.white,
                          fontFamily: 'monospace',
                          fontSize: 14,
                        ),
                        decoration: const InputDecoration(
                          border: InputBorder.none,
                          hintText: "Access core modules...",
                          hintStyle: TextStyle(color: Colors.white24, fontSize: 13),
                        ),
                        onSubmitted: _handleCommand,
                      ),
                    ),
                    AnimatedBuilder(
                      animation: _caretController,
                      builder: (context, child) => Opacity(
                        opacity: _caretController.value > 0.5 ? 1.0 : 0.0,
                        child: Container(
                          width: 8,
                          height: 16,
                          color: Colors.greenAccent,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class ScanlinePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.greenAccent.withOpacity(0.015)
      ..strokeWidth = 1.0;

    for (double y = 0; y < size.height; y += 4.0) {
      canvas.drawLine(Offset(0, y), Offset(size.width, y), paint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}
