import 'package:flutter/material.dart';

class VoiceAnimation extends StatefulWidget {
  final bool isSpeaking;

  VoiceAnimation({required this.isSpeaking});

  @override
  _VoiceAnimationState createState() => _VoiceAnimationState();
}

class _VoiceAnimationState extends State<VoiceAnimation> with SingleTickerProviderStateMixin {
  late AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(seconds: 1),
      vsync: this,
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return widget.isSpeaking
        ? ScaleTransition(
      scale: Tween(begin: 1.0, end: 1.5).animate(_controller),
      child: Icon(Icons.mic, color: Colors.blue, size: 50),
    )
        : Icon(Icons.mic_off, color: Colors.grey, size: 50);
  }
}
