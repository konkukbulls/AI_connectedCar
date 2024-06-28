import 'package:firebase_database/firebase_database.dart';
import 'package:firebase_auth/firebase_auth.dart';

class DatabaseManager {
  final DatabaseReference _database;
  final FirebaseAuth _auth = FirebaseAuth.instance;
  User? _user;

  DatabaseManager(String databaseURL) : _database = FirebaseDatabase(databaseURL: databaseURL).reference() {
    _user = _auth.currentUser;
  }

  Future<String?> getVehicleNumber() async {
    if (_user == null) return null;
    DatabaseEvent generalEvent = await _database.child('general').orderByChild('email').equalTo(_user!.email).once();
    DatabaseEvent emergencyEvent = await _database.child('emergency').orderByChild('email').equalTo(_user!.email).once();

    if (generalEvent.snapshot.value != null) {
      Map<dynamic, dynamic> generalData = generalEvent.snapshot.value as Map<dynamic, dynamic>;
      return generalData.keys.first;
    } else if (emergencyEvent.snapshot.value != null) {
      Map<dynamic, dynamic> emergencyData = emergencyEvent.snapshot.value as Map<dynamic, dynamic>;
      return emergencyData.keys.first;
    }
    return null;
  }

  DatabaseReference getDatabaseRef() {
    return _database;
  }

  void listenForTextUpdates(String vehicleNumber, bool isVoiceGuideEnabled, Function(String) onTextUpdate) {
    _database.child('general').child(vehicleNumber).child('problem').onValue.listen((event) {
      DataSnapshot dataSnapshot = event.snapshot;
      if (dataSnapshot.value != null) {
        Map<dynamic, dynamic> values = dataSnapshot.value as Map<dynamic, dynamic>;
        if (isVoiceGuideEnabled) {
          if (values['myText'] != null) onTextUpdate(values['myText']);
          if (values['rxText'] != null) onTextUpdate(values['rxText']);
          if (values['txText'] != null) onTextUpdate(values['txText']);
        }
      } else {
        print("No data in snapshot");
      }
    });
  }

  void listenForCallUpdates(String vehicleNumber, Function(String) onCallUpdate) {
    _database.child('general').child(vehicleNumber).child('report').onValue.listen((event) {
      DataSnapshot dataSnapshot = event.snapshot;
      if (dataSnapshot.value != null) {
        Map<dynamic, dynamic> values = dataSnapshot.value as Map<dynamic, dynamic>;
        if (values['112'] == 1) onCallUpdate('112');
        if (values['119'] == 1) onCallUpdate('119');
        if (values['0800482000'] == 1) onCallUpdate('0800482000');
      } else {
        print("No data in snapshot");
      }
    });
  }

  void listenForNavigationUpdates(String vehicleNumber, Function(String, double, double) onNavigationUpdate) {
    _database.child('general').child(vehicleNumber).child('Service').onValue.listen((event) {
      DataSnapshot dataSnapshot = event.snapshot;
      if (dataSnapshot.value != null) {
        Map<dynamic, dynamic> values = dataSnapshot.value as Map<dynamic, dynamic>;
        if (values['chargeStation'] != null) {
          var chargeStation = values['chargeStation'];
          if (chargeStation['location']['lat'] != null && chargeStation['location']['long'] != null) {
            double lat = chargeStation['location']['lat'].toDouble();
            double long = chargeStation['location']['long'].toDouble();
            String name = chargeStation['name'];
            if (lat != 0.0 && long != 0.0) {
              print('Navigating to charge station: $name, lat: $lat, long: $long');
              onNavigationUpdate(name, lat, long);
            } else {
              print('Invalid charge station coordinates.');
            }
          }
        }
        if (values['gasStation'] != null) {
          var gasStation = values['gasStation'];
          if (gasStation['location']['lat'] != null && gasStation['location']['long'] != null) {
            double lat = gasStation['location']['lat'].toDouble();
            double long = gasStation['location']['long'].toDouble();
            String name = gasStation['name'];
            if (lat != 0.0 && long != 0.0) {
              print('Navigating to gas station: $name, lat: $lat, long: $long');
              onNavigationUpdate(name, lat, long);
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
}
