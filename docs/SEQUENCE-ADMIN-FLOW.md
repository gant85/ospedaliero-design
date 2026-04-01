# Admin User Flow (AH-OSP-admin)

This document describes the administrative interactions within the system, based on the `User Flow AH-OSP-admin.png` diagram. It focuses on Role-Based Access Control (RBAC), context switching to view specific client data, and management operations.

## Sequence Diagram

![Admin User Flow Diagram](diagrams/sequence-admin-flow.puml)

## Flow Description

1. **Authentication & Authorization**:
   - The user authenticates via Microsoft Entra ID. The Laravel BFF evaluates the Entra ID claims/roles.
   - Access to the `/admin` prefix and associated APIs is strictly gated based on these centralized roles.

2. **Context Switching (Impersonation Pattern)**:
   - Unlike standard users who see only their own facility's data, Administrators have a "Client Selection" step in their flows (`Invoices`, `DDT`, `Order History`, `Report`, etc.).
   - The BFF acts as an intermediary, requesting the external APIs to return data scoped to the selected `client_id` or `facility_id`, overriding the user's default context but maintaining auditability.

3. **Administration Tasks**:
   - The "Administration" menu unlocks features like user management, file imports (*Import Hospital Data*), and modifying news/offers (*Offers Management*).
   - When an Administrator updates global configurations like Offers or News via the BFF, the BFF notifies the underlying external APIs and is responsible for invalidating the local **Redis Cache** so that regular users see the updated banners and news feeds immediately.
