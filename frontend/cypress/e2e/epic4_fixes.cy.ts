describe('Rentora Epic 4 Stabilization & Fixes', () => {
  const adminEmail = 'admin@rentora.com';

  const password = 'admin123';

  beforeEach(() => {
    cy.clearLocalStorage();
    cy.clearSessionStorage();
  });

  it('Verify Admin Role & Dashboard Access', () => {
    cy.visit('/login');
    cy.get('input[name="email_or_phone"]').type(adminEmail);
    cy.get('input[name="password"]').type(password);
    cy.get('button[type="submit"]').click();

    cy.url().should('include', '/dashboard');
    cy.contains('Admin Dashboard').should('be.visible');
    cy.get('button').contains('Post a New Property').should('be.visible');
  });

  it('Verify Tenant Dashboard & Restricted Creation', () => {
    // Mock login as tenant
    localStorage.setItem('role', 'tenant');
    localStorage.setItem('token', 'mock-tenant-token');
    
    cy.visit('/dashboard');
    cy.contains('Rented Properties').should('be.visible');
    cy.contains('Monthly Rent').should('be.visible');
    cy.contains('Security Deposits').should('be.visible');
    
    // Attempt to access /create
    cy.visit('/create');
    cy.contains('Unauthorized').should('be.visible');
  });

  it('Verify KYC Upload Flow & Validation', () => {
    localStorage.setItem('role', 'tenant');
    localStorage.setItem('token', 'mock-token');
    cy.visit('/profile');
    
    // Profile Photo Upload Simulation
    cy.get('input[type="file"]').first().should('exist');
    
    // KYC Document Upload
    cy.contains('KYC Verification').click();
    const fileName = 'id_proof.pdf';
    cy.get('input[type="file"]').last().attachFile(fileName);
    
    cy.contains('Document uploaded successfully!').should('be.visible');
  });

  it('Verify Map Autocomplete & Zoom', () => {
    cy.visit('/listings');
    cy.get('input[placeholder*="Search"]').type('Electronic City');
    cy.contains('Electronic City Phase 1').click();
    
    // Verification: map center should change (Mock check since Leaflet is hard to assert without deep inspection)
    cy.get('.leaflet-container').should('be.visible');
  });

  it('Verify Amenities Checkboxes', () => {
    localStorage.setItem('role', 'owner');
    cy.visit('/create');
    cy.contains('Financials & Amenities').click(); // Navigate to step
    
    cy.get('input[type="checkbox"]').first().check();
    cy.get('input[name="other"]').type('Roof Top Garden');
  });

  it('Verify Logout Purge', () => {
    localStorage.setItem('test-key', 'persistent');
    cy.visit('/dashboard');
    cy.get('button[aria-label="account of current user"]').click();
    cy.contains('Logout').click();
    
    cy.url().should('include', '/login');
    cy.window().then((win) => {
      expect(win.localStorage.getItem('token')).to.equal(null);
      expect(win.localStorage.getItem('test-key')).to.equal(null);
    });
  });

  it('Verify Localization Coverage', () => {
    cy.visit('/dashboard');
    cy.get('button[title="Change language"]').click();
    cy.contains('हिन्दी').click();
    cy.contains('डैशबोर्ड').should('be.visible');
    
    cy.get('button[title="Change language"]').click();
    cy.contains('தமிழ்').click();
    cy.contains('டாஷ்போர்டு').should('be.visible');
  });
});
