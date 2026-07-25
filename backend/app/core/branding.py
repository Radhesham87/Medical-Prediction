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
    "header_as_flowable": True,
    "footer_path": str(ASSETS_DIR / "brightfuture_footer.jpg"),
    "header_h_mm": 26.1,
    "footer_h_mm": 42.6,
    "footer_text": "Generated via Bright Future Education Group",
    "counselling_layout": True,
}

_ASPIRE_LETTERHEAD = {
    "header_path": str(ASSETS_DIR / "aspire_header.jpg"),
    "header_w_mm": 182,
    "header_h_mm": 77.4,
    "header_as_flowable": True,  # drawn as the first element of page 1 only
    "footer_path": str(ASSETS_DIR / "aspire_footer.jpg"),
    "footer_h_mm": 58,  # letterboxed: address strip + phone bar, centered
    "watermark_path": str(ASSETS_DIR / "aspire_watermark.jpg"),
    "watermark_w_mm": 105,
    "footer_text": "Generated via Aspire Career Counselling Center",
    "counselling_layout": True,
}

_GROVY_LETTERHEAD = {
    "header_path": str(ASSETS_DIR / "grovy_header.jpg"),
    "header_w_mm": 182,
    "header_h_mm": 46.8,
    "header_as_flowable": True,
    "footer_path": str(ASSETS_DIR / "grovy_footer.jpg"),
    "footer_h_mm": 24.3,
    "watermark_path": str(ASSETS_DIR / "grovy_watermark.jpg"),
    "watermark_w_mm": 105,
    "footer_text": "Generated via Grovy Education Consultant",
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
    # letterhead strips on first/last page + counselling-report body,
    # plus a faint logo watermark behind the content of every page.
    "jadav784@gmail.com": {
        "letterhead": {
            **_BRIGHTFUTURE_LETTERHEAD,
            "watermark_path": str(ASSETS_DIR / "brightfuture_watermark.jpg"),
            "watermark_w_mm": 110,
        },
    },
    # Aspire Career Counselling Center: banner header on page 1, logo watermark
    # on every page, Latur address strip on the last page.
    "aspirecareer1212@gmail.com": {
        "letterhead": _ASPIRE_LETTERHEAD,
    },
    # Grovy Education Consultant, Nanded: logo banner headline, circular-mark
    # watermark, address/phone footer bar on the last page.
    "gncnanded@gmail.com": {
        "letterhead": _GROVY_LETTERHEAD,
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
