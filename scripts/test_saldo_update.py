import csv
import os
import sys
from pathlib import Path
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib
import argparse
import imaplib
import time

# Ensure we can import the top-level config.py when running from the scripts folder or frozen
if getattr(sys, "frozen", False):
    # In PyInstaller onefile, data may live in sys._MEIPASS, but user-editable files (settings.json) should be next to the exe
    EXE_DIR = Path(os.path.dirname(sys.executable))
    MEIPASS_DIR = Path(getattr(sys, "_MEIPASS", EXE_DIR))
    BASE_DIR = EXE_DIR
else:
    EXE_DIR = Path(__file__).resolve().parent.parent
    MEIPASS_DIR = EXE_DIR
    BASE_DIR = EXE_DIR
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import config

# Use absolute paths so the script can be run from anywhere
def _resolve_html_map():
    # Prefer rekeningen_split next to the exe, else inside MEIPASS bundle
    p1 = EXE_DIR / "rekeningen_split"
    if p1.exists():
        return str(p1)
    p2 = MEIPASS_DIR / "rekeningen_split"
    return str(p2)

HTML_MAP = _resolve_html_map()
# Default CSV lives in the scripts folder (note the casing in the filename)
DEFAULT_CSV_PAD = str(Path(__file__).resolve().parent / "Ledenadministratie - Leden.csv")

def _load_settings():
    # Prefer external settings.json next to the exe (user-editable)
    for settings_path in [EXE_DIR / "settings.json", MEIPASS_DIR / "settings.json"]:
        if not settings_path.exists():
            continue
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def get_csv_path():
    """Prefer CSV path from config (CSV_PAD), else fall back to default in scripts folder."""
    settings = _load_settings()
    csv_from_config = settings.get("csv_path") or getattr(config, "CSV_PAD", None)
    if csv_from_config:
        # Expand ~ and env vars and normalize
        cfg = os.path.expandvars(os.path.expanduser(csv_from_config))
        if os.path.exists(cfg):
            print(f"CSV path from config: {cfg}")
            return cfg
        else:
            print(f"Warning: CSV path in config not found: {cfg}; falling back to default: {DEFAULT_CSV_PAD}")
    else:
        print(f"No CSV_PAD in config; using default: {DEFAULT_CSV_PAD}")
    return DEFAULT_CSV_PAD
SMTP_SERVER = 'mail.antagonist.nl'
SMTP_PORT = 465
IMAP_FOLDER = 'INBOX.Sent'

def lees_csv(pad):
    with open(pad, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def genereer_dynamische_tekst(voornaam, betaal_link):
    return f"""
        <p>Hoi lieve {voornaam},</p>
        <p>Bijgevoegd vind je jouw saldo-update van het afgelopen kwartiel.</p>
        <p>Mocht je een negatief saldo hebben, dan verzoek ik je graag om het openstaande bedrag over te maken via onderstaand betaalverzoek:</p>
        <p><a href="{betaal_link}">{betaal_link}</a></p>
        <p>En oja, check ook even je wbw-saldo! Het is fijn als de verschillen hier niet te groot zijn :)</p>
        <p>Bij vragen, let met know!</p>
    """

def stuur_mail(ontvanger_email, onderwerp, html_bericht, bijlage_pad):
    msg = MIMEMultipart('related')
    msg['Subject'] = onderwerp
    msg['From'] = config.sender_email
    msg['To'] = ontvanger_email

    msg_alt = MIMEMultipart('alternative')
    msg.attach(msg_alt)
    msg_alt.attach(MIMEText(html_bericht, 'html'))

    msg = config.attach_logo(msg)

    with open(bijlage_pad, 'rb') as f:
        attachment = MIMEApplication(f.read(), _subtype='html')
        attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(bijlage_pad))
        msg.attach(attachment)

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(config.sender_email, config.password)
            server.send_message(msg)
            print(f"Testmail verzonden naar {ontvanger_email}")

        with imaplib.IMAP4_SSL(SMTP_SERVER) as imap:
            imap.login(config.sender_email, config.password)
            imap.append(IMAP_FOLDER, '', imaplib.Time2Internaldate(time.time()), msg.as_bytes())
            print(f"Testmail opgeslagen in Verzonden map")

    except Exception as e:
        print(f"❌ Fout bij verzenden testmail: {e}")

