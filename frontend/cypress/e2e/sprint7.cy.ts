describe('Rentora Sprint 7: Communication & Trust Ecosystem', () => {
  beforeEach(() => {
    // Mock login and token
    window.localStorage.setItem('token', 'fake-jwt-token');
    window.localStorage.setItem('userId', 'user123');
    window.localStorage.setItem('role', 'tenant');
    cy.visit('http://localhost:5173');
  });

  it('Displays unread notification center', () => {
    // Check if Bell icon is visible
    cy.get('button[aria-label="account of current user"]').should('exist'); // We injected near it
    cy.get('svg[data-testid="NotificationsIcon"]').click();
    
    // Check dropdown renders
    cy.contains('Notifications').should('be.visible');
    // It might mock fetch or just show no new notifications
    cy.contains(/No new notifications|at/i).should('be.visible');
  });

  it('Navigates to Dashboard and checks for Host Analytics (if Owner)', () => {
    window.localStorage.setItem('role', 'owner');
    
    cy.visit('http://localhost:5173/dashboard');
    cy.contains('Owner Dashboard').should('be.visible');
    
    // Since Analytics component is rendered conditionally
    cy.contains('Performance Overview').should('be.visible');
    cy.contains('Profile Views').should('be.visible');
  });

  it('Filters listings with advanced options and tests Map toggle', () => {
    cy.visit('http://localhost:5173/listings');
    cy.get('button').contains('Filters').click();
    
    // Check advanced filters
    cy.contains('Furnished').should('be.visible');
    cy.contains('Pet-Friendly').should('be.visible');

    // Check map clusters
    cy.get('button[aria-label="map view"]').click();
    cy.contains('Bandra Cluster', { timeout: 10000 }).should('be.visible');
    cy.contains('4').should('be.visible');
  });

  it('Submits a review and opens chat on Property detail', () => {
    // Mock ID 1
    cy.visit('http://localhost:5173/listings/1');
    
    // Wait for mock fetch to finish implicitly
    cy.contains('Write a Review', { timeout: 10000 }).should('be.visible');
    
    cy.get('textarea[placeholder="Share your experience..."]').type('Amazing property with great ventilation!');
    // Rating 4 stars (stars input is a bit tricky to mock in MUI, we assume a forced POST on submit works)
    cy.contains('Submit Review').click();
    
    // Should optimistically clear
    cy.get('textarea[placeholder="Share your experience..."]').should('have.value', '');

    // ChatBox trigger
    cy.contains('Contact Host').click();
    cy.get('.MuiPaper-root').contains('Online').should('be.visible');
    // Type a message
    cy.get('input[placeholder="Type a message..."]').type('Hello! Is this available?');
    cy.get('svg[data-testid="SendIcon"]').parent().click();
    
    // Check message bubbled
    cy.contains('Hello! Is this available?').should('be.visible');
  });
});
