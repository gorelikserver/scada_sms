# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Add this import
import sys
from os.path import join, dirname, abspath

# Add src to path
src_path = join(dirname(abspath('__file__')), 'src')
sys.path.insert(0, src_path)
# List all your source files
src_files = [
    'src/main.py',
    'src/__init__.py',
    'src/config.py',
    'src/database.py',
    'src/date_dimension.py',
    'src/date_initializer.py',
    'src/db_init.py',
    'src/logger.py',
    'src/queue_manager.py',
    'src/sms_sender.py',
]

# Additional data files to include
added_files = [
    ('config.ini', '.'),  # Include config.ini in the root directory
    ('src/*.py', 'src'),  # Include all Python files in src directory
]

# Define analysis
a = Analysis(
    ['src/main.py'],  # Main entry point
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'pyodbc',
        'pyluach',
        'pyluach.dates',
        'pyluach.hebrewcal',
        'click',
        'requests',
        'configparser',
        'pandas',
        'numpy',
        'msvcrt',
        'logging.handlers',
        'datetime',
        'json',
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

# Define PYZ (bundle of Python modules)
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

# Define EXE
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='scada_sms',
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
    icon=None,  # Add an icon file path here if you have one
)