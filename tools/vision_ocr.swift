import Foundation
import Vision
import AppKit

let args = CommandLine.arguments
guard args.count >= 3 else { exit(2) }
let input = args[1]
let output = args[2]
let files = try FileManager.default.contentsOfDirectory(atPath: input)
    .filter { $0.hasSuffix(".png") }
    .sorted()
var all = ""
for file in files {
    let path = (input as NSString).appendingPathComponent(file)
    guard let image = NSImage(contentsOfFile: path),
          let tiff = image.tiffRepresentation,
          let rep = NSBitmapImageRep(data: tiff),
          let cg = rep.cgImage else { continue }
    let request = VNRecognizeTextRequest()
    request.recognitionLanguages = ["zh-Hans", "en-US"]
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = true
    try VNImageRequestHandler(cgImage: cg, options: [:]).perform([request])
    all += "\n===== \(file) =====\n"
    all += (request.results ?? []).compactMap { $0.topCandidates(1).first?.string }.joined(separator: "\n")
    all += "\n"
}
try all.write(toFile: output, atomically: true, encoding: .utf8)
