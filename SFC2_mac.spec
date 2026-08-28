# -*- mode: python ; coding: utf-8 -*-
# SFC2 をmacOS用アプリケーション (.app) にパッケージングするためのPyInstaller specファイル。
#
# 使い方:
#   1. あらかじめ resources/favicon.icns を準備してください。(本リポジトリにはicnsがありません。)
#   2. pyinstaller SFC2_mac.spec

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    # アプリ内部から利用できるように ico や icns 等のリソースを同梱
    datas=[("resources/favicon.ico", "resources")],
    hiddenimports=["services.cli_conversion", "services.windows_context_menu"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="SFC2",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="resources/favicon.icns",
)

# macOS用 .app バンドル設定（追加）
app = BUNDLE(
    exe,
    name="SFC2.app",
    icon="resources/favicon.icns",
    bundle_identifier="com.yourdomain.sfc2",
)