import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_database/firebase_database.dart';
import 'package:aiconnectcar/features/home/widgets/tts_manager.dart';

class SettingsScreen extends StatefulWidget {
  final TtsManager ttsManager;

  SettingsScreen({required this.ttsManager});

  @override
  _SettingsScreenState createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _voiceGuide = true;
  bool _warningSound = true;
  double _brightness = 0.5;

  final TextEditingController _vehicleController = TextEditingController();
  final TextEditingController _profileController = TextEditingController();

  final FirebaseAuth _auth = FirebaseAuth.instance;
  final DatabaseReference _database = FirebaseDatabase(
    databaseURL: 'https://ai-connectcar-default-rtdb.asia-southeast1.firebasedatabase.app/',
  ).reference();

  @override
  void initState() {
    super.initState();
    _loadSettings();
    _loadVehicleInfo();
  }

  void _loadSettings() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    setState(() {
      _voiceGuide = prefs.getBool('voiceGuide') ?? true;
      _warningSound = prefs.getBool('warningSound') ?? true;
      _brightness = prefs.getDouble('brightness') ?? 0.5;
      _profileController.text = prefs.getString('profileInfo') ?? '';
    });
  }

  void _loadVehicleInfo() async {
    User? user = _auth.currentUser;
    if (user != null) {
      DatabaseEvent generalEvent = await _database.child('general').orderByChild('email').equalTo(user.email).once();
      if (generalEvent.snapshot.value != null) {
        Map<dynamic, dynamic> generalData = generalEvent.snapshot.value as Map<dynamic, dynamic>;
        String vehicleNumber = generalData.keys.first;
        setState(() {
          _vehicleController.text = vehicleNumber;
        });
      }
    }
  }

  void _saveSettings() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    prefs.setBool('voiceGuide', _voiceGuide);
    prefs.setBool('warningSound', _warningSound);
    prefs.setDouble('brightness', _brightness);
    prefs.setString('vehicleInfo', _vehicleController.text);
    prefs.setString('profileInfo', _profileController.text);

    // Update TtsManager state
    widget.ttsManager.enableVoiceGuide(_voiceGuide);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Settings'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: ListView(
          children: [
            SwitchListTile(
              title: Text('Voice Guide'),
              value: _voiceGuide,
              onChanged: (bool value) {
                setState(() {
                  _voiceGuide = value;
                });
                _saveSettings();
              },
            ),
            SwitchListTile(
              title: Text('Warning Sound'),
              value: _warningSound,
              onChanged: (bool value) {
                setState(() {
                  _warningSound = value;
                });
                _saveSettings();
              },
            ),
            ListTile(
              title: Text('Brightness'),
              subtitle: Slider(
                value: _brightness,
                onChanged: (double value) {
                  setState(() {
                    _brightness = value;
                  });
                  _saveSettings();
                },
                min: 0.0,
                max: 1.0,
              ),
            ),
            ListTile(
              title: TextField(
                controller: _vehicleController,
                style: TextStyle(color: Colors.white),
                decoration: InputDecoration(labelText: 'Vehicle Info', labelStyle: TextStyle(color: Colors.grey)),
                enabled: false, // Making the vehicle info field non-editable
              ),
            ),
            ListTile(
              title: TextField(
                controller: _profileController,
                decoration: InputDecoration(labelText: 'Profile Info'),
                onChanged: (String value) {
                  _saveSettings();
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
