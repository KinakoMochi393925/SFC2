"""Windows Explorer context-menu registration, kept outside GUI start-up."""
from __future__ import annotations

import os
import sys
from pathlib import Path


def default_command() -> str:
    """Build the command string for context menu execution."""
    if getattr(sys, "frozen", False):
        executable = str(Path(sys.executable).resolve())
        return f'"{executable}" --convert "%1"'
    
    # In development: run via python interpreter
    python_exe = str(Path(sys.executable).resolve())
    # Prefer main.py at project root
    project_root = Path(__file__).resolve().parent.parent
    main_script = project_root / "main.py"
    if not main_script.is_file():
        main_script = Path(sys.argv[0]).resolve()
    return f'"{python_exe}" "{main_script}" --convert "%1"'


def _get_supported_extensions() -> set[str]:
    from utils.constants import VIDEO_EXTENSIONS, AUDIO_EXTENSIONS, IMAGE_EXTENSIONS
    return VIDEO_EXTENSIONS | AUDIO_EXTENSIONS | IMAGE_EXTENSIONS


def register_context_menu(command_override: str | None = None) -> None:
    """Register ``SFC2で変換`` for supported file types in the current user hive."""
    if os.name != "nt":
        raise OSError("Windows Explorer context menus are only available on Windows.")

    import winreg

    command = command_override or default_command()
    
    extensions = _get_supported_extensions()
    
    for ext in extensions:
        menu_key = rf"Software\Classes\SystemFileAssociations\{ext}\shell\SFC2.Convert"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, menu_key) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "SFC2で変換")
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, menu_key + r"\command") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)


def unregister_context_menu() -> None:
    """Remove the current-user Explorer registration created by this module."""
    if os.name != "nt":
        raise OSError("Windows Explorer context menus are only available on Windows.")

    import winreg

    extensions = _get_supported_extensions()
    
    for ext in extensions:
        menu_key = rf"Software\Classes\SystemFileAssociations\{ext}\shell\SFC2.Convert"
        for key_name in (menu_key + r"\command", menu_key):
            try:
                winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_name)
            except FileNotFoundError:
                pass
                
    # Also clean up the old global registration if it exists
    old_menu_key = r"Software\Classes\*\shell\SFC2.Convert"
    for key_name in (old_menu_key + r"\command", old_menu_key):
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_name)
        except FileNotFoundError:
            pass
