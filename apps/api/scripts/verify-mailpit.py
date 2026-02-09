#!/usr/bin/env python3
"""Verify Mailpit is running and can capture emails.

Run this after devcontainer rebuild to confirm email infrastructure works.
Usage: python scripts/verify-mailpit.py
"""

import json
import smtplib
import sys
import urllib.request
from email.message import EmailMessage

SMTP_HOST = "mailpit"
SMTP_PORT = 1025
API_BASE = "http://mailpit:8025"


def check_smtp_connection() -> bool:
    """Verify SMTP port is accepting connections."""
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=5) as smtp:
            smtp.noop()
        print("[OK] SMTP connection to mailpit:1025")
        return True
    except Exception as e:
        print(f"[FAIL] SMTP connection: {e}")
        return False


def check_web_ui() -> bool:
    """Verify Mailpit web UI is responding."""
    try:
        req = urllib.request.Request(f"{API_BASE}/api/v1/info")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            print(f"[OK] Mailpit web UI - version: {data.get('Version', 'unknown')}")
        return True
    except Exception as e:
        print(f"[FAIL] Web UI: {e}")
        return False


def send_test_email() -> bool:
    """Send a test email via SMTP."""
    msg = EmailMessage()
    msg["Subject"] = "Test Email from Phase 6 Setup"
    msg["From"] = "test@localhost"
    msg["To"] = "recipient@example.com"
    msg.set_content("This is a test email to verify Mailpit is working.")

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=5) as smtp:
            smtp.send_message(msg)
        print("[OK] Test email sent")
        return True
    except Exception as e:
        print(f"[FAIL] Send email: {e}")
        return False


def check_email_captured() -> bool:
    """Verify the test email appears in Mailpit."""
    try:
        req = urllib.request.Request(f"{API_BASE}/api/v1/messages")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
            count = len(data.get("messages", []))
            if count > 0:
                latest = data["messages"][0]
                subject = latest.get("Subject", "")
                print(f"[OK] {count} message(s) in Mailpit - latest: '{subject}'")
                return True
            print("[FAIL] No messages found in Mailpit")
            return False
    except Exception as e:
        print(f"[FAIL] Check messages: {e}")
        return False


def main() -> int:
    print("=== Mailpit Verification ===\n")

    results = []
    results.append(check_smtp_connection())
    results.append(check_web_ui())
    results.append(send_test_email())
    results.append(check_email_captured())

    print()
    if all(results):
        print("ALL CHECKS PASSED - Mailpit is fully operational")
        return 0
    passed = sum(results)
    total = len(results)
    print(f"CHECKS: {passed}/{total} passed")
    print("Ensure Mailpit is running (rebuild devcontainer if needed)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
