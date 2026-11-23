from __future__ import annotations

import os
import platform
import sys
from datetime import datetime, timezone


def runtime_manifest():

    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "pid": os.getpid(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "hardening": {
            "bounded_memory": True,
            "explicit_tools": True,
            "sensitive_actions_blocked": True,
            "evidence_first": True,
            "authorization_required_for_side_effects": True,
        },
    }