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

sender_email = ""
password = ""


# Configuratie variabelen (worden overschreven door main_gui.py)
test_email = ""
TEXT_NOTE = "Dit veld word niet meer gebruikt"
CSV_PAD = ""
BETAAL_LINK = ""
