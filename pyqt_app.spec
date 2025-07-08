# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['app/pyqt_app.py'],
    pathex=['app'],
    binaries=[],
    datas=[
        ('kokoro-env/lib/python3.11/site-packages/language_tags/data/json', 'language_tags/data/json'),
        ('kokoro-env/lib/python3.11/site-packages/espeakng_loader/espeak-ng-data', 'espeakng_loader/espeak-ng-data'),
        ('kokoro-env/lib/python3.11/site-packages/misaki/data/us_gold.json', 'misaki/data'),
        ('kokoro-env/lib/python3.11/site-packages/misaki/data/us_silver.json', 'misaki/data'),
        ('kokoro-env/lib/python3.11/site-packages/misaki/data/gb_gold.json', 'misaki/data'),
        ('kokoro-env/lib/python3.11/site-packages/misaki/data/gb_silver.json', 'misaki/data'),
        ('kokoro-env/lib/python3.11/site-packages/misaki/data/vi_acronyms.json', 'misaki/data'),
        ('kokoro-env/lib/python3.11/site-packages/misaki/data/vi_symbols.json', 'misaki/data'),
        ('kokoro-env/lib/python3.11/site-packages/misaki/data/vi_teencode.json', 'misaki/data'),
        ('kokoro-env/lib/python3.11/site-packages/misaki/data/ja_words.txt', 'misaki/data'),
        ('kokoro-env/lib/python3.11/site-packages/misaki/data/__init__.py', 'misaki/data'),
    ],
    hiddenimports=[],
    hookspath=['hooks'],
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
