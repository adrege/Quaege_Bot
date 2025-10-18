import sys
from bs4 import BeautifulSoup
import re
import os

# Bestand inlezen
# with open("boekhouding 24-25.html", "r", encoding="utf-8") as f:
# 	html = f.read()

if len(sys.argv) < 2:
	print("Usage: python export_html.py <input_file>")
	sys.exit(1)

f = sys.argv[1]
with open(f, "r", encoding="utf-8") as file:
	html = file.read()

if not os.path.exists(f):
	print(f"Error: File not found — {f}")
	sys.exit(1)

print(f"Using file: {f}")

soup = BeautifulSoup(html, "html.parser")

# Aangepaste CSS
custom_css = '''
<style>
	@media screen, print {
		body {
			font-family: "Go Boom!";
			color: #ea0e0e;
			margin: 0 auto;
			padding: 1em;
		}
		h2, h3, h4, h5, h6 {
			border-bottom: 1px solid #ccc;
			margin: 1em 0 0.2em 0;
		}
		.top {
			margin: 10px 0 20px 0;
		}
		.heading1, .heading2, .heading3 {
			display: block;
		}
		thead {
			display: table-header-group;
		}
		table {
			width: 100%;
		}
		.STable_caption {
			padding: 5px;
			text-align: left;
			font-size: 120%;
			font-weight: bold;
		}
		.STable {
			border: 2px solid black;
			border-collapse: collapse;
			color: black;
		}
		.SDefault {
			font-size: 10pt;
			vertical-align: top;
		}
		.SHeading {
			background: #ea0e0e;
			color: white;
			font-weight: bold;
			text-align: center;
			vertical-align: top;
		}
		.SBold { font-weight: bold; }
		.SItalic { font-style: italic; }
		.SNoWrap { overflow: hidden; }
		.Style80 { font-size: 80%; }
		.Style100 { font-size: 100%; }
		.Style120 { font-size: 120%; }
		.Style140 { font-size: 140%; }
		.SALeft { text-align: left; }
		.SARight { text-align: right; }
		.SACenter { text-align: center; }
		.SMinus { color: #ea0e0e; }
	}
	@media print {
		body {
			font-size: 10pt;
			font-family: "Go Boom!";
		}
		.top { display: none; }
		.t1_header { margin-top: 5%; }
	}
</style>
'''

# CSS vervangen
if soup.head.style:
    soup.head.style.replace_with(BeautifulSoup(custom_css, "html.parser"))

# Output folder
os.makedirs("rekeningen_split", exist_ok=True)

# Zoek alle tabellen met id=Table_AccountCard_...
tables = soup.find_all("table", id=re.compile(r"^Table_AccountCard_"))

for table in tables:
    rekening_code = table["id"].replace("Table_AccountCard_", "")
    
    # Alleen rekeningen die beginnen met S of R
    if not rekening_code.startswith("S") and not rekening_code.startswith("R"): 
        continue

    # Zoek bijbehorende caption block
    caption_tag = table.find_previous_sibling("p", class_="STable_caption")
    caption_html = str(caption_tag) if caption_tag else ""

    # HTML samenstellen
    sub_html = f"""<html><head><meta charset="UTF-8">{custom_css}</head><body>
{caption_html}
{str(table)}
</body></html>"""

    # Opslaan
    bestand_naam = f"rekeningen_split/Rekening_{rekening_code}.html"
    with open(bestand_naam, "w", encoding="utf-8") as f_out:
        f_out.write(sub_html)

    print(f"Rekening {rekening_code} geëxporteerd naar {bestand_naam}")
