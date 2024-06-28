import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_database/firebase_database.dart';

class SignUpScreen extends StatefulWidget {
  @override
  _SignUpScreenState createState() => _SignUpScreenState();
}

class _SignUpScreenState extends State<SignUpScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _carNumberController = TextEditingController();
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final DatabaseReference _database = FirebaseDatabase(
    databaseURL: 'https://ai-connectcar-default-rtdb.asia-southeast1.firebasedatabase.app/',
  ).reference();
  String _errorMessage = '';
  List<bool> _selectedCarType = [true, false]; // Initial selection: Regular

  void _signUp() async {
    try {
      UserCredential userCredential = await _auth.createUserWithEmailAndPassword(
        email: _emailController.text,
        password: _passwordController.text,
      );
      User? user = userCredential.user;

      if (user != null) {
        String carType = _selectedCarType[0] ? 'general' : 'emergency';
        String vehicleNumber = _carNumberController.text.replaceAll(RegExp(r'[^0-9]'), ''); // 숫자만 추출

        if (carType == 'general') {
          await _database.child(carType).child(vehicleNumber).set({
            'email': _emailController.text,
            'location': {
              'lat': 0,
              'long': 0,
            },
            'trigger': '',
            'problem': {
              'rxState': '',
              'txState': '',
              'myState': '',
              'txText': '',
              'rxText': '',
              'myText': '',
            },
            'Service': {
              'gasStation': {
                'name': '',
                'location': {
                  'lat': 0,
                  'long': 0,
                },
              },
              'chargeStation': {
                'name': '',
                'location': {
                  'lat': 0,
                  'long': 0,
                },
              },
              'restArea': {
                'name': '',
                'location': {
                  'lat': 0,
                  'long': 0,
                },
              },
            },
            'report': {
              '112': 0,
              '119': 0,
              '0800482000': 0,
            },
          });
        } else {
          await _database.child(carType).child(vehicleNumber).set({
            'email': _emailController.text,
            'location': {
              'lat': 0,
              'long': 0,
            },
            'trigger': '',
            'problem': {
              'egState': '',
              'egText': '',
            },
            'intersectionGPS': {
              'lat': 0,
              'long': 0,
            },
          });
        }

        _showSuccessDialog(context);
      }
    } on FirebaseAuthException catch (e) {
      setState(() {
        _errorMessage = e.message ?? 'An unknown error occurred';
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'An unknown error occurred';
      });
    }
  }

  void _showSuccessDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: Text('축하합니다!'),
          content: Text('회원가입 되었습니다!'),
          actions: [
            TextButton(
              child: Text('확인'),
              onPressed: () {
                Navigator.of(context).pop(); // Close the dialog
                Navigator.pushReplacementNamed(context, '/home'); // Navigate to home screen
              },
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('회원가입')),
      body: Padding(
        padding: EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TextField(
              controller: _emailController,
              decoration: InputDecoration(labelText: '이메일'),
            ),
            TextField(
              controller: _passwordController,
              decoration: InputDecoration(labelText: '비밀번호'),
              obscureText: true,
            ),
            TextField(
              controller: _carNumberController,
              decoration: InputDecoration(labelText: '차량 번호'),
            ),
            SizedBox(height: 20),
            Text('차량 타입'),
            ToggleButtons(
              isSelected: _selectedCarType,
              onPressed: (int index) {
                setState(() {
                  for (int i = 0; i < _selectedCarType.length; i++) {
                    _selectedCarType[i] = i == index;
                  }
                });
              },
              children: <Widget>[
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16.0),
                  child: Text('일반차량'),
                ),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16.0),
                  child: Text('응급차량'),
                ),
              ],
            ),
            SizedBox(height: 20),
            if (_errorMessage.isNotEmpty)
              Text(
                _errorMessage,
                style: TextStyle(color: Colors.red),
              ),
            SizedBox(height: 20),
            ElevatedButton(
              onPressed: _signUp,
              child: Text('Sign Up'),
            ),
          ],
        ),
      ),
    );
  }
}
