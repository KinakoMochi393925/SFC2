# -*- mode: python ; coding: utf-8 -*-
# SFC2 を1ファイルのexeにパッケージングするためのPyInstaller specファイル。
#
# 使い方:
#   pip install pyinstaller
#   pyinstaller SFC2.spec
#
# resources/favicon.ico を実行ファイルのアイコンにし、かつexe内部にも
# 組み込むことで、タイトルバー・タスクバーのアイコン表示にも対応する。

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    # 実行時に utils.resource_path.resource_path() で参照できるよう同梱する
    datas=[("resources/favicon.ico", "resources")],
    # These are loaded only after CLI argument detection, so PyInstaller cannot
    # discover them through normal static import analysis.
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
    # Normal SFC2 launches must remain GUI-only. CLI calls attach to a parent
    # terminal at runtime in main.py.
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="resources/favicon.ico",
)
