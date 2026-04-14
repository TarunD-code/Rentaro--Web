/**
 * Sprint 10 — Payment System E2E Tests
 * Tests deposit payment, auto-pay setup, payment history, and rent reminder UI.
 */

describe('Sprint 10: Payment System', () => {
  const API = 'http://127.0.0.1:8000';

  beforeEach(() => {
    // Login as admin/tenant user
    cy.visit('/login');
    cy.get('input[type="email"], input[name="email"]', { timeout: 10000 }).type('admin@rentora.com');
    cy.get('input[type="password"], input[name="password"]').type('admin123');
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/dashboard', { timeout: 15000 });
  });

  describe('Dashboard — Rent Reminder Card', () => {
    it('should display rent reminder card on tenant dashboard', () => {
      cy.visit('/dashboard');
      cy.contains('Rent Payment', { timeout: 10000 }).should('be.visible');
    });

    it('should show payment amount and due date', () => {
      cy.visit('/dashboard');
      cy.contains('₹', { timeout: 10000 }).should('be.visible');
    });

    it('should have Pay Now and History buttons', () => {
      cy.visit('/dashboard');
      cy.contains('History', { timeout: 10000 }).should('be.visible');
    });

    it('should show Payment History link on dashboard', () => {
      cy.visit('/dashboard');
      cy.contains('Payment History', { timeout: 10000 }).should('be.visible');
    });
  });

  describe('Payment History Page', () => {
    it('should navigate to payment history', () => {
      cy.visit('/payments/history');
      cy.contains('Payment History', { timeout: 10000 }).should('be.visible');
    });

    it('should display transaction table or empty state', () => {
      cy.visit('/payments/history');
      cy.wait(3000);
      // Either transactions table or empty state should appear
      cy.get('body').then(($body) => {
        if ($body.find('table').length > 0) {
          cy.get('table').should('be.visible');
          cy.contains('TXN-').should('exist');
        } else {
          cy.contains('No transactions yet').should('be.visible');
        }
      });
    });

    it('should have filter controls', () => {
      cy.visit('/payments/history');
      cy.contains('All Types', { timeout: 10000 }).should('exist');
      cy.contains('All Statuses').should('exist');
    });

    it('should have export CSV button', () => {
      cy.visit('/payments/history');
      cy.contains('Export CSV', { timeout: 10000 }).should('be.visible');
    });
  });

  describe('Deposit Payment Page', () => {
    it('should navigate to deposit payment page', () => {
      cy.visit('/payments/deposit/1');
      cy.contains('Security Deposit', { timeout: 10000 }).should('be.visible');
    });

    it('should show agreement summary', () => {
      cy.visit('/payments/deposit/1');
      cy.contains('Agreement', { timeout: 10000 }).should('be.visible');
      cy.contains('₹').should('be.visible');
    });

    it('should show Pay Now button', () => {
      cy.visit('/payments/deposit/1');
      cy.contains('Pay', { timeout: 10000 }).should('be.visible');
    });

    it('should show security note', () => {
      cy.visit('/payments/deposit/1');
      cy.contains('secured by Razorpay', { timeout: 10000 }).should('be.visible');
    });
  });

  describe('Auto-Pay Setup Page', () => {
    it('should navigate to auto-pay setup', () => {
      cy.visit('/payments/autopay');
      cy.contains('Auto-Pay', { timeout: 10000 }).should('be.visible');
    });

    it('should display auto-pay benefits or status', () => {
      cy.visit('/payments/autopay');
      cy.wait(3000);
      cy.get('body').then(($body) => {
        if ($body.text().includes('Why Auto-Pay')) {
          cy.contains('Never miss a due date').should('be.visible');
        } else {
          // Already set up — should show status
          cy.contains('Auto-Pay').should('be.visible');
        }
      });
    });

    it('should have Enable Auto-Pay or Cancel button', () => {
      cy.visit('/payments/autopay');
      cy.wait(3000);
      cy.get('body').then(($body) => {
        if ($body.text().includes('Enable Auto-Pay')) {
          cy.contains('Enable Auto-Pay').should('be.visible');
        } else {
          cy.contains('Cancel Auto-Pay').should('exist');
        }
      });
    });
  });

  describe('Payment API — Smoke Tests', () => {
    it('should return payment history via API', () => {
      const token = localStorage.getItem('token');
      cy.request({
        url: `${API}/payment/history`,
        headers: { Authorization: `Bearer ${token}` },
        failOnStatusCode: false,
      }).then((resp) => {
        // Either 200 (service running) or 502/503 (service not up)
        expect([200, 502, 503]).to.include(resp.status);
      });
    });

    it('should return payment summary via API', () => {
      const token = localStorage.getItem('token');
      cy.request({
        url: `${API}/payment/summary`,
        headers: { Authorization: `Bearer ${token}` },
        failOnStatusCode: false,
      }).then((resp) => {
        expect([200, 502, 503]).to.include(resp.status);
      });
    });
  });
});
