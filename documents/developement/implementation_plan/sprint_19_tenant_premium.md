# Implementation Plan - Sprint 19: Tenant Premium & Concierge

Introduce high-touch services and recurring monetization for tenants through subscriptions and advanced filtering.

## Design Decisions

> [!IMPORTANT]
> To support **geospatial POI proximity** in SQLite, I will implement a mathematical Haversine filter in the application layer. This avoids the need for external spatial database extensions while maintaining accuracy for property searches.

## Proposed Changes

### 1. New Backend Microservices
#### [NEW] [subscription_service](file:///d:/Python%20Projects/Rentaro/subscription_service/main.py)
- **Port**: 8011
- **Logic**: Handles Razorpay subscriptions (recurring billing), invoice history, and the **Concierge Request** workflow.
- **Schema**: `subscriptions`, `invoices`, `concierge_requests`.

#### [NEW] [support_service](file:///d:/Python%20Projects/Rentaro/support_service/main.py)
- **Port**: 8012
- **Logic**: Ticket-based support system with a **Priority Queue** (In-memory/Redis) for premium tenants.
- **SLA**: Real-time status updates for premium tickets.

### 2. Property Service Enhancements
#### [MODIFY] [property_service/models.py](file:///d:/Python%20Projects/Rentaro/property_service/models.py)
- Add columns: `is_verified`, `owner_verified`, `is_furnished`, `is_pet_friendly`.
#### [MODIFY] [property_service/main.py](file:///d:/Python%20Projects/Rentaro/property_service/main.py)
- Update `GET /` to handle boolean flags and POI proximity filtering logic.

### 3. Infrastructure
#### [MODIFY] [gateway/main.py](file:///d:/Python%20Projects/Rentaro/gateway/main.py)
- Register routes for `/subscriptions` and `/support`.

#### [MODIFY] [start.bat](file:///d:/Python%20Projects/Rentaro/start.bat)
- Orchestrate the two new services.

### 4. Frontend Premium Experience
#### [NEW] [SubscriptionLanding.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/pages/tenant/SubscriptionLanding.tsx)
- Modern landing page with plan benefits (Priority Support, Concierge, Advanced Search).
- Integration with Razorpay recurrent checkout.

#### [NEW] [ConciergeModal.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/components/ConciergeModal.tsx)
- Unified request form for viewing coordination and property shortlisting.

#### [MODIFY] [Listings.tsx](file:///d:/Python%20Projects/Rentaro/frontend/src/pages/Listings.tsx)
- Add "Premium Filters" section (Verified, Pet Friendly, POI Distance slider).
