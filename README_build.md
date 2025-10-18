# Building Quaege Bot for Distribution

This guide explains how to build the Quaege Bot application into standalone Windows executables that can be distributed to users who don't have Python installed.

## Prerequisites

### For Building
- **Python 3.8+** installed on your system
- **Virtual environment** (recommended): `quaege tools.venv`
- **PyInstaller** (will be installed automatically by the build script)
- All project dependencies installed (see `requirements.txt` if you have one)

### Required Python Packages
The following packages must be installed in your Python environment:
- `pyinstaller` (for building executables)
- `pandas` (for CSV/Excel handling)
- `openpyxl` (for Excel files)
- `beautifulsoup4` (for HTML parsing)
- `pypdf` (for PDF operations)

## Quick Build Instructions

### Option 1: Automated Build (Recommended)

1. **Open PowerShell** in the project directory
2. **Run the build script:**
   ```powershell
   .\build_windows.ps1
   ```

The script will:
- Activate your virtual environment (if found)
- Install PyInstaller if needed
- Clean previous builds
- Build all executables using `build_windows.spec`
- Copy additional files (logo, settings, HTML templates)
- Create a distributable folder at `dist\Quaege_Bot\`

### Option 2: Manual Build

If you prefer to build manually:

```powershell
# Activate virtual environment
.\quaege tools.venv\Scripts\Activate.ps1

# Install PyInstaller
python -m pip install pyinstaller

# Clean previous builds
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

# Build with spec file
python -m PyInstaller build_windows.spec --clean

# Copy additional files
Copy-Item -Recurse rekeningen_split dist\Quaege_Bot\
Copy-Item settings.json dist\Quaege_Bot\
```

## Build Output

After building, you'll find the complete application in:
```
dist\Quaege_Bot\
├── Quaege_Tools.exe           ← Main GUI (double-click to run)
├── split_rekeningen.exe       ← Tool: Split HTML files
├── generate_transactions.exe  ← Tool: Convert betaalafschrift
├── test_saldo_update.exe      ← Tool: Send test email
├── Stuur_saldo_updates.exe    ← Tool: Send bulk emails
├── config.py                  ← Email template & settings
├── settings.json              ← User-configurable settings
├── Adrege_logo.png           ← Logo image
├── rekeningen_split\          ← HTML templates folder
└── [Various DLLs and dependencies]
```

## What Gets Built

The build process creates **5 executables**:

### 1. **Quaege_Tools.exe** (Main GUI)
- The main launcher with a graphical interface
- No console window (runs as a GUI app)
- Calls the other tool executables as needed

### 2-5. **Tool Executables**
- `split_rekeningen.exe` - Splits accounting HTML files
- `generate_transactions.exe` - Converts payment statements
- `test_saldo_update.exe` - Sends test emails
- `Stuur_saldo_updates.exe` - Sends bulk balance updates
- Console applications (show terminal output)

## Distribution

### Creating a Distributable Package

1. **After building**, zip the entire `dist\Quaege_Bot` folder:
   ```powershell
   Compress-Archive -Path "dist\Quaege_Bot" -DestinationPath "Quaege_Bot_v1.0.zip"
   ```

2. **Share the ZIP file** with users via:
   - Email
   - Cloud storage (Google Drive, OneDrive, etc.)
   - Network share
   - USB drive

### User Installation

Users should:
1. **Extract the ZIP file** to any location (e.g., `C:\Tools\Quaege_Bot\`)
2. **Double-click `Quaege_Tools.exe`** to run the application
3. **Configure settings** in the Settings tab on first run

**No Python installation required!** All dependencies are bundled.

## File Structure Explanation

### Critical Files
- **config.py**: Email template, SMTP settings, logo path
- **settings.json**: User-configurable paths and settings (CSV, payment link, etc.)
- **Adrege_logo.png**: Logo embedded in emails

### Why These Files?
- The GUI reads/writes `settings.json` for user preferences
- The tool scripts import `config.py` for email formatting
- All scripts look for the logo in the same directory

## Troubleshooting

### Build Fails with "ModuleNotFoundError"
**Solution**: Install missing package:
```powershell
python -m pip install <package-name>
```

### "PyInstaller not found" Error
**Solution**: Install PyInstaller:
```powershell
python -m pip install pyinstaller
```

### Executables Don't Run on User's Machine
**Possible causes**:
1. **Antivirus blocking**: Some antivirus software flags PyInstaller executables
   - Solution: Add exception or whitelist the folder
2. **Missing Visual C++ Runtime**: Older Windows may need it
   - Solution: Install [Microsoft Visual C++ Redistributable](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)

### "Config file not found" at Runtime
**Solution**: Ensure `config.py` is in the same folder as the executables

### Logo Not Appearing in Emails
**Solution**: Verify `Adrege_logo.png` is in the distribution folder

## Advanced Configuration

### Customizing the Build

Edit `build_windows.spec` to:
- Add more scripts/tools
- Include additional data files
- Change icon: Modify `icon='Adrege_logo.png'` (use `.ico` file)
- Adjust hidden imports for libraries

### Adding a Desktop Icon

Create a shortcut:
```powershell
# PowerShell command to create shortcut
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut("$env:USERPROFILE\Desktop\Quaege Tools.lnk")
$Shortcut.TargetPath = "C:\Path\To\dist\Quaege_Bot\Quaege_Tools.exe"
$Shortcut.Save()
```

## Development vs Distribution

| Aspect | Development | Distribution |
|--------|-------------|--------------|
| Python Required | ✅ Yes | ❌ No |
| Runs From | Source `.py` files | Compiled `.exe` |
| Script Location | `scripts/` folder | Same folder as GUI |
| Startup Time | Fast | Slower (unpacking) |
| File Size | Small | ~50-100 MB |
| Updates | Edit code directly | Rebuild & redistribute |

## Updating the Application

When you make changes:

1. **Edit the source files** (`.py` files)
2. **Test thoroughly** in development mode
3. **Rebuild** using `.\build_windows.ps1`
4. **Redistribute** the new `dist\Quaege_Bot` folder
5. **Version your releases**: Rename to `Quaege_Bot_v1.1.zip`, etc.

## Security Considerations

### Email Credentials
The `config.py` file contains the email password (`config.password`). 

**⚠️ Important:**
- **DO NOT** include `config.py` with passwords in public distributions
- Users should add their own password after extracting
- Or better: Use environment variables or secure credential storage

### Alternative Approach
Modify scripts to prompt for password at runtime:
```python
import getpass
password = getpass.getpass("Enter email password: ")
```

## Support

For issues:
1. Check that all files are present in the distribution
2. Verify `settings.json` is configured correctly
3. Check Windows Event Viewer for error details
4. Run from Command Prompt to see error messages

---

**Built with ❤️ using PyInstaller**
