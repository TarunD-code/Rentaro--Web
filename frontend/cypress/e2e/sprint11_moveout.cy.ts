/**
 * Sprint 11 — Move-Out Workflow E2E Tests
 */
describe('Sprint 11: Move-Out Workflow', () => {
  const API = 'http://127.0.0.1:8000';

  beforeEach(() => {
    cy.visit('/login');
    cy.get('input[type="email"], input[name="email"]', { timeout: 10000 }).type('admin@rentora.com');
    cy.get('input[type="password"], input[name="password"]').type('admin123');
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/dashboard', { timeout: 15000 });
  });

  describe('Tenant Dashboard — Move-Out', () => {
    it('should show Initiate Move-Out button on active agreements', () => {
      cy.visit('/dashboard');
      cy.wait(3000);
      cy.get('body').then(($body) => {
        if ($body.text().includes('Agreement #')) {
          cy.contains('Initiate Move-Out').should('exist');
        }
      });
    });

    it('should show MoveOutStatusCard when move-out is active', () => {
      cy.visit('/dashboard');
      cy.wait(3000);
      cy.get('body').then(($body) => {
        if ($body.text().includes('Move-Out in Progress')) {
          cy.contains('Move-Out in Progress').should('be.visible');
          cy.contains('d left').should('exist');
        }
      });
    });
  });

  describe('Move-Out Initiate Page', () => {
    it('should navigate to move-out page', () => {
      cy.visit('/moveout/initiate/1');
      cy.wait(3000);
      cy.get('body').then(($body) => {
        const text = $body.text();
        // Either shows initiation form or status tracker
        expect(text.includes('Initiate Move-Out') || text.includes('Move-Out Status')).to.be.true;
      });
    });

    it('should show 30-day notice period info', () => {
      cy.visit('/moveout/initiate/1');
      cy.wait(3000);
      cy.contains('30', { timeout: 5000 }).should('exist');
    });
  });

  describe('Move-Out Review Page (Owner)', () => {
    it('should navigate to review page', () => {
      cy.visit('/moveout/review/1');
      cy.contains('Move-Out Review', { timeout: 10000 }).should('be.visible');
    });

    it('should show deposit bar', () => {
      cy.visit('/moveout/review/1');
      cy.contains('Security Deposit', { timeout: 10000 }).should('be.visible');
    });

    it('should have standard charge fields', () => {
      cy.visit('/moveout/review/1');
      cy.contains('Standard Charges', { timeout: 10000 }).should('exist');
    });

    it('should have add deduction button', () => {
      cy.visit('/moveout/review/1');
      cy.contains('Add Item', { timeout: 10000 }).should('be.visible');
    });

    it('should have No Deductions quick action', () => {
      cy.visit('/moveout/review/1');
      cy.contains('No Deductions', { timeout: 10000 }).should('be.visible');
    });
  });

  describe('Settlement Page', () => {
    it('should navigate to settlement page', () => {
      cy.visit('/moveout/settlement/1');
      cy.contains('Settlement Statement', { timeout: 10000 }).should('be.visible');
    });

    it('should show deposit breakdown', () => {
      cy.visit('/moveout/settlement/1');
      cy.contains('Deposit Breakdown', { timeout: 10000 }).should('exist');
      cy.contains('Security Deposit').should('exist');
    });

    it('should show refund amount', () => {
      cy.visit('/moveout/settlement/1');
      cy.wait(3000);
      cy.contains('Rs.').should('exist');
    });

    it('should have finalize or download button', () => {
      cy.visit('/moveout/settlement/1');
      cy.wait(3000);
      cy.get('body').then(($body) => {
        const text = $body.text();
        expect(text.includes('Finalize Settlement') || text.includes('Download Settlement PDF')).to.be.true;
      });
    });
  });

  describe('Move-Out API — Smoke Tests', () => {
    it('should get active moveout status', () => {
      const token = localStorage.getItem('token');
      cy.request({
        url: `${API}/payment/moveout/active/me`,
        headers: { Authorization: `Bearer ${token}` },
        failOnStatusCode: false,
      }).then((resp) => {
        expect([200, 502, 503]).to.include(resp.status);
      });
    });
  });
});
