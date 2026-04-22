import csv
import os
import smtplib
import imaplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

import sys
import argparse
from pathlib import Path

# Pad naar HTML-bestanden en CSV
# Use absolute paths so the script can be run from anywhere
BASE_DIR = Path(__file__).resolve().parent.parent
HTML_MAP = str(BASE_DIR / "rekeningen_split")
DEFAULT_CSV_PAD = str(Path(__file__).resolve().parent / "Ledenadministratie - Leden.csv")
# Ensure we can import the top-level config.py when running from the scripts folder

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import config

def get_csv_path():
    csv_from_config = getattr(config, "CSV_PAD", None)
    if csv_from_config:
        cfg = os.path.expandvars(os.path.expanduser(csv_from_config))
        if os.path.exists(cfg):
            print(f"CSV path from config: {cfg}")
            return cfg
        else:
            print(f"Warning: CSV path in config not found: {cfg}; falling back to default: {DEFAULT_CSV_PAD}")
    else:
        print(f"No CSV_PAD in config; using default: {DEFAULT_CSV_PAD}")
    return DEFAULT_CSV_PAD

def get_betaal_link():
    if hasattr(config, "BETAAL_LINK") and getattr(config, "BETAAL_LINK"):
        print("betaal_link loaded from config.BETAAL_LINK")
        return getattr(config, "BETAAL_LINK")
    if hasattr(config, "betaal_link") and getattr(config, "betaal_link"):
        print("betaal_link loaded from config.betaal_link")
        return getattr(config, "betaal_link")
    fallback = "Er is iets misgegaan bij het laden van de betaal link. Graag gebruik maken van een overboeking."
    print("Warning: betaal_link not set in config; using fallback default. Update config.BETAAL_LINK in settings.")
    return fallback

# SMTP en IMAP instellingen
SMTP_SERVER = 'mail.antagonist.nl'
SMTP_PORT = 465
IMAP_FOLDER = 'INBOX.Sent'

def lees_csv(pad):
    with open(pad, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def genereer_dynamische_tekst(voornaam, betaal_link):
    return config.genereer_dynamische_tekst(voornaam, betaal_link)

def stuur_mail(ontvanger_email, onderwerp, html_bericht, bijlage_pad):
    msg = MIMEMultipart('related')
    msg['Subject'] = onderwerp
    msg['From'] = config.sender_email
    msg['To'] = ontvanger_email

    msg_alt = MIMEMultipart('alternative')
    msg.attach(msg_alt)
    msg_alt.attach(MIMEText(html_bericht, 'html'))

    msg = config.attach_logo(msg)
    # Voeg bijlage toe
    with open(bijlage_pad, 'rb') as f:
        attachment = MIMEApplication(f.read(), _subtype='html')
        attachment.add_header('Content-Disposition', 'attachment', filename=os.path.basename(bijlage_pad))
        msg.attach(attachment)
    
    # Verstuur e-mail
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(config.sender_email, config.password)
            server.send_message(msg)
            print(f"E-mail verzonden naar {ontvanger_email}")

        with imaplib.IMAP4_SSL(SMTP_SERVER) as imap:
            imap.login(config.sender_email, config.password)
            imap.append(IMAP_FOLDER, '', imaplib.Time2Internaldate(time.time()), msg.as_bytes())
            print(f"Kopie opgeslagen in Verzonden map voor {ontvanger_email}")

    except Exception as e:
        print(f"Fout bij {ontvanger_email}: {e}")

def hoofdprogramma(dry_run=False):
    csv_pad = get_csv_path()
    leden = lees_csv(csv_pad)
    betaal_link = get_betaal_link()
    onderwerp = getattr(config, "EMAIL_SUBJECT", "") or "Adrege Saldo Update"

    to_send = []
    for lid in leden:
        voornaam = lid["Voornaam"].strip()
        email = lid["Emailadres"].strip()
        status = lid["Banana status"].strip()
        nummer = lid["#"].strip()

        if status != "S":
            continue

        bestand = f"Rekening_{status}{nummer}.html"
        pad = os.path.join(HTML_MAP, bestand)

        if not os.path.exists(pad):
            print(f"Bestand ontbreekt: {pad} — e-mail wordt overgeslagen.")
            continue

        to_send.append({
            "voornaam": voornaam,
            "email": email,
            "bestand": bestand,
            "pad": pad,
        })

    if dry_run:
        print("DRY-RUN: geen e-mails verzonden.")
        print(f"CSV: {csv_pad}")
        print(f"betaal_link: {betaal_link}")
        print(f"Aantal te mailen leden met status S: {len(to_send)}")
        for info in to_send:
            print(f"Zou sturen naar: {info['email']} (bestand: {info['bestand']})")
        return

    # Show list of recipients and ask for confirmation before sending
    print("\n" + "="*60)
    print(f"KLAAR OM TE VERZENDEN naar {len(to_send)} leden met status S:")
    print("="*60)
    for idx, info in enumerate(to_send, 1):
        print(f"{idx}. {info['voornaam']} - {info['email']} (bestand: {info['bestand']})")
    print("="*60 + "\n")

    if not _confirmed_to_send():
        print("Verzenden geannuleerd.")
        return

    print("\nVerzenden gestart...\n")
    for info in to_send:
        with open(info["pad"], encoding='utf-8') as f:
            rekening_html = f.read()
        dynamische_tekst = genereer_dynamische_tekst(info["voornaam"], betaal_link)
        volledige_html = config.get_html_email(dynamische_tekst + rekening_html)
        stuur_mail(info["email"], onderwerp, volledige_html, info["pad"])

def _confirmed_to_send() -> bool:
    try:
        if not sys.stdin or not sys.stdin.isatty():
            print("Non-interactive omgeving gedetecteerd (waarschijnlijk via GUI); bevestiging wordt overgeslagen.")
            return True
    except Exception:
        print("Kan stdin niet lezen; ga ervan uit dat bevestiging ok is.")
        return True
    bevestiging = input("Weet je zeker dat je een mail wilt sturen naar het hele dispuut? (y/N): ").strip().lower()
    return bevestiging == "y"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stuur saldo updates naar leden met status S")
    parser.add_argument("--dry-run", action="store_true", help="Toon wat er gestuurd zou worden zonder te verzenden")
    args = parser.parse_args()
    hoofdprogramma(dry_run=args.dry_run)
