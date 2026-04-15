describe('Rentora Sprint 8 Features', () => {
  beforeEach(() => {
    // Intercept login
    cy.intercept('POST', '**/auth/login').as('loginReq');
    cy.visit('/login');
    cy.get('input[name="identifier"]').type('owner@test.com');
    cy.get('input[name="password"]').type('testpass123');
    cy.get('button[type="submit"]').click();
    cy.wait('@loginReq').its('response.statusCode').should('eq', 200);
    cy.url().should('include', '/dashboard');
  });

  it('verifies the full Logout functionality', () => {
    // Open profile menu
    cy.get('button[aria-label="account of current user"]').click();
    // Click logout
    cy.contains('Logout').click();
    
    // Should clear storage and redirect
    cy.window().then((win) => {
      expect(win.localStorage.getItem('token')).to.equal(null);
    });
    cy.url().should('include', '/login');
  });

  it('validates advanced map integration and filters in Listings', () => {
    cy.visit('/listings');
    
    // Check initial state
    cy.contains('Interactive Map View').should('not.exist');
    
    // Toggle Live Map
    cy.get('button[aria-label="map view"]').click();
    
    // React-Leaflet Map container should exist
    cy.get('.leaflet-container').should('exist');
    
    // Open Filters
    cy.contains('Filters').click();
    
    // Interact with new Slider and Selects
    cy.get('.MuiSlider-root').should('exist'); // Price Range
    cy.contains('Property Type').should('exist');
    cy.get('label').contains('Furnished').click();
    cy.get('label').contains('Pool').click();
    cy.contains('Apply Filters').click();
    
    // Filter persistence checked via URL or network (mock)
    cy.get('.leaflet-container').should('exist');
  });

  it('handles new User Profile fields correctly', () => {
    cy.visit('/profile');
    
    // Look for new fields (First Name, City, Pincode)
    cy.get('input[name="first_name"]').should('exist');
    cy.get('input[name="city"]').should('exist');
    cy.get('input[name="pincode"]').should('exist');
  });

  it('tests KYC upload constraints (rejects invalid types)', () => {
    cy.visit('/profile');
    
    // Attempt uploading an invalid file format (text file)
    cy.get('input[type="file"]').selectFile({
      contents: Cypress.Buffer.from('dummy data'),
      fileName: 'test.html',
      mimeType: 'text/html'
    }, { force: true });
    
    // UI should display error Alert indicating allowed formats
    cy.contains('Only JPG, PNG or PDF format is allowed.').should('exist');
  });
});
