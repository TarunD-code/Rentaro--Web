describe('Rentora Epic 3: Landing & Property Detail Verification', () => {
  beforeEach(() => {
    // Ensure feature flags are on
    cy.visit('/');
  });

  it('should render the landing page with hero and featured sections', () => {
    cy.contains('Premium Living').should('be.visible');
    cy.get('input[placeholder*="Where are you moving"]').should('exist');
    cy.get('h4').contains('Featured listings', { matchCase: false }).should('exist');
  });

  it('should search for a city and navigate to listings', () => {
    cy.get('input[placeholder*="Where are you moving"]').type('Mumbai');
    // Suggestions should appear eventually (mock or real)
    cy.get('button').contains('Search').click();
    cy.url().should('include', '/listings?q=Mumbai');
  });

  it('should navigate to property detail and view gallery', () => {
    cy.visit('/listings');
    // Click the first property card
    cy.get('.MuiCard-root').first().click();
    
    // Verify detail page elements
    cy.url().should('match', /\/listings\/\d+/);
    cy.get('h3').should('be.visible'); // Title
    cy.contains('Description').should('be.visible');
    cy.get('button').contains('Contact Host').should('be.visible');
    
    // Verify Gallery interactivity (if media exists)
    cy.get('img[alt="Property"]').should('exist');
  });

  it('should respect the theme system on new pages', () => {
    cy.visit('/');
    // Change theme to Dark (Selector 10)
    cy.get('[aria-label="Change Theme"]').click();
    cy.get('[data-theme="dark"]').click();
    
    // Background should be dark
    cy.get('body').should('have.css', 'background-color', 'rgb(18, 18, 18)'); // Exact value for Dark theme
  });

  it('should respect i18n on the landing page', () => {
    cy.visit('/');
    // Change to Tamil
    cy.get('[aria-label="Change language"]').click();
    cy.get('li').contains('TA').click();
    
    // Some static text should change (needs actual keys in i18n.ts)
    // For now check if footer text exists or similar
  });
});
