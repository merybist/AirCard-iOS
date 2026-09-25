import XCTest
@testable import AirCard_iOS

final class AirCardFeatureRootViewTests: XCTestCase {
    func testWallpapersTabIsPartOfTheFeatureRoot() {
        XCTAssertTrue(AirCardFeatureRootView.enabledTabs.contains(.wallpapers))
    }
}
