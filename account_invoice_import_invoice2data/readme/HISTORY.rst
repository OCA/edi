
14.0.2.5.0 (2026-08-02)
~~~~~~~~~~~~~~~~~~~~~~~

* [FIX] Restore compatibility with invoice2data >= 1.0. The pre-1.0 API
  path ``invoice2data.main`` was removed upstream; import from
  ``invoice2data`` directly.
* [IMP] Surface actionable errors: on a matched-but-incomplete template,
  the wizard now shows the template name + the specific fields that
  could not be parsed (via ``raise_on_error=True`` and the new typed
  exceptions ``NoTemplateFoundError`` / ``RequiredFieldsMissingError`` /
  ``TemplateSyntaxError``).
* [IMP] Log which template matched (``template_name``, added in
  invoice2data 1.0) alongside the extracted result.

14.0.2.2.0 (2023-03-03)
~~~~~~~~~~~~~~~~~~~~~~~

* [ADD] Support for invoicelines.
  (`#74 <https://github.com/OCA/edi/issues/568>`_)
