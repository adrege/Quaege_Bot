from html import escape
import os
import sys
from pathlib import Path

# Always resolve logo paths relative to the executable or script location.
def get_base_dir():
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(__file__)
logo_pad = os.path.join(get_base_dir(), "Adrege_logo.png")
logo_lang_pad = os.path.join(get_base_dir(), "Adrege_logo_lang.png")

sender_email = "quaege@adrege.nl"
password = "Wachtwoord van quaege account"


# Configuratie variabelen (worden overschreven door main_gui.py)
test_email = ""
TEXT_NOTE = ""
EMAIL_SUBJECT = ""
CSV_PAD = ""
BETAAL_LINK = ""
SIGNATURE_GREETING = "Met Stormende groet,"
SIGNATURE_NAME = ""
SIGNATURE_ROLE = "Quaegé der Demosdispuut Adregé"
SIGNATURE_PHONE = ""
SIGNATURE_EMAIL = "quaege@adrege.nl"
SIGNATURE_BANK_ACCOUNT = "NL02 SNSB 8846 2041 82"
SIGNATURE_ACCOUNT_HOLDER = ""

# A packaged application is read-only under /opt. Load the user's writable
# configuration after the defaults so SMTP credentials never need to be edited
# inside the installation directory.
try:
    from app_paths import USER_CONFIG_PATH
    if (
        USER_CONFIG_PATH.exists()
        and USER_CONFIG_PATH.resolve() != Path(__file__).resolve()
        and not os.environ.get("QUAEGE_LOADING_USER_CONFIG")
    ):
        os.environ["QUAEGE_LOADING_USER_CONFIG"] = "1"
        try:
            with USER_CONFIG_PATH.open(encoding="utf-8") as user_config:
                exec(compile(user_config.read(), str(USER_CONFIG_PATH), "exec"), globals())
        finally:
            os.environ.pop("QUAEGE_LOADING_USER_CONFIG", None)
except (OSError, SyntaxError) as error:
    print(f"Warning: user configuration could not be loaded: {error}")


def get_html_email(dynamische_tekst):
    """Genereert complete HTML email met styling en ondertekening."""
    greeting = escape(SIGNATURE_GREETING or "Met Stormende groet,")
    quaege_name = escape(SIGNATURE_NAME or "De Quaege")
    role = escape(SIGNATURE_ROLE)
    phone = escape(SIGNATURE_PHONE)
    email = escape(SIGNATURE_EMAIL)
    bank_account = escape(SIGNATURE_BANK_ACCOUNT)
    account_holder = escape(SIGNATURE_ACCOUNT_HOLDER)
    contact_details = "".join(
        line
        for line in (
            f"    T: {phone}<br>\n" if phone else "",
            (
                f'    E: <a href="mailto:{email}" style="color: red; text-decoration: none;">'
                f"{email}</a><br>\n"
                if email
                else ""
            ),
            f"    B: {bank_account}<br>\n" if bank_account else "",
            f"    <small>(ten name van {account_holder})</small>\n"
            if account_holder
            else "",
        )
    )
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
<p style="color: red;">{greeting}</p>
<p style="color: red;">
    {quaege_name}<br>
    <i>{role}</i><br>
</p>
<p style="color: red;">
{contact_details}</p>
  <div><img src="cid:logo_lang" width="200" alt="Adregé Demosdispuut"></div>
</body>
</html>
"""


def attach_logo(msg):
    """Voegt het lange logo toe als inline afbeelding in de e-mailhandtekening."""
    from email.mime.image import MIMEImage

    with open(logo_lang_pad, "rb") as img_file:
        img = MIMEImage(img_file.read())
        img.add_header("Content-ID", "<logo_lang>")
        img.add_header("Content-Disposition", "inline", filename="Adrege_logo_lang.png")
        img.add_header("Content-Transfer-Encoding", "base64")
        msg.attach(img)
    return msg


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