def _get_betaal_link():
    """Resolve betaal link. Prefer config.BETAAL_LINK (GUI writes this), then config.betaal_link, else fallback."""
    settings = _load_settings()
    if settings.get("betaal_link"):
        print("betaal_link loaded from settings.json")
        return settings["betaal_link"]
    if hasattr(config, "BETAAL_LINK") and getattr(config, "BETAAL_LINK"):
        print("betaal_link loaded from config.BETAAL_LINK")
        return getattr(config, "BETAAL_LINK")
    if hasattr(config, "betaal_link") and getattr(config, "betaal_link"):
        print("betaal_link loaded from config.betaal_link")
        return getattr(config, "betaal_link")
    fallback = "https://diensten.snsbank.nl/online/betaalverzoek/#/v2/13f4b9a7-1314-4655-93f6-704f7bfcc383/9QcAQvwU8RRMuWoQtH6LjbyBCiX5FLXZ"
    print("Warning: betaal_link not set in config; using fallback default. Update config.BETAAL_LINK in settings.")
    return fallback


def _confirmed_to_send() -> bool:
    """Return True if we should send the email. In non-interactive (GUI) mode, auto-confirm."""
    try:
        if not sys.stdin or not sys.stdin.isatty():
            print("Non-interactive environment detected (likely launched from GUI); skipping confirmation and sending.")
            return True
    except Exception:
        # If checking isatty fails, be safe and proceed (GUI case)
        print("Unable to read from stdin; assuming non-interactive and sending.")
        return True

    bevestiging = input("Weet je zeker dat je deze testmail wilt verzenden? (y/N): ").strip().lower()
    return bevestiging == "y"


def main(dry_run: bool = False):
    csv_pad = get_csv_path()
    leden = lees_csv(csv_pad)
    betaal_link = _get_betaal_link()
    onderwerp = "Testmail: Adrege Saldo Update"

    settings = _load_settings()
    test_email = settings.get("eigen_email") or getattr(config, "test_email", None)
    if not test_email:
        print("Geen test_email gevonden in settings.json of config.py")
        return
    test_lid = next((lid for lid in leden if lid["Emailadres"].strip().lower() == test_email.lower()), None)

    if not test_lid:
        print(f"Geen lid gevonden met e-mailadres {test_email}")
        return

    voornaam = test_lid["Voornaam"].strip()
    status = test_lid["Banana status"].strip()
    nummer = test_lid["#"].strip()

    bestand = f"Rekening_{status}{nummer}.html"
    pad = os.path.join(HTML_MAP, bestand)

    if not os.path.exists(pad):
        print(f"Bestand ontbreekt: {pad} — testmail wordt niet verzonden.")
        return

    with open(pad, encoding='utf-8') as f:
        rekening_html = f.read()

    dynamische_tekst = genereer_dynamische_tekst(voornaam, betaal_link)
    volledige_html = config.get_html_email(dynamische_tekst + rekening_html)

    if dry_run:
        print("DRY-RUN: geen e-mail verzonden.")
        print(f"Zou sturen naar: {test_email}")
        print(f"Onderwerp: {onderwerp}")
        print(f"Bijlage: {pad}")
        print(f"Gebruikte betaal_link: {betaal_link}")
        print(f"Bron CSV: {csv_pad}")
        return

    print(f"Verstuur testmail naar {test_email} met bestand {bestand}")

    if not _confirmed_to_send():
        print("Verzenden geannuleerd.")
        return

    stuur_mail(test_email, onderwerp, volledige_html, pad)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stuur test saldo-update e-mail")
    parser.add_argument("--dry-run", action="store_true", help="Toon wat er gestuurd zou worden zonder te verzenden")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
