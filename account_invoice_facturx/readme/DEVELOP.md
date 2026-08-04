## Extension hooks

The XML generator exposes two pure methods on `account.move` that are
specifically intended to be inherited by other modules. Both return data
that controls the content of the produced Factur-X / ZUGFeRD XML, never
the XML structure itself, so overrides do not have to know the schema.

### `_cii_get_delivery_date(self)`

Returns the date that is exported as the actual delivery / service date
of the invoice (BT-72 in the EN 16931 vocabulary, mapped to XPath
`/CrossIndustryInvoice/SupplyChainTradeTransaction/ApplicableHeaderTradeDelivery/ActualDeliverySupplyChainEvent/OccurrenceDateTime`,
namespace prefixes elided as is conventional in EN 16931 documentation).

Default implementation returns `self.invoice_date`. Override in modules
that store a dedicated delivery / service date on the invoice header
(for example a Goods Issue date from a Stock module, or a service
completion date from a custom workflow).

The element is emitted in the `BASIC`, `EN16931` and `EXTENDED`
profiles only (the `MINIMUM` and `BASICWL` profiles do not allow it).

### `_cii_get_line_period(self, iline)`

Returns a `(start_date, end_date)` tuple representing the service period
of a single invoice line (BG-26 "Invoice line period", mapped to XPath
`IncludedSupplyChainTradeLineItem/SpecifiedLineTradeSettlement/BillingSpecifiedPeriod`
with `StartDateTime` and `EndDateTime` children, relative to the
`SupplyChainTradeTransaction` root).

Default implementation looks for two well-known field sets on
`account.move.line`, in order of precedence:

1. `deferred_start_date` / `deferred_end_date`, provided by Odoo
   Enterprise's `account_accountant` module. The check is performed at
   runtime via `account.move.line._fields`, so this OCA module does not
   gain a hard dependency on Enterprise code: it simply exposes the
   service period when those fields are available.
2. `start_date` / `end_date`, provided by the OCA module
   `account_invoice_start_end_dates`.

If neither source yields a value, the method returns `(False, False)`
and the caller skips the `BillingSpecifiedPeriod` element entirely.

Override in subscription, recurring billing or contract modules that
store the service period in dedicated fields. Example:

```python
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _cii_get_line_period(self, iline):
        if iline.my_subscription_period_id:
            return (
                iline.my_subscription_period_id.date_start,
                iline.my_subscription_period_id.date_end,
            )
        return super()._cii_get_line_period(iline)
```

The element is emitted in the `EN16931` and `EXTENDED` profiles only,
matching what BG-26 allows in the Factur-X schematron.

## Profile constants

The module defines `PROFILES_EN_UP = ("en16931", "extended")` to gate
elements that are reserved to EN 16931 and EXTENDED. All five profiles
(`MINIMUM`, `BASICWL`, `BASIC`, `EN16931`, `EXTENDED`) are exercised by
the test suite so contributors can rely on the constant rather than
re-introducing per-profile branches by hand.
