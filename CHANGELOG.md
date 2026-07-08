# Changelog

## [1.1.0] - 2026-07-08

### Added
- Modular project structure: extracted CSS and JavaScript from inline templates into separate static files
- `static/css/styles.css` - dedicated stylesheet file
- `static/js/app.js` - dedicated JavaScript file
- Version tagging system with git tags

### Changed
- `templates/index.html` now references external CSS and JS files via Flask's `url_for('static', ...)`
- Version bump from 1.0.0 to 1.1.0
- Improved maintainability by separating concerns (HTML/CSS/JS)

### Fixed
- Removed duplicate CSS/JS code from HTML template
- Cleaner template structure for future development
- Automatic update detection now uses semantic version comparison instead of date-based checks, ensuring reliable update notifications when version numbers change

## [1.0.1] - 2026-07-08

### Fixed
- Implemented semantic version comparison for update checker
- Added `get_github_remote_version()` to fetch `version.txt` from GitHub
- Added `compare_versions()` to properly compare semantic versions (e.g., 1.0.0 vs 1.1.0)
- Modified `check_for_updates()` to compare version numbers instead of commit dates
- Added `local_version.json` with initial version 1.0.0 for reliable update detection
