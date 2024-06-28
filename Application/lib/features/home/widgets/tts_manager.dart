import 'package:flutter_tts/flutter_tts.dart';

class TtsManager {
  final FlutterTts _flutterTts = FlutterTts();
  bool isSpeaking = false;
  bool isVoiceGuideEnabled = true;

  TtsManager() {
    _flutterTts.setStartHandler(() {
      isSpeaking = true;
    });

    _flutterTts.setCompletionHandler(() {
      isSpeaking = false;
    });

    _flutterTts.setErrorHandler((msg) {
      isSpeaking = false;
    });

    _initializeTtsSettings();
  }

  Future<void> speak(String text) async {
    if (isVoiceGuideEnabled) {
      await _flutterTts.speak(text);
    }
  }

  void setStartHandler(void Function() handler) {
    _flutterTts.setStartHandler(handler);
  }

  void setCompletionHandler(void Function() handler) {
    _flutterTts.setCompletionHandler(handler);
  }

  void enableVoiceGuide(bool isEnabled) {
    isVoiceGuideEnabled = isEnabled;
  }

  void _initializeTtsSettings() async {
    await _flutterTts.setVolume(1.0);
    await _flutterTts.setSpeechRate(0.5);
    await _flutterTts.setPitch(1.0);
  }
}
