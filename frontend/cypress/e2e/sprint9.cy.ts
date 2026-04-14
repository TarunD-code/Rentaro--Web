describe('Digital Agreement Workflow', () => {
    beforeEach(() => {
        cy.visit('http://localhost:5173/login');
        // Admin user logs in to bypass strict auth simulation logic for E2E
        cy.get('input[type="text"]').type('testing'); 
        cy.get('input[type="password"]').type('testing');
        cy.contains('Sign In').click();
    });

    it('Owner Generates Agreement -> Both parties sign -> Contract verifies', () => {
        // Assume jumping directly to property listing
        cy.visit('http://localhost:5173/listings/1');

        // Initial Generation by Owner/Admin
        cy.contains('Generate Agreement').click();

        // Redirects to workflow interface automatically
        cy.url().should('include', '/agreements/');
        cy.contains('Rental Agreement Workflow').should('be.visible');

        // Check PDF Download Draft button properties
        cy.contains('Download PDF (draft)').should('be.visible');

        // Sign contract
        cy.contains('Sign with E-Sign').click();

        // Mock sign callback alert bypass
        cy.on('window:alert', (str) => {
            expect(str).to.include('Signed successfully');
        });

        // View signed cryptographic hash injected in UI
        cy.contains('legally active').should('be.visible');
        cy.contains('Cryptographic Checksum').should('be.visible');
    });
});
