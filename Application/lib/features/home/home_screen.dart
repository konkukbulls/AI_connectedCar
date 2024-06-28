import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_database/firebase_database.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../settings/settings_screen.dart';
import 'widgets/call_manager.dart';
import 'widgets/database_manager.dart';
import 'widgets/navigation_manager.dart';
import 'widgets/tts_manager.dart';
import 'widgets/voice_animation.dart';
import 'dart:async';

class HomeScreen extends StatefulWidget {
  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final DatabaseManager _databaseManager = DatabaseManager('https://ai-connectcar-default-rtdb.asia-southeast1.firebasedatabase.app/');
  final TtsManager _ttsManager = TtsManager();
  final CallManager _callManager = CallManager();
  final NavigationManager _navigationManager = NavigationManager();
  User? _user;
  String? _vehicleNumber;
  bool _isVoiceGuideEnabled = true;
  String? _displayedImage;
  String _ttsText = '';

  final double imageWidth = 200.0;
  final double imageHeight = 200.0;

  final Map<String, String> _stateToImage = {
    'alcohol': 'assets/images/alcohol.png',
    'drowsy': 'assets/images/drowsy.png',
    'overload': 'assets/images/overload.png',
    'threat': 'assets/images/threat.png',
    'breakdown': 'assets/images/breakdown.png',
    'lightOff': 'assets/images/lightOff.png',
    'fire': 'assets/images/fire.png',
    'fuelLeak': 'assets/images/fuelLeak.png',
    'noFuel': 'assets/images/noFuel.png',
    'noBattery': 'assets/images/noBattery.png',
    'moveOver': 'assets/images/moveOver.png',
    'intersection': 'assets/images/intersection.png',
    'SUA': 'assets/images/SUA.png',
    'blackIce': 'assets/images/blackIce.png',
    'potHole': 'assets/images/potHole.png',
    'roadDefects': 'assets/images/roadDefects.png',
    'lowBattery': 'assets/images/lowBattery.png',
    'fuelShortage': 'assets/images/fuelShortage.png'
  };


  @override
  void initState() {
    super.initState();
    _user = _auth.currentUser;
    if (_user != null) {
      _getVehicleNumberAndListenForUpdates();
    } else {
      print("User is not logged in");
    }
    _ttsManager.setStartHandler(() {
      setState(() {
        _ttsManager.isSpeaking = true;
      });
    });

    _ttsManager.setCompletionHandler(() {
      setState(() {
        _ttsManager.isSpeaking = false;
      });
    });

    _loadSettings();
  }

  void _getVehicleNumberAndListenForUpdates() async {
    print("Getting vehicle number...");
    _vehicleNumber = await _databaseManager.getVehicleNumber();
    if (_vehicleNumber != null) {
      print("Listening for updates...");
      _listenForStateUpdates('general', _vehicleNumber!);
      _listenForCallUpdates('general', _vehicleNumber!);
      _listenForNavigationUpdates('general', _vehicleNumber!);
    } else {
      print("User type: not found in database");
    }
  }

  void _listenForStateUpdates(String userType, String vehicleNumber) {
    print("Listening for state updates...");

    _databaseManager.getDatabaseRef().child(userType).child(vehicleNumber).child('problem').onValue.listen((event) {
      DataSnapshot dataSnapshot = event.snapshot;
      if (dataSnapshot.value != null) {
        Map<dynamic, dynamic> values = dataSnapshot.value as Map<dynamic, dynamic>;
        _updateTtsText(values['myText'] ?? '');
        _updateTtsText(values['rxText'] ?? '');
        _updateTtsText(values['txText'] ?? '');
        _displayStateImage(values['rxState']);
        _displayStateImage(values['txState']);
        _displayStateImage(values['myState']);
      } else {
        print("No data in snapshot");
      }
    });
  }

  void _updateTtsText(String text) {
    if (text.isNotEmpty) {
      setState(() {
        _ttsText = text;
      });
      _ttsManager.speak(text);
    }
  }

