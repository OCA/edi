Adds support for UNECE unit codes during UBL invoice import to automatically detect and
assign the appropriate unit of measure or product packaging on invoice lines.

When a UNECE code matches a product packaging, the packaging is set with priority.
Otherwise, the corresponding unit of measure is applied based on the UNECE code.
