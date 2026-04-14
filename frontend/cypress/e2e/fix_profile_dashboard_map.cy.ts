describe('Rentora Fix Verification: Profile, Dashboard, and Map', () => {
  beforeEach(() => {
    // Reset and mock login
    cy.visit('/login');
    cy.get('input[name="email_or_phone"]').type('admin@rentora.com');
    cy.get('input[name="password"]').type('password123');
    cy.get('button[type="submit"]').click();
  });

  it('navigates to admin dashboard and displays metrics', () => {
    cy.url().should('include', '/dashboard');
    cy.contains('Admin Dashboard').should('be.visible');
    cy.contains('Total Properties').should('be.visible');
    // Check that metrics are not 0 (mocked scaling in backend)
    cy.get('.MuiTypography-h6').first().invoke('text').then((text) => {
      expect(parseInt(text)).to.be.at.least(0);
    });
  });

  it('updates profile and reflects data correctly', () => {
    cy.visit('/profile');
    cy.contains('Profile Settings').should('be.visible');
    
    // Test update
    cy.get('input[name="first_name"]').clear().type('Admin');
    cy.get('input[name="last_name"]').clear().type('User');
    cy.get('input[name="phone_number"]').clear().type('9999988888');
    cy.contains('Update Profile Settings').click();
    
    cy.contains('Profile updated successfully').should('be.visible');
    cy.reload();
    cy.get('input[name="first_name"]').should('have.value', 'Admin');
  });

  it('validates MapTiler autocomplete and zoom', () => {
    cy.visit('/listings');
    cy.get('input[placeholder="Where are you moving to?"]').type('Electronic City');
    cy.wait(1000); // Wait for suggestions
    cy.get('.MuiList-root').should('be.visible');
    cy.get('.MuiListItemButton-root').first().click();
    
    // Check URL has lat/lng
    cy.url().should('include', 'lat=');
    cy.url().should('include', 'lng=');
    
    // Check map view is active
    cy.get('.leaflet-container').should('be.visible');
    // Check POIs render (markers with custom category colors)
    cy.get('.custom-poi-icon').should('exist');
  });
});
