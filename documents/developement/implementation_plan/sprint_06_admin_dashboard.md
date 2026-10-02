# Sprint 6: Implementation Plan — Admin Dashboard & Analytics

## Goal
Build admin dashboard with platform metrics, user management, and owner analytics (HostAnalytics).

## Proposed Changes

### 1. Admin Dashboard
- Platform-wide metrics: total users, properties, agreements, revenue
- User management table with role badges
- Property moderation tools
- Admin-only route protection

### 2. Owner Analytics (HostAnalytics)
- Property occupancy rates
- Revenue tracking and trends
- Agreement status overview
- Metrics cards with icons and gradients

### 3. Dashboard Routing
- Role-based dashboard rendering: TenantDashboard, OwnerDashboard, AdminDashboard
- Separate dashboard components per role

## Verification
- Admin login → See platform metrics → Manage users
- Owner login → See HostAnalytics with property stats
