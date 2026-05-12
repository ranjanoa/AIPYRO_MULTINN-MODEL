# -*- mode: python ; coding: utf-8 -*-
import sys
sys.setrecursionlimit(sys.getrecursionlimit() * 5)

from PyInstaller.utils.hooks import collect_submodules

# Collect all submodules for problematic packages
dns_submodules = collect_submodules('dns')
eventlet_submodules = collect_submodules('eventlet')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[('templates', 'templates'), ('static', 'static'), ('logo.ico', '.')],
    hiddenimports=[
        'engineio.async_drivers.eventlet',
        'engineio.async_drivers.threading',
        'socketio.async_drivers.eventlet',
        'socketio.async_drivers.threading',
        'importlib_metadata',
        'pyarrow',
        'fastparquet',
        'dns.btree',  # Explicitly include commonly missed submodules
        'dns.node',
    ] + dns_submodules + eventlet_submodules,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['hook-eventlet.py'],
    excludes=['files'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CimporApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logo.ico',
)
