describe('Sprint 6 Features E2E', () => {
  beforeEach(() => {
    // Intercept API calls to mock backend responses
    cy.intercept('GET', '**/profile/', {
      statusCode: 200,
      body: {
        id: 1,
        full_name: 'Test Setup User',
        kyc_status: 'verified',
        age: 30,
        phone_number: '+919876543210'
      }
    }).as('getProfile');

    cy.intercept('PUT', '**/profile/', {
      statusCode: 200,
      body: {
        id: 1,
        full_name: 'Test Verified User',
        kyc_status: 'verified',
        age: 30,
        phone_number: '+919876543210',
        address: '123 Test St'
      }
    }).as('updateProfile');

    cy.intercept('GET', '**/property/search/suggestions?q=Mu*', {
      statusCode: 200,
      body: ['Mumbai', 'Mustang Village']
    }).as('getSuggestions');

    cy.intercept('GET', '**/property/*', {
      statusCode: 200,
      body: [
        {
          id: 1,
          title: 'Sea View Apartment',
          price: 50000,
          address: 'Bandra, Mumbai',
          amenities: 'Pool, Gym'
        }
      ]
    }).as('getProperties');

    cy.intercept('GET', '**/property/favorites', {
      statusCode: 200,
      body: [1]
    }).as('getFavorites');

    // Simulate login
    window.localStorage.setItem('token', 'mock_token');
  });

  it('Verifies profile editing is unlocked for verified users', () => {
    cy.visit('/profile');
    cy.wait('@getProfile');

    // Form fields should not be disabled
    cy.get('input[name="full_name"]').should('not.be.disabled');
    cy.get('input[name="phone_number"]').should('not.be.disabled');

    cy.get('input[name="full_name"]').clear().type('Test Verified User');
    cy.contains('Update Settings').click();

    cy.wait('@updateProfile');
    cy.contains('Profile updated successfully!').should('be.visible');
  });

  it('Verifies the Grid/Map toggle in Listings', () => {
    cy.visit('/listings');
    cy.wait('@getProperties');

    // Grid View is default
    cy.get('button[value="grid"]').should('have.class', 'Mui-selected');
    cy.contains('Sea View Apartment').should('be.visible');

    // Toggle Map
    cy.get('button[value="map"]').click();
    cy.contains('Interactive Map View').should('be.visible');
    cy.contains('Sea View Apartment').should('not.exist');
  });

  it('Verifies autocomplete search suggestions', () => {
    cy.visit('/');
    cy.get('input[placeholder="Where are you moving to?"]').type('Mu');
    
    // Wait for debounce and intercept
    cy.wait('@getSuggestions');
    cy.contains('Mumbai').should('be.visible');
  });

  it('Verifies Dashboard shows saved favorites', () => {
    // Intercept individual property detail call triggered by favorites list
    cy.intercept('GET', '**/property/1', {
      statusCode: 200,
      body: {
        id: 1,
        title: 'Sea View Apartment',
        price: 50000,
        media: []
      }
    }).as('getPropertyDetail');

    cy.visit('/dashboard');
    cy.wait('@getFavorites');
    cy.wait('@getPropertyDetail');

    cy.contains('My Saved Favorites').should('be.visible');
    cy.contains('Sea View Apartment').should('be.visible');
  });
  
  it('Verifies localization switcher loading JSON correctly', () => {
    // Wait for initial i18next load over network
    cy.intercept('GET', '**/locales/en/translation.json').as('getEnLocale');
    cy.visit('/');
    cy.wait('@getEnLocale');

    cy.contains('Welcome to Rentora').should('be.visible');
  });
});
