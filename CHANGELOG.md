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