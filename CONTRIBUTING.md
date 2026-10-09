# Contributing

Please try the Windows quick start before opening a bug report. Include the Python version, reproduction steps, expected and actual behavior, and a small non-sensitive example where possible. Do not upload private recordings or media you cannot share.

For code changes, create a branch, keep changes focused, run `python -m unittest discover -s tests -v` and describe what you tested. Changes to animation should account for both browser preview and MP4 output. Never commit `data/`, `.venv/`, credentials or FFmpeg binaries.

For potentially sensitive security issues, do not include secrets or exploitable personal data in public issues. Use GitHub's private vulnerability reporting if the repository has it enabled.
