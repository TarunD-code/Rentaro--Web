describe('Rentora Remediation Verification Suite', () => {
  const TEST_USER = {
    email: `test_v${Date.now()}@rentora.com`,
    password: 'Password123!',
    fullName: 'Test User 4'
  };

  before(() => {
    // Seed any necessary state if needed
  });

  it('should complete the full KYC lifecycle from not_submitted to verified', () => {
    cy.visit('/register');
    cy.get('input[name="email_or_phone"]').type(TEST_USER.email);
    cy.get('input[name="password"]').type(TEST_USER.password);
    cy.get('button').contains('Sign Up').click();
    
    // Simulate OTP
    cy.url().should('include', '/verify');
    cy.get('input').each((el) => cy.wrap(el).type('1'));
    cy.get('button').contains('Verify').click();
    
    cy.visit('/profile');
    cy.contains('not_submitted', { matchCase: false }).should('exist');
    
    // Upload document
    const fileName = 'test_id.jpg';
    cy.get('input[type="file"]').selectFile({
      contents: Cypress.Buffer.from('file contents'),
      fileName: fileName,
      lastModified: Date.now(),
    }, { force: true });
    
    cy.contains('draft', { matchCase: false }).should('exist');
    cy.get('button').contains('Submit for Review').click();
    cy.contains('pending_review', { matchCase: false }).should('exist');
    
    // Admin Verify Bypass (Mock button in UI)
    cy.get('button').contains('Mock Approve').click();
    cy.contains('verified', { matchCase: false }).should('exist');
  });

  it('should create a property with multiple media files', () => {
    cy.visit('/login');
    // Login with existing owner if needed or use the test user
    cy.get('input[name="email_or_phone"]').type('admin@rentora.com');
    cy.get('input[name="password"]').type('testing123');
    cy.get('[value="owner"]').click();
    cy.get('button').contains('Login').click();

    cy.visit('/create');
    cy.get('input[name="title"]').type('Luxury Penthouse Cypress Test');
    cy.get('input[name="address"]').type('Marine Drive, Mumbai');
    cy.get('textarea[name="description"]').type('Beautiful view of the Arabian Sea');
    cy.get('button').contains('Next').click();
    
    cy.get('input[name="price"]').type('85000');
    cy.get('input[name="amenities"]').type('Pool, Gym, Beach Access');
    cy.get('button').contains('Next').click();
    
    // Select 2 images
    cy.get('input[type="file"]').selectFile([
      { contents: Cypress.Buffer.from('img1'), fileName: 'penthouse1.jpg' },
      { contents: Cypress.Buffer.from('img2'), fileName: 'penthouse2.jpg' }
    ], { force: true });
    
    cy.contains('2 files selected').should('exist');
    cy.get('button').contains('Publish Listing').click();
    
    cy.url().should('include', '/listings');
    cy.contains('Luxury Penthouse Cypress Test').should('exist');
  });

  it('should show search suggestions and apply filters', () => {
    cy.visit('/listings');
    
    // Search Suggestions
    cy.get('input[placeholder*="Search"]').type('Mum');
    cy.contains('Mumbai').should('exist').click();
    cy.get('input[placeholder*="Search"]').should('have.value', 'Mumbai');
    
    // Filters
    cy.get('button').contains('Filters').click();
    cy.get('label').contains('Min Price').parent().find('input').type('50000');
    cy.get('button').contains('Apply').click();
    cy.wait(500);
    // Verify count or items if needed
  });

  it('should toggle favorites and persist state', () => {
    cy.visit('/listings');
    // Login as tenant
    cy.get('button').contains('Profile').click(); // Just check if logged in
    
    cy.get('[aria-label*="Favorite border"]').first().click();
    // Revisit to check persistence
    cy.reload();
    cy.get('[aria-label*="Favorite"] svg').should('have.attr', 'data-testid', 'FavoriteIcon');
  });

  it('should switch between all Indian languages', () => {
    const langs = ['hi', 'ta', 'te', 'kn', 'ml', 'mr', 'bn'];
    cy.visit('/');
    
    langs.forEach(lang => {
      cy.get('[aria-label="Change language"]').click();
      cy.get('li').contains(lang.toUpperCase(), { matchCase: false }).should('exist').click();
      // Verify a key string changes
      if (lang === 'hi') cy.contains('डैशबोर्ड').should('exist');
      if (lang === 'ta') cy.contains('டாஷ்போர்டு').should('exist');
    });
  });
});
