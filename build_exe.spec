# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Import for adding data files
from PyInstaller.utils.hooks import collect_data_files
import os

# Get the base directory
base_dir = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['main_gui.py'],
    pathex=[base_dir],
    binaries=[],
    datas=[
        ('config.py', '.'),
        ('scripts/*.py', 'scripts'),
        ('rekeningen_split/*.html', 'rekeningen_split'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'tkinter.ttk',
        'subprocess',
        'json',
        're',
        'pandas',
        'numpy',
        'openpyxl',
        'pypdf',
        'bs4',
        'beautifulsoup4',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='QuaegeBot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to False to hide console window for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # You can add an .ico file path here if you have an icon
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='QuaegeBot',
)
