"""SFC2 entry point. GUI imports stay out of the headless CLI path."""
import sys


def _run_cli(arguments: list[str]) -> int | None:
    """Handle CLI-only commands before importing QApplication."""
    # Filter out macOS Finder process serial number arguments (e.g. -psn_0_123456)
    clean_arguments = [arg for arg in arguments if not arg.startswith("-psn_")]
    if not clean_arguments:
        return None

    # Search rather than assuming position zero: Windows launchers may prepend
    # their own arguments, but an explicit conversion request must never fall
    # through to GUI startup.
    if "--convert" in clean_arguments:
        _prepare_cli_console()
        from utils.logger import enable_console_logging
        enable_console_logging()
        from services.cli_conversion import (
            EXIT_CONVERSION_FAILED,
            EXIT_DEFAULT_SETTINGS_MISSING,
            EXIT_FFMPEG_NOT_FOUND,
            EXIT_PATH_NOT_FOUND,
            EXIT_SUCCESS,
            run_cli_conversion,
        )

        convert_index = clean_arguments.index("--convert")
        paths = clean_arguments[convert_index + 1:]
        if not paths:
            _write_cli_message("The specified file or folder does not exist.", error=True)
            return EXIT_PATH_NOT_FOUND
        try:
            result = run_cli_conversion(paths)
        except Exception:
            result = EXIT_CONVERSION_FAILED

        messages = {
            EXIT_SUCCESS: "Conversion completed successfully.",
            EXIT_DEFAULT_SETTINGS_MISSING: "Default conversion settings are not configured.",
            EXIT_PATH_NOT_FOUND: "The specified file or folder does not exist.",
            EXIT_FFMPEG_NOT_FOUND: "FFmpeg was not found.",
            EXIT_CONVERSION_FAILED: "Conversion failed.",
        }
        _write_cli_message(messages.get(result, "Conversion failed."), error=result != EXIT_SUCCESS)
        _send_enter_to_console()
        return result

    if clean_arguments[0] in {"--register-context-menu", "--unregister-context-menu"}:
        try:
            from services.context_menu_manager import register_context_menu, unregister_context_menu
            if clean_arguments[0] == "--register-context-menu":
                register_context_menu()
            else:
                unregister_context_menu()
            return 0
        except Exception as e:
            _write_cli_message(f"Failed to update context menu: {e}", error=True)
            return 4

    return None


def _write_cli_message(message: str, *, error: bool) -> None:
    """Write when the executable has inherited a usable standard stream."""
    stream = sys.stderr if error else sys.stdout
    try:
        if stream is not None:
            print(message, file=stream)
    except (OSError, ValueError):
        pass


def _send_enter_to_console() -> None:
    """Send an Enter key press to the attached console to refresh the prompt."""
    if sys.platform != "win32":
        return
    
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        console_window = kernel32.GetConsoleWindow()
        if console_window:
            user32.PostMessageW(console_window, 0x0100, 0x0D, 0) # WM_KEYDOWN, VK_RETURN
            user32.PostMessageW(console_window, 0x0101, 0x0D, 0) # WM_KEYUP, VK_RETURN
    except Exception:
        pass


def _prepare_cli_console() -> None:
    """Attach a windowed one-file build to its invoking terminal, when present."""
    if sys.platform != "win32" or (sys.stdout is not None and sys.stderr is not None):
        return

    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        # In a PyInstaller one-file build the immediate parent is the temporary
        # bootloader process, not cmd.exe. Walk ancestor processes so that
        # AttachConsole reaches the real terminal rather than that process.
        attached = any(kernel32.AttachConsole(pid) for pid in _parent_process_ids())
        if not attached and kernel32.GetLastError() != 5:  # already attached
            return
        if sys.stdout is None:
            sys.stdout = open("CONOUT$", "w", buffering=1, encoding="utf-8", errors="replace")
        if sys.stderr is None:
            sys.stderr = open("CONOUT$", "w", buffering=1, encoding="utf-8", errors="replace")
    except (OSError, AttributeError):
        pass


def _parent_process_ids() -> list[int]:
    """Return process ancestors, closest first, for Windows console attachment."""
    import ctypes
    from ctypes import wintypes

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.c_size_t),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", wintypes.WCHAR * 260),
        ]

    kernel32 = ctypes.windll.kernel32
    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)  # TH32CS_SNAPPROCESS
    invalid_handle = ctypes.c_void_p(-1).value
    if snapshot == invalid_handle:
        return []

    parents: dict[int, int] = {}
    entry = PROCESSENTRY32W()
    entry.dwSize = ctypes.sizeof(entry)
    try:
        if kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
            while True:
                parents[entry.th32ProcessID] = entry.th32ParentProcessID
                if not kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                    break
    finally:
        kernel32.CloseHandle(snapshot)

    result: list[int] = []
    process_id = kernel32.GetCurrentProcessId()
    while process_id in parents:
        process_id = parents[process_id]
        if not process_id or process_id in result:
            break
        result.append(process_id)
    return result


def main() -> int:
    cli_result = _run_cli(sys.argv[1:])
    if cli_result is not None:
        return cli_result

    from pathlib import Path
    from PyQt6.QtGui import QIcon
    from PyQt6.QtWidgets import QApplication
    from ui.style import STYLE_SHEET
    from utils.logger import install_excepthook
    from utils.resource_path import resource_path

    install_excepthook()

    app = QApplication(sys.argv)
    app.setApplicationName("SFC2")
    app.setStyleSheet(STYLE_SHEET)

    icon_file = "resources/favicon.ico" if sys.platform == "win32" else "resources/SFC_cnv.png"
    icon_path = resource_path(icon_file)
    if not Path(icon_path).is_file():
        icon_path = resource_path("resources/favicon.ico")
    if Path(icon_path).is_file():
        app.setWindowIcon(QIcon(icon_path))

    # メインウィンドウの読み込みはここで行う（重いプレビュー/FFmpeg関連は
    # ウィジェット側で実際に使うタイミングまで遅延初期化される）
    from ui.main_window import MainWindow

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())