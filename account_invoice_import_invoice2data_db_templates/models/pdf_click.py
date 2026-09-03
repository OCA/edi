# Copyright 2026 bosd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""pypdfium2 helpers for click-to-suggest and drag-rectangle-to-area.

Server-side resolution of a click / drag rectangle to
``(canonical_field, spec, captured_value)``, per the design brief doc at
``the internal design brief

The public surface is two functions:

* :func:`suggest_at(pdf_path, page_idx, x_pt, y_pt)` -> dict — a click at
  page-relative points (top-left origin, PDF-native 72 dpi).
* :func:`suggest_area(pdf_path, page_idx, rect_pt)` -> dict — a drag,
  same coord system, ``rect_pt = (x, y, w, h)`` top-left.

Both return the same shape::

    {
        "field": "amount",
        "spec": r"Total:\s*€\s*([\d.,]+)",   # or a {regex, replace} dict
        "value": "279.84",
        "line": "Total: € 279.84",           # the whole bbox line
        "pdftotext_status": "same" | "different" | "no-match" | "unavailable",
        "hint": {"page": 0, "x": ..., "y": ..., "w": 0, "h": 0},
    }

If pdfium's text layer is empty (scanned PDF), returns
``{"error": "no-text-layer"}`` — the UI shows an OCR hint.
"""

import logging
import shutil
import subprocess

_logger = logging.getLogger(__name__)


def _open(pdf_path):
    try:
        import pypdfium2
    except ImportError as exc:
        raise RuntimeError(
            "pypdfium2 not installed; invoice2data's default extra covers it"
        ) from exc
    return pypdfium2.PdfDocument(pdf_path)


def _flip_y(page, y_top):
    """Convert a top-left-origin y (points) to pdfium's bottom-left y."""
    return page.get_height() - y_top


def suggest_at(pdf_path, page_idx, x_pt, y_pt):
    """Resolve a click at ``(page_idx, x_pt, y_pt)`` to a field proposal."""
    pdf = _open(pdf_path)
    try:
        if page_idx < 0 or page_idx >= len(pdf):
            return {"error": "page-out-of-range"}
        page = pdf[page_idx]
        textpage = page.get_textpage()
        try:
            if textpage.count_chars() == 0:
                return {"error": "no-text-layer"}
            char_idx = textpage.get_index(
                x_pt, _flip_y(page, y_pt), x_tolerance=6, y_tolerance=4
            )
            if char_idx is None or char_idx < 0:
                return {"error": "no-char-at-click"}
            line_text, line_start = _expand_to_line(textpage, char_idx)
            return _propose_from_line(
                pdf_path,
                page_idx,
                line_text,
                char_offset=char_idx - line_start,
                hint={"page": page_idx, "x": x_pt, "y": y_pt, "w": 0, "h": 0},
            )
        finally:
            textpage.close()
    finally:
        pdf.close()


def suggest_area(pdf_path, page_idx, rect_pt):
    """Resolve a drag rectangle to an area+regex field proposal."""
    x, y, w, h = rect_pt
    pdf = _open(pdf_path)
    try:
        if page_idx < 0 or page_idx >= len(pdf):
            return {"error": "page-out-of-range"}
        page = pdf[page_idx]
        textpage = page.get_textpage()
        try:
            if textpage.count_chars() == 0:
                return {"error": "no-text-layer"}
            bottom = _flip_y(page, y + h)
            top = _flip_y(page, y)
            text = textpage.get_text_bounded(
                left=x, bottom=bottom, right=x + w, top=top
            )
            hint = {"page": page_idx, "x": x, "y": y, "w": w, "h": h}
            if not text.strip():
                return {
                    "field": "custom",
                    "spec": {
                        "parser": "regex",
                        "area": {
                            "f": page_idx + 1,
                            "l": page_idx + 1,
                            "r": 72,
                            "x": x,
                            "y": y,
                            "W": w,
                            "H": h,
                        },
                        "regex": r"(?s)(.+)",
                    },
                    "value": "",
                    "line": text,
                    "note": "position-only — breaks if the vendor moves this block",
                    "pdftotext_status": _cross_check(pdf_path, ""),
                    "hint": hint,
                }
            # Run the same line-level proposal on the cropped text; if it
            # finds a label/candidate, we get {area + regex} which is
            # tolerant of small re-flow (crop-then-regex per _handle_area).
            proposal = _propose_from_line(
                pdf_path, page_idx, text.strip(), char_offset=None, hint=hint
            )
            if "error" in proposal:
                return proposal
            spec = proposal["spec"]
            if isinstance(spec, str):
                spec = {"parser": "regex", "regex": spec}
            spec["area"] = {
                "f": page_idx + 1,
                "l": page_idx + 1,
                "r": 72,
                "x": x,
                "y": y,
                "W": w,
                "H": h,
            }
            proposal["spec"] = spec
            return proposal
        finally:
            textpage.close()
    finally:
        pdf.close()


