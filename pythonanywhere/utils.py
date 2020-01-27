import getpass
import os


def ensure_domain(domain):
    if domain == "your-username.pythonanywhere.com":
        username = getpass.getuser().lower()
        pa_domain = os.environ.get("PYTHONANYWHERE_DOMAIN", "pythonanywhere.com")
        return "{username}.{pa_domain}".format(username=username, pa_domain=pa_domain)
    else:
        return domain
