import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:provider/provider.dart';
import '../constants/colors.dart';
import '../constants/translations.dart';
import '../providers/providers.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;
  bool _obscurePassword = true;
  String? _errorMessage;

  Future<void> _signInWithEmail(String lang) async {
    if (_emailController.text.trim().isEmpty || _passwordController.text.trim().isEmpty) {
      setState(() => _errorMessage = t('error_fill_fields', lang));
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      await FirebaseAuth.instance.signInWithEmailAndPassword(
        email: _emailController.text.trim(),
        password: _passwordController.text.trim(),
      );
      if (mounted) {
        Navigator.pushNamedAndRemoveUntil(context, '/main', (route) => false);
      }
    } on FirebaseAuthException catch (e) {
      setState(() {
        if (e.code == 'user-not-found') {
          _errorMessage = t('error_user_not_found', lang);
        } else if (e.code == 'wrong-password') {
          _errorMessage = t('error_wrong_password', lang);
        } else if (e.code == 'invalid-email') {
          _errorMessage = t('error_invalid_email', lang);
        } else {
          _errorMessage = '${t('error_auth_failed', lang)}: ${e.message}';
        }
      });
    } catch (e) {
      setState(() => _errorMessage = t('error_auth_failed', lang));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _signInWithGoogle(String lang) async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final GoogleSignIn googleSignIn = GoogleSignIn();
      await googleSignIn.signOut();
      
      final GoogleSignInAccount? googleUser = await googleSignIn.signIn();
      if (googleUser == null) {
        setState(() => _isLoading = false);
        return;
      }

      final GoogleSignInAuthentication googleAuth = await googleUser.authentication;
      final AuthCredential credential = GoogleAuthProvider.credential(
        accessToken: googleAuth.accessToken,
        idToken: googleAuth.idToken,
      );

      await FirebaseAuth.instance.signInWithCredential(credential);
      if (mounted) {
        Navigator.pushNamedAndRemoveUntil(context, '/main', (route) => false);
      }
    } catch (e) {
      debugPrint("GOOGLE_SIGNIN_ERROR: $e");
      setState(() => _errorMessage = '${t('error_google_failed', lang)}: $e');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final lang = context.watch<LanguageProvider>().lang;

    return Scaffold(
      backgroundColor: const Color(0xFF030303),
      body: Stack(
        children: [
          // ══ ОПТИМИЗАЦИЯЛАНГАН ФОН ══
          ...[
            Positioned(top: -100, left: -50, child: _Blob(color: AppColors.accent.withValues(alpha: 0.15), size: 300)),
            Positioned(bottom: -50, right: -50, child: _Blob(color: AppColors.blue.withValues(alpha: 0.15), size: 350)),
            // Бир гана жалпы блур
            Positioned.fill(
              child: BackdropFilter(
                filter: ImageFilter.blur(sigmaX: 80, sigmaY: 80),
                child: Container(color: Colors.transparent),
              ),
            ),
          ],

          Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(30),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    width: 100,
                    height: 100,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      boxShadow: [BoxShadow(color: AppColors.accent.withValues(alpha: 0.2), blurRadius: 40, spreadRadius: 10)],
                    ),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(50),
                      child: Image.asset('assets/logo.jpg', fit: BoxFit.cover)),
                  ),
                  const SizedBox(height: 40),
                  Text(t('welcome_back', lang), style: const TextStyle(color: Colors.white, fontSize: 32, fontWeight: FontWeight.w900, letterSpacing: -1)),
                  Text(t('security_tagline', lang), style: const TextStyle(color: Colors.white54, fontSize: 14)),
                  const SizedBox(height: 50),

                  _buildGlassCard([
                    _buildTextField(Icons.email_outlined, t('email', lang), _emailController),
                    _buildDivider(),
                    _buildTextField(
                      Icons.lock_outline_rounded, 
                      t('password', lang), 
                      _passwordController, 
                      isPassword: true,
                      obscure: _obscurePassword,
                      onToggleVisibility: () => setState(() => _obscurePassword = !_obscurePassword),
                    ),
                  ]),
                  const SizedBox(height: 25),

                  _buildMainButton(t('login_btn', lang), () => _signInWithEmail(lang)),
                  
                  const SizedBox(height: 25),
                  Row(
                    children: [
                      const Expanded(child: Divider(color: Colors.white10)),
                      Padding(padding: const EdgeInsets.symmetric(horizontal: 15), child: Text(t('or_text', lang), style: const TextStyle(color: Colors.white24, fontSize: 12))),
                      const Expanded(child: Divider(color: Colors.white10)),
                    ],
                  ),
                  const SizedBox(height: 25),

                  _buildGoogleButton(lang),

                  const SizedBox(height: 20),
                  
                  TextButton(
                    onPressed: () => Navigator.pushNamed(context, '/registration'),
                    child: RichText(
                      text: TextSpan(
                        style: const TextStyle(color: Colors.white54, fontSize: 14),
                        children: [
                          TextSpan(text: t('no_account', lang)),
                          TextSpan(
                            text: t('register_link', lang),
                            style: const TextStyle(color: AppColors.accent, fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                    ),
                  ),

                  if (_errorMessage != null)
                    Padding(
                      padding: const EdgeInsets.only(top: 20),
                      child: Text(_errorMessage!, 
                        textAlign: TextAlign.center,
                        style: const TextStyle(color: Colors.redAccent, fontSize: 12)),
                    ),
                ],
              ),
            ),
          ),
          
          if (_isLoading)
            Container(
              color: Colors.black54,
              child: const Center(child: CircularProgressIndicator(color: AppColors.accent)),
            ),
        ],
      ),
    );
  }

  Widget _buildGlassCard(List<Widget> children) {
    return ClipRRect(
      borderRadius: BorderRadius.circular(30),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
        child: Container(
          decoration: BoxDecoration(
            color: Colors.white.withValues(alpha: 0.03),
            borderRadius: BorderRadius.circular(30),
            border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
          ),
          child: Column(children: children),
        ),
      ),
    );
  }

  Widget _buildTextField(
    IconData icon, 
    String hint, 
    TextEditingController controller, {
    bool isPassword = false,
    bool obscure = false,
    VoidCallback? onToggleVisibility,
  }) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 10),
      child: TextField(
        controller: controller,
        obscureText: isPassword ? obscure : false,
        style: const TextStyle(color: Colors.white),
        decoration: InputDecoration(
          icon: Icon(icon, color: Colors.white38, size: 20),
          hintText: hint,
          hintStyle: const TextStyle(color: Colors.white24),
          border: InputBorder.none,
          suffixIcon: isPassword ? IconButton(
            icon: Icon(
              obscure ? Icons.visibility_off_outlined : Icons.visibility_outlined,
              color: Colors.white38,
              size: 20,
            ),
            onPressed: onToggleVisibility,
          ) : null,
        ),
      ),
    );
  }

  Widget _buildDivider() => Divider(height: 1, color: Colors.white.withValues(alpha: 0.05), indent: 50);

  Widget _buildMainButton(String text, VoidCallback onTap) {
    return Container(
      width: double.infinity,
      height: 60,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(20),
        gradient: const LinearGradient(colors: [AppColors.accent, AppColors.blue]),
        boxShadow: [BoxShadow(color: AppColors.accent.withValues(alpha: 0.3), blurRadius: 20, offset: const Offset(0, 10))],
      ),
      child: ElevatedButton(
        onPressed: onTap,
        style: ElevatedButton.styleFrom(backgroundColor: Colors.transparent, shadowColor: Colors.transparent, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20))),
        child: Text(text.toUpperCase(), style: const TextStyle(color: Colors.black, fontWeight: FontWeight.w900, fontSize: 16)),
      ),
    );
  }

  Widget _buildGoogleButton(String lang) {
    return InkWell(
      onTap: () => _signInWithGoogle(lang),
      borderRadius: BorderRadius.circular(20),
      child: _buildGlassCard([
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 18, horizontal: 20),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.g_mobiledata_rounded, color: Colors.white, size: 24),
              const SizedBox(width: 15),
              Text(t('continue_with_google', lang), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
            ],
          ),
        ),
      ]),
    );
  }
}

class _Blob extends StatelessWidget {
  final Color color;
  final double size;
  const _Blob({required this.color, required this.size});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(shape: BoxShape.circle, color: color),
    );
  }
}
