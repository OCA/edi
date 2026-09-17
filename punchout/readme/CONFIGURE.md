To configure this module:

1. Go to **Settings > Technical > PunchOut > PunchOut Backends**
2. Create a new backend record with:
   - **Name**: A unique identifier for this supplier connection
   - **Description**: Human-readable description
   - **Protocol**: Select the punchout protocol (cXML, OCI, or IDS - requires
     additional modules)
   - **URL**: The supplier's punchout setup URL
   - **Browser form post URL**: The callback URL where the supplier sends the
     shopping cart (can be relative like `/punchout/cxml/receive/`)
   - **Session duration**: Maximum time (in seconds) a punchout session is valid

3. Configure protocol-specific credentials (requires Administrator access):
   - cXML: From/To identities, SharedSecret
   - OCI: Custom vendor parameters
   - IDS: Customer name, number, and password

4. Optionally add UoM mappings to translate supplier unit codes to Odoo UoMs

**Note**: Backend configuration and credential fields are restricted to users with
the `Administration/Settings` permission group for security reasons.
