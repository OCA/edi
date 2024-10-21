- Add operator in template lines (= or ilike)
- Simplify auto-detection (defining a text only to search the system
  should search the corresponding regular expression).
- Allow compatibility with registration process created from email alias
  (for purchase order for example).
- Remove error if some file is not auto-detected template, options:
  boolean (default option according to system parameter) to omit error
  for not found files or change process to 2 steps, auto-detect and show
  lines (each one with respect to a file) with template applied (similar
  to dms_auto_classification).
- Create test_base_import_pdf_simple module with sale, purchase and
  account dependencies to leave templates created in runboat and tests
  more useful for testers.
- Display a more readable error if there is an error in Preview process,
  example: wrong pattern. Message: "Please check template defined, some
  items are not correctly set".
- Add a progress bar (widget=“gauge”) in the import wizard process,
  useful if we import for example sales orders with 20 lines and thus
  know the progress.

Compatibility with csv, xls, etc:

- Separate much of the logic to new module base_import_simple that would
  contain the logic of templates, type of files (csv, excel, etc) in the
  templates and wizard and this module would depend on the other adding
  only what relates to PDF.
- The base module should take into account for each template whether
  each line is a new record or not, and start line (in case you want to
  omit any), only page 1 would be imported.
- The preview smart-btton would serve exactly the same purpose.
- In the case of csv and Excel that each record is a line, the document
  will NOT be attached to the record.
- If you indicate that each record is a line the column will be the key,
  otherwise you must specify to which line each line of the template
  refers.
- In the case of csv it will try to auto-detect the lines and columns
  (no need to complicate delimiters configuration).
- The menu "Import PDF" of the favorite menu would become "Import file",
  and the allowed file extensions would be those obtained from a method
  (it would be extended by other modules that add other formats such as
  PDF).
- Add queue_job_base_import_simple module to process everything by
  queues (example: Excel with hundreds of lines, each one a record).
