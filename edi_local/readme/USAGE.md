## Manage headers

Headers define how EDI local lines are grouped and ordered.

1. Go to Settings > Technical > EDI > Edi local header.
2. Create or edit a header.
3. Set the sequence, code, and name.
4. Save.

The module includes a default header with code `gen` and name `General`.

## Generate text files

1. Go to Settings > Technical > EDI > Edi local.
2. Create or open an EDI local configuration.
3. Set Type to `Out`.
4. Select the target model.
5. Define the domain in Apply on.
6. Select a file sequence in Filename.
7. Set the local output directory in Dir File.
8. Add header lines in the Headers tab.
9. If needed, select a one2many or many2many field and add detail lines in the Lines tab.
10. Enable the configuration.
11. Click Test generate file to validate the configured lines without writing the final file.
12. Click Generate file.

  ![EDI LOCAL GENERATE FILE](../static/readme/edi_local_generate_file.png)

Generated files are stored in the configured output directory and posted in the record chatter.

## Import text files

1. Go to Settings > Technical > EDI > Edi local.
2. Create or open an EDI local configuration.
3. Set Type to `In`.
4. Select the target model.
5. If importing from a directory, set Dir Import File.
6. If importing from attachments, add `.txt` attachments.
7. Add header and line mappings.
8. Enable the configuration.
9. Click Test read file to validate the import reading process.
10. Click Import file.

  ![EDI LOCAL IMPORT FILE](../static/readme/edi_local_import_file.png)

Only files with the `.txt` extension are accepted by the current file type.

## Scheduled processing

The module provides two inactive scheduled actions:

- Edi Local: Generate files
- Edi Local: Import files

CRON will only run on configurations that meet one of the following conditions:

1. Outbound type: Must be enabled and the domain must be valid.

2. Inbound type: Must be enabled.

  ![EDI LOCAL CRON](../static/readme/edi_local_cron.png)

