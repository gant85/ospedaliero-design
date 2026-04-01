# Clients Configuration & Context Validation

This functional flow covers the **Gestione Clienti** capabilities and the complex **Context Switching** scenarios required by Super Users and Administrators.

## Covered Features
- **ID 3**: Clients Management (Configurations).
- **ID 4**: ERP/CRM Integration (Maintaining continuity with Korian systems).
- **ID 5**: Facilities/Sedi Management (Configurations).
- **ID 7**: Facility context-switch for Super Users.
- **ID 20**: Client/Facility search functionality during Administrator tasks (e.g., Invoices).

## Sequence Diagram

![Clients Configuration & Context Switch](diagrams/sequence-feat-context-clients.puml)

## Flow Details

1. **ERP/CRM Integration**: The BFF serves as a passthrough validation layer, polling or synchronizing client and facility (Sedi) metadata dynamically from the legacy ERP/CRM backend (Korian).
2. **Context Selection API**: Because Super Users and Administrators are allowed to 'act as' another client or facility, a generic context-switching API allows the frontend to persist a temporary target context.
3. **Data Request Tunneling**: When the user queries data downstream (like Orders or Invoices), the BFF overrides the default identity query parameters with the active context selected in step 2.
