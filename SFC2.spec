# -*- mode: python ; coding: utf-8 -*-
# SFC2 を1ファイルのexeにパッケージングするためのPyInstaller specファイル。
#
# 使い方:
#   pip install pyinstaller
#   pyinstaller SFC2.spec
#
# resources/favicon.ico を実行ファイルのアイコンにし、かつexe内部にも
# 組み込むことで、タイトルバー・タスクバーのアイコン表示にも対応する。
# (参考: https://qiita.com/y-tsutsu/items/a8cc1578dd2f930e5439)

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    # 実行時に utils.resource_path.resource_path() で参照できるよう同梱する
    datas=[("resources/favicon.ico", "resources")],
    hiddenimports=[],
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
    icon="resources/favicon.ico",
)
