# Product Catalog & Content Delivery

This functional flow covers the **PRODOTTO** and **DEPOSITI** macro-areas, defining the data retrieval architecture for browsing pharmacological products and validating complex stock scenarios.

## Covered Features
- **ID 10**: Standard Product Search.
- **ID 11**: Management and querying of backup deposits (off-site/non-hospital).
- **ID 12**: Advanced Medical Search (Search by Active Ingredient/Principle).
- **ID 13**: Viewing of descriptive leaflets / package inserts.
- **ID 14**: User-dictated procurement choices (Sourcing selection).
- **ID 15**: Viewing of Product Photographs.
- **ID 16**: Live updating Catalog ensuring dynamic sync.

## Sequence Diagram

![Product Catalog & Sourcing Strategy](diagrams/sequence-feat-products.puml)

## Flow Details

1. **Complex Search Engine**: The frontend allows users to toggle the search strategy. The request propagates to the BFF which redirects the `active_principle` payload to the specific pharmacological catalog endpoints, enabling medical professionals to find equivalent generic drugs.
2. **Media Rendering**: Assets like product photos and multi-page illustrative leaflets are retrieved securely. The BFF avoids passing massive blobs by fetching secure, ephemeral presigned URLs from the File Storage service.
3. **Multi-tier Inventory Sourcing**: When checking availability, the BFF orchestrates a waterfall request. If the primary intra-hospital supply is exhausted, it transparently queries configured Backup Deposits, allowing the user to select their preferred sourcing timeline.
