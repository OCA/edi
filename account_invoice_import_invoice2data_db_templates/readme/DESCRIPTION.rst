This module extends *Account Invoice Import Invoice2data* with **DB-stored
templates** and a **GUI editor** for authoring them.

It implements the long-standing roadmap item the parent module references
as *"An graphical template builder"*: instead of (or alongside) the
disk-loaded ``invoice2data_templates_dir`` set, accountants can author
templates directly in Odoo. Each ``invoice2data.template`` record is
merged into the lib's template list at import time, so the cascade
behaviour is unchanged.

Two authoring modes live side by side:

* **Guided** -- fill in *Name*, *Keywords* and a list of *Fields*
  (canonical invoice2data field names, regex or static value, optional
  ``replace`` pair, opt-in ``extract_number`` flag for text-mixed
  numerics). The JSON is composed from those on save.
* **Power user** -- paste a full invoice2data JSON template into the
  *JSON* tab; the *Fields* tab is then ignored.

A **Suggest fields** button uses the lib's authoring helpers
(``invoice2data.extract.template_builder.suggested_template`` and the
label-detection helpers) to pre-fill the field grid from the latest
attached PDF -- the "guessing framework" the parent module's 2017 TODO
list asked for.
