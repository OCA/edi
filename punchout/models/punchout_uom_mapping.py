# Copyright 2023 ACSONE SA/NV
# Copyright 2025 Bosd (migration to 18.0)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PunchoutUomMapping(models.Model):
    """Map supplier-specific UoM codes to Odoo UoMs.

    A mapping may be scoped to a backend, to a supplier, or global (both
    scopes unset). Resolution priority (highest wins):

    1. Backend-specific mapping (backend_id set)
    2. Supplier-specific mapping (supplier_id set, backend_id unset)
    3. Global mapping (both unset)
    4. UNECE code match on ``uom.uom.unece_code`` (via uom_unece)
    5. ``uom.uom.name`` match (case-insensitive)
    6. No match — caller picks the default
    """

    _name = "punchout.uom.mapping"
    _description = "Punchout UoM Mapping"

    backend_id = fields.Many2one(
        comodel_name="punchout.backend",
        ondelete="cascade",
        index=True,
        help="Mapping only applies to this backend. Leave empty for a "
        "supplier-wide or global mapping.",
    )
    supplier_id = fields.Many2one(
        comodel_name="res.partner",
        string="Supplier",
        ondelete="cascade",
        index=True,
        help="Mapping applies to any backend using this supplier. Ignored "
        "when a backend is set. Leave empty for a global mapping.",
    )
    supplier_code = fields.Char(
        required=True,
        help="The UoM code used by the supplier in punchout responses.",
    )
    uom_id = fields.Many2one(
        comodel_name="uom.uom",
        string="UoM",
        required=True,
        ondelete="restrict",
        help="The Odoo UoM to use for products with this supplier code.",
    )
    notes = fields.Text(
        help="Optional notes about this mapping.",
    )

    @api.constrains("supplier_code")
    def _check_supplier_code(self):
        for rec in self:
            if not rec.supplier_code or not rec.supplier_code.strip():
                raise ValidationError(
                    _("Supplier code cannot be empty for mapping %(name)s")
                    % {"name": rec.display_name}
                )

    @api.constrains("backend_id", "supplier_id", "supplier_code")
    def _check_unique_scope(self):
        """Prevent duplicate mappings within the same scope.

        SQL-level UNIQUE treats NULLs as distinct, so we enforce uniqueness
        in Python where any combination of backend/supplier scope (including
        both unset) must be unique on ``supplier_code``.
        """
        for rec in self:
            if not rec.supplier_code:
                continue
            domain = [
                ("id", "!=", rec.id),
                ("supplier_code", "=", rec.supplier_code),
                ("backend_id", "=", rec.backend_id.id or False),
                ("supplier_id", "=", rec.supplier_id.id or False),
            ]
            if self.search_count(domain):
                raise ValidationError(
                    _(
                        "A mapping for supplier code %(code)s already exists "
                        "for this scope."
                    )
                    % {"code": rec.supplier_code}
                )

    @api.depends("supplier_code", "uom_id", "backend_id", "supplier_id")
    def _compute_display_name(self):
        for rec in self:
            scope = []
            if rec.backend_id:
                scope.append(_("Backend: %s") % rec.backend_id.display_name)
            elif rec.supplier_id:
                scope.append(_("Supplier: %s") % rec.supplier_id.display_name)
            else:
                scope.append(_("global"))
            code = rec.supplier_code or ""
            uom = rec.uom_id.display_name or ""
            rec.display_name = f"{code} → {uom} ({', '.join(scope)})"

    @api.model
    def _get_uom_by_supplier_code(self, backend, supplier_code, supplier=None):
        """Resolve a supplier UoM code to an ``uom.uom`` record.

        Follows the 6-tier resolution described in the class docstring.
        Returns an empty recordset if no match is found; the caller decides
        the default.
        """
        UomUom = self.env["uom.uom"]
        if not supplier_code:
            return UomUom.browse()

        code = supplier_code.strip()
        if supplier is None and backend:
            supplier = backend.partner_id

        # 1. Backend-specific mapping
        if backend:
            mapping = self.search(
                [
                    ("backend_id", "=", backend.id),
                    ("supplier_code", "=", code),
                ],
                limit=1,
            )
            if mapping:
                return mapping.uom_id

        # 2. Supplier-specific mapping (not pinned to a backend)
        if supplier:
            mapping = self.search(
                [
                    ("backend_id", "=", False),
                    ("supplier_id", "=", supplier.id),
                    ("supplier_code", "=", code),
                ],
                limit=1,
            )
            if mapping:
                return mapping.uom_id

        # 3. Global mapping
        mapping = self.search(
            [
                ("backend_id", "=", False),
                ("supplier_id", "=", False),
                ("supplier_code", "=", code),
            ],
            limit=1,
        )
        if mapping:
            return mapping.uom_id

        # 4. UNECE code (uppercase match against uom_unece data)
        uom = UomUom.search([("unece_code", "=", code.upper())], limit=1)
        if uom:
            return uom

        # 5. UoM name (case-insensitive)
        uom = UomUom.search([("name", "=ilike", code)], limit=1)
        if uom:
            return uom

        # 6. No match — caller picks the default
        return UomUom.browse()
