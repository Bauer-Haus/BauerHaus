WindowSmith

<p align="center">
<i>Precision window management for the modern macOS workspace.</i>
</p>

🚀 The "Elevator Pitch"

The Problem: macOS is a beautiful operating system, but its native window management leaves power users dragging, dropping, and manually resizing windows across massive ultra-wide monitors or multi-display setups. This causes friction, breaks focus, and wastes time.

The Solution: WindowSmith is a lightning-fast, keyboard-driven window manager and layout tool built natively for macOS. Designed for developers, designers, and multitaskers, it allows users to instantly snap windows into precise grid layouts (Halves, Thirds, Quadrants, or Custom Grids), "throw" windows across multiple displays, and define absolute pixel-perfect sizing.

It lives quietly in your menu bar, stays out of your way, and activates instantly via customizable global hotkeys. Whether you need a rigid 25/50/25 "Focus" layout for coding or a complex custom grid, WindowSmith bends the macOS desktop to your will.

🛠 The Tech Stack

WindowSmith is built from the ground up to be lightweight, performant, and deeply integrated into the macOS ecosystem.

Language: Swift 5+

UI Frameworks: * SwiftUI: Utilized for modern, reactive, and fluid interfaces in the Menu Bar popover and Settings windows.

AppKit: Handled low-level window lifecycle management, NSPopover interactions, and global event monitoring.

Core APIs & Frameworks:

ApplicationServices (Accessibility API): The C-based AXUIElement framework powers the core engine, allowing WindowSmith to read and manipulate third-party application windows with zero latency.

CoreGraphics: For handling complex multi-monitor bounds, frame calculations, and coordinate geometry.

ServiceManagement: For seamless "Launch at Login" functionality.

Combine: For reactive state management across the application lifecycle.

🧠 Challenges & Solutions

Building a native macOS window manager requires interacting with deeply embedded, legacy Apple frameworks. Here is a look at one of the core technical hurdles overcome during development:

Challenge: The Dual-Coordinate System & Multi-Monitor Math

Moving a window on macOS isn't as simple as setting an (x, y) coordinate. AppKit uses a bottom-left origin coordinate system (where y=0 is the bottom of the screen), while the macOS Accessibility API (AXUIElement) requires a top-left origin system.

When a user triggers a hotkey to "Throw" a window from a 14-inch MacBook Pro screen to a 32-inch 4K external monitor, calculating the exact relative geometry requires translating coordinates between these two inverted systems, factoring in the different resolutions, and accounting for the physical arrangement of the displays in System Settings (which dictates the global coordinate space).

The Solution

Instead of relying on slow AppleScript bridges, I built a custom, low-level geometry engine using CoreGraphics and the C-based Accessibility API.

Coordinate Normalization: The engine dynamically queries NSScreen.screens to map the global desktop space. It captures the target window's frame, translates the bottom-left AppKit bounds to a normalized 0.0 to 1.0 relative floating-point ratio, and projects that ratio onto the target monitor's visibleFrame.

Inversion & Injection: Before injecting the new coordinates via AXUIElementSetAttributeValue, the engine intercepts the height of the primary screen and mathematically inverts the Y-axis.

Concurrency: To prevent the visual "stuttering" or "rubber-banding" that plagues many window managers when resizing heavy apps (like Chrome or Xcode), the sizing and positioning commands are dispatched asynchronously on a background userInteractive queue, utilizing a micro-sleep (usleep) buffer to allow the third-party app's internal UI thread to catch up before applying the final coordinate snap.

The result is a window manipulation engine that feels instantaneous, regardless of the app being moved or the complexity of the monitor setup.
