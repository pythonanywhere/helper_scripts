import getpass
import os


def ensure_domain(domain):
    if domain == "your-username.pythonanywhere.com":
        username = getpass.getuser().lower()
        pa_domain = os.environ.get("PYTHONANYWHERE_DOMAIN", "pythonanywhere.com")
        return f"{username}.{pa_domain}"
    else:
        return domain


def format_log_deletion_message(domain, log_type, log_index):
    """Generate message describing log deletion.

    Args:
        domain: Domain name (e.g., 'www.example.com')
        log_type: Log type string ('access', 'error', or 'server')
        log_index: 0 for current log, >0 for archived log

    Returns:
        Formatted message string
    """
    if log_index:
        return f"Deleting old (archive number {log_index}) {log_type} log file for {domain} via API"
    return f"Deleting current {log_type} log file for {domain} via API"
