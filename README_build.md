# Building Windows .exe for Quaege Tools

This project can be bundled into standalone Windows executables using PyInstaller. The output can be shared with users who do not have Python installed.

## Prerequisites
- Windows
- A working Python environment (use the existing `quaege tools.venv` if available)
- The required packages installed (pandas, numpy, openpyxl, pypdf, beautifulsoup4, python-dateutil, pytz, etc.)

## Quick build
1. Open Windows PowerShell in this folder.
2. Run the build script:

```powershell
# optional flags: -OneFile to build single-file exe, default builds a folder (faster startup)
# -NoConsole hides the console window for the GUI app (default)
./build_windows.ps1
```

Artifacts will be in the `dist` folder:
- `dist/QuaegeTools/QuaegeTools.exe` – the GUI launcher
- Tool executables: `split_rekeningen.exe`, `generate_transactions.exe`, `test_saldo_update.exe`, `Stuur_saldo_updates.exe`

Place `settings.json` next to the .exe to configure CSV path, betaal link, and test email. The folder `rekeningen_split/` and `Adrege_logo.png` are bundled; you can replace them next to the exe if needed.

## Notes
- If packaging fails with import errors for numpy/pandas/openpyxl, ensure those packages are installed in your environment.
- Large scientific packages make single-file startup slower. Prefer the default one-folder build for better UX.
- Email credentials are read from `config.py`. For distribution, prefer environment variables or a secure secret manager instead of committing plaintext passwords.
