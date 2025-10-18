"""
Script om transacties uit PDF bankafschrift te extraheren en te matchen met ledenadministratie.
Genereert Excel output met spaar- en regesbijdragen.
"""

import pandas as pd
from pypdf import PdfReader
import re
from datetime import datetime
import os

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
    
    def extract_transactions_from_pdf(self):
        """Extraheer transacties uit PDF"""
        reader = PdfReader(self.pdf_path)
        all_text = ""
        
        # Lees alle pagina's
        for page in reader.pages:
            all_text += page.extract_text() + "\n"
        
        lines = all_text.split('\n')
        transactions = []
        
        # Patronen voor transactie detectie
        # Zoek naar regels met datum (DD-MM-YYYY of DD/MM/YYYY)
        date_pattern = r'(\d{2}[-/]\d{2}[-/]\d{4})'
        amount_pattern = r'[+-]?\s*€?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2}))'
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Zoek naar datum in de regel
            date_match = re.search(date_pattern, line)
            if date_match:
                date_str = date_match.group(1)
                
                # Probeer transactie informatie te extraheren
                # Meestal staan naam en bedrag op dezelfde of volgende regel
                description = line
                amount = None
                
                # Zoek naar bedrag in huidige en volgende regels
                for j in range(i, min(i+5, len(lines))):
                    amount_match = re.search(amount_pattern, lines[j])
                    if amount_match:
                        amount_str = amount_match.group(1).replace('.', '').replace(',', '.')
                        amount = float(amount_str)
                        # Bepaal teken op basis van eerste regel (Bij/Af)
                        header_line = lines[i]
                        if re.search(r'\bAf\b', header_line):
                            amount = -abs(amount)
                        elif re.search(r'\bBij\b', header_line):
                            amount = abs(amount)
                        else:
                            # fallback: positief laten (we filteren later toch op > 0)
                            amount = abs(amount)
                        
                        # Verzamel beschrijving uit meerdere regels
                        description = ' '.join(lines[i:j+1])
                        break
                
                if amount is not None and amount > 0:  # Alleen inkomende transacties
                    transactions.append({
                        'date': date_str,
                        'description': description,
                        'amount': amount,
                        'raw_text': description
                    })
            
            i += 1
        
        print(f"Gevonden: {len(transactions)} inkomende transacties in PDF")
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
    
    def process_transactions(self):
        """Verwerk alle transacties en match met leden"""
        # Laad leden
        self.load_members()
        
        # Extraheer transacties
        transactions = self.extract_transactions_from_pdf()
        
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
            
            if member:
                # Parse datum
                date_str = trans['date'].replace('-', '/')
                
                banana_status = member['banana_status']
                voornaam = member['voornaam']
                
                if banana_status.startswith('S'):
                    # Sparen
                    beschrijving = f"Sparen {voornaam}"
                    debit_rek = "1020"
                    credit_rek = "1125"
                    member_id = member.get('id') or ''
                    kp1 = f"S{member_id}".strip()
                elif banana_status.startswith('R'):
                    # Regesbijdrage
                    beschrijving = f"Regesbijdrage {voornaam}"
                    debit_rek = "1020"
                    credit_rek = "2500"
                    kp1 = ""
                else:
                    # Onbekende status, skip
                    continue
                
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
        """Exporteer resultaten naar CSV (tab-separated voor compatibiliteit)"""
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
        if not (output_path.lower().endswith('.csv') or output_path.lower().endswith('.tsv')):
            output_path = f"{output_path}.csv"
        # Exporteer naar CSV met tab separator
        df.to_csv(output_path, index=False, sep='\t', encoding='utf-8')
        print(f"CSV bestand aangemaakt: {output_path}")
        return True


def main():
    """Hoofdfunctie voor standalone gebruik"""
    import sys
    
    if len(sys.argv) < 2:
        print("Gebruik: python generate_transactions.py <pdf_path> [csv_path] [output_path]")
        print("\nStandaard waarden:")
        print("  csv_path: scripts/Ledenadministratie - Leden.csv")
        print("  output_path: transacties_output.xlsx")
        return
    
    pdf_path = sys.argv[1]
    csv_path = sys.argv[2] if len(sys.argv) > 2 else "scripts/Ledenadministratie - Leden.csv"
    output_path = sys.argv[3] if len(sys.argv) > 3 else "transacties_output.xlsx"
    
    # Controleer of bestanden bestaan
    if not os.path.exists(pdf_path):
        print(f"Fout: PDF bestand niet gevonden: {pdf_path}")
        return
    
    if not os.path.exists(csv_path):
        print(f"Fout: CSV bestand niet gevonden: {csv_path}")
        return
    
    # Verwerk transacties
    processor = TransactionProcessor(pdf_path, csv_path)
    results = processor.process_transactions()
    
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
