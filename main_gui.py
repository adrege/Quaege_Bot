import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import subprocess
import sys
import os
import json
import re
import csv

# ---- Paths ----
# When frozen with PyInstaller, use the executable's directory
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(__file__)

SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
CONFIG_PATH = os.path.join(BASE_DIR, "config.py")
SETTINGS_JSON = os.path.join(BASE_DIR, "settings.json")

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
    "selected_recipients": []
}

# ---- Load / Save JSON helper ----
def load_settings():
    if not os.path.exists(SETTINGS_JSON):
        return DEFAULT_SETTINGS.copy()
    with open(SETTINGS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    for k in DEFAULT_SETTINGS:
        data.setdefault(k, DEFAULT_SETTINGS[k])
    return data

def save_settings(data):
    with open(SETTINGS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

# ---- Update config.py helper ----
def update_config_variable(var_name, new_value):
    if not os.path.exists(CONFIG_PATH):
        messagebox.showerror("Error", f"config.py not found: {CONFIG_PATH}")
        return False

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = rf'^{var_name}\s*=\s*["\'].*?["\']'
    replacement = f'{var_name} = "{new_value}"'

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
        self.root.geometry("980x680")
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
                ttk.Label(frame, textvariable=tool["file_var"], width=52, anchor="w").pack(side="left", padx=5)

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

            ttk.Button(frame, text="Uitvoeren", style="Accent.TButton",
                       command=lambda t=tool: self.run_script(t)).pack(side="right", padx=5)

        # Log box
        ttk.Label(self.main_tab, text="Uitvoerlog").pack(pady=(12, 0))
        self.log_box = scrolledtext.ScrolledText(self.main_tab, wrap=tk.WORD, height=10)
        self.log_box.pack(fill="both", expand=True, padx=10, pady=5)

        ttk.Label(self.main_tab, text="Gemaakt met liefde voor de Quaege", style="Subtitle.TLabel").pack(pady=10)

    def select_file(self, tool):
        filename = filedialog.askopenfilename(title="Select File")
        if filename:
            tool["file_var"].set(filename)

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

        try:
            # If this is a mail script, run a dry-run first and ask for confirmation
            is_test_mail = tool["script"] == "test_saldo_update.py"
            is_bulk_mail = tool["script"] == "Stuur_saldo_updates.py"
            preview_output = ""
            
            if is_test_mail or is_bulk_mail:
                dry_run_args = args + ["--dry-run"]
                # Set cwd to BASE_DIR so scripts find resources
                preview = subprocess.run(dry_run_args, capture_output=True, text=True, cwd=BASE_DIR)
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
            result = subprocess.run(args, capture_output=True, text=True, cwd=BASE_DIR)
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
            filename = filedialog.askopenfilename(title="Selecteer leden CSV", filetypes=[("CSV Files", "*.csv")])
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

        #test email
        ttk.Label(frm, text="Eigen Adrege-e-mailadres (voor testmail):").grid(row=4, column=0, sticky="w", pady=5)
        self.email_var = tk.StringVar(value=self.settings.get("eigen_email", ""))
        ttk.Entry(frm, textvariable=self.email_var, width=55).grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        self.include_r_var = tk.BooleanVar(value=self.settings.get("include_r_recipients", False))
        ttk.Checkbutton(
            frm, text="Status R meenemen als er geen handmatige selectie is",
            variable=self.include_r_var,
        ).grid(row=5, column=1, sticky="w", padx=5, pady=8)

        # Save button
        save_btn = ttk.Button(frm, text="Instellingen opslaan", style="Accent.TButton",
                              command=self.save_all_settings)
        save_btn.grid(row=6, column=0, pady=15, sticky="e")

    # --- Recipients Tab ---
    def create_recipients_tab(self):
        container = ttk.Frame(self.recipients_tab, padding=18)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        ttk.Label(container, text="Ontvangers saldo-update", style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            container,
            text="Selecteer meerdere personen. Zonder handmatige selectie worden status S (en optioneel R) gebruikt.",
            style="Subtitle.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(34, 10))

        table_frame = ttk.Frame(container)
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        self.recipient_tree = ttk.Treeview(
            table_frame,
            columns=("name", "email", "status", "number"),
            show="headings",
            selectmode="extended",
        )
        self.recipient_tree.bind("<<TreeviewSelect>>", lambda _event: self.update_recipient_status())
        for column, heading, width in (
            ("name", "Naam", 220),
            ("email", "E-mailadres", 300),
            ("status", "Status", 90),
            ("number", "Nummer", 100),
        ):
            self.recipient_tree.heading(column, text=heading)
            self.recipient_tree.column(column, width=width, anchor="w")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical",
                                  command=self.recipient_tree.yview)
        self.recipient_tree.configure(yscrollcommand=scrollbar.set)
        self.recipient_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        buttons = ttk.Frame(container)
        buttons.grid(row=2, column=0, sticky="w", pady=(12, 0))
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
                  style="Subtitle.TLabel").grid(row=3, column=0, sticky="w", pady=8)

    def refresh_recipients(self):
        if not hasattr(self, "recipient_tree"):
            return
        self.recipient_tree.delete(*self.recipient_tree.get_children())
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
                        self.recipient_tree.insert(
                            "", "end", iid=email.lower(),
                            values=(f"{first_name} {last_name}".strip(), email, status, number)
                        )
        except (OSError, csv.Error) as error:
            self.recipient_status.set(f"CSV kon niet worden gelezen: {error}")
            return

        selected = {str(value).lower() for value in self.settings.get("selected_recipients", [])}
        for item in self.recipient_tree.get_children():
            values = self.recipient_tree.item(item, "values")
            if item.lower() in selected or str(values[3]).lower() in selected:
                self.recipient_tree.selection_add(item)
        self.update_recipient_status()

    def select_s_recipients(self):
        self.clear_recipient_selection()
        items = [
            item for item in self.recipient_tree.get_children()
            if str(self.recipient_tree.item(item, "values")[2]).upper().startswith("S")
        ]
        self.recipient_tree.selection_set(items)
        self.update_recipient_status()

    def select_all_recipients(self):
        self.recipient_tree.selection_set(self.recipient_tree.get_children())
        self.update_recipient_status()

    def clear_recipient_selection(self):
        self.recipient_tree.selection_remove(self.recipient_tree.selection())
        self.update_recipient_status()

    def update_recipient_status(self):
        count = len(self.recipient_tree.selection())
        self.recipient_status.set(
            f"{count} handmatige ontvanger(s) geselecteerd. "
            "Een lege selectie gebruikt de statusinstellingen."
        )

    def save_recipient_selection(self):
        self.settings["selected_recipients"] = [
            str(self.recipient_tree.item(item, "values")[3]).strip()
            or str(self.recipient_tree.item(item, "values")[1]).strip()
            for item in self.recipient_tree.selection()
        ]
        save_settings(self.settings)
        self.update_recipient_status()
        messagebox.showinfo("Opgeslagen", "De ontvangerselectie is opgeslagen.")

    def browse_csv(self):
        filename = filedialog.askopenfilename(title="Select CSV file", filetypes=[("CSV Files", "*.csv")])
        if filename:
            self.csv_var.set(filename)

    def save_all_settings(self):
        new_csv = self.csv_var.get().strip()
        new_link = self.link_var.get().strip()
        new_text = self.text_box.get("1.0", "end").strip()
        new_subject = self.subject_var.get().strip()
        new_email = self.email_var.get().strip()

        self.settings["csv_path"] = new_csv
        self.settings["betaal_link"] = new_link
        self.settings["text"] = new_text
        self.settings["email_subject"] = new_subject
        self.settings["eigen_email"] = new_email
        self.settings["include_r_recipients"] = self.include_r_var.get()
        transaction_tool = next(
            (tool for tool in TOOLS if tool["script"] == "generate_transactions.py"),
            None,
        )
        if transaction_tool:
            self.settings["include_negative_transactions"] = transaction_tool["negative_var"].get()
        if hasattr(self, "recipient_tree"):
            self.settings["selected_recipients"] = [
                str(self.recipient_tree.item(item, "values")[3]).strip()
                or str(self.recipient_tree.item(item, "values")[1]).strip()
                for item in self.recipient_tree.selection()
            ]

        save_settings(self.settings)
        update_config_variable("CSV_PAD", new_csv)
        update_config_variable("BETAAL_LINK", new_link)
        update_config_variable("TEXT_NOTE", new_text)
        update_config_variable("EMAIL_SUBJECT", new_subject)
        update_config_variable("test_email", new_email)
        self.refresh_recipients()

        messagebox.showinfo("Saved", "Settings updated successfully!")

# ---- Run ----
if __name__ == "__main__":
    root = tk.Tk()
    app = ScriptRunnerApp(root)
    root.mainloop()
