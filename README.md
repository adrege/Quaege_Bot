# Quaege Bot 🎉

**Python tools die het leven van de quaege makkelijker maken**

A collection of automated tools for managing Adrege's financial administration and member communications.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📋 Features

### Main GUI Application
- **User-friendly interface** with tabs for scripts and settings
- **Integrated tools** for common Quaege tasks
- **Configuration management** via GUI (no code editing needed)
- **Dry-run mode** for email operations with confirmation dialogs

### Available Tools

1. **📄 Split Boekhouding**
   - Splits accounting HTML files into individual member statements
   - Input: Combined accounting HTML file
   - Output: Individual HTML files in `rekeningen_split/` folder

2. **💰 Betaalafschrift Converter**
   - Converts payment statements to savings table format
   - Input: Payment statement file
   - Output: Excel/CSV transaction table

3. **✉️ Test E-mail**
   - Sends a test balance update email to yourself
   - Useful for previewing email format and content
   - No arguments needed (uses your email from settings)

4. **📧 Saldo Updates (Bulk)**
   - Sends balance updates to all members with status 'S'
   - Includes dry-run preview before sending
   - Attaches individual HTML statements
   - ⚠️ Use with caution - sends to all active members!

---

## 🚀 Quick Start

### For End Users (No Python Required)

1. **Download** the `Quaege_Bot.zip` file
2. **Extract** to any location (e.g., `C:\Tools\Quaege_Bot\`)
3. **Run** `Quaege_Tools.exe`
4. **Configure** settings in the Settings tab:
   - Set path to CSV (ledenadministratie)
   - Add payment link
   - Enter your email for test messages
5. **Use the tools** from the Scripts tab

### For Developers

#### Prerequisites
- Python 3.8 or higher
- Virtual environment (recommended)

#### Installation

```powershell
# Clone the repository
git clone https://github.com/oli4tje01/Quaege_Bot.git
cd Quaege_Bot

# Create and activate virtual environment
python -m venv "quaege tools.venv"
.\quaege tools.venv\Scripts\Activate.ps1

# Install dependencies
pip install pandas openpyxl beautifulsoup4 pypdf pyinstaller
```

#### Running from Source

```powershell
# Activate virtual environment
.\quaege tools.venv\Scripts\Activate.ps1

# Run the GUI
python main_gui.py
```

---

## 📦 Building Executables

Want to create a standalone executable that others can use without Python?

### Quick Build

```powershell
.\build_windows.ps1
```

The distributable application will be in `dist\Quaege_Bot\`

**📖 Detailed build instructions:** See [README_build.md](README_build.md)

---

## ⚙️ Configuration

### Settings File (`settings.json`)

The GUI creates and manages this file automatically. Contains:

```json
{
    "csv_path": "path/to/Ledenadministratie - Leden.csv",
    "betaal_link": "https://your-payment-link",
    "text": "Custom message text",
    "eigen_email": "your-email@adrege.nl"
}
```

### Config File (`config.py`)

Contains email template, SMTP settings, and logo configuration. Edit directly for:
- Email HTML template
- SMTP server settings
- Logo path
- Sender email

**⚠️ Security Note:** Never commit `config.py` with passwords to Git!

---

## 📁 Project Structure

```
Quaege_Bot/
├── main_gui.py                  # Main GUI application
├── config.py                    # Email config & templates
├── settings.json                # User settings (generated)
├── Adrege_logo.png             # Logo for emails
├── build_windows.ps1           # Build script
├── build_windows.spec          # PyInstaller configuration
├── README.md                   # This file
├── README_build.md             # Build documentation
├── scripts/
│   ├── split_rekeningen.py     # HTML splitter tool
│   ├── generate_transactions.py # Transaction converter
│   ├── test_saldo_update.py    # Test email sender
│   └── Stuur_saldo_updates.py  # Bulk email sender
├── rekeningen_split/           # Output folder for split HTML
└── quaege tools.venv/          # Virtual environment
```

---

## 🔧 Usage Examples

### Using the GUI

1. **Launch** `Quaege_Tools.exe` (or `python main_gui.py` from source)
2. **Select a tool** from the Scripts tab
3. **Browse** for input file if needed
4. **Click Run**
5. **Check the output log** for results

### Running Scripts Directly (Development)

```powershell
# Split rekeningen
python scripts/split_rekeningen.py path/to/combined.html

# Generate transactions
python scripts/generate_transactions.py path/to/statement.pdf

# Send test email
python scripts/test_saldo_update.py

# Send bulk emails (with dry-run)
python scripts/Stuur_saldo_updates.py --dry-run
python scripts/Stuur_saldo_updates.py  # Actually send
```

---

## 🛡️ Safety Features

- **Dry-run mode** for email operations
- **Confirmation dialogs** before sending bulk emails
- **Preview output** in the GUI log
- **Settings validation** before running tools

---

## 📝 Requirements

### Python Packages
- `pandas` - Data manipulation for CSV/Excel
- `openpyxl` - Excel file handling
- `beautifulsoup4` - HTML parsing
- `pypdf` - PDF operations
- `pyinstaller` - Executable creation (dev only)

### System Requirements
- **OS**: Windows 10/11
- **RAM**: 4GB minimum
- **Storage**: 200MB for application + data

---

## 🐛 Troubleshooting

### Common Issues

**"Script not found" error:**
- Make sure all files are in the correct location
- Check that `scripts/` folder exists with all `.py` files

**Emails not sending:**
- Verify SMTP settings in `config.py`
- Check email credentials
- Ensure firewall allows SMTP connections

**GUI won't start:**
- Check Python version (3.8+ required)
- Verify all dependencies installed: `pip list`
- Try running from terminal to see error messages

**Frozen exe doesn't work:**
- Ensure all files are extracted together
- Check Windows Defender/antivirus settings
- Verify `config.py` and `Adrege_logo.png` are present

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👤 Author

**Olivier van Doorn**  
*Quaegé 2025 der Demosdispuut Adregé*



---

## 🙏 Acknowledgments

- Created with ❤️ for Demosdispuut Adregé
- Built with Python and PyInstaller
- Special thanks to all Quaegés who tested this tool

---

**Gemaakt met liefde 45 :)**
