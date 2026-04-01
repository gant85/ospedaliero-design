# Main User Flow (AH-OSP)

This document describes the primary user interactions flowing through the system, based on the `User Flow AH-OSP.png` diagram. It illustrates how the frontend (Vue SPA) interacts with the Laravel Backend-for-Frontend (BFF), orchestrating requests to Microsoft Entra ID for authentication and external APIs for application data.

## Sequence Diagram

![Main User Flow Diagram](diagrams/sequence-main-flow.puml)

## Flow Description

1. **Authentication & Initialization**:
   - The user seamlessly logs in via **Microsoft Entra ID** (OAuth2/OIDC).
   - Upon successful login, the BFF retrieves user identity data to determine if they are a 'Super User'.
   - Super users must perform a 'Scelta Struttura' (Facility Selection) before entering the home page.

2. **Dashboard Assembly (Home Page)**:
   - When loading the home page, the BFF asynchronously gathers required data chunks: *News*, *Banners*, and *Latest Orders*.
   - Redis caching is utilized heavily for static or semi-static content like communications and marketing banners to improve load times.

3. **Products & Cart**:
   - The user browses products through the Vue interface, fetching real-time availability via the BFF.
   - Adding products updates the centralized session and external cart APIs, immediately reflecting changes in the application Header.

4. **Order Finalization**:
   - Depending on the user's explicit permissions loaded during authentication, they can either finalize the order directly, or submit a request for finalization that a Super User must subsequently approve.
