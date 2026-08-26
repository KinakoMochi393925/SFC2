"""アプリ共通ロガー。例外はすべてここを通じて logs/app.log に保存する。"""
import logging
import sys
from logging.handlers import RotatingFileHandler

from utils.constants import LOG_FILE, LOGS_DIR

_logger = None


def get_logger() -> logging.Logger:
    """シングルトンのロガーを返す。初回呼び出し時のみファイルハンドラを作成する（起動時の無駄なI/Oを避けるため遅延初期化）。"""
    global _logger
    if _logger is not None:
        return _logger

    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("SFC2")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        file_handler = RotatingFileHandler(
            LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _logger = logger
    return _logger


def enable_console_logging() -> None:
    """Also send application logs to stderr for an interactive CLI invocation."""
    logger = get_logger()
    if any(getattr(handler, "_sfc2_cli_handler", False) for handler in logger.handlers):
        return

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler._sfc2_cli_handler = True
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(console_handler)


def install_excepthook() -> None:
    """未捕捉例外をすべてログに記録する。"""

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        get_logger().critical(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = handle_exception
