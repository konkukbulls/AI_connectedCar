import 'package:kakao_flutter_sdk_navi/kakao_flutter_sdk_navi.dart';
import 'package:url_launcher/url_launcher.dart';

class NavigationManager {
  Future<void> navigateToDestination(String name, double lat, double long) async {
    final destination = Location(name: name, x: long.toString(), y: lat.toString());

    try {
      if (await NaviApi.instance.isKakaoNaviInstalled()) {
        await NaviApi.instance.navigate(
          destination: destination,
          option: NaviOption(coordType: CoordType.wgs84),
        );
        print('Navigation request sent successfully to $name at lat: $lat, long: $long');
      } else {
        await launchUrl(Uri.parse(NaviApi.webNaviInstall));
      }
    } catch (e) {
      print('Navigation Error: $e');
    }
  }

  Future<void> shareDestination(String name, double lat, double long) async {
    final destination = Location(name: name, x: long.toString(), y: lat.toString());

    try {
      if (await NaviApi.instance.isKakaoNaviInstalled()) {
        await NaviApi.instance.shareDestination(
          destination: destination,
          option: NaviOption(coordType: CoordType.wgs84),
        );
        print('Destination shared successfully to $name at lat: $lat, long: $long');
      } else {
        await launchUrl(Uri.parse(NaviApi.webNaviInstall));
      }
    } catch (e) {
      print('Share Destination Error: $e');
    }
  }
}
