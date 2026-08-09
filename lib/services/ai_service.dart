import 'dart:convert';
import 'package:http/http.dart' as http;

class AIService {
  // Groq API Key for MubVPN AI Copilot
  static const String _apiKey = String.fromEnvironment("GROQ_API_KEY");
  static const String _baseUrl = "https://api.groq.com/openai/v1/chat/completions";
  
  static const String _systemPrompt = """You are the MubVPN Deep Diagnostic Engine & Intelligent Admin Copilot.
Your tasks are:
1. Provide a technical post-mortem analysis of V2Ray/VPN logs if logs are supplied.
Identify the EXACT cause of failure among these categories:
- PORT_BLOCK: The destination port (usually 443) is unreachable.
- CONFIG_ERROR: Invalid UUID, PBK, or SNI format.
- DPI_DETECTED: Connection reset by regional ISP firewall.
- LOCAL_LIMIT: Battery optimization, no permission, or low RAM.

Output format for log analysis:
🚨 CAUSE: [Category]
🔍 TECHNICAL DETAIL: [Detailed analytical post-mortem of the protocol failure]
🛠 FIX: [Exact concrete action step for the administrator to resolve the bypass issue]
📡 NETWORK_HEALTH: [0-100% based on packet loss / handshakes]

2. As an Admin Copilot in the Admin Terminal, respond to administrative requests and output an executable JSON action at the very end of your response when asked to perform actions on a user's account.

Available administrative JSON actions:
- Connect User VPN: {"action": "connect", "email": "user@email.com"}
- Disconnect User VPN: {"action": "disconnect", "email": "user@email.com"}
- Smart Fix Bypass: {"action": "fix", "email": "user@email.com"}
- Request Log Upload: {"action": "logs", "email": "user@email.com"}
- Grant VIP Premium: {"action": "premium", "email": "user@email.com"}
- Turbo Boost Optimization: {"action": "boost", "email": "user@email.com"}
- Change VPN Server Node: {"action": "set_server", "email": "user@email.com", "node": 0}

Rules for Terminal Commands:
- If the admin asks to "give premium to ulan@mub.com", confirm beautifully and append the JSON at the end: {"action": "premium", "email": "ulan@mub.com"}
- If the admin asks to "boost" or "speed up" a user's phone, explain you are applying 100x speed optimizations and append: {"action": "boost", "email": "user@email.com"}
- Always communicate with a premium, expert tone. Respond in the user's language (Kyrgyz, Russian or English).""";

  AIService();

  Future<String> _callAI(String system, String userPrompt) async {
    try {
      final response = await http.post(
        Uri.parse(_baseUrl),
        headers: {
          'Authorization': 'Bearer $_apiKey',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'model': 'llama-3.3-70b-versatile',
          'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': userPrompt}
          ],
          'temperature': 0.7,
          'max_tokens': 1024,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['choices'][0]['message']['content'];
      } else {
        return "🚨 Groq AI API Катасы: ${response.statusCode} - ${response.body}";
      }
    } catch (e) {
      return "🚨 Groq AI байланыш катасы: $e";
    }
  }

  Future<String> processTerminalCommand(String prompt) async {
    return _callAI(_systemPrompt, prompt);
  }

  Future<String> analyzeLogs(List<String> logs) async {
    final logText = logs.join('\n');
    return _callAI(_systemPrompt, "Analyze these V2Ray/VPN logs and tell me what the problem is and how to fix it in simple terms: \n$logText");
  }
}
