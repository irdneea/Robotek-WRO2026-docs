// List on-screen windows: "<windowID>\t<owner>\t<title>\t<width>x<height>". Usage: swift list_windows.swift [owner-substring]
import CoreGraphics
import Foundation

let filter = CommandLine.arguments.count > 1 ? CommandLine.arguments[1].lowercased() : ""
let options: CGWindowListOption = [.optionOnScreenOnly, .excludeDesktopElements]
guard let info = CGWindowListCopyWindowInfo(options, kCGNullWindowID) as? [[String: Any]] else { exit(1) }
for window in info {
    let owner = (window[kCGWindowOwnerName as String] as? String) ?? ""
    let title = (window[kCGWindowName as String] as? String) ?? ""
    let layer = (window[kCGWindowLayer as String] as? Int) ?? 0
    let bounds = (window[kCGWindowBounds as String] as? [String: Any]) ?? [:]
    let width = Int((bounds["Width"] as? Double) ?? 0), height = Int((bounds["Height"] as? Double) ?? 0)
    if layer != 0 || width < 100 || height < 100 { continue }
    if !filter.isEmpty && !(owner + " " + title).lowercased().contains(filter) { continue }
    print("\(window[kCGWindowNumber as String] as? Int ?? 0)\t\(owner)\t\(title)\t\(width)x\(height)")
}
