---
Date: 2026-06-28
TaskRef: Fix server connection error in Image Downloader

Learnings:
- requests.get() without timeout can hang indefinitely, causing SSE connections to timeout
- Missing User-Agent header causes CDN/servers to block HTTP requests
- Flask debug mode (app.run(debug=True)) spawns a child process via the reloader, causing duplicate processes on the same port
- use_reloader=False prevents duplicate Flask processes
- EventSource (SSE) onerror fires when the connection is interrupted, not on message content errors
- taskkill with proper PID works better than vague process killing
- PowerShell here-strings (@''@) are useful for writing files with special characters

Difficulties:
- Editor tool had trouble matching Cyrillic text due to encoding issues
- Had to use PowerShell to write the complete file
- Multiple Python processes kept appearing on port 5000 due to Flask reloader

Successes:
- Identified root cause: missing timeout + missing User-Agent + duplicate processes
- All fixes applied and verified
- Image downloaded successfully after fixes

Improvements_Identified_For_Consolidation:
- General pattern: Always add timeout to requests.get() in Python web scrapers
- General pattern: Always add User-Agent header to avoid CDN blocking
- Flask apps: Always use use_reloader=False in production or when starting from scripts
- Windows: Use taskkill /F /PID for reliable process termination
---
