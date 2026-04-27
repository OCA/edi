**Important Security Considerations**

Due to the nature of punchout protocols (cXML, OCI, IDS), authentication credentials
must be transmitted through the user's browser when redirecting to supplier websites.
This means:

- **cXML**: The SharedSecret and identity credentials are sent in the POST body to
  the supplier's punchout URL. Users with browser developer tools can view this data
  in the Network tab.

- **OCI**: Vendor-specific authentication parameters may be included in URL query
  strings, making them visible in the browser address bar.

- **IDS**: Customer credentials (name, number, password) are sent via POST form data
  to the supplier, visible in browser developer tools.

**This is an inherent limitation of punchout protocols, not a bug.**

**Recommendations:**

1. Only enable punchout access for trusted users who need procurement functionality
2. Use the Odoo permission system to restrict access:
   - Backend configuration requires `Administration/Settings` group
   - Session data is only visible to administrators
3. Use HTTPS for all punchout communications
4. Regularly rotate credentials with suppliers
5. Consider using IP allowlisting on the supplier side if available
