# Browser Automation

## Purpose
Define the Browser Automation capability — the ability for IGRIS to control web browsers, navigate websites, extract data, and perform web-based tasks on behalf of the user.

## Responsibilities
- Control browser navigation (open, close, navigate)
- Extract data from web pages
- Fill forms and submit data
- Take screenshots of web pages
- Monitor web pages for changes
- Execute JavaScript in page context

## Design Goals
- **Headless-capable**: Run with or without visible browser
- **Privacy-safe**: User credentials never stored in automation state
- **Observable**: User can see what browser automation is doing
- **Controllable**: User can pause or cancel automation at any time

## Architecture
```
User Request → Browser Automation Skill → Selenium/Playwright → Browser
                                                    │
                                                    ▼
                                            Page Actions
                                                    │
                                                    ▼
                                           Data / Screenshot
```

## Components
- **Browser Controller**: Manages browser instances
- **Page Navigator**: URL navigation and history
- **Data Extractor**: Structured data extraction
- **Form Filler**: Auto-fill forms with context
- **Screenshot Manager**: Page and element screenshots
- **Change Monitor**: Track page changes over time

## Data Flow
Command → Browser Controller → Open Page → Execute Actions → Extract Data → Return Results

## Public Interfaces
- `POST /browser/open` → Open URL
- `POST /browser/navigate` → Navigate to URL
- `POST /browser/extract` → Extract data from page
- `POST /browser/screenshot` → Take screenshot
- `POST /browser/execute` → Execute JavaScript
- `POST /browser/close` → Close browser

## Configuration
- Browser engine: `browser_engine` (default: chromium)
- Headless mode: `headless` (default: true)
- Browser data dir: `browser_data_dir` (default: `~/.igris/browser/`)
- Page timeout: `page_timeout_seconds` (default: 30)
- Max concurrent browsers: `max_browsers` (default: 3)

## Dependencies
- Playwright or Selenium WebDriver
- Browser binaries (chromium, firefox, webkit)

## Security Considerations
- Browser automation runs in isolated profile
- No credentials stored in browser profile
- User credentials must be explicitly provided each session
- Automation cannot access browser password managers
- All automation is local and user-visible

## Failure Recovery
- Page load timeout → retry → cancel → return error
- Element not found → clear error with page state
- Browser crash → auto-restart new browser
- Navigation blocked → report and suggest alternatives

## Future Improvements
- Phase 2: Visual element selection (click this button)
- Phase 3: Complex multi-page workflows
- Phase 4: User-trained automation recipes

## Engineering Notes
Browser automation is inherently fragile. Use robust selectors and implement retry logic.

## Acceptance Criteria
- Browser opens and navigates to URLs
- Data extraction returns structured results
- Screenshots are captured correctly
- User can observe automation in real-time
- Automation can be cancelled by user

## References
- Volume-3-Capabilities/06-Desktop-Automation.md
- Volume-3-Capabilities/01-Skill-System.md
