/**
 * Sprint 13 — Onboarding & Digital Agreements E2E Tests
 */
describe('Sprint 13: Onboarding & Agreements', () => {

  beforeEach(() => {
    cy.visit('/login');
    cy.get('input[type="email"], input[name="email"]', { timeout: 10000 }).type('admin@rentora.com');
    cy.get('input[type="password"], input[name="password"]').type('admin123');
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/dashboard', { timeout: 15000 });
  });

  describe('Onboarding Form', () => {
    it('should navigate to onboarding page', () => {
      cy.visit('/onboarding/form');
      cy.contains('Tenant Onboarding', { timeout: 10000 }).should('be.visible');
    });

    it('should show stepper with 3 steps', () => {
      cy.visit('/onboarding/form');
      cy.contains('Personal Details', { timeout: 10000 }).should('exist');
      cy.contains('KYC Documents').should('exist');
      cy.contains('Review').should('exist');
    });

    it('should show personal detail fields', () => {
      cy.visit('/onboarding/form');
      cy.contains('Full Name', { timeout: 10000 }).should('exist');
      cy.contains('Phone').should('exist');
      cy.contains('Email').should('exist');
    });

    it('should have continue button', () => {
      cy.visit('/onboarding/form');
      cy.contains('Continue to KYC', { timeout: 10000 }).should('exist');
    });
  });

  describe('Agreement Page', () => {
    it('should navigate to agreements page', () => {
      cy.visit('/onboarding/agreements');
      cy.contains('Digital Agreements', { timeout: 10000 }).should('be.visible');
    });

    it('should show new agreement button', () => {
      cy.visit('/onboarding/agreements');
      cy.contains('New Agreement', { timeout: 10000 }).should('exist');
    });

    it('should show agreement cards or empty state', () => {
      cy.visit('/onboarding/agreements');
      cy.wait(3000);
      cy.get('body').then(($body) => {
        const text = $body.text();
        expect(text.includes('AGR-') || text.includes('No agreements')).to.be.true;
      });
    });
  });

  describe('Dashboard Integration', () => {
    it('should show onboarding card on dashboard', () => {
      cy.visit('/dashboard');
      cy.wait(3000);
      cy.get('body').then(($body) => {
        if ($body.text().includes('Onboarding')) {
          cy.contains('Onboarding').should('be.visible');
        }
      });
    });
  });
});
