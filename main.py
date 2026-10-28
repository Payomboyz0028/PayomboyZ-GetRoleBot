#!/usr/bin/env python3
"""
================================================================================
  PAYOMBØYZ GET-ROLE & TICKET BOT — CLOUD RUNNER
  Container 3: Get-ROLE Bot
================================================================================
"""

import os
import sys
import glob

# Auto-detect and prepend .local site-packages for Bot-Hosting.net Linux containers
for _lp in [
    "/home/container/.local/lib/python3.11/site-packages",
    "/home/container/.local/lib/python3.10/site-packages",
    os.path.expanduser("~/.local/lib/python3.11/site-packages"),
    os.path.expanduser("~/.local/lib/python3.10/site-packages")
] + glob.glob("/home/container/.local/lib/python*/site-packages"):
    if os.path.isdir(_lp) and _lp not in sys.path:
        sys.path.insert(0, _lp)

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.security import install_global_redactor
install_global_redactor()

from bot.role_bot import start_role_bot

if __name__ == "__main__":
    token = os.getenv("DISCORD_ROLE_BOT_TOKEN") or os.getenv("DISCORD_BOT_TOKEN")
    start_role_bot(token)
