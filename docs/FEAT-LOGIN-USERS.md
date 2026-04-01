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
2. **User Administration & Role Management**: User roles are not managed in the application's local database. Application-level roles and group memberships are exclusively managed through Microsoft Entra ID. When a user's group is changed or a role is added/removed in Entra, Microsoft Entra ID triggers session and token invalidation, requiring the user to re-authenticate and fetch updated permissions.
3. **Multi-PDV Super Users**: While the "Super User" role itself is granted via Entra ID, Administrators can specify which multiple PDVs (Points of Sale/Facilities) that Super User is allowed to view. This mapping is managed in the application extending their visibility.
