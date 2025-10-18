import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import subprocess
import sys
import os
import json
import re

# ---- Paths ----
BASE_DIR = os.path.dirname(__file__)
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
CONFIG_PATH = os.path.join(BASE_DIR, "config.py")
SETTINGS_JSON = os.path.join(BASE_DIR, "settings.json")

# ---- Default settings ----
DEFAULT_SETTINGS = {
    "csv_path": "",
    "betaal_link": "",
    "text": "",
    "eigen_email": ""
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
    {"name": "converteer betaalafscrift naar spaar tabel", "script": "generate_transactions.py", "needs_file": True, "needs_text": False},
    {"name": "Stuur test e-mail naar jezelf", "script": "test_saldo_update.py", "needs_file": False, "needs_text": False},
    {"name": "Stuur Saldo update naar iedereen(ZORG ERVOOR DAT CSV GEUPDATE IS!)", "script": "Stuur_saldo_updates.py", "needs_file": False, "needs_text": False},
]

# ---- GUI ----
class ScriptRunnerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("My Python Tools")
        self.root.geometry("800x520")

        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True)

        self.main_tab = ttk.Frame(self.tabs)
        self.settings_tab = ttk.Frame(self.tabs)

        self.tabs.add(self.main_tab, text="Scripts")
        self.tabs.add(self.settings_tab, text="Settings")

        self.create_main_tab()
        self.create_settings_tab()

    # --- Main Tab ---
    def create_main_tab(self):
        tk.Label(self.main_tab, text="Quaege Python Tools", font=("Arial", 14, "bold")).pack(pady=10)

        for tool in TOOLS:
            frame = tk.LabelFrame(self.main_tab, text=tool["name"], padx=10, pady=5)
            frame.pack(fill="x", padx=10, pady=5)

            tool["file_var"] = tk.StringVar()
            tool["text_var"] = tk.StringVar()

            if tool["needs_file"]:
                tk.Button(frame, text="Browse File", command=lambda t=tool: self.select_file(t)).pack(side="left", padx=5)
                tk.Label(frame, textvariable=tool["file_var"], width=40, anchor="w").pack(side="left", padx=5)

            if tool["needs_text"]:
                tk.Entry(frame, textvariable=tool["text_var"], width=30).pack(side="left", padx=5)

            tk.Button(frame, text="Run", command=lambda t=tool: self.run_script(t)).pack(side="right", padx=5)

        # Log box
        tk.Label(self.main_tab, text="Output log:").pack(pady=(10, 0))
        self.log_box = scrolledtext.ScrolledText(self.main_tab, wrap=tk.WORD, height=10)
        self.log_box.pack(fill="both", expand=True, padx=10, pady=5)

        tk.Label(self.main_tab, text="Gemaakt met liefde 45 :)", font=("Arial", 8)).pack(pady=10)

    def select_file(self, tool):
        filename = filedialog.askopenfilename(title="Select File")
        if filename:
            tool["file_var"].set(filename)

    def run_script(self, tool):
        script_path = os.path.join(SCRIPTS_DIR, tool["script"])
        if not os.path.exists(script_path):
            messagebox.showerror("Error", f"Script not found:\n{script_path}")
            return

        args = [sys.executable, script_path]
        if tool["needs_file"]:
            file_path = tool["file_var"].get()
            if not file_path:
                messagebox.showwarning("Missing file", "Please select a file.")
                return
            args.append(file_path)
        if tool["needs_text"]:
            text_input = tool["text_var"].get()
            args.append(text_input)

        try:
            # If this is a mail script, run a dry-run first and ask for confirmation
            is_test_mail = tool["script"] == "test_saldo_update.py"
            is_bulk_mail = tool["script"] == "Stuur_saldo_updates.py"
            preview_output = ""
            
            if is_test_mail or is_bulk_mail:
                dry_run_args = args + ["--dry-run"]
                preview = subprocess.run(dry_run_args, capture_output=True, text=True)
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
            result = subprocess.run(args, capture_output=True, text=True)
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

        frm = tk.Frame(self.settings_tab)
        frm.pack(fill="both", expand=True, padx=20, pady=20)

        # CSV File
        tk.Label(frm, text="pad naar CSV van de ledenadministratie:").grid(row=0, column=0, sticky="w")
        self.csv_var = tk.StringVar(value=self.settings["csv_path"])
        csv_entry = tk.Entry(frm, textvariable=self.csv_var, width=45, state="readonly")
        csv_entry.grid(row=0, column=1, pady=2, sticky="w")
        def select_csv_file():
            filename = filedialog.askopenfilename(title="Selecteer leden CSV", filetypes=[("CSV Files", "*.csv")])
            if filename:
                self.csv_var.set(filename)
        select_csv_btn = tk.Button(frm, text="Selecteer CSV", command=select_csv_file)
        select_csv_btn.grid(row=0, column=2, pady=2, sticky="w")

        # Link
        tk.Label(frm, text="betaalverzoek Link (word opgeslagen in config.py):").grid(row=1, column=0, sticky="w", pady=5)
        self.link_var = tk.StringVar(value=self.settings["betaal_link"])
        tk.Entry(frm, textvariable=self.link_var, width=45).grid(row=1, column=1, padx=5, pady=5)

        # Text
        tk.Label(frm, text="Text (stored in config.py):").grid(row=2, column=0, sticky="nw")
        self.text_box = tk.Text(frm, width=45, height=5)
        self.text_box.insert("1.0", self.settings["text"])
        self.text_box.grid(row=2, column=1, padx=5, pady=5)

        #test email
        tk.Label(frm, text="Je eigen Adrege e-mailadres (voor test e-mail):").grid(row=3, column=0, sticky="w", pady=5)
        self.email_var = tk.StringVar(value=self.settings.get("eigen_email", ""))
        tk.Entry(frm, textvariable=self.email_var, width=45).grid(row=3, column=1, padx=5, pady=5)

        # Save button
        save_btn = tk.Button(frm, text="💾 Save Settings", command=self.save_all_settings)
        save_btn.grid(row=6, column=0, pady=15, sticky="e")

    def browse_csv(self):
        filename = filedialog.askopenfilename(title="Select CSV file", filetypes=[("CSV Files", "*.csv")])
        if filename:
            self.csv_var.set(filename)

    def save_all_settings(self):
        new_csv = self.csv_var.get().strip()
        new_link = self.link_var.get().strip()
        new_text = self.text_box.get("1.0", "end").strip()
        new_email = self.email_var.get().strip()

        self.settings["csv_path"] = new_csv
        self.settings["betaal_link"] = new_link
        self.settings["text"] = new_text
        self.settings["eigen_email"] = new_email

        save_settings(self.settings)
        update_config_variable("CSV_PAD", new_csv)
        update_config_variable("BETAAL_LINK", new_link)
        update_config_variable("TEXT_NOTE", new_text)
        update_config_variable("test_email", new_email)

        messagebox.showinfo("Saved", "Settings updated successfully!")

# ---- Run ----
if __name__ == "__main__":
    root = tk.Tk()
    app = ScriptRunnerApp(root)
    root.mainloop()
