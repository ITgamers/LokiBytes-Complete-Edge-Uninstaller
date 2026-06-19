# LokiBytes Edge Uninstaller

A small Windows utility that **fully removes Microsoft Edge (Chromium)** — including the
EdgeUpdate service, scheduled tasks, leftover files, shortcuts, and registry keys — and then
blocks Windows from silently reinstalling it.

![platform](https://img.shields.io/badge/platform-Windows%2010%2F11-blue)
![license](https://img.shields.io/badge/license-GPLv3%20%2B%20Commons%20Clause-blue)

## Why this exists

Microsoft only exposes a real "Uninstall" button for Edge when Windows' region (GeoID) is set
to a country in the European Economic Area, due to the EU's Digital Markets Act. Everywhere
else, Edge is treated as an undetachable system component.

This tool temporarily switches your system region to an EEA country so the same uninstall gate
EU users get is unlocked, force-uninstalls Edge via its own installer, then cleans up everything
that normally gets left behind. The **Microsoft Edge WebView2 Runtime is deliberately left
alone** — it's a separate component many third-party apps depend on independently of the Edge
browser itself.

## What it does

1. Records your current Windows region (GeoID) so you can revert manually if needed
2. Temporarily switches the region to an EEA country (Germany by default)
3. Restarts Explorer so the region change takes effect
4. Closes any running Edge / Edge Update processes
5. Force-uninstalls Edge via its own `setup.exe` (system-level and user-level)
6. Removes EdgeUpdate scheduled tasks and services (`edgeupdate`, `edgeupdatem`)
7. Deletes leftover Edge/EdgeUpdate folders, registry keys, and Start Menu/Desktop shortcuts
8. Sets an EdgeUpdate policy that blocks Edge from silently reinstalling itself (can be opted
   out of via the GUI checkbox or `-SkipAutoReinstallBlock`)
9. Optionally reverts the region back to its original value

A reboot is recommended after running it, and Windows feature updates (not regular Edge
auto-updates) can still reinstall Edge — if that happens, just run the tool again.

## Download

Grab the latest `LokiBytes-Edge-Uninstaller.exe` from the
[Releases](../../releases/latest) page. No installation or Python required — just run it.

## Usage

1. Download and run `LokiBytes-Edge-Uninstaller.exe`
2. Accept the UAC prompt (administrator rights are required)
3. Pick a temporary EEA region (Germany is fine for everyone — any EEA country satisfies the
   uninstall gate), optionally check "revert region after uninstalling", and leave "block Edge
   from silently reinstalling itself" checked (recommended)
4. Click **Uninstall Edge**, make sure you already have another browser installed, then wait
   out the 5-second countdown and click **Continue**
5. Watch the live log, then reboot when it's done

### Running from source instead

```powershell
git clone https://github.com/ITgamers/LokiBytes-Edge-Uninstaller.git
cd LokiBytes-Edge-Uninstaller
pip install -r requirements.txt
python "Uninstall-Edge-GUI.py"
```

The GUI re-launches itself elevated automatically — no need to open an admin terminal first.

### Using the PowerShell script directly (no GUI)

```powershell
.\Uninstall-Edge.ps1                       # uses Germany, leaves region switched
.\Uninstall-Edge.ps1 -TempRegion FR        # use France instead
.\Uninstall-Edge.ps1 -RevertRegionAfter    # switch back automatically when done
```

Must be run from an elevated (Administrator) PowerShell window.

## Building the .exe yourself

```powershell
pip install -r requirements.txt pyinstaller
pyinstaller build.spec
```

The output is written to `dist\LokiBytes-Edge-Uninstaller.exe`. The build spec embeds a manifest
that requires administrator elevation, so Windows prompts for UAC before any app code runs.

## Requirements

- Windows 10 or 11
- Administrator rights
- Python 3.10+ (only if running/building from source — the released `.exe` is standalone)

## Disclaimer

This tool modifies your system's region setting, registry, and scheduled tasks. It only ever
targets Edge/EdgeUpdate-related keys and leaves WebView2 untouched, but as with any tool that
edits the registry, use it at your own risk. Review [Uninstall-Edge.ps1](Uninstall-Edge.ps1)
before running it if you want to see exactly what it changes.

## License

GNU GPLv3 with a Commons Clause restriction (no reselling) — see [LICENSE](LICENSE).

## Support

If this saved you some time, consider [donating via PayPal](https://paypal.me/ITgamer).
