# Desktop Automation

## Purpose
Define the Desktop Automation capability — the ability for IRIS to control desktop applications, simulate user input, and automate repetitive desktop tasks.

## Responsibilities
- Simulate keyboard input and mouse actions
- Control application windows
- Automate file operations
- Capture screen regions
- Record and replay desktop macros

## Design Goals
- **Cross-platform**: Works on Windows, macOS, Linux
- **Non-intrusive**: Automation is visible and controllable
- **Safe**: Prevent dangerous actions (rm -rf, format, etc.)
- **Recordable**: Users can record macros for replay

## Architecture
```
Command → Desktop Automation Skill → Platform Adapter → OS Operations
                                                    │
                                                    ▼
                                         Keyboard / Mouse / Window / File
```

## Components
- **Input Simulator**: Keyboard and mouse simulation
- **Window Manager**: Application window control
- **File Operator**: File and directory operations
- **Screen Capture**: Region and full-screen capture
- **Macro Recorder**: Record and replay macro sequences

## Data Flow
Command → Platform Detection → Platform Adapter → OS API → Operation → Result

## Public Interfaces
- `POST /desktop/click` → Click at coordinates
- `POST /desktop/type` → Type text
- `POST /desktop/window` → Window operations (focus, move, close)
- `POST /desktop/screenshot` → Capture screen region
- `POST /desktop/file` → File operations
- `POST /desktop/macro/record` → Start macro recording
- `POST /desktop/macro/replay` → Replay macro

## Configuration
- Automation enabled: `desktop_automation_enabled` (default: false)
- Input speed: `input_speed` (default: normal)
- Danger filter: `danger_filter` (default: strict)
- Allowed paths: `allowed_paths` for file operations
- Screenshot directory: `screenshot_dir` (default: `~/.iris/screenshots/`)

## Dependencies
- pyautogui (cross-platform GUI automation)
- platform-specific: win32api (Windows), AppKit (macOS), xdotool (Linux)

## Security Considerations
- Desktop automation is opt-in (disabled by default)
- Dangerous commands are filtered and blocked
- File operations limited to allowed paths
- User can reject any automation action
- Macros are stored locally and encrypted

## Failure Recovery
- Action timeout → cancel and release input control
- Window not found → search or report error
- Permission denied → clear error with instructions
- Invalid coordinates → clamp to screen bounds

## Future Improvements
- Phase 2: Visual element detection (find buttons by image)
- Phase 3: AI-guided automation (learn from demonstration)
- Phase 4: Cross-application workflows

## Engineering Notes
Desktop automation should be used sparingly. Most tasks should prefer API integration over GUI automation.

## Acceptance Criteria
- Keyboard and mouse simulation works on target platform
- File operations respect allowed path restrictions
- Screenshots capture correct regions
- Macro recording and replay preserves timing
- User can pause/cancel automation at any time

## References
- Volume-3-Capabilities/05-Browser-Automation.md
- Volume-5-Security/04-Permissions.md
