# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = []
hiddenimports += collect_submodules('proxy')


a = Analysis(
    ['C:/Users/Parsa/Desktop/gateway-main/app/desktop.py'],
    pathex=['C:/Users/Parsa/Desktop/gateway-main'],
    binaries=[],
    datas=[('C:/Users/Parsa/Desktop/gateway-main/index.html', '.'), ('C:/Users/Parsa/Desktop/gateway-main/styles.css', '.'), ('C:/Users/Parsa/Desktop/gateway-main/data.js', '.'), ('C:/Users/Parsa/Desktop/gateway-main/app.js', '.')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Code Gateway',
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
    icon=['C:/Users/Parsa/Desktop/gateway-main/icon.ico'],
)
