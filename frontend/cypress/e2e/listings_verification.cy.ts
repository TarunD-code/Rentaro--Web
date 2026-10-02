describe('Rentora Listings E2E Verification', () => {
  beforeEach(() => {
    cy.clearLocalStorage();
    cy.window().then((win) => {
      win.sessionStorage.clear();
    });
    
    // Perform login with correct credentials
    cy.visit('/login');
    cy.get('input[name="email_or_phone"]').type('admin@rentaro.com');
    cy.get('input[name="password"]').type('admin123');
    cy.get('button[type="submit"]').click();
    
    // Should redirect to dashboard
    cy.url().should('include', '/dashboard');
  });

  it('Verifies listings grid view rendering and data display', () => {
    cy.visit('/listings');
    
    // Wait for loading screen to clear
    cy.contains('Loading Rentora...').should('not.exist');
    
    // Initially Grid view should be selected and grid container should be visible
    cy.get('button[value="grid"]').should('have.class', 'Mui-selected');
    cy.get('.MuiGrid-container').should('exist');
    
    // Ensure we have property cards listed
    cy.get('.MuiPaper-root').should('exist');
    cy.contains('Luxury Sea-View Apartment in Bandra').should('be.visible');
    cy.contains('Cozy 1BHK in Indiranagar').should('be.visible');
  });

  it('Verifies toggle to map view and leaflet initialization', () => {
    cy.visit('/listings');
    cy.contains('Loading Rentora...').should('not.exist');
    
    // Toggle to map view
    cy.get('button[value="map"]').click();
    cy.get('button[value="map"]').should('have.class', 'Mui-selected');
    
    // Verify leaflet map is initialized and container is visible
    cy.get('.leaflet-container').should('be.visible');
  });

  it('Verifies navigation to property details page', () => {
    cy.visit('/listings');
    cy.contains('Loading Rentora...').should('not.exist');
    
    // Wait for the grid container to load
    cy.get('.MuiGrid-container', { timeout: 10000 }).should('exist');
    cy.contains('Luxury Sea-View Apartment in Bandra', { timeout: 10000 }).click();
    
    // Verify it navigates to property details (usually /listings/:id)
    cy.url().should('match', /\/listings\/\d+/);
    cy.contains('Mumbai').should('be.visible');
    cy.contains('Luxury Sea-View Apartment in Bandra').should('be.visible');
  });
});
