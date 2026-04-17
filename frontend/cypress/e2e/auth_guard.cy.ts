describe('Authentication Guard & Redirection', () => {
  beforeEach(() => {
    // Clear localStorage to ensure a clean state
    cy.clearLocalStorage();
  });

  it('redirects unauthenticated users from root to login', () => {
    cy.visit('/');
    cy.url().should('include', '/login');
    cy.contains('Login').should('be.visible');
  });

  it('redirects unauthenticated users from dashboard to login', () => {
    cy.visit('/dashboard');
    cy.url().should('include', '/login');
    cy.contains('Login').should('be.visible');
  });

  it('allows authenticated users to access the dashboard', () => {
    // Mock a successful login or set token manually
    localStorage.setItem('token', 'mock_token');
    localStorage.setItem('role', 'tenant');
    
    cy.visit('/dashboard');
    cy.url().should('include', '/dashboard');
    cy.contains('Tenant Dashboard').should('be.visible');
  });

  it('redirects to dashboard if already logged in when visiting root', () => {
    localStorage.setItem('token', 'mock_token');
    localStorage.setItem('role', 'owner');
    
    cy.visit('/');
    cy.url().should('include', '/dashboard');
    cy.contains('Owner Dashboard').should('be.visible');
  });

  it('blocks admin routes for non-admin users', () => {
    localStorage.setItem('token', 'mock_token');
    localStorage.setItem('role', 'tenant');
    
    cy.visit('/reconciliation');
    // Should redirect back to dashboard since tenant is not 'admin'
    cy.url().should('include', '/dashboard');
  });
});
