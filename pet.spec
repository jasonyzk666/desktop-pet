# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['src/pet.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/pet_idle.png', 'assets'),
           ('assets/pet_walk.png', 'assets'),
           ('assets/pet_walk_left.png', 'assets'),
           ('assets/app.ico', 'assets'),
           ('assets/app_icon.png', 'assets'),
           ('assets/app_icon_round.png', 'assets'),
           ('assets/tray_icon.png', 'assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='desktop_pet',
    icon='assets/app.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
