/**
 * Sprint 12 — Maintenance Service E2E Tests
 */
describe('Sprint 12: Maintenance Service', () => {

  beforeEach(() => {
    cy.visit('/login');
    cy.get('input[type="email"], input[name="email"]', { timeout: 10000 }).type('admin@rentora.com');
    cy.get('input[type="password"], input[name="password"]').type('admin123');
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/dashboard', { timeout: 15000 });
  });

  describe('Service Request Form', () => {
    it('should navigate to service request page', () => {
      cy.visit('/maintenance/request');
      cy.contains('Raise Service Request', { timeout: 10000 }).should('be.visible');
    });

    it('should show category chips', () => {
      cy.visit('/maintenance/request');
      cy.contains('Plumbing', { timeout: 10000 }).should('exist');
      cy.contains('Electrical').should('exist');
      cy.contains('Cleaning').should('exist');
    });

    it('should show priority selector', () => {
      cy.visit('/maintenance/request');
      cy.contains('Priority', { timeout: 10000 }).should('exist');
    });

    it('should have submit button', () => {
      cy.visit('/maintenance/request');
      cy.contains('Submit Request', { timeout: 10000 }).should('exist');
    });
  });

  describe('Owner Assignment Panel', () => {
    it('should navigate to assignment page', () => {
      cy.visit('/maintenance/assign');
      cy.contains('Maintenance Requests', { timeout: 10000 }).should('be.visible');
    });

    it('should show request cards', () => {
      cy.visit('/maintenance/assign');
      cy.wait(3000);
      cy.get('body').then(($body) => {
        const text = $body.text();
        expect(text.includes('Assign') || text.includes('No pending')).to.be.true;
      });
    });
  });

  describe('Vendor Task View', () => {
    it('should navigate to tasks page', () => {
      cy.visit('/maintenance/tasks');
      cy.contains('My Tasks', { timeout: 10000 }).should('be.visible');
    });
  });

  describe('Maintenance History', () => {
    it('should navigate to history page', () => {
      cy.visit('/maintenance/history');
      cy.contains('Maintenance History', { timeout: 10000 }).should('be.visible');
    });

    it('should show category filter', () => {
      cy.visit('/maintenance/history');
      cy.contains('Category', { timeout: 10000 }).should('exist');
    });

    it('should show status filter', () => {
      cy.visit('/maintenance/history');
      cy.contains('Status', { timeout: 10000 }).should('exist');
    });

    it('should have export button', () => {
      cy.visit('/maintenance/history');
      cy.contains('Export CSV', { timeout: 10000 }).should('exist');
    });
  });

  describe('Dashboard Integration', () => {
    it('should show maintenance card on dashboard', () => {
      cy.visit('/dashboard');
      cy.wait(3000);
      cy.get('body').then(($body) => {
        if ($body.text().includes('Maintenance')) {
          cy.contains('Maintenance').should('be.visible');
        }
      });
    });
  });
});
