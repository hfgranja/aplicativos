// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "PECObservation",
    platforms: [.iOS(.v17)],
    products: [
        .library(name: "PECObservation", targets: ["PECObservation"]),
    ],
    dependencies: [],
    targets: [
        .target(
            name: "PECObservation",
            path: "Sources/PECObservation",
            swiftSettings: [
                .enableExperimentalFeature("StrictConcurrency"),
            ]
        ),
        .testTarget(
            name: "PECObservationTests",
            dependencies: ["PECObservation"],
            path: "Tests/PECObservationTests"
        ),
    ]
)
