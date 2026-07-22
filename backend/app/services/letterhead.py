"""Letterhead canvas: stamps a header image on the first page and a
footer image on the last page of a reportlab document, with the standard
small text footer on all other pages."""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as _canvas


def make_letterhead_canvas(letterhead: dict):
    header_path = letterhead.get("header_path")
    footer_path = letterhead.get("footer_path")
    header_h = float(letterhead.get("header_h_mm", 0)) * mm
    footer_h = float(letterhead.get("footer_h_mm", 0)) * mm
    footer_text = letterhead.get("footer_text", "")

    class LetterheadCanvas(_canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._saved_pages = []

        def showPage(self):
            self._saved_pages.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._saved_pages)
            W, H = A4
            for i, state in enumerate(self._saved_pages, start=1):
                self.__dict__.update(state)
                if i == 1 and header_path and header_h:
                    self.drawImage(
                        header_path, 14 * mm, H - 6 * mm - header_h,
                        width=W - 28 * mm, height=header_h,
                        preserveAspectRatio=True, anchor="n",
                    )
                if i == total and footer_path and footer_h:
                    self.drawImage(
                        footer_path, 14 * mm, 6 * mm,
                        width=W - 28 * mm, height=footer_h,
                        preserveAspectRatio=True, anchor="s",
                    )
                else:
                    self.setFont("Helvetica", 8)
                    self.setFillColor(colors.grey)
                    if footer_text:
                        self.drawString(15 * mm, 10 * mm, footer_text)
                    self.drawRightString(W - 15 * mm, 10 * mm, f"Page {i} of {total}")
                    self.setStrokeColor(colors.lightgrey)
                    self.line(15 * mm, 13 * mm, W - 15 * mm, 13 * mm)
                super().showPage()
            super().save()

    return LetterheadCanvas
