# Notification Engine Architecture

This document describes the foundational architecture fulfilling the **NOTIFICATION** feature requirement, standardizing how asynchronous events are served to the user across all application states.

## Covered Features
- **ID 26**: Unified Notifications dealing with Sent Carts, Abandoned Carts, Availability Restocks, New Documents, and General News alerts.

## Sequence Diagram

![Notification Engine Flow](diagrams/sequence-feat-notifications.puml)

## Flow Details

1. **Decoupled Ingestion**: External services (ERP, Inventory, Document Generators) never hit the frontend directly. They emit domain events into a Message Broker.
2. **Alert resolution**: The dedicated Notification microservice isolates the logic for user-targeting. Should a product restock, it identifies all users who requested an availability alert.
3. **Delivery Mechanism**: 
   - The BFF handles real-time syncing via WebSockets (e.g. Laravel Echo or Server-Sent Events).
   - Alternatively, a graceful fallback API polling fetches `/unread` counters.
4. **Deep Linking**: Read acknowledgment endpoints seamlessly couple with redirection logic to transport users directly to the impacted area (the populated cart, the specific order status, the newly generated invoice).
