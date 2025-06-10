"""Lean wrapper around PyMuPDF, now version-agnostic re: widgets()."""

import fitz  # PyMuPDF


class PDFEngine:
    def __init__(self, path: str):
        self.doc = fitz.open(path)
        self.current_page = 0

    # ---------- Rendering --------------------------------------------------
    def page_count(self) -> int:
        return len(self.doc)

    def render_page(self, page_number: int, zoom: float = 2.0):
        page = self.doc.load_page(page_number)
        return page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))

    # ---------- Form-field helpers ----------------------------------------
    def _iter_widgets(self):
        """Yield every widget in every page (works on all PyMuPDF versions)."""
        for pno in range(len(self.doc)):
            page = self.doc.load_page(pno)
            try:
                widgets = page.widgets()          # modern API
            except AttributeError:
                widgets = []                      # page has none / old build
            for w in widgets or []:
                yield w

    def list_form_fields(self):
        """Return a list of {name, value, type} dicts for all form widgets."""
        fields = []
        for w in self._iter_widgets():
            if w.field_name:                      # skip un-named widgets
                fields.append(
                    {
                        "name": w.field_name,
                        "value": w.field_value,
                        "type": w.field_type,
                    }
                )
        return fields

    def update_form_field(self, name: str, value: str):
        """Set a new value for the first widget matching *name*."""
        for w in self._iter_widgets():
            if w.field_name == name:
                w.field_value = value
                w.update()
                return

    # ---------- Saving -----------------------------------------------------
    def save(self, path: str, incremental: bool = False):
        self.doc.save(path, incremental=incremental)


    # ---------- Add Text -----------------------------------------------------

    def insert_text(self, page_number: int, x: float, y: float, text: str, font_size: float = 12):
        """Add permanent text to the page at (x, y)."""
        page = self.doc.load_page(page_number)
        page.insert_text((x, y), text, fontsize=font_size)