  void _displayStateImage(String? state) {
    if (state != null && _stateToImage.containsKey(state)) {
      setState(() {
        _displayedImage = _stateToImage[state];
      });
      Timer(Duration(seconds: 5), () {
        setState(() {
          _displayedImage = null;
        });
      });
    }
  }

  void _listenForCallUpdates(String userType, String vehicleNumber) {
    print("Listening for call updates...");

    _databaseManager.getDatabaseRef().child(userType).child(vehicleNumber).child('report').onValue.listen((event) {
      DataSnapshot dataSnapshot = event.snapshot;
      if (dataSnapshot.value != null) {
        Map<dynamic, dynamic> values = dataSnapshot.value as Map<dynamic, dynamic>;
        if (values['112'] == 1) {
          _callManager.makePhoneCall('112');
        }
        if (values['119'] == 1) {
          _callManager.makePhoneCall('119');
        }
        if (values['0800482000'] == 1) {
          _callManager.makePhoneCall('0800482000');
        }
      } else {
        print("No data in snapshot");
      }
    });
  }

  void _listenForNavigationUpdates(String userType, String vehicleNumber) {
    print("Listening for navigation updates...");

    _databaseManager.getDatabaseRef().child(userType).child(vehicleNumber).child('Service').onValue.listen((event) async {
      DataSnapshot dataSnapshot = event.snapshot;
      if (dataSnapshot.value != null) {
        Map<dynamic, dynamic> values = dataSnapshot.value as Map<dynamic, dynamic>;
        if (values['chargeStation'] != null) {
          var chargeStation = values['chargeStation'];
          if (chargeStation['location']['lat'] != null && chargeStation['location']['long'] != null) {
            double lat = _convertToDouble(chargeStation['location']['lat']);
            double long = _convertToDouble(chargeStation['location']['long']);
            String name = chargeStation['name'];
            if (lat != 0.0 && long != 0.0) {
              print('Navigating to charge station: $name, lat: $lat, long: $long');
              try {
                await _navigationManager.navigateToDestination(name, lat, long);
              } catch (e) {
                print('Error launching navigation: $e');
              }
            } else {
              print('Invalid charge station coordinates.');
            }
          }
        }
        if (values['gasStation'] != null) {
          var gasStation = values['gasStation'];
          if (gasStation['location']['lat'] != null && gasStation['location']['long'] != null) {
            double lat = _convertToDouble(gasStation['location']['lat']);
            double long = _convertToDouble(gasStation['location']['long']);
            String name = gasStation['name'];
            if (lat != 0.0 && long != 0.0) {
              print('Navigating to gas station: $name, lat: $lat, long: $long');
              try {
                await _navigationManager.navigateToDestination(name, lat, long);
              } catch (e) {
                print('Error launching navigation: $e');
              }
            } else {
              print('Invalid gas station coordinates.');
            }
          }
        }
      } else {
        print("No data in snapshot");
      }
    });
  }

  double _convertToDouble(dynamic value) {
    if (value is double) return value;
    if (value is int) return value.toDouble();
    if (value is String) return double.tryParse(value) ?? 0.0;
    return 0.0;
  }

  void _loadSettings() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    setState(() {
      _isVoiceGuideEnabled = prefs.getBool('isVoiceGuideEnabled') ?? true;
    });
    _ttsManager.enableVoiceGuide(_isVoiceGuideEnabled);
  }

  void _logout(BuildContext context) async {
    await _auth.signOut();
    Navigator.pushReplacementNamed(context, '/login');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('AIConnectCar'),
        actions: [
          IconButton(
            icon: Icon(Icons.logout),
            onPressed: () => _logout(context),
          ),
          IconButton(
            icon: Icon(Icons.settings),
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => SettingsScreen(ttsManager: _ttsManager),
              ),
            ),
          ),
        ],
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            if (_displayedImage != null)
              Image.asset(
                _displayedImage!,
                width: imageWidth,
                height: imageHeight,
              ),
            SizedBox(height: 40,),
            VoiceAnimation(isSpeaking: _ttsManager.isSpeaking),
            SizedBox(height: 20),
            Padding(
              padding: const EdgeInsets.all(30.0),
              child: Text(
                _ttsText.isNotEmpty ? _ttsText : '듣고 있습니다',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
