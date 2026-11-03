import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import subprocess
import sys
import os
import json
import re
import csv
import shutil
from pathlib import Path
from app_paths import (
    EXPORT_DIR, SETTINGS_PATH, USER_CONFIG_PATH, ensure_directories,
    ensure_user_config,
)

# ---- Paths ----
# When frozen with PyInstaller, use the executable's directory
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(__file__)

SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
CONFIG_PATH = str(USER_CONFIG_PATH)
SETTINGS_JSON = str(SETTINGS_PATH)

def get_venv_python():
    override = os.environ.get("VENV_PYTHON")
    if override:
        return override

    venv_dir = os.path.join(BASE_DIR, "quaege tools.venv")
    candidates = [
        os.path.join(venv_dir, "Scripts", "python.exe"),
        os.path.join(venv_dir, "bin", "python"),
    ]

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    return candidates[0] if os.name == "nt" else candidates[1]

VENV_PYTHON = get_venv_python()
# ---- Default settings ----
DEFAULT_SETTINGS = {
    "csv_path": "",
    "betaal_link": "",
    "text": "",
    "email_subject": "",
    "eigen_email": "",
    "include_negative_transactions": False,
    "include_r_recipients": False,
    "r_as_savings": False,
    "selected_recipients": [],
    "smtp_sender": "",
    "smtp_password": "",
    "signature_greeting": "Met Stormende groet,",
    "signature_name": "",
    "signature_role": "Quaegé der Demosdispuut Adregé",
    "signature_phone": "",
    "signature_email": "quaege@adrege.nl",
    "signature_bank_account": "NL02 SNSB 8846 2041 82",
    "signature_account_holder": "",
}

