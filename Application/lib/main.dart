import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:kakao_flutter_sdk_common/kakao_flutter_sdk_common.dart';
import 'features/authentication/login_screen.dart';
import 'features/authentication/sign_up_screen.dart';
import 'features/home/home_screen.dart';
import 'features/splash/splash_screen.dart';
import 'features/settings/settings_screen.dart';
import 'firebase_options.dart';
import 'features/home/widgets/tts_manager.dart'; // Import TtsManager

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  KakaoSdk.init(nativeAppKey: '485169cb19d2eda65a5d36105f83a53b');

  final TtsManager ttsManager = TtsManager();

  runApp(MyApp(ttsManager: ttsManager));
}

class MyApp extends StatelessWidget {
  final TtsManager ttsManager;

  MyApp({required this.ttsManager});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'AIConnectCar',
      theme: ThemeData.dark().copyWith(
        primaryColor: Colors.blueAccent,
        hintColor: Colors.white,
        buttonTheme: ButtonThemeData(
          buttonColor: Colors.blueAccent,
          textTheme: ButtonTextTheme.primary,
        ),
      ),
      initialRoute: '/splash',
      routes: {
        '/splash': (context) => SplashScreen(),
        '/login': (context) => LoginScreen(),
        '/sign_up': (context) => SignUpScreen(),
        '/home': (context) => HomeScreen(),
        '/settings': (context) => SettingsScreen(ttsManager: ttsManager), // Pass TtsManager instance
      },
    );
  }
}
