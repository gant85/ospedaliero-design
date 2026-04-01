# Shopping Cart, Document Fulfillment & Reporting

This functional flow covers the **ORDERS**, **INVOICES**, **DDT**, and **REPORT** macro-areas. It tracks the chronological progression logically from Cart Assembly to Order Fulfillment, followed by Document Retrieval (Invoices/Delivery Notes) and finally Analytical Reporting.

## Covered Features
- **ID 17**: Core Cart functionality.
- **ID 18**: Routing orders specifically through internal hospital warehouses.
- **ID 19**: Invoice visualization and export.
- **ID 21**: Delivery Notes (DDT - Documento di Trasporto) retrieval.
- **ID 22**: Historical Orders logging.
- **ID 23**: Advanced Analysis and Report exports.

## Sequence Diagram

![Orders & Documentation Operations](diagrams/sequence-feat-orders-docs.puml)

## Flow Details

1. **Cart & Fulfillment Pathing**: The cart API allows the user front-end to explicitly denote the sourcing context (e.g. `source=hospital_warehouse`). The BFF passes this flag to the underlying Order Engine ensuring the logistics network processes it correctly upon checkout.
2. **Historical Financial Documents**: For querying strictly immutable data like historical Invoices and Delivery Notes, the BFF acts as an elegant proxy piping generated PDFs from the backend ERP/Billing engines directly to the user's browser, preventing unnecessary intermediate storage.
3. **Analytics Export Engine**: A specialized request path exists for the Analytics dashboard. The BFF gathers aggregated matrix responses for visual charts in the UI while offering a dedicated `/export` mechanism where the underlying microservice processes intensive Excel/CSV stream generations.
