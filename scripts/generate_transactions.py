"""
Script om transacties uit PDF bankafschrift te extraheren en te matchen met ledenadministratie.
Genereert Excel output met spaar- en regesbijdragen.
"""

import pandas as pd
import pdfplumber
import csv
import re
from datetime import datetime
import os
import sys
import argparse
from pathlib import Path

# Ensure we can import the top-level config.py when running from the scripts folder
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import config
from app_paths import EXPORT_DIR

# Default CSV lives in the scripts folder
DEFAULT_CSV_PAD = str(Path(__file__).resolve().parent / "Ledenadministratie - Leden.csv")
BANK_COLUMNS = [
    "Datum", "Je rekening", "Van / naar", "Naam", "Adres", "Postcode",
    "Woonplaats", "Valuta saldo", "Saldo voor boeking", "Valuta",
    "Bedrag bij / af", "Verwerkingsdatum", "Valutadatum", "Code", "Type",
    "Volgnummer", "Betalingskenmerk", "Omschrijving", "Afschriftnummer",
    "Categorie",
]

def get_csv_path():
    """Prefer CSV path from config (CSV_PAD), else fall back to default in scripts folder."""
    csv_from_config = getattr(config, "CSV_PAD", None)
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

class TransactionProcessor:
    def __init__(self, pdf_path, csv_path):
        self.pdf_path = pdf_path
        self.csv_path = csv_path
        self.transactions = []
        self.members = {}
        
    def load_members(self):
        """Laad ledenadministratie en maak dictionary met achternaam als key"""
        df = pd.read_csv(self.csv_path)
        for _, row in df.iterrows():
            achternaam = str(row['Achternaam']).strip().lower()
            voornaam = str(row['Voornaam']).strip()
            banana_status = str(row['Banana status']).strip()
            
            # Sla leden op met hun gegevens
            self.members[achternaam] = {
                'voornaam': voornaam,
                'banana_status': banana_status,
                'banana_naam': str(row['Naam Banana\'s']).strip(),
                'id': str(row.get('#', '')).strip()
            }
        
        print(f"Geladen: {len(self.members)} leden uit CSV")
        return self.members
    
    def _normalize_amount(self, amount_text):
        """Converteer bedrag met komma-notatie naar float."""
        value = amount_text.strip().replace("€", "").replace(" ", "")
        if "," in value:
            value = value.replace(".", "").replace(",", ".")
        return float(value)

    def get_intermediate_csv_path(self, output_path=None):
        """Maak een duidelijke naam voor de tussen-CSV met ruwe transacties."""
        pdf_stem = Path(self.pdf_path).stem
        file_name = f"{pdf_stem}_ruwe_transacties.csv"

        if output_path:
            output_dir = Path(output_path).parent
        else:
            output_dir = Path(self.pdf_path).parent

        return str(output_dir / file_name)

    def extract_from_text(self, output_csv):
        """Extraheer transacties uit PDF tekst naar tussen-CSV."""
        transactions = []

        tx_pattern = re.compile(
            r"^(?P<datum>\d{2}[-/]\d{2}[-/]\d{4})\s+"
            r"(?P<bij_af>Bij|Af)\s+"
            r"(?:EUR\s+|€\s*)?"
            r"(?P<bedrag>-?\d{1,3}(?:\.\d{3})*,\d{2})"
            r"\s*(?P<omschrijving>.*)$"
        )

        pdf_file = Path(self.pdf_path)
        with pdfplumber.open(str(pdf_file)) as pdf:
            total_pages = len(pdf.pages)
            for page_index, page in enumerate(pdf.pages, start=1):
                print(f"Processing page {page_index}/{total_pages}...")
                text = page.extract_text()
                if not text:
                    continue

                lines = text.split('\n')
                current_row = None

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    match = tx_pattern.match(line)
                    if match:
                        if current_row:
                            transactions.append(current_row)

                        current_row = [
                            match.group("datum"),
                            match.group("bij_af"),
                            match.group("bedrag"),
                            match.group("omschrijving").strip(),
                        ]
                    elif current_row:
                        # Voeg vervolgregels toe aan meerregelige omschrijvingen.
                        current_row[3] += " " + line

                if current_row:
                    transactions.append(current_row)

        output_path = Path(output_csv)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(BANK_COLUMNS)
            for date, direction, amount, description in transactions:
                signed_amount = amount.replace(",", ".")
                if direction == "Af" and not signed_amount.startswith("-"):
                    signed_amount = f"-{signed_amount}"
                writer.writerow([
                    date, "", "", "", "", "", "", "EUR", "", "EUR",
                    signed_amount, date, date, "", "", "", "", description, "", "",
                ])

        print(f"Extractie voltooid. {len(transactions)} rijen opgeslagen in: {output_csv}")
        return output_csv

    def load_transactions_from_csv(self, extracted_csv_path, include_negative=False):
        """Laad tussen-CSV en zet inkomende en optioneel uitgaande transacties om."""
        transactions = []
        df = pd.read_csv(extracted_csv_path, dtype=str, sep=None, engine="python").fillna("")

        for _, row in df.iterrows():
            direction_column = str(row.get('Bij/Af', '')).strip()
            amount_column = str(row.get('Bedrag bij / af', '')).strip()
            if amount_column:
                try:
                    signed_amount = self._normalize_amount(amount_column)
                except ValueError:
                    signed_amount = 0
                bij_af = "Af" if signed_amount < 0 else "Bij"
                bedrag = amount_column
            else:
                bij_af = direction_column
                bedrag = str(row.get('Bedrag', '')).strip()
            if bij_af not in ('Bij', 'Af'):
                continue
            if bij_af == 'Af' and not include_negative:
                continue

            if not bedrag:
                continue

            try:
                amount = self._normalize_amount(bedrag)
            except ValueError:
                continue

            amount = abs(amount)
            if amount == 0:
                continue

            date_str = str(row.get('Datum', '')).strip().replace("-", "/")
            description = str(row.get('Omschrijving', '')).strip()
            if not date_str or not description:
                continue

            transactions.append({
                'date': date_str,
                'description': description,
                'amount': amount if bij_af == 'Bij' else -amount,
                'direction': bij_af,
                'raw_text': description
            })

        print(f"Gevonden: {len(transactions)} transacties in tussen-CSV")
        return transactions
    
    def find_member_in_transaction(self, description):
        """Zoek lid in transactie beschrijving op basis van achternaam"""
        description_lower = description.lower()
        for achternaam, member_info in self.members.items():
            # Match op woordgrenzen om false positives te voorkomen
            pattern = r"\b" + re.escape(achternaam) + r"\b"
            if re.search(pattern, description_lower):
                return member_info
        
        return None
    
    def process_transactions(self, output_path=None, extracted_csv_path=None,
                             include_negative=False, r_as_savings=False):
        """Verwerk alle transacties via tussen-CSV en match met leden."""
        # Laad leden
        self.load_members()

        if not extracted_csv_path:
            extracted_csv_path = self.get_intermediate_csv_path(output_path)

        # Stap 1: PDF naar tussen-CSV
        if Path(self.pdf_path).suffix.lower() == ".csv":
            extracted_csv_path = self.pdf_path
        else:
            self.extract_from_text(extracted_csv_path)

        # Stap 2: Tussen-CSV naar intern formaat
        transactions = self.load_transactions_from_csv(
            extracted_csv_path, include_negative=include_negative
        )
        
        # Bepaal maand/jaar voor document naam op basis van transactiedata
        if transactions:
            parsed_dates = []
            for t in transactions:
                d = t['date'].replace('-', '/')
                try:
                    parsed_dates.append(datetime.strptime(d, '%d/%m/%Y'))
                except ValueError:
                    try:
                        parsed_dates.append(datetime.strptime(d, '%d-%m-%Y'))
                    except ValueError:
                        pass
            if parsed_dates:
                doc_date = min(parsed_dates)
            else:
                doc_date = datetime.now()
        else:
            doc_date = datetime.now()
        
        month_names = ['Januari', 'Februari', 'Maart', 'April', 'Mei', 'Juni',
                      'Juli', 'Augustus', 'September', 'Oktober', 'November', 'December']
        doc_name = f"Rekeningoverzicht_{month_names[doc_date.month-1]}_{doc_date.year}"
        
        # Verwerk elke transactie
        results = []
        for trans in transactions:
            member = self.find_member_in_transaction(trans['description'])
            
            if trans['direction'] == 'Af':
                results.append({
                    'Datum': trans['date'],
                    'Doc': '',
                    'Beschrijving': f"AF: {trans['description']}",
                    'Debit Rek': '',
                    'Credit Rek': '1020',
                    'Bedrag': f"{trans['amount']:.2f}".replace('.', ','),
                    'kp1': '',
                })
                continue

            if member:
                # Parse datum
                date_str = trans['date'].replace('-', '/')
                
                banana_status = member['banana_status']
                voornaam = member['voornaam']
                
                if banana_status.startswith('S') or (
                    r_as_savings and banana_status.startswith('R')
                ):
                    # Sparen
                    beschrijving = f"Sparen {voornaam}"
                    member_rek = "1125"
                    member_id = member.get('id') or ''
                    kp1 = f"S{member_id}".strip()
                elif banana_status.startswith('R'):
                    # Regesbijdrage
                    beschrijving = f"Regesbijdrage {voornaam}"
                    member_rek = "2500"
                    kp1 = ""
                else:
                    # Onbekende status, skip
                    continue
                
                if trans['direction'] == 'Bij':
                    debit_rek, credit_rek = "1020", member_rek
                else:
                    # Uitgaande betalingen boeken terug vanaf het lid naar kas/bank.
                    debit_rek, credit_rek = member_rek, "1020"

                results.append({
                    'Datum': date_str,
                    'Doc': doc_name,
                    'Beschrijving': beschrijving,
                    'Debit Rek': debit_rek,
                    'Credit Rek': credit_rek,
                    'Bedrag': f"{trans['amount']:.2f}".replace('.', ','),
                    'kp1': kp1
                })
        
        self.transactions = results
        print(f"Verwerkt: {len(results)} transacties gematcht met leden")
        return results
    
    def export_to_excel(self, output_path):
        """Exporteer resultaten naar Excel"""
        if not self.transactions:
            print("Geen transacties om te exporteren!")
            return False
        
        df = pd.DataFrame(self.transactions)
        
        # Sorteer op datum
        df['Datum_sort'] = pd.to_datetime(df['Datum'], format='%d/%m/%Y')
        df = df.sort_values('Datum_sort')
        df = df.drop('Datum_sort', axis=1)
        # Zorg dat map bestaat en extensie klopt
        dir_name = os.path.dirname(output_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        if not output_path.lower().endswith('.xlsx'):
            output_path = f"{output_path}.xlsx"
        # Exporteer naar Excel met expliciete engine
        df.to_excel(output_path, index=False, sheet_name='Transacties', engine='openpyxl')
        print(f"Excel bestand aangemaakt: {output_path}")
        return True
    
    def export_to_csv(self, output_path):
        """Exporteer een bank-CSV met dezelfde kolommen als de SNS-export."""
        if not self.transactions:
            print("Geen transacties om te exporteren!")
            return False
        
        # Zorg dat map bestaat en extensie klopt
        dir_name = os.path.dirname(output_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        if not (output_path.lower().endswith('.csv') or output_path.lower().endswith('.tsv')):
            output_path = f"{output_path}.csv"
        rows = []
        for transaction in self.transactions:
            amount = str(transaction["Bedrag"]).replace(",", ".")
            if transaction["Credit Rek"] == "1020" and not amount.startswith("-"):
                amount = f"-{amount}"
            rows.append([
                transaction["Datum"].replace("/", "-"), "", "", "", "", "", "",
                "EUR", "", "EUR", amount, transaction["Datum"].replace("/", "-"),
                transaction["Datum"].replace("/", "-"), "", "", "", "",
                transaction["Beschrijving"], "", "",
            ])
        pd.DataFrame(rows, columns=BANK_COLUMNS).to_csv(
            output_path, index=False, encoding="utf-8"
        )
        print(f"CSV bestand aangemaakt: {output_path}")
        return True


def main():
    """Hoofdfunctie voor standalone gebruik"""
    parser = argparse.ArgumentParser(
        description="Converteer een bankafschrift naar een transactie-Excelbestand."
    )
    parser.add_argument("pdf_path", help="PDF of CSV van het bankafschrift")
    parser.add_argument("csv_path", nargs="?", default=None,
                        help="Ledenadministratie CSV (optioneel)")
    parser.add_argument("output_path", nargs="?", default="transacties_output.xlsx",
                        help="Naam van het uitvoerbestand")
    parser.add_argument(
        "--include-negative", action="store_true",
        help="Neem ook 'Af'-transacties op; deze krijgen crediteur 1020."
    )
    parser.add_argument(
        "--r-as-savings", action="store_true",
        help="Boek inkomende transacties van leden met status R als sparen."
    )
    args = parser.parse_args()

    pdf_path = args.pdf_path
    csv_path = args.csv_path or get_csv_path()
    output_path = args.output_path
    if output_path == "transacties_output.xlsx":
        output_path = str(EXPORT_DIR / output_path)
    
    # Controleer of bestanden bestaan
    if not os.path.exists(pdf_path):
        print(f"Fout: PDF bestand niet gevonden: {pdf_path}")
        return
    
    if not os.path.exists(csv_path):
        print(f"Fout: CSV bestand niet gevonden: {csv_path}")
        return
    
    # Verwerk transacties
    processor = TransactionProcessor(pdf_path, csv_path)
    results = processor.process_transactions(
        output_path=output_path,
        include_negative=args.include_negative,
        r_as_savings=args.r_as_savings,
    )
    
    if results:
        # Exporteer naar beide formaten; laat export functies extensies bepalen
        processor.export_to_excel(output_path)
        processor.export_to_csv(output_path)
        
        print(f"\n{'='*60}")
        print(f"Verwerking voltooid!")
        print(f"Totaal transacties verwerkt: {len(results)}")
        print(f"{'='*60}")
    else:
        print("Geen transacties gevonden die matchen met leden!")


if __name__ == "__main__":
    main()
