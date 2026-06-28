"""
session_service.py

In-memory conversation state store.

Each session entry looks like:
{
    "action": "CREATE_CLAIM",
    "step":   "WAITING_FOR_INCIDENT_TYPE"
              | "WAITING_FOR_DESCRIPTION"
              | "WAITING_FOR_CONFIRMATION",
    "incident_type": "FLOOD",      # set after step 1
    "description":   "...",        # set after step 2
}

FIX: was a bare dict — now wrapped in a class with helper methods
so main.py never accesses the dict directly and can't accidentally
leave stale state.
"""

from typing import Optional


class SessionStore:

    def __init__(self):
        self._store: dict = {}

    # ── read ─────────────────────────────────────────────────────────────────

    def get(self, session_id: str) -> Optional[dict]:
        return self._store.get(session_id)

    def has_pending(self, session_id: str) -> bool:
        return session_id in self._store

    def get_step(self, session_id: str) -> Optional[str]:
        s = self._store.get(session_id)
        return s.get("step") if s else None

    # ── write ────────────────────────────────────────────────────────────────

    def set_waiting_for_incident_type(self, session_id: str):
        self._store[session_id] = {
            "action": "CREATE_CLAIM",
            "step":   "WAITING_FOR_INCIDENT_TYPE",
        }

    def set_waiting_for_description(self, session_id: str, incident_type: str):
        self._store[session_id] = {
            "action":        "CREATE_CLAIM",
            "step":          "WAITING_FOR_DESCRIPTION",
            "incident_type": incident_type,
        }

    def set_waiting_for_confirmation(
        self, session_id: str, incident_type: str, description: str
    ):
        self._store[session_id] = {
            "action":        "CREATE_CLAIM",
            "step":          "WAITING_FOR_CONFIRMATION",
            "incident_type": incident_type,
            "description":   description,
        }

    def clear(self, session_id: str):
        self._store.pop(session_id, None)

    # ── escape hatch ─────────────────────────────────────────────────────────

    def override_with_new_intent(self, session_id: str):
        """
        FIX 6: Called when the user sends a completely different intent
        (e.g. 'track claim 2') while a CREATE_CLAIM flow is in progress.
        Clears pending state so the new intent is handled cleanly.
        """
        self.clear(session_id)


# Singleton — imported by main.py
sessions = SessionStore()