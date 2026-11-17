// swift-tools-version:5.9
import PackageDescription

// (target name, folder under Sources/, has a Shaders.metal file)
let examples: [(String, String, Bool)] = [
    ("HelloView", "01-HelloView", false),
    ("HelloTriangle", "02-HelloTriangle", true),
    ("Shaders", "03-Shaders", true),
    ("Textures", "04-Textures", true),
    ("Transformations", "05-Transformations", true),
    ("CoordinateSystems", "06-CoordinateSystems", true),
    ("Camera", "07-Camera", true),
    ("BasicLighting", "08-BasicLighting", true),
    ("LightingMaps", "09-LightingMaps", true),
    ("MultipleLights", "10-MultipleLights", true),
    ("ModelLoading", "11-ModelLoading", true),
    ("RenderTargets", "12-RenderTargets", true),
    ("Instancing", "13-Instancing", true),
    ("ShadowMapping", "14-ShadowMapping", true),
    ("HDRBloom", "15-HDRBloom", true),
    ("PBR", "16-PBR", true),
    ("ComputeParticles", "17-ComputeParticles", true),
]

let package = Package(
    name: "LearnMetalExamples",
    platforms: [.macOS(.v13)],
    targets: [.target(name: "LearnMetalKit", path: "Sources/LearnMetalKit")] + examples.map { name, folder, hasShaders in
        .executableTarget(
            name: name,
            dependencies: ["LearnMetalKit"],
            path: "Sources/\(folder)",
            resources: hasShaders ? [.copy("Shaders.metal")] : []
        )
    }
)
