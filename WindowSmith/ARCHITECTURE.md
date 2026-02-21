```mermaid
graph TD
    %% Define Styles
    classDef ui fill:#0f4c75,stroke:#3282b8,stroke-width:2px,color:#fff,rx:5px,ry:5px;
    classDef core fill:#1b262c,stroke:#bbe1fa,stroke-width:2px,color:#fff,rx:5px,ry:5px;
    classDef sys fill:#3282b8,stroke:#0f4c75,stroke-width:2px,color:#fff,rx:5px,ry:5px;
    classDef target fill:#1a1a2e,stroke:#e94560,stroke-width:3px,color:#fff,rx:10px,ry:10px;

    subgraph UI [&quot;User Interface (SwiftUI &amp; AppKit)&quot;]
    MB[&quot;Menu Bar Status Item&quot;]
    PO[&quot;Glass Hosting Controller &amp;lt;br/&amp;gt; Popover Manager&quot;]
    SW[&quot;Settings Window Manager&quot;]
    
    subgraph Views [&quot;SwiftUI View Layer&quot;]
        MenuBarView[&quot;MenuBarView&quot;]
        SettingsView[&quot;SettingsView&quot;]
        Grid[&quot;InteractiveGridSelector&quot;]
        Snap[&quot;SnapLayoutView&quot;]
    end
    
    MB --&amp;gt;|Toggles| PO
    PO --&amp;gt;|Hosts| MenuBarView
    SW --&amp;gt;|Hosts| SettingsView
    MenuBarView --&amp;gt;|Renders| Snap
    SettingsView --&amp;gt;|Renders| Grid
end

subgraph Core [&quot;Core Engine (Swift)&quot;]
    WC[&quot;WindowController &amp;lt;br/&amp;gt; Singleton Orchestrator&quot;]
    GKM[&quot;GlobalKeyMonitor &amp;lt;br/&amp;gt; NSEvent Tracker&quot;]
    
    subgraph Logic [&quot;Business &amp; State Logic&quot;]
        Layout[&quot;Layout Presets &amp; Math Engine&quot;]
        State[&quot;State &amp; Permissions Manager&quot;]
        Pulse[&quot;Pulse Animation Timer&quot;]
    end
    
    UD[(&quot;UserDefaults / JSON Encoder&quot;)]
end

subgraph MacOS [&quot;macOS System APIs&quot;]
    AX[&quot;Accessibility API &amp;lt;br/&amp;gt; AXUIElement&quot;]
    WS[&quot;NSWorkspace &amp;lt;br/&amp;gt; Active App Tracker&quot;]
    CG[&quot;CoreGraphics &amp; NSScreen &amp;lt;br/&amp;gt; Screen Bounds &amp; Geometry&quot;]
    GCD[&quot;Grand Central Dispatch &amp;lt;br/&amp;gt; userInteractive Queue&quot;]
end

subgraph Target [&quot;Target Environment&quot;]
    TA[&quot;Third-Party OS Window &amp;lt;br/&amp;gt; e.g., Safari, Xcode, Figma&quot;]
end

%% Core Connections
MenuBarView --&amp;gt;|Trigger Snap Command| WC
Grid --&amp;gt;|Save Custom Grid| State
State &amp;lt;--&amp;gt;|Persist/Load Presets| UD

GKM == &quot;Intercepts Ctrl+Opt&quot; ==&amp;gt; WC
WC --&amp;gt;|Calculates Relative Rect| Layout
WC --&amp;gt;|Triggers Icon Feedback| Pulse

%% OS API Connections
WC --&amp;gt;|Query Frontmost PID| WS
WC --&amp;gt;|Query Target Screen Bounds| CG

Layout == &quot;Dispatches Resizing Task&quot; ==&amp;gt; GCD
GCD == &quot;Async Coordinate Injection &amp;lt;br/&amp;gt; (w/ usleep buffer)&quot; ==&amp;gt; AX

%% Execution
AX == &quot;Translates &amp; Resizes Frame&quot; ==&amp;gt; TA

%% Assign Classes
class MB,PO,SW,MenuBarView,SettingsView,Grid,Snap ui;
class WC,GKM,Layout,State,Pulse,UD core;
class AX,WS,CG,GCD sys;
class TA target;
```
