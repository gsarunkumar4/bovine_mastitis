"""
§5 — Early-warning notification channels.

Provides a pluggable notification system with three channel
implementations:

• ConsoleChannel  — always active; prints formatted alerts to stdout.
• WebhookChannel  — POSTs JSON to a configurable URL (free — works
                    with Discord, Slack, ntfy.sh, or any webhook
                    receiver).
• SmsStub         — Twilio-shaped stub.  Logs "SMS would be sent …"
                    but does NOT actually send.  Requires a real
                    Twilio account_sid / auth_token to activate.
                    This is a NON-FUNCTIONAL PLACEHOLDER.

Every notification attempt (success or failure) is persisted to the
``notification_log`` database table for audit.
"""

import json
import traceback
from abc import ABC, abstractmethod
from datetime import datetime, timezone

from app.services.database import connect


# ── abstract channel ────────────────────────────────────────────────

class NotificationChannel(ABC):
    """Base class for notification delivery channels."""

    name: str = "base"

    @abstractmethod
    def send(self, alert: dict) -> bool:
        """Deliver *alert* and return True on success."""


# ── console channel (always on) ─────────────────────────────────────

class ConsoleChannel(NotificationChannel):
    name = "console"

    def send(self, alert: dict) -> bool:
        cow = alert.get("cow_id", "?")
        msg = alert.get("message", "")
        score = alert.get("risk_score", "")
        ts = alert.get("timestamp", "")
        print(
            f"[MastiSense Notification] cow={cow}  "
            f"risk_score={score}  ts={ts}\n  {msg}"
        )
        return True


# ── webhook channel ─────────────────────────────────────────────────

class WebhookChannel(NotificationChannel):
    name = "webhook"

    def __init__(self, url: str):
        self.url = url

    def send(self, alert: dict) -> bool:
        import urllib.request

        payload = json.dumps({
            "source": "MastiSense",
            "event": "mastitis_alert",
            "cow_id": alert.get("cow_id"),
            "risk_score": alert.get("risk_score"),
            "message": alert.get("message"),
            "timestamp": alert.get("timestamp"),
            "model_version": alert.get("model_version"),
        }).encode()

        req = urllib.request.Request(
            self.url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return 200 <= resp.status < 300
        except Exception as exc:
            print(f"[Webhook] POST to {self.url} failed: {exc!r}")
            return False


# ── SMS stub (NON-FUNCTIONAL — requires real Twilio credentials) ────

class SmsStub(NotificationChannel):
    """
    Twilio-shaped SMS stub.

    This does NOT send real SMS messages.  It logs what WOULD be sent
    and returns True so downstream code treats it as delivered.

    To activate real SMS, replace this class with a genuine Twilio
    integration using your account_sid, auth_token, and from_number.
    """

    name = "sms_stub"

    def __init__(
        self,
        account_sid: str = "",
        auth_token: str = "",
        from_number: str = "",
        to_number: str = "",
    ):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.to_number = to_number

    def send(self, alert: dict) -> bool:
        body = (
            f"[MastiSense] Alert for cow {alert.get('cow_id', '?')}: "
            f"{alert.get('message', '')}"
        )
        print(
            f"[SMS Stub] Would send SMS to {self.to_number} "
            f"from {self.from_number}:\n  {body}\n"
            "  ⚠ SMS is NOT enabled — this is a non-functional stub."
        )
        return True


# ── notification dispatcher ─────────────────────────────────────────

def _build_channels() -> list[NotificationChannel]:
    """Build the active channel list from config at import time."""
    channels: list[NotificationChannel] = [ConsoleChannel()]
    try:
        from config import WEBHOOK_URL
        if WEBHOOK_URL:
            channels.append(WebhookChannel(WEBHOOK_URL))
    except ImportError:
        pass
    return channels


_channels = _build_channels()


def _log_notification(
    alert_id: int | None,
    channel: str,
    payload: str,
    success: bool,
    error: str = "",
) -> None:
    """Persist notification attempt to notification_log table."""
    conn = connect()
    try:
        conn.execute(
            """
            INSERT INTO notification_log
                (alert_id, channel, payload, success, error)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                alert_id,
                channel,
                payload,
                1 if success else 0,
                error,
            ),
        )
        conn.commit()
    except Exception:
        traceback.print_exc()
    finally:
        conn.close()


def send_notification(alert: dict) -> dict:
    """
    Dispatch *alert* to all configured channels.

    Returns a summary dict with per-channel success/failure.
    """
    results: dict[str, bool] = {}
    alert_id = alert.get("id") or alert.get("alert_id")
    payload_str = json.dumps(alert, default=str)

    for ch in _channels:
        try:
            ok = ch.send(alert)
            results[ch.name] = ok
            _log_notification(alert_id, ch.name, payload_str, ok)
        except Exception as exc:
            results[ch.name] = False
            _log_notification(
                alert_id, ch.name, payload_str, False, repr(exc)
            )
            traceback.print_exc()

    return results


def get_notification_log(limit: int = 50) -> list[dict]:
    """Return recent notification log entries."""
    conn = connect()
    try:
        rows = conn.execute(
            """
            SELECT * FROM notification_log
            ORDER BY id DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def send_test_notification() -> dict:
    """Send a test notification through all channels."""
    test_alert = {
        "cow_id": "TEST",
        "risk_score": 0.0,
        "message": "This is a test notification from MastiSense.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_version": "test",
    }
    return send_notification(test_alert)
