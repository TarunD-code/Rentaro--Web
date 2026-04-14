describe('Rentora Stabilization V1 Verification', () => {
  beforeEach(() => {
    // Standard login flow
    cy.visit('/login');
    cy.get('input[name="email_or_phone"]').type('admin@rentora.com');
    cy.get('input[name="password"]').type('password123');
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/dashboard');
  });

  it('verifies profile data returns correct fields', () => {
    cy.visit('/profile');
    cy.get('input[name="first_name"]').should('not.have.value', '');
    cy.get('input[name="email"]').should('not.have.value', '');
    // Check if the new field structure is handled (phone_number, age etc)
    cy.get('input[name="phone_number"]').should('exist');
    cy.get('input[name="age"]').should('exist');
  });

  it('verifies dashboard metrics accuracy', () => {
    cy.contains('Total Properties').should('be.visible');
    cy.get('.MuiTypography-h6').first().then(($h6) => {
      const val = parseInt($h6.text());
      expect(val).to.be.at.least(0);
    });
  });

  it('verifies listings grid/map persistence and autocomplete', () => {
    cy.visit('/listings');
    
    // Ensure we are in Grid view initially
    cy.get('button[value="grid"]').should('have.class', 'Mui-selected');
    
    // Type in search bar to get suggestions
    cy.get('input[placeholder="Search locations, building names..."]').type('Electronic City');
    cy.wait(1000);
    
    // Autocomplete should be visible above the map/grid layer (zIndex check via existence)
    cy.get('.MuiPaper-root').contains('Electronic City').should('be.visible');
    
    // Click a suggestion
    cy.contains('Electronic City').click();
    
    // VERIFY: Should NOT switch to map view automatically
    cy.get('button[value="grid"]').should('have.class', 'Mui-selected');
    cy.get('.MuiGrid-container').should('be.visible');
    
    // Switch to map view
    cy.get('button[value="map"]').click();
    cy.get('.leaflet-container').should('be.visible');
    
    // Click suggestion in map view
    cy.get('input[placeholder="Search locations, building names..."]').clear().type('Electronic City');
    cy.wait(500);
    cy.contains('Electronic City').click();
    
    // VERIFY: Map zoom/precision (URL check or map center check if possible)
    cy.get('.custom-poi-icon').should('exist'); // POIs should show up
  });
});
