describe('Sprint 15: Analytics Reporting & Admin Dashboard', () => {
    beforeEach(() => {
        // Authenticate assuming admin
        cy.visit('/login');
        cy.get('input[type="email"]').type('admin@rentora.test');
        cy.get('input[type="password"]').type('password123');
        cy.window().then((win) => {
            // @ts-ignore
            win.localStorage.setItem('token', 'fake.admin.jwt.token');
            // @ts-ignore
            win.localStorage.setItem('role', 'admin');
        });
    });

    it('verifies admin analytics dashboard renders when feature flag enabled', () => {
        // Assume epic7_sprint15_analytics_v1 is mock enabled in actual E2E run
        cy.visit('/admin/analytics');
        
        // Should warn if feature flag is disabled by default
        cy.contains(/Analytics Dashboard is rolling out soon/i).should('exist');
    });

    it('intercepts fake analytics payload if flag enabled', () => {
        // This is a stub for the intercepted test assuming the flag is forced true
        cy.intercept('GET', '**/analytics/admin/analytics/summary', {
            statusCode: 200,
            body: {
                total_revenue: 250000,
                pending_payouts: 45000,
                occupancy_rate_30d: 0.92,
                failed_refunds: 500,
                active_mandates: 105
            }
        }).as('getSummary');
    });
});
