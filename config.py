def get_html_email(dynamische_tekst):
    """Genereert complete HTML email met styling en ondertekening"""
    return f"""\
<html>
  <head>
    <style>
      body {{ color: red; font-family: Arial, sans-serif; }}
      p {{ color: red; }}
      a {{ color: red !important; text-decoration: none; }}
      a:visited {{ color: red !important; }}
      a:hover {{ color: red !important; }}
      img {{ display: block; border: 0; overflow-clip-margin: content-box; overflow: clip; overflow-x: ; overflow-y: ; color: red; }}
      i {{ color: red; }}
      small {{ color: red; }}
    </style>
  </head>
  <body>
    {dynamische_tekst}
    <br>
    <br>
<p style="color: red;">Met Stormende&nbsp;groet,</p>
<p style="color: red;">
    [Jouw Naam :)]<br>
    <i>Quaegé der Demosdispuut Adregé</i><br>
</p>
  <div><img src="cid:logo" width="224" data-image-whitelisted="" class="CToWUd" data-bit="iit"></div>
<p style="color: red;">
    T: [Jouw telefoonnummer]<br>
    E: <a href="mailto:quaege@adrege.nl" style="color: red; text-decoration: none;">quaege@adrege.nl</a><br>
    B: NL02 SNSB 8846 2041 82<br>
    <small>(ten name van [Rekeninghouders])</small>
</p>
</body>
</html>
"""

def attach_logo(msg):
    # """Voegt logo toe als inline afbeelding"""
    from email.mime.image import MIMEImage
    
    with open(logo_pad, 'rb') as img_file:
        img = MIMEImage(img_file.read())
        img.add_header('Content-ID', '<logo>')
        img.add_header('Content-Disposition', 'inline', filename="adrege_logo.png")
        img.add_header('Content-Transfer-Encoding', 'base64')
        msg.attach(img)
    return msg

# Always resolve logo path relative to the executable or script location
import os
import sys
def get_base_dir():
  if getattr(sys, 'frozen', False):
    return os.path.dirname(sys.executable)
  return os.path.dirname(__file__)
logo_pad = os.path.join(get_base_dir(), "Adrege_logo.png")

sender_email = "quaege@adrege.nl"
password = "Wachtwoord van quaege account"


# Configuratie variabelen (worden overschreven door main_gui.py)
test_email = ""
TEXT_NOTE = ""
EMAIL_SUBJECT = ""
CSV_PAD = ""
BETAAL_LINK = ""

def genereer_dynamische_tekst(voornaam, betaal_link):
    """Genereert dynamische e-mail tekst met voornaam, betaal link en TEXT_NOTE"""
    return f"""
        <p>Hoi lieve {voornaam},</p>
        <p>{TEXT_NOTE}</p>
        <p>Mocht je een negatief saldo hebben, dan verzoek ik je graag om het openstaande bedrag over te maken via onderstaand betaalverzoek:</p>
        <p><a href="{betaal_link}">{betaal_link}</a></p>
        <p>En oja, check ook even je wbw-saldo! Het is fijn als de verschillen hier niet te groot zijn :)</p>
        <p>Bij vragen, let met know!</p>
    """
