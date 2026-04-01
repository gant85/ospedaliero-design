# Tasks & Notifications Flow (AH-OSP-tasks)

This document describes the workflow for tasks and system notifications as outlined in the `User Flow AH-OSP-tasks.png` analysis. The system differentiates between standard notifications (like status updates) and actionable tasks (like order approvals).

## Sequence Diagram

![Tasks User Flow Diagram](diagrams/sequence-tasks-flow.puml)

## Flow Description

1. **Order Approval Tasks**:
   - Standard users who lack direct ordering permissions must submit an "Order Approval Request".
   - The BFF coordinates with the External APIs to generate an actionable "Task" assigned to the associated Super User.
   - When the Super User logs in, the BFF fetches unread notifications and tasks, displaying them in the Header. Note that resolving this task programmatically finalizes the blocked order.

2. **Automated Status Notifications**:
   - **Product Restock**: A user can subscribe to an out-of-stock item. Once the external inventory system notifies the Notification Service of availability, an alert is queued for the user.
   - **Order Lifecycle**: As orders progress through internal states (*Preso in carico, Lavorazione, Spedito*), the External APIs push events to the Notification Service, which the Vue SPA polls via the Laravel BFF to display toast messages or header badges.

3. **BFF Acting as Aggregator**:
   - In all these flows, the Laravel BFF is responsible for abstracting the underlying microservices (Orders API, Inventory API, Notifications API) into a single, cohesive `/api/notifications` endpoint for the Vue SPA.
