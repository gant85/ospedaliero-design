# Authentication & User Provisioning

This functional flow covers the **Login** and **Gestione Utenti** macro-areas identified from the integration features.

## Covered Features
- **ID 1**: Login via "ENTRA" system.
- **ID 2**: Management of new user registration within the portal.
- **ID 6**: User Management (creation/modification).
- **ID 8**: Assignment of Super User roles over multiple Points of Sale (PDV).

## Sequence Diagram

![Authentication & User Provisioning](diagrams/sequence-feat-login-users.puml)

## Flow Details

1. **ENTRA Login & Just-In-Time Provisioning**: The application delegates all authentication directly to Microsoft Entra ID. If a user logs in for the first time successfully, the BFF intercepts the callback and creates a local DB record for the user (Feature 2), acting as a JIT (Just-In-Time) provisioning system.
2. **User Administration**: Administrators utilize specific endpoints within the BFF to manage application-level roles that aren't inherently present in Entra ID (like linking a user to particular hospital departments).
3. **Multi-PDV Super Users**: Administrators can attach multiple PDV (Points of Sale/Facilities) to a single user making them a "Super User," extending their standard visibility.
