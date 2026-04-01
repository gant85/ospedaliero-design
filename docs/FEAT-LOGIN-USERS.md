# Authentication & User Provisioning

This functional flow covers the **Login** and **User Management** macro-areas identified from the integration features.

## Covered Features
- **ID 1**: Login via "ENTRA" system.
- **ID 2**: Management of new user registration within the portal.
- **ID 6**: User Management (creation/modification).
- **ID 8**: Assignment of Super User roles over multiple Points of Sale (PDV).

## Login Sequence Diagram

![Authentication & User Provisioning](diagrams/sequence-feat-login-users.puml)

## Flow Details

1. **ENTRA Login & Provisioning**: The application delegates all authentication directly to Microsoft Entra ID (OIDC). If a user logs in for the first time successfully and wasn't manually pre-provisioned, the BFF creates a local DB record for the user (Feature 2) via JIT (Just-In-Time) provisioning. If the user was already created proactively by an administrator, the BFF simply maps the incoming Entra profile to the locally stored profile.
2. **Session & Token Management**: The Laravel BFF securely manages the Entra ID tokens (Access & Refresh Tokens) internally, issuing an HTTP-only secure session cookie to the Vue SPA. This completely shields the frontend from token complexity. When an access token expires, Laravel automatically and transparently uses the **Refresh Token** to obtain a new access token from Entra ID before forwarding any requests to the underlying APIs or Microservices.
3. **User Administration & Role Management**: User roles are not managed in the application's local database. Application-level roles and group memberships are exclusively managed through Microsoft Entra ID. When a user's group is changed or a role is added/removed in Entra, Microsoft Entra ID triggers session and token invalidation, requiring the user to re-authenticate and fetch updated permissions.
4. **Multi-PDV Super Users**: While the "Super User" role itself is granted via Entra ID, Administrators can specify which multiple PDVs (Points of Sale/Facilities) that Super User is allowed to view. This mapping is managed in the application extending their visibility.

## Admin User Management Flow

![Admin User Management](diagrams/sequence-admin-users.puml)

### Proactive User Management

5. **Proactive User Creation (Admin)**: Instead of waiting for a user to log in to perform JIT provisioning, an Administrator can proactively create or invite a new user via the Backoffice interface ("User Management"). The Vue SPA collects the user profile (Email, Name, Role, Facilities mapped) and sends it to the BFF. The BFF interacts with Microsoft Entra ID via the Graph API to provision the user (or dispatch an invite) and assigns the correct Entra Group based on the chosen Role.
6. **User Modification & Deletion**: Modifying an existing user (such as changing their role) results in the BFF updating their group assignment directly via Entra ID Graph API. Entra ID then triggers token/session revocation. Deletions or disablements are synchronized directly with Entra ID.
