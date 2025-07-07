# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['app/pyqt_app.py'],
    pathex=['app'],
    binaries=[],
    datas=[
        ('kokoro-env/lib/python3.11/site-packages/language_tags/data/json', 'language_tags/data/json'),
        ('kokoro-env/lib/python3.11/site-packages/espeakng_loader/espeak-ng-data', 'espeakng_loader/espeak-ng-data'),
    ],
    hiddenimports=[],
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
    name='pyqt_app',
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
)
app = BUNDLE(
    exe,
    name='VibeTails.app',
    icon='assets/logo.icns',
    bundle_identifier='com.vibetails.desktop',
)
