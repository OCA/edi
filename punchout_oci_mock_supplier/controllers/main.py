# Copyright 2025 Bosd
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from urllib.parse import urlparse

from odoo.http import Controller, request, route

# Mock product catalog. Mirrors the spread of UoMs the punchout module's
# 6-tier resolution chain handles, so the end-to-end demo exercises every
# code path on a real cart.
MOCK_PRODUCTS = [
    {
        "vendormat": "MOCK-EA-001",
        "description": "Steel Bracket (UNECE EA)",
        "longtext": "Galvanised steel L-bracket, 50×50×3 mm. UNECE 'EA' unit.",
        "unit": "EA",
        "price": "12.50",
        "leadtime": "3",
    },
    {
        "vendormat": "MOCK-PCE-002",
        "description": "Hex Bolt M8 (UNECE PCE)",
        "longtext": "Stainless A2 hex bolt, M8×20 mm. UNECE 'PCE' unit.",
        "unit": "PCE",
        "price": "0.45",
        "leadtime": "1",
    },
    {
        "vendormat": "MOCK-M-003",
        "description": "Cable, 2.5 mm² (global M mapping)",
        "longtext": "Stranded copper cable per metre. Tests M -> meter mapping.",
        "unit": "M",
        "price": "1.20",
        "leadtime": "2",
    },
    {
        "vendormat": "MOCK-L-004",
        "description": "Hydraulic Oil ISO 32 (global L mapping)",
        "longtext": "Anti-wear hydraulic oil, sold per litre.",
        "unit": "L",
        "price": "5.99",
        "leadtime": "5",
    },
    {
        "vendormat": "MOCK-KG-005",
        "description": "Welding Powder (global KG mapping)",
        "longtext": "Submerged-arc welding flux, sold by the kilogram.",
        "unit": "KG",
        "price": "8.40",
        "leadtime": "7",
    },
]


def _is_safe_hook_url(url):
    """Only POST back to the same Odoo instance.

    Without this, a public mock could be abused to relay OCI POSTs to
    arbitrary URLs.
    """
    if not url:
        return False
    base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url") or ""
    if base_url and url.startswith(base_url):
        return True
    parsed = urlparse(url)
    return parsed.hostname in ("127.0.0.1", "localhost")


class PunchoutOciMockSupplierController(Controller):
    @route(
        "/punchout_oci_mock_supplier/catalog",
        type="http",
        auth="public",
        methods=["GET"],
        csrf=False,
    )
    def catalog(self, **kwargs):
        """Render a fake supplier catalog page for the OCI buyer to browse."""
        hook_url = kwargs.get("HOOK_URL", "")
        return request.env["ir.qweb"]._render(
            "punchout_oci_mock_supplier.catalog_page",
            {
                "hook_url": hook_url,
                "hook_url_safe": _is_safe_hook_url(hook_url),
                "products": MOCK_PRODUCTS,
            },
        )

    @route(
        "/punchout_oci_mock_supplier/checkout",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def checkout(self, **kwargs):
        """Build the OCI form-POST that the browser auto-submits to HOOK_URL."""
        hook_url = kwargs.get("hook_url", "")
        if not _is_safe_hook_url(hook_url):
            return request.make_response(
                "Refusing to POST OCI cart to a non-local HOOK_URL.",
                status=400,
                headers=[("Content-Type", "text/plain")],
            )

        selected = []
        for product in MOCK_PRODUCTS:
            qty_raw = (kwargs.get(f"qty_{product['vendormat']}") or "0").strip()
            try:
                qty = float(qty_raw)
            except ValueError:
                qty = 0.0
            if qty > 0:
                selected.append({"product": product, "qty": qty})

        if not selected:
            return request.make_response(
                "No items selected — go back and set a quantity on at least one row.",
                status=400,
                headers=[("Content-Type", "text/plain")],
            )

        oci_fields = []
        for index, entry in enumerate(selected, start=1):
            p = entry["product"]
            qty = entry["qty"]
            for oci_key, value in (
                ("DESCRIPTION", p["description"]),
                ("MATNR", p["vendormat"]),
                ("VENDORMAT", p["vendormat"]),
                ("QUANTITY", f"{qty:g}"),
                ("UNIT", p["unit"]),
                ("PRICE", p["price"]),
                ("CURRENCY", "EUR"),
                ("LEADTIME", p["leadtime"]),
                ("LONGTEXT", p["longtext"]),
            ):
                oci_fields.append(
                    {
                        "name": f"NEW_ITEM-{oci_key}[{index}]",
                        "value": value,
                    }
                )
        return request.env["ir.qweb"]._render(
            "punchout_oci_mock_supplier.checkout_interstitial",
            {"hook_url": hook_url, "oci_fields": oci_fields},
        )
