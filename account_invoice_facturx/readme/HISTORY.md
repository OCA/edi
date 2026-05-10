## Unreleased

### Features

- Add `_cii_get_line_period(iline)` extension hook on `account.move`,
  used to populate the line-level `BillingSpecifiedPeriod` block (BG-26,
  "Invoice line period") for the `EN16931` and `EXTENDED` profiles. The
  default implementation transparently picks up either
  `deferred_start_date` / `deferred_end_date` from Odoo Enterprise's
  `account_accountant` module (detected at runtime via `_fields`, no
  hard dependency added) or `start_date` / `end_date` from the OCA
  module `account_invoice_start_end_dates`. Subscription and recurring
  billing modules can override the hook to inject their own date
  fields without patching the line generator.
- Add a Schematron-based test suite that exercises all five Factur-X
  profiles (`MINIMUM`, `BASICWL`, `BASIC`, `EN16931`, `EXTENDED`)
  through the bundled `factur-x` library. Two scenarios (default
  invoice, invoice with line-level discount) plus the BG-26
  subscription scenario above ensure that the produced XML stays
  schematron-clean across all profiles.

### Fixes

- The `BASIC` profile now emits a non-empty
  `ApplicableHeaderTradeDelivery` block with an
  `ActualDeliverySupplyChainEvent/OccurrenceDateTime` child (BT-72),
  fixing both `PEPPOL-EN16931-R008` ("document MUST not contain empty
  elements") and `BR-FX-EN-04` ("Each invoice must contain a delivery
  date or invoicing period"). The delivery date is read through the
  existing `_cii_get_delivery_date()` hook so the source field is not
  re-decided here.
- The `MINIMUM` profile no longer emits
  `BuyerTradeParty/PostalTradeAddress` and
  `BuyerTradeParty/SpecifiedTaxRegistration`. Those elements are marked
  as "not used" by the `MINIMUM` schematron, while the corresponding
  `SellerTradeParty` blocks are kept because `MINIMUM` does require BT-31
  (Seller VAT identifier).
- The line-level `GrossPriceProductTradePrice/AppliedTradeAllowanceCharge`
  block no longer emits `CalculationPercent` and `BasisAmount` in the
  `EN16931` profile. Those two children are explicitly marked as "not
  used" by the EN 16931 schematron and were causing two failures per
  discounted line. The `EXTENDED` profile keeps emitting them.
