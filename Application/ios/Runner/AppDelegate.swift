import UIKit
import Flutter
import GoogleMaps
import KakaoSDKCommon

@UIApplicationMain
@objc class AppDelegate: FlutterAppDelegate {
  override func application(
    _ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
  ) -> Bool {
    KakaoSDK.initSDK(appKey: "485169cb19d2eda65a5d36105f83a53b")
    GMSServices.provideAPIKey("AIzaSyALSd3dqWMcVdun61oLS5xHUb2FL6kiFjQ")
    GeneratedPluginRegistrant.register(with: self)
    return super.application(application, didFinishLaunchingWithOptions: launchOptions)
  }
}
