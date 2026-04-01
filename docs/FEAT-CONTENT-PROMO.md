# Content Management & Promotional Engine

This functional flow covers the **AREA SERVIZI**, **PROMOZIONI**, and **LISTINI** macro-areas. It highlights workflows exclusively driven by the Administrator role, emphasizing how configuration states propagate to standard users.

## Covered Features
- **ID 9**: Heavy payload handling for "Importazione Ospedaliero" price lists.
- **ID 24**: Formative and Informative content insertion.
- **ID 25**: Management of generalized notices, news, and modular content.
- **ID 27, 29**: UI-scoped promotional banners and advertisements.
- **ID 28**: Customer-specific targeted pricing configurations (Slated for Phase 2).

## Sequence Diagram

![Content & Promo Engine Operations](diagrams/sequence-feat-content-promo.puml)

## Flow Details

1. **Mass Ingestion**: Large imports like the *Ospedaliero* listini bypass simple JSON payloads in favor of Multipart-form streaming directly to the ERP processing engine, ensuring the BFF remains memory-efficient.
2. **Content Lifecycle**: Administrators creating documents, news, or videos interact with the internal CMS. Any publication mandates that the BFF explicitly flushes the Redis Cache, ensuring standard users see the latest alerts immediately.
3. **Promotions & Dynamic Pricing (Phase 2)**: Configuring Promotional boxes visually pairs with deep-rooted pricing manipulations. When a standard user logs in, the BFF aggregates statically cached Ad-slots with dynamically calculated personalized pricing models sourced from the remote ERP.
