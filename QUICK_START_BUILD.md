# Quick Start Guide - Building Your Executable

## 🎯 Goal
Create a Windows executable (.exe) that anyone can use without installing Python.

## ⚡ Quick Build (3 Steps)

### Step 1: Open PowerShell in your project folder
```powershell
cd "c:\Users\20233963\Documents\Quaege\Quaege_Bot"
```

### Step 2: Run the build script
```powershell
.\build_windows.ps1
```

### Step 3: Find your distributable app
Location: `dist\Quaege_Bot\`

**That's it!** 🎉

## 📦 What You Get

After building, you'll have a complete application in `dist\Quaege_Bot\`:

```
Quaege_Bot/
├── Quaege_Tools.exe         ← Main app (double-click this!)
├── split_rekeningen.exe
├── generate_transactions.exe
├── test_saldo_update.exe
├── Stuur_saldo_updates.exe
├── config.py
├── settings.json
├── Adrege_logo.png
└── [DLL files and dependencies]
```

## 🚀 Distributing to Others

### Option 1: Create ZIP
```powershell
Compress-Archive -Path "dist\Quaege_Bot" -DestinationPath "Quaege_Bot_v1.0.zip"
```

Send this ZIP to anyone. They just:
1. Extract it
2. Double-click `Quaege_Tools.exe`
3. No Python needed! ✨

### Option 2: Copy Folder
Simply copy the entire `dist\Quaege_Bot` folder to:
- USB drive
- Network share
- Cloud storage

## 🔧 If Build Fails

### "PyInstaller not found"
```powershell
.\quaege tools.venv\Scripts\Activate.ps1
pip install pyinstaller
```

### "Module not found" errors
```powershell
pip install pandas openpyxl beautifulsoup4 pypdf
```

### Virtual environment not activating
Try running as administrator, or use:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 📚 More Help

- **Detailed build guide**: See `README_build.md`
- **User manual**: See `README.md`
- **Build configuration**: Edit `build_windows.spec`

## ✅ What Changed

To make this work, I updated:

1. **`main_gui.py`**
   - Detects when running as .exe
   - Calls tool .exe files instead of Python scripts
   - Sets correct working directory

2. **Created `build_windows.spec`**
   - PyInstaller configuration
   - Builds 5 executables (GUI + 4 tools)
   - Bundles all dependencies

3. **Created `build_windows.ps1`**
   - Automated build script
   - Checks dependencies
   - Creates distributable folder

4. **Created documentation**
   - `README_build.md` - Build instructions
   - `README.md` - Usage guide

## 🎯 First Build Checklist

- [ ] Virtual environment activated?
- [ ] All dependencies installed? (`pip install pandas openpyxl beautifulsoup4 pypdf pyinstaller`)
- [ ] `config.py` configured with email settings?
- [ ] `Adrege_logo.png` exists?
- [ ] Run `.\build_windows.ps1`
- [ ] Check `dist\Quaege_Bot\` folder
- [ ] Test `Quaege_Tools.exe` works!

---

**Questions?** Check the detailed guides or contact support!