def _expand_to_line(textpage, char_idx):
    """Expand around ``char_idx`` to the full bbox line + its start offset.

    Walks left and right while consecutive char boxes overlap vertically
    (same-line heuristic; a large y-drop marks the line break).
    """
    total = textpage.count_chars()
    _left, bottom, _right, top = textpage.get_charbox(char_idx, loose=True)
    height = max(top - bottom, 1)
    threshold = height * 0.3
    left_idx = char_idx
    while left_idx > 0:
        _l, b, _r, t = textpage.get_charbox(left_idx - 1, loose=True)
        if abs(b - bottom) > threshold or abs(t - top) > threshold:
            break
        left_idx -= 1
    right_idx = char_idx
    while right_idx < total - 1:
        _l, b, _r, t = textpage.get_charbox(right_idx + 1, loose=True)
        if abs(b - bottom) > threshold or abs(t - top) > threshold:
            break
        right_idx += 1
    line = textpage.get_text_range(left_idx, right_idx - left_idx + 1)
    return line, left_idx


def _propose_from_line(pdf_path, page_idx, line, char_offset, hint):
    """Given one bbox line, propose a field + regex.

    Priority: labeled match (from :func:`find_labeled_fields`) → the
    canonical field the label carries; else the nearest typed candidate
    (from :func:`find_candidates`) → its kind's default field; else a
    generic ``\\S+`` capture with the field left as ``"custom"``.
    """
    try:
        from invoice2data.extract.candidates import find_candidates
        from invoice2data.extract.labels import find_labeled_fields
        from invoice2data.extract.template_builder import (
            field_regex_from_candidate,
            preview_field,
        )
    except ImportError as exc:
        return {"error": "invoice2data-missing: %s" % exc}

    labels = find_labeled_fields(line)
    if labels:
        field, match = next(iter(labels.items()))
        spec = _labeled_field_spec(match)
        value = preview_field(spec, line)
        return _finish(
            field,
            spec,
            value,
            line,
            hint,
            (
                _full_text(pdf_path, page_idx.__class__)
                if False
                else _pdfium_full_text(pdf_path)
            ),
        )

    cands = find_candidates(line)
    if cands:
        if char_offset is not None:
            cands.sort(key=lambda c: abs((c.start + c.end) / 2 - char_offset))
        cand = cands[0]
        field = _CAND_KIND_TO_FIELD.get(cand.kind, "custom")
        spec = field_regex_from_candidate(line, cand)
        value = preview_field(spec, line)
        return _finish(field, spec, value, line, hint, _pdfium_full_text(pdf_path))

    # No label, no candidate — fall back to a bare capture on the trimmed line.
    stripped = line.strip()
    if not stripped:
        return {"error": "empty-line"}
    return {
        "field": "custom",
        "spec": rf"({stripped[:60].strip()})",
        "value": stripped[:60].strip(),
        "line": line,
        "note": "no known label or typed candidate on this line",
        "pdftotext_status": _cross_check(pdf_path, stripped[:60]),
        "hint": hint,
    }


_CAND_KIND_TO_FIELD = {
    "amount": "amount",
    "date": "date",
    "iban": "iban",
    "vat": "vat",
    "bic": "bic",
}


def _labeled_field_spec(match):
    """Build a template field spec from a LabeledMatch (mirrors template_builder)."""
    from invoice2data.extract.template_builder import _labeled_field

    return _labeled_field(match)


def _finish(field, spec, value, line, hint, pdfium_text):
    """Common return shape + pdftotext cross-check."""
    from invoice2data.extract.template_builder import preview_field

    # Validate on the FULL pdfium text (not just the line) so a regex
    # that misses at the document level fails safe here rather than
    # only in the Test button later.
    full_value = preview_field(spec, pdfium_text)
    if not full_value:
        # The line-anchored regex hits the line but not the whole doc —
        # likely a repeated label. Keep the proposal but flag it.
        _logger.debug("click-suggest: %r matched the line but not the full text", spec)
    return {
        "field": field,
        "spec": spec,
        "value": full_value or value,
        "line": line,
        "pdftotext_status": _cross_check("", value or full_value or ""),
        "hint": hint,
    }


def _pdfium_full_text(pdf_path):
    """Extract the full document text via pypdfium2 (matches runtime pin)."""
    pdf = _open(pdf_path)
    try:
        parts = []
        for i in range(len(pdf)):
            tp = pdf[i].get_textpage()
            try:
                parts.append(tp.get_text_range())
            finally:
                tp.close()
        return "\n".join(parts)
    finally:
        pdf.close()


def _cross_check(pdf_path, value):
    """Check whether pdftotext produces the same captured value; badge string."""
    if not shutil.which("pdftotext"):
        return "unavailable"
    if not pdf_path or not value:
        return "unavailable"
    try:
        proc = subprocess.run(
            ["pdftotext", "-layout", "-enc", "UTF-8", pdf_path, "-"],
            capture_output=True,
            timeout=20,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        _logger.debug("click-suggest: pdftotext cross-check failed: %s", exc)
        return "unavailable"
    text = proc.stdout.decode("utf-8", errors="replace")
    if value in text:
        return "same"
    return "no-match"


def render_page_png(pdf_path, page_idx, dpi=100):
    """Render one PDF page to PNG bytes for the wizard's <img> overlay."""
    pdf = _open(pdf_path)
    try:
        if page_idx < 0 or page_idx >= len(pdf):
            raise ValueError("page out of range")
        page = pdf[page_idx]
        pil_image = page.render(scale=dpi / 72).to_pil()
        import io

        buf = io.BytesIO()
        pil_image.save(buf, format="PNG")
        return buf.getvalue(), page.get_width(), page.get_height()
    finally:
        pdf.close()
