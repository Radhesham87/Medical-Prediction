"""Per-user PDF branding.

Certain fixed accounts get their own branding on every PDF they download:
either a custom headline (counselling-report style) or a letterhead
(image strips stamped on the first/last page). Everyone else gets the
default report branding.
"""
from pathlib import Path
from typing import Optional

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

_BRIGHTFUTURE_LETTERHEAD = {
    "header_path": str(ASSETS_DIR / "brightfuture_header.jpg"),
    "footer_path": str(ASSETS_DIR / "brightfuture_footer.jpg"),
    "header_h_mm": 26.1,
    "footer_h_mm": 42.6,
    "footer_text": "Generated via Bright Future Education Group",
    "counselling_layout": True,
}

BRANDED_PDF_USERS = {
    "radheshamtaynath8@gmail.com": {
        "headline": "DR SHINDE EDUCATION SERVICES PVT LTD Latur",
    },
    "jadhavs785@gmail.com": {
        "letterhead": _BRIGHTFUTURE_LETTERHEAD,
    },
    # The shared multi-device account gets the same Bright Future treatment:
    # letterhead strips on first/last page + counselling-report body.
    "jadav784@gmail.com": {
        "letterhead": _BRIGHTFUTURE_LETTERHEAD,
    },
}


def pdf_brand_for(email: Optional[str]) -> Optional[dict]:
    if not email:
        return None
    return BRANDED_PDF_USERS.get(email.strip().lower())


def pdf_headline_for(email: Optional[str]) -> Optional[str]:
    brand = pdf_brand_for(email)
    return brand.get("headline") if brand else None


def pdf_letterhead_for(email: Optional[str]) -> Optional[dict]:
    brand = pdf_brand_for(email)
    return brand.get("letterhead") if brand else None
