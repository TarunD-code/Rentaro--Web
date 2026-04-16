describe('Sprint 16: Real-Time Chat & Communication', () => {
  beforeEach(() => {
    // Mock login and token
    localStorage.setItem('token', 'fake-jwt-token');
    localStorage.setItem('userEmail', 'tenant@rentora.com');
    localStorage.setItem('userRole', 'tenant');
    
    // Visit Chat Page
    cy.visit('/chat');
  });

  it('should load chat history and send a message', () => {
    // Check if sidebar loads contacts
    cy.contains('Rentora Support').should('be.visible');
    cy.contains('Property Owner').should('be.visible').click();

    // Verify typing indicator or online status
    cy.contains('Online').should('be.visible');

    // Send a message
    const testMessage = 'Hello from Cypress Test';
    cy.get('input[placeholder="Type a message..."]').type(testMessage);
    cy.get('button').find('svg[data-testid="SendIcon"]').click();

    // Verify message appears in list
    cy.contains(testMessage).should('be.visible');
  });

  it('should initiate a masked call', () => {
    cy.contains('Property Owner').click();
    
    // Intercept the call request
    cy.intercept('POST', '**/communication/calls/initiate', {
      statusCode: 200,
      body: { success: true, masked_number: "+15550001234" }
    }).as('callInit');

    cy.get('button').find('svg[data-testid="PhoneIcon"]').click();
    
    cy.wait('@callInit');
    cy.on('window:alert', (str) => {
      expect(str).to.equal(`Masked call initiated! You will receive a call on your registered number shortly.`);
    });
  });
});
