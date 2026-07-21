"""Per-user PDF branding.

Certain fixed accounts get their own headline on every PDF they download.
Everyone else gets the default report branding.
"""
from typing import Optional

BRANDED_PDF_USERS = {
    "radheshamtaynath8@gmail.com": {
        "headline": "DR SHINDE EDUCATION SERVICES PVT LTD Latur",
    },
}


def pdf_headline_for(email: Optional[str]) -> Optional[str]:
    if not email:
        return None
    entry = BRANDED_PDF_USERS.get(email.strip().lower())
    return entry["headline"] if entry else None