# ---- Load / Save JSON helper ----
def load_settings():
    ensure_directories()
    ensure_user_config(Path(BASE_DIR) / "config.py")
    if not os.path.exists(SETTINGS_JSON):
        return DEFAULT_SETTINGS.copy()
    with open(SETTINGS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    for k in DEFAULT_SETTINGS:
        data.setdefault(k, DEFAULT_SETTINGS[k])
    return data

def save_settings(data):
    ensure_directories()
    with open(SETTINGS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ---- Update config.py helper ----
def update_config_variable(var_name, new_value):
    ensure_directories()
    if not os.path.exists(CONFIG_PATH):
        shutil.copyfile(os.path.join(BASE_DIR, "config.py"), CONFIG_PATH)

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = rf'^{var_name}\s*=\s*["\'].*?["\']'
    replacement = f'{var_name} = {new_value!r}'

    if re.search(pattern, content, flags=re.MULTILINE):
        new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    else:
        new_content = content.strip() + f'\n{replacement}\n'

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    return True

# ---- Tool list ----
TOOLS = [
    {"name": " Split boekhouding in verschillende html bestanden", "script": "split_rekeningen.py", "needs_file": True, "needs_text": False},
    {"name": "Converteer betaalafschrift naar transactietabel", "script": "generate_transactions.py", "needs_file": True, "needs_text": False},
    {"name": "Stuur test e-mail naar jezelf", "script": "test_saldo_update.py", "needs_file": False, "needs_text": False},
    {"name": "Stuur Saldo update naar iedereen(ZORG ERVOOR DAT CSV GEUPDATE IS!)", "script": "Stuur_saldo_updates.py", "needs_file": False, "needs_text": False},
]

# ---- GUI ----
class ScriptRunnerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quaege Bot")
        self.root.geometry("1200x1000")
        self.root.minsize(820, 560)
        self._configure_style()

        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True)

        self.main_tab = ttk.Frame(self.tabs)
        self.settings_tab = ttk.Frame(self.tabs)
        self.recipients_tab = ttk.Frame(self.tabs)

        self.tabs.add(self.main_tab, text="Scripts")
        self.tabs.add(self.settings_tab, text="Settings")
        self.tabs.add(self.recipients_tab, text="Recipients")

        self.settings = load_settings()
        self.create_main_tab()
        self.create_settings_tab()
        self.create_recipients_tab()
        self.refresh_recipients()

    def _configure_style(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("TkDefaultFont", 18, "bold"))
        style.configure("Subtitle.TLabel", foreground="#5f6b7a")
        style.configure("Accent.TButton", padding=(12, 7))
        try:
            icon_path = Path(BASE_DIR) / "Adrege_logo.png"
            self.window_icon = tk.PhotoImage(file=str(icon_path))
            self.root.iconphoto(True, self.window_icon)
        except tk.TclError:
            self.window_icon = None

    # --- Main Tab ---
    def create_main_tab(self):
        ttk.Label(self.main_tab, text="Quaege Bot", style="Title.TLabel").pack(pady=(18, 2))
        ttk.Label(
            self.main_tab,
            text="Automatiseer boekhouding, saldo-overzichten en communicatie.",
            style="Subtitle.TLabel",
        ).pack(pady=(0, 14))

        for tool in TOOLS:
            frame = ttk.LabelFrame(self.main_tab, text=tool["name"], padding=10)
            frame.pack(fill="x", padx=18, pady=5)

            tool["file_var"] = tk.StringVar()
            tool["text_var"] = tk.StringVar()

            if tool["needs_file"]:
                ttk.Button(frame, text="Bestand kiezen", command=lambda t=tool: self.select_file(t)).pack(side="left", padx=5)
                ttk.Label(frame, textvariable=tool["file_var"], width=20, anchor="w").pack(side="left", padx=5)

            if tool["needs_text"]:
                ttk.Entry(frame, textvariable=tool["text_var"], width=30).pack(side="left", padx=5)

            if tool["script"] == "generate_transactions.py":
                tool["negative_var"] = tk.BooleanVar(
                    value=self.settings.get("include_negative_transactions", False)
                )
                ttk.Checkbutton(
                    frame,
                    text="Ook negatieve ('Af') transacties",
                    variable=tool["negative_var"],
                ).pack(side="left", padx=12)
                tool["r_savings_var"] = tk.BooleanVar(
                    value=self.settings.get("r_as_savings", False)
                )
                ttk.Checkbutton(
                    frame,
                    text="Inkomend van R als sparen",
                    variable=tool["r_savings_var"],
                ).pack(side="left", padx=12)

            ttk.Button(frame, text="Uitvoeren", style="Accent.TButton",
                       command=lambda t=tool: self.run_script(t)).pack(side="right", padx=5)

        # Log box
        ttk.Label(self.main_tab, text="Uitvoerlog").pack(pady=(12, 0))
        self.log_box = scrolledtext.ScrolledText(self.main_tab, wrap=tk.WORD, height=10)
        self.log_box.pack(fill="both", expand=True, padx=10, pady=5)

        ttk.Label(self.main_tab, text="Gemaakt met liefde voor de Quaege", style="Subtitle.TLabel").pack(pady=10)

    def select_file(self, tool):
        filename = self.native_file_selector(
            title="Bestand kiezen",
            filetypes="*.pdf *.csv *.html" if tool["script"] != "generate_transactions.py"
            else "*.pdf *.csv",
        )
        if filename:
            tool["file_var"].set(filename)

    def native_file_selector(self, title, filetypes):
        """Use Fedora's GTK/KDE chooser when available, with Tk as fallback."""
        for command in (("zenity", "--file-selection", f"--title={title}",
                         f"--file-filter=Bestanden | {filetypes}"),
                        ("kdialog", "--getopenfilename", str(Path.home()),
                         f"*.{{{filetypes.replace(' ', ',')}}}")):
            if not shutil.which(command[0]):
                continue
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            return ""
        return filedialog.askopenfilename(title=title)

    def get_script_runner(self):
        if getattr(sys, 'frozen', False):
            return None

        if os.path.exists(VENV_PYTHON):
            return VENV_PYTHON

        return sys.executable

    def run_script(self, tool):
        # When frozen, call the .exe; when running from source, call Python script
        if getattr(sys, 'frozen', False):
            script_name = tool["script"].replace(".py", "")
            candidates = [
                os.path.join(BASE_DIR, f"{script_name}.exe"),
                os.path.join(BASE_DIR, script_name),
                os.path.join(BASE_DIR, script_name, script_name),
            ]
            script_exe = next((path for path in candidates if os.path.exists(path)), None)
            if not script_exe:
                messagebox.showerror(
                    "Error",
                    "Executable not found. Expected one of:\n" + "\n".join(candidates),
                )
                return
            args = [script_exe]
        else:
            # Running from source
            script_path = os.path.join(SCRIPTS_DIR, tool["script"])
            if not os.path.exists(script_path):
                messagebox.showerror("Error", f"Script not found:\n{script_path}")
                return
            args = [self.get_script_runner(), script_path]
        
        if tool["needs_file"]:
            file_path = tool["file_var"].get()
            if not file_path:
                messagebox.showwarning("Missing file", "Please select a file.")
                return
            args.append(file_path)
        if tool["needs_text"]:
            text_input = tool["text_var"].get()
            args.append(text_input)
        if tool["script"] == "generate_transactions.py" and tool["negative_var"].get():
            args.append("--include-negative")
        if tool["script"] == "generate_transactions.py" and tool["r_savings_var"].get():
            args.append("--r-as-savings")

        try:
            environment = os.environ.copy()
            environment["QUAEGE_EXPORT_DIR"] = str(EXPORT_DIR)
            environment["QUAEGE_CONFIG_DIR"] = str(USER_CONFIG_PATH.parent)
            # If this is a mail script, run a dry-run first and ask for confirmation
            is_test_mail = tool["script"] == "test_saldo_update.py"
            is_bulk_mail = tool["script"] == "Stuur_saldo_updates.py"
            preview_output = ""
            
            if is_test_mail or is_bulk_mail:
                dry_run_args = args + ["--dry-run"]
                # Set cwd to BASE_DIR so scripts find resources
                try:
                    preview = subprocess.run(
                        dry_run_args, capture_output=True, text=True,
                        cwd=BASE_DIR, env=environment, timeout=60,
                    )
                except subprocess.TimeoutExpired:
                    messagebox.showerror(
                        "Dry-run mislukt",
                        "De voorbeeldberekening duurde langer dan 60 seconden.",
                    )
                    return
                preview_output = (preview.stdout or "").strip()
                preview_error = (preview.stderr or "").strip()
                # Show preview in log
                self.log_box.insert(tk.END, f"\n> Voorbeeld (dry-run)\n{preview_output or '(no output)'}\n", "output")
                if preview_error:
                    self.log_box.insert(tk.END, f"⚠️ Error (dry-run):\n{preview_error}\n", "error")
                self.log_box.see(tk.END)

                # Ask for confirmation
                if is_test_mail:
                    confirm_msg = "Wil je deze test e-mail nu echt verzenden?\n(Je hebt zojuist de dry-run gezien in de log)"
                else:
                    confirm_msg = "Wil je nu echt e-mails sturen naar ALLE leden met status S?\n(Check de dry-run lijst in de log!)"
                
                proceed = messagebox.askyesno(
                    "Bevestig verzenden",
                    confirm_msg,
                )
                if not proceed:
                    self.log_box.insert(tk.END, "\nVerzenden geannuleerd door gebruiker.\n", "output")
                    self.log_box.see(tk.END)
                    return

            # Run the actual script
            process_timeout = 300 if is_bulk_mail else 120
            try:
                result = subprocess.run(
                    args, capture_output=True, text=True, cwd=BASE_DIR,
                    env=environment, timeout=process_timeout,
                )
            except subprocess.TimeoutExpired as timeout_error:
                message = (
                    f"Het uitvoeren duurde langer dan {process_timeout} seconden "
                    "en is afgebroken. De laatste uitvoer:"
                )
                partial_output = timeout_error.stdout or ""
                partial_error = timeout_error.stderr or ""
                if isinstance(partial_output, bytes):
                    partial_output = partial_output.decode(errors="replace")
                if isinstance(partial_error, bytes):
                    partial_error = partial_error.decode(errors="replace")
                self.log_box.insert(tk.END, f"\n⚠️ Timeout:\n{message}\n", "error")
                if partial_output:
                    self.log_box.insert(tk.END, f"{partial_output}\n", "output")
                if partial_error:
                    self.log_box.insert(tk.END, f"⚠️ Foutuitvoer:\n{partial_error}\n", "error")
                self.log_box.see(tk.END)
                messagebox.showerror(
                    "Uitvoering afgebroken",
                    f"{message}\nZie de uitvoerlog voor de exacte SMTP/IMAP-stap.",
                )
                return
            output = result.stdout.strip() or "(no output)"
            error = result.stderr.strip()
            self.log_box.insert(tk.END, f"\n> {tool['name']} executed\n{output}\n", "output")
            if error:
                self.log_box.insert(tk.END, f"⚠️ Error:\n{error}\n", "error")
            self.log_box.see(tk.END)
        except Exception as e:
            messagebox.showerror("Execution failed", str(e))

    # --- Settings Tab ---
    def create_settings_tab(self):
        self.settings = load_settings()

        frm = ttk.Frame(self.settings_tab)
        frm.pack(fill="both", expand=True, padx=20, pady=20)
        frm.columnconfigure(1, weight=1)

        # CSV File
        ttk.Label(frm, text="Pad naar CSV van de ledenadministratie:").grid(row=0, column=0, sticky="w")
        self.csv_var = tk.StringVar(value=self.settings["csv_path"])
        csv_entry = ttk.Entry(frm, textvariable=self.csv_var, width=55, state="readonly")
        csv_entry.grid(row=0, column=1, pady=2, sticky="w")
        def select_csv_file():
            filename = self.native_file_selector("Selecteer ledenadministratie CSV", "*.csv")
            if filename:
                self.csv_var.set(filename)
                self.refresh_recipients()
        select_csv_btn = ttk.Button(frm, text="Selecteer CSV", command=select_csv_file)
        select_csv_btn.grid(row=0, column=2, pady=2, sticky="w")

        # Link
        ttk.Label(frm, text="Betaalverzoek-link:").grid(row=1, column=0, sticky="w", pady=5)
        self.link_var = tk.StringVar(value=self.settings["betaal_link"])
        ttk.Entry(frm, textvariable=self.link_var, width=55).grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Text
        ttk.Label(frm, text="Tekst in e-mail:").grid(row=2, column=0, sticky="nw")
        self.text_box = tk.Text(frm, width=45, height=5)
        self.text_box.insert("1.0", self.settings["text"])
        self.text_box.grid(row=2, column=1, padx=5, pady=5)

        # Email Subject
        ttk.Label(frm, text="E-mailonderwerp:").grid(row=3, column=0, sticky="w", pady=5)
        self.subject_var = tk.StringVar(value=self.settings.get("email_subject", ""))
        ttk.Entry(frm, textvariable=self.subject_var, width=55).grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(frm, text="Groet in e-mailhandtekening:").grid(row=4, column=0, sticky="w", pady=5)
        self.signature_greeting_var = tk.StringVar(
            value=self.settings.get("signature_greeting", "Met Stormende groet,")
        )
        ttk.Entry(frm, textvariable=self.signature_greeting_var, width=55).grid(
            row=4, column=1, padx=5, pady=5, sticky="ew"
        )

        ttk.Label(frm, text="Naam van de Quaege:").grid(row=5, column=0, sticky="w", pady=5)
        self.signature_name_var = tk.StringVar(value=self.settings.get("signature_name", ""))
        ttk.Entry(frm, textvariable=self.signature_name_var, width=55).grid(
            row=5, column=1, padx=5, pady=5, sticky="ew"
        )

        ttk.Label(frm, text="Functie/omschrijving:").grid(row=6, column=0, sticky="w", pady=5)
        self.signature_role_var = tk.StringVar(
            value=self.settings.get("signature_role", "Quaegé der Demosdispuut Adregé")
        )
        ttk.Entry(frm, textvariable=self.signature_role_var, width=55).grid(
            row=6, column=1, padx=5, pady=5, sticky="ew"
        )

        ttk.Label(frm, text="Telefoonnummer in handtekening:").grid(row=7, column=0, sticky="w", pady=5)
        self.signature_phone_var = tk.StringVar(value=self.settings.get("signature_phone", ""))
        ttk.Entry(frm, textvariable=self.signature_phone_var, width=55).grid(
            row=7, column=1, padx=5, pady=5, sticky="ew"
        )

        ttk.Label(frm, text="E-mailadres in handtekening:").grid(row=8, column=0, sticky="w", pady=5)
        self.signature_email_var = tk.StringVar(
            value=self.settings.get("signature_email", "quaege@adrege.nl")
        )
        ttk.Entry(frm, textvariable=self.signature_email_var, width=55).grid(
            row=8, column=1, padx=5, pady=5, sticky="ew"
        )

        ttk.Label(frm, text="Bankrekeningnummer:").grid(row=9, column=0, sticky="w", pady=5)
        self.signature_bank_account_var = tk.StringVar(
            value=self.settings.get("signature_bank_account", "NL02 SNSB 8846 2041 82")
        )
        ttk.Entry(frm, textvariable=self.signature_bank_account_var, width=55).grid(
            row=9, column=1, padx=5, pady=5, sticky="ew"
        )

        ttk.Label(frm, text="Ten name van:").grid(row=10, column=0, sticky="w", pady=5)
        self.signature_account_holder_var = tk.StringVar(
            value=self.settings.get("signature_account_holder", "")
        )
        ttk.Entry(frm, textvariable=self.signature_account_holder_var, width=55).grid(
            row=10, column=1, padx=5, pady=5, sticky="ew"
        )

        # test email
        ttk.Label(frm, text="Eigen Adrege-e-mailadres (voor testmail):").grid(row=11, column=0, sticky="w", pady=5)
        self.email_var = tk.StringVar(value=self.settings.get("eigen_email", ""))
        ttk.Entry(frm, textvariable=self.email_var, width=55).grid(row=11, column=1, padx=5, pady=5, sticky="ew")

        self.include_r_var = tk.BooleanVar(value=self.settings.get("include_r_recipients", False))
        ttk.Checkbutton(
            frm, text="Status R meenemen als er geen handmatige selectie is",
            variable=self.include_r_var,
        ).grid(row=12, column=1, sticky="w", padx=5, pady=8)

        ttk.Label(frm, text="SMTP-gebruikersnaam:").grid(row=13, column=0, sticky="w", pady=5)
        self.smtp_sender_var = tk.StringVar(value=self.settings.get("smtp_sender", ""))
        ttk.Entry(frm, textvariable=self.smtp_sender_var, width=55).grid(
            row=13, column=1, padx=5, pady=5, sticky="ew"
        )
        ttk.Label(frm, text="SMTP-wachtwoord:").grid(row=14, column=0, sticky="w", pady=5)
        self.smtp_password_var = tk.StringVar(value=self.settings.get("smtp_password", ""))
        ttk.Entry(frm, textvariable=self.smtp_password_var, show="*", width=55).grid(
            row=14, column=1, padx=5, pady=5, sticky="ew"
        )
        ttk.Label(
            frm,
            text=f"Bestanden: {EXPORT_DIR}\nConfiguratie: {USER_CONFIG_PATH}",
            style="Subtitle.TLabel",
        ).grid(row=15, column=1, sticky="w", padx=5, pady=8)
        ttk.Button(frm, text="Open exportmap", command=lambda: self.open_path(EXPORT_DIR)).grid(
            row=15, column=2, sticky="w"
        )
        ttk.Button(frm, text="Open configuratiemap",
                   command=lambda: self.open_path(USER_CONFIG_PATH.parent)).grid(
            row=16, column=2, sticky="w"
        )

        save_btn = ttk.Button(frm, text="Instellingen opslaan", style="Accent.TButton",
                              command=self.save_all_settings)
        save_btn.grid(row=17, column=0, pady=15, sticky="e")

    # --- Recipients Tab ---
    def create_recipients_tab(self):
        container = ttk.Frame(self.recipients_tab, padding=18)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(2, weight=1)

        ttk.Label(container, text="Ontvangers saldo-update", style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            container,
            text="Selecteer meerdere personen. Zonder handmatige selectie worden status S (en optioneel R) gebruikt.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 10))

        table_frame = ttk.Frame(container)
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        self.recipient_canvas = tk.Canvas(table_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical",
                                  command=self.recipient_canvas.yview)
        self.recipient_list = ttk.Frame(self.recipient_canvas)
        self.recipient_window = self.recipient_canvas.create_window(
            (0, 0), window=self.recipient_list, anchor="nw"
        )
        self.recipient_list.bind(
            "<Configure>",
            lambda _event: self.recipient_canvas.configure(
                scrollregion=self.recipient_canvas.bbox("all")
            ),
        )
        self.recipient_canvas.bind(
            "<Configure>",
            lambda event: self.recipient_canvas.itemconfigure(
                self.recipient_window, width=event.width
            ),
        )
        self.recipient_canvas.configure(yscrollcommand=scrollbar.set)
        self.recipient_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        buttons = ttk.Frame(container)
        buttons.grid(row=3, column=0, sticky="w", pady=(12, 0))
        ttk.Button(buttons, text="Selecteer alle status S",
                   command=self.select_s_recipients).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Selecteer iedereen",
                   command=self.select_all_recipients).pack(side="left", padx=6)
        ttk.Button(buttons, text="Wis handmatige selectie",
                   command=self.clear_recipient_selection).pack(side="left", padx=6)
        ttk.Button(buttons, text="Selectie opslaan", style="Accent.TButton",
                   command=self.save_recipient_selection).pack(side="left", padx=6)

        self.recipient_status = tk.StringVar()
        ttk.Label(container, textvariable=self.recipient_status,
                  style="Subtitle.TLabel").grid(row=4, column=0, sticky="w", pady=8)

    def refresh_recipients(self):
        if not hasattr(self, "recipient_list"):
            return
        for child in self.recipient_list.winfo_children():
            child.destroy()
        self.recipient_vars = {}
        csv_path = self.csv_var.get().strip() if hasattr(self, "csv_var") else self.settings.get("csv_path", "")
        if not csv_path or not os.path.exists(csv_path):
            self.recipient_status.set("Selecteer eerst een geldige ledenadministratie-CSV in Settings.")
            return
        try:
            with open(csv_path, newline="", encoding="utf-8-sig") as file:
                for row in csv.DictReader(file):
                    number = row.get("#", "").strip()
                    email = row.get("Emailadres", "").strip()
                    first_name = row.get("Voornaam", "").strip()
                    last_name = row.get("Achternaam", "").strip()
                    status = row.get("Banana status", "").strip()
                    if email:
                        selected = (
                            email.lower() in {
                                str(value).lower()
                                for value in self.settings.get("selected_recipients", [])
                            }
                            or number.lower() in {
                                str(value).lower()
                                for value in self.settings.get("selected_recipients", [])
                            }
                        )
                        variable = tk.BooleanVar(value=selected)
                        self.recipient_vars[email.lower()] = (variable, number, email, status)
                        ttk.Checkbutton(
                            self.recipient_list,
                            text=f"{first_name} {last_name}  |  {email}  |  status {status}  |  #{number}",
                            variable=variable,
                        ).pack(anchor="w", fill="x", padx=8, pady=2)
        except (OSError, csv.Error) as error:
            self.recipient_status.set(f"CSV kon niet worden gelezen: {error}")
            return

        self.update_recipient_status()

    def select_s_recipients(self):
        for variable, _number, _email, _status in self.recipient_vars.values():
            variable.set(False)
        for variable, _number, _address, status in self.recipient_vars.values():
            if status.upper().startswith("S"):
                variable.set(True)
        self.update_recipient_status()

    def select_all_recipients(self):
        for variable, _number, _email, _status in self.recipient_vars.values():
            variable.set(True)
        self.update_recipient_status()

    def clear_recipient_selection(self):
        for variable, _number, _email, _status in self.recipient_vars.values():
            variable.set(False)
        self.update_recipient_status()

    def update_recipient_status(self):
        count = sum(variable.get() for variable, _number, _email, _status in self.recipient_vars.values())
        self.recipient_status.set(
            f"{count} handmatige ontvanger(s) geselecteerd. "
            "Een lege selectie gebruikt de statusinstellingen."
        )

    def save_recipient_selection(self):
        self.settings["selected_recipients"] = [
            number or email
            for variable, number, email, _status in self.recipient_vars.values()
            if variable.get()
        ]
        save_settings(self.settings)
        self.update_recipient_status()
        messagebox.showinfo("Opgeslagen", "De ontvangerselectie is opgeslagen.")

    def browse_csv(self):
        filename = self.native_file_selector("Selecteer ledenadministratie CSV", "*.csv")
        if filename:
            self.csv_var.set(filename)

    def open_path(self, path):
        ensure_directories()
        path = str(path)
        try:
            if sys.platform.startswith("linux"):
                subprocess.Popen(["xdg-open", path])
            elif os.name == "nt":
                os.startfile(path)
            else:
                subprocess.Popen(["open", path])
        except OSError as error:
            messagebox.showerror("Openen mislukt", str(error))

    def save_all_settings(self):
        new_csv = self.csv_var.get().strip()
        new_link = self.link_var.get().strip()
        new_text = self.text_box.get("1.0", "end").strip()
        new_subject = self.subject_var.get().strip()
        new_email = self.email_var.get().strip()
        new_signature_greeting = self.signature_greeting_var.get().strip()
        new_signature_name = self.signature_name_var.get().strip()
        new_signature_role = self.signature_role_var.get().strip()
        new_signature_phone = self.signature_phone_var.get().strip()
        new_signature_email = self.signature_email_var.get().strip()
        new_signature_bank_account = self.signature_bank_account_var.get().strip()
        new_signature_account_holder = self.signature_account_holder_var.get().strip()

        self.settings["csv_path"] = new_csv
        self.settings["betaal_link"] = new_link
        self.settings["text"] = new_text
        self.settings["email_subject"] = new_subject
        self.settings["eigen_email"] = new_email
        self.settings["signature_greeting"] = new_signature_greeting
        self.settings["signature_name"] = new_signature_name
        self.settings["signature_role"] = new_signature_role
        self.settings["signature_phone"] = new_signature_phone
        self.settings["signature_email"] = new_signature_email
        self.settings["signature_bank_account"] = new_signature_bank_account
        self.settings["signature_account_holder"] = new_signature_account_holder
        self.settings["include_r_recipients"] = self.include_r_var.get()
        self.settings["smtp_sender"] = self.smtp_sender_var.get().strip()
        self.settings["smtp_password"] = self.smtp_password_var.get()
        transaction_tool = next(
            (tool for tool in TOOLS if tool["script"] == "generate_transactions.py"),
            None,
        )
        if transaction_tool:
            self.settings["include_negative_transactions"] = transaction_tool["negative_var"].get()
            self.settings["r_as_savings"] = transaction_tool["r_savings_var"].get()
        if hasattr(self, "recipient_vars"):
            self.settings["selected_recipients"] = [
                number or email
                for variable, number, email, _status in self.recipient_vars.values()
                if variable.get()
            ]

        save_settings(self.settings)
        update_config_variable("CSV_PAD", new_csv)
        update_config_variable("BETAAL_LINK", new_link)
        update_config_variable("TEXT_NOTE", new_text)
        update_config_variable("EMAIL_SUBJECT", new_subject)
        update_config_variable("test_email", new_email)
        update_config_variable("SIGNATURE_GREETING", new_signature_greeting)
        update_config_variable("SIGNATURE_NAME", new_signature_name)
        update_config_variable("SIGNATURE_ROLE", new_signature_role)
        update_config_variable("SIGNATURE_PHONE", new_signature_phone)
        update_config_variable("SIGNATURE_EMAIL", new_signature_email)
        update_config_variable("SIGNATURE_BANK_ACCOUNT", new_signature_bank_account)
        update_config_variable("SIGNATURE_ACCOUNT_HOLDER", new_signature_account_holder)
        update_config_variable("sender_email", self.settings["smtp_sender"])
        update_config_variable("password", self.settings["smtp_password"])
        self.refresh_recipients()

        messagebox.showinfo("Saved", "Settings updated successfully!")

# ---- Run ----
if __name__ == "__main__":
    root = tk.Tk()
    app = ScriptRunnerApp(root)
    root.mainloop()
