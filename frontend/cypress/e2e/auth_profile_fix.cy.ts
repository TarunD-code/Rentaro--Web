describe('Admin Profile Bug Fix Validations', () => {
    it('successfully logs in as admin, avoids logout loop on profile, mapping properly', () => {
        // Step 1: Login sequence via manual credentials
        cy.visit('http://localhost:5173/login');
        cy.get('input[name="email_or_phone"]').type('admin@rentora.com'); 
        cy.get('input[name="password"]').type('testing'); // Mock pass for test suite configs
        cy.contains('Sign In').click();

        // Step 2: Ensure redirect correctly lands on Admin dashboard, checking injected 'admin' string
        cy.url().should('include', '/dashboard');
        cy.contains('Admin Control Center').should('be.visible');

        // Step 3: Trigger navigation to profile
        // Wait briefly for network idle to stabilize localStorage injections
        cy.wait(500);
        cy.contains('Profile').click();

        // Step 4: Validate Profile does not crash or redirect back to login!
        cy.url().should('include', '/profile');
        cy.contains('Account Settings').should('be.visible');
        
        // Ensure UI components are rendered and profile fetch block passed gracefully
        cy.contains('Update Settings').should('exist');
    });
});
