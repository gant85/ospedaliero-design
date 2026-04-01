# Ospedaliero Design - Application Flow & Features Overview

This document provides a high-level overview of the complete application flow, integrating all core features and functionalities extracted from the centralized requirements matrix. It maps the end-to-end user journey from authentication through the specialized operational tools available for both Standard Users and Administrators.

## 1. Authentication & Onboarding
*Related Document: [Authentication & User Provisioning](FEAT-LOGIN-USERS.md)*

The journey begins securely through corporate identity management.
- **SSO Login (Feat 1, 2)**: Users authenticate exclusively via Microsoft Entra ID. The system handles Just-In-Time (JIT) provisioning for new users signing into the portal for the very first time.
- **Role Provisioning (Feat 6, 8)**: Administrators can globally manage internal permission levels, including elevating Standard Users to "Super User" status linked dynamically to groups of Points of Sale (PDV).

## 2. Customer Configuration & Context
*Related Document: [Clients Configuration & Context Validation](FEAT-CONTEXT-CLIENTS.md)*

Once authenticated, the system resolves the user's boundaries and operating context geographically and structurally.
- **ERP Synchronization (Feat 3, 4, 5)**: Client rules and facility configurations (Facilities) are seamlessly integrated and maintained in strict synchronization with the legacy Korian ERP/CRM infrastructure.
- **Context Switching (Feat 7, 20)**: Super Users can legally change their active operating facility (*Change Facility*), while Administrators can execute actions impersonating any client globally to deliver support.

## 3. Product Catalog & Sourcing
*Related Document: [Product Catalog & Content Delivery](FEAT-PRODUCTS.md)*

Within the dashboard hub, users explore pharmacological offerings using agile and data-rich interfaces.
- **Dynamic Search (Feat 10, 12, 16)**: An always-updated, live catalog allows users to perform complex programmatic searches by either commercial name or active principle.
- **Rich Media (Feat 13, 15)**: Users can inspect digital assets securely on the platform, ranging from high-fidelity product photos to dense illustrative pharmaceutical leaflets.
- **Advanced Sourcing (Feat 11, 14)**: Users dictate their procurement preferences. The platform validates stocks sequentially against primary hospital warehouses, gracefully falling back to secondary external backup deposits if exhausted.

## 4. Ordering & Document Fulfillment
*Related Document: [Shopping Cart, Document Fulfillment & Reporting](FEAT-ORDERS-DOCS.md)*

The procurement phase transitions seamlessly into logistics and subsequent financial documentation.
- **Cart Checkout (Feat 17, 18)**: Users assemble real-time carts specifically flagged for depletion against selected internal hospital warehouses.
- **Historical Tracing (Feat 19, 21, 22)**: The platform surfaces immutable logistical records. Users can download direct PDF copies of validated Invoices (*Invoices*) and Delivery Notes (*Delivery Notes*), alongside reviewing their comprehensive order histories.
- **Analytical Reporting (Feat 23)**: Powerful aggregated reports surface directly on-screen or can be manually exported (Excel/CSV) for external accounting consolidation.

## 5. Content Management & Promotions (Admin Exclusives)
*Related Document: [Content Management & Promotional Engine](FEAT-CONTENT-PROMO.md)*

Administrators actively shape the portal's content, bridging the gap between strict tabular data and a customized modern UX.
- **Mass Data Imports (Feat 9)**: The foundational ability to ingest massive "Hospital" global pharmaceutical price lists via robust CSV multi-part streaming uploads.
- **Formative Services (Feat 24, 25)**: Administrative Editors can broadcast educational content, modular alerts, and operational news across the portal dynamically.
- **Promotional Ecosystem (Feat 27, 28, 29)**: The graphical interface hosts isolated promotional slots displaying customized products. *Phase 2* ensures these dynamic advertising spaces bind mathematically to targeted, client-specific pricing configurations handled inside the ERP logic.

## 6. Real-Time Notification Engine
*Related Document: [Notification Engine Architecture](FEAT-NOTIFICATIONS.md)*

The system maintains a critical communication thread with users silently in the background, minimizing operational friction.
- **Systematic Alerts (Feat 26)**: A unified pub-sub notification framework orchestrates complex system events—such as products returning in-stock, abandoned cart urgencies, order status lifecycle progressions, and unread news alerts—serving them directly natively to the user's Vue interface.

---

> [!TIP]
> For deep-dive technical sequence diagrams (PlantUML) and granular BFF layer API routing related to any of these flows, please refer to the individual Markdown documents linked under each designated section above.
