# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for lolrus.

Build with: pyinstaller lolrus.spec
"""

import sys
from pathlib import Path

# Determine platform-specific settings
is_windows = sys.platform == "win32"
is_macos = sys.platform == "darwin"
is_linux = sys.platform.startswith("linux")

# Application metadata
app_name = "lolrus"
app_version = "0.1.0"

# Source path
src_path = Path("src/lolrus")
assets_path = Path("assets")

# Icon paths
icon_windows = str(assets_path / "lolrus.ico") if is_windows else None
icon_macos = str(assets_path / "lolrus.png")  # Use PNG for macOS (convert to .icns for production)

# Collect all source files
a = Analysis(
    [str(src_path / "__main__.py")],
    pathex=[],
    binaries=[],
    datas=[
        (str(assets_path / "lolrus.png"), "assets"),
        (str(assets_path / "lolrus.ico"), "assets"),
    ],
    hiddenimports=[
        # boto3 and botocore have many dynamic imports
        "boto3",
        "botocore",
        "botocore.regions",
        "botocore.httpsession",
        "botocore.credentials",
        "botocore.config",
        "botocore.handlers",
        "botocore.hooks",
        "botocore.loaders",
        "botocore.parsers",
        "botocore.retryhandler",
        "botocore.translate",
        "botocore.utils",
        "botocore.endpoint",
        "botocore.endpoint_provider",
        # keyring backends
        "keyring.backends",
        "keyring.backends.Windows",
        "keyring.backends.macOS",
        "keyring.backends.SecretService",
        "keyring.backends.kwallet",
        "keyring.backends.libsecret",
        # dearpygui
        "dearpygui",
        "dearpygui.dearpygui",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        # Note: tkinter is needed for clipboard functionality
        # Note: PIL/Pillow is needed for image previews
        "matplotlib",
        "pandas",
        "scipy",
        "cv2",
        "torch",
        "tensorflow",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Platform-specific executable settings
if is_macos:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=app_name,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,  # GUI app, no console
        disable_windowed_traceback=False,
        argv_emulation=True,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=app_name,
    )
    app = BUNDLE(
        coll,
        name=f"{app_name}.app",
        icon=icon_macos,  # Use PNG; convert to .icns for production builds
        bundle_identifier=f"com.zimventures.{app_name}",
        info_plist={
            "CFBundleName": app_name,
            "CFBundleDisplayName": "lolrus - S3 Browser",
            "CFBundleVersion": app_version,
            "CFBundleShortVersionString": app_version,
            "NSHighResolutionCapable": True,
        },
    )
elif is_windows:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name=app_name,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,  # GUI app, no console
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=icon_windows,
    )
else:  # Linux
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name=app_name,
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
