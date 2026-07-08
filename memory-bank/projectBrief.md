# Project: Image Downloader

## Core Requirements
- Flask web application for downloading sequential images from URLs
- Uses Server-Sent Events (SSE) for real-time progress
- Supports multiple URLs, configurable iterations, and custom output folders

## Key Technical Decisions
- Flask 3.1.3 with Python 3.14
- requests library (2.34.2) for HTTP downloads
- SSE (text/event-stream) for real-time progress
- Regex-based URL pattern recognition for sequential image numbering

## Root Cause Analysis of Server Connection Error
- Primary cause: requests.get() had no timeout parameter, hanging indefinitely on unreachable servers
- Secondary cause: Missing User-Agent header caused CDN/servers to block requests
- Infrastructure cause: Two Flask instances on port 5000 due to reloader creating child processes
