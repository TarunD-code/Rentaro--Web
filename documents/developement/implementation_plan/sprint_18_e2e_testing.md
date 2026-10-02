# E2E Testing Plan

To ensure Rentora is highly stable, we will create comprehensive end-to-end (E2E) tests. Because Rentora has many microservices, I propose we start by automating tests for our most recent and critical flows: **Featured Listings** and **Notifications**, along with core **Authentication**.

## Proposed Testing Phases

### Phase 1: Core Event Flow & Notifications (Current Focus)
We will write API-level E2E tests using `pytest` and `httpx` that interact directly with the API Gateway to simulate full user journeys.

- **Test Case 1**: Owner Login -> Retrieve Token.
- **Test Case 2**: Create a Property -> Verify it appears in the listing without a featured badge.
- **Test Case 3**: Purchase "Gold" Featured Listing -> Simulate checkout via Billing Service.
- **Test Case 4**: Verify Property Status -> Ensure `is_featured = True` on the Property Service.
- **Test Case 5**: Verify Notification -> Ensure a "Property Featured!" notification was created in the Notification Service for the owner.

### Phase 2: Frontend UI Automation (Using Browser Agent)
After verifying the API layer, I will use the browser automation agent to launch the Vite frontend and perform the exact same flow visually:
- Click the **Notifications** bell to ensure it drops down.
- Verify the **Gold Badge** renders on the property card.
