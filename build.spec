# -*- mode: python ; coding: utf-8 -*-
# PyInstaller build spec for LokiBytes Edge Uninstaller.
#
# Build with:  pyinstaller build.spec
# Output:      dist/LokiBytes-Edge-Uninstaller.exe
#
# uac_admin=True embeds a manifest requiring administrator elevation, so
# Windows prompts for UAC before any of the app's code runs.

a = Analysis(
    ["Uninstall-Edge-GUI.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("Uninstall-Edge.ps1", "."),
        ("resources/lokibytes_logo.png", "resources"),
        ("resources/lokibytes_icon.ico", "resources"),
        ("resources/LokiBytes_About.png", "resources"),
    ],
    hiddenimports=["customtkinter"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="LokiBytes-Edge-Uninstaller",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    uac_admin=True,
    icon="resources/lokibytes_icon.ico",
)
