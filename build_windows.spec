# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for building Quaege_Bot tools
This creates multiple executables:
  - main_gui.exe (the main GUI launcher)
  - split_rekeningen.exe
  - generate_transactions.exe
  - test_saldo_update.exe
  - Stuur_saldo_updates.exe
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import os

block_cipher = None

# Common data files to include
datas = [
    ('Adrege_logo.png', '.'),
    ('config.py', '.'),
    ('settings.json', '.'),
]

# Hidden imports needed across all scripts
hiddenimports = [
    'tkinter',
    'email.mime.multipart',
    'email.mime.text',
    'email.mime.image',
    'email.mime.application',
    'smtplib',
    'imaplib',
    'csv',
    'pandas',
    'openpyxl',
    'bs4',
    'pypdf',
]

# ========== Script 1: split_rekeningen.py ==========
a_split = Analysis(
    ['scripts\\split_rekeningen.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports + ['bs4.builder._htmlparser', 'bs4.builder._lxml'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz_split = PYZ(a_split.pure, a_split.zipped_data, cipher=block_cipher)

exe_split = EXE(
    pyz_split,
    a_split.scripts,
    [],
    exclude_binaries=True,
    name='split_rekeningen',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Console for command-line tools
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# ========== Script 2: generate_transactions.py ==========
a_gen = Analysis(
    ['scripts\\generate_transactions.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports + ['openpyxl.cell._writer'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz_gen = PYZ(a_gen.pure, a_gen.zipped_data, cipher=block_cipher)

exe_gen = EXE(
    pyz_gen,
    a_gen.scripts,
    [],
    exclude_binaries=True,
    name='generate_transactions',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# ========== Script 3: test_saldo_update.py ==========
a_test = Analysis(
    ['scripts\\test_saldo_update.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz_test = PYZ(a_test.pure, a_test.zipped_data, cipher=block_cipher)

exe_test = EXE(
    pyz_test,
    a_test.scripts,
    [],
    exclude_binaries=True,
    name='test_saldo_update',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# ========== Script 4: Stuur_saldo_updates.py ==========
a_stuur = Analysis(
    ['scripts\\Stuur_saldo_updates.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz_stuur = PYZ(a_stuur.pure, a_stuur.zipped_data, cipher=block_cipher)

exe_stuur = EXE(
    pyz_stuur,
    a_stuur.scripts,
    [],
    exclude_binaries=True,
    name='Stuur_saldo_updates',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# ========== Main GUI: main_gui.py ==========
a_gui = Analysis(
    ['main_gui.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz_gui = PYZ(a_gui.pure, a_gui.zipped_data, cipher=block_cipher)

exe_gui = EXE(
    pyz_gui,
    a_gui.scripts,
    [],
    exclude_binaries=True,
    name='Quaege_Tools',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='Adrege_logo.png',  # Optional: add icon
)

# ========== COLLECT: Bundle everything together ==========
coll = COLLECT(
    exe_gui,
    a_gui.binaries,
    a_gui.zipfiles,
    a_gui.datas,
    exe_split,
    a_split.binaries,
    a_split.zipfiles,
    a_split.datas,
    exe_gen,
    a_gen.binaries,
    a_gen.zipfiles,
    a_gen.datas,
    exe_test,
    a_test.binaries,
    a_test.zipfiles,
    a_test.datas,
    exe_stuur,
    a_stuur.binaries,
    a_stuur.zipfiles,
    a_stuur.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Quaege_Bot',
)
