import getpass
import os


def ensure_domain(domain):
    if domain == "your-username.pythonanywhere.com":
        username = getpass.getuser().lower()
        pa_domain = os.environ.get("PYTHONANYWHERE_DOMAIN", "pythonanywhere.com")
        return f"{username}.{pa_domain}"
    else:
        return domain
