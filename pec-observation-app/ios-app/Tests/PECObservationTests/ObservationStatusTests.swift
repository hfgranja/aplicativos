import XCTest
@testable import PECObservation

final class ObservationStatusTests: XCTestCase {

    func testAllStatusesHaveDisplayName() {
        for status in ObservationStatus.allCases {
            XCTAssertFalse(status.displayName.isEmpty,
                           "\(status.rawValue) should have a non-empty display name")
        }
    }

    func testAllStatusesRoundTrip() {
        for status in ObservationStatus.allCases {
            let raw = status.rawValue
            XCTAssertNotNil(ObservationStatus(rawValue: raw),
                            "\(raw) should be decodable from raw value")
        }
    }

    func testSyncCommandTypeRoundTrip() {
        for type_ in SyncCommandType.allCases {
            XCTAssertNotNil(SyncCommandType(rawValue: type_.rawValue))
        }
    }

    func testFeedbackItemEquality() {
        let a = FeedbackItem(title: "Planejamento", description: "Aula bem planejada")
        let b = FeedbackItem(title: "Planejamento", description: "Aula bem planejada")
        XCTAssertEqual(a, b)
    }
}

// Extend SyncCommandType to be CaseIterable for tests
extension SyncCommandType: CaseIterable {
    public static var allCases: [SyncCommandType] {
        [.uploadAudio, .createObservation, .updateObservation, .createSchool, .createTeacher]
    }
}
