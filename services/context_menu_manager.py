"""Cross-platform context menu registration manager for SFC2."""
from __future__ import annotations

import sys


def register_context_menu(executable_path: str | None = None) -> bool:
    """Register context menu / quick action depending on the current OS.

    Returns True if successfully registered, False if unsupported OS or error.
    """
    if sys.platform == "win32":
        from services.windows_context_menu import register_context_menu as win_register
        win_register(executable_path)
        return True
    elif sys.platform == "darwin":
        from services.mac_context_menu import register_context_menu as mac_register
        mac_register(executable_path)
        return True
    else:
        raise OSError(f"Context menu integration is not supported on {sys.platform}.")


def unregister_context_menu() -> bool:
    """Unregister context menu / quick action depending on the current OS.

    Returns True if successfully unregistered, False if unsupported OS or error.
    """
    if sys.platform == "win32":
        from services.windows_context_menu import unregister_context_menu as win_unregister
        win_unregister()
        return True
    elif sys.platform == "darwin":
        from services.mac_context_menu import unregister_context_menu as mac_unregister
        mac_unregister()
        return True
    else:
        raise OSError(f"Context menu integration is not supported on {sys.platform}.")
