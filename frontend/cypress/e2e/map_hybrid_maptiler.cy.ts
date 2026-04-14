describe('MapTiler Hybrid Navigation', () => {
  beforeEach(() => {
    cy.visit('http://localhost:5173/listings');
  });

  it('searches locations using MapTiler Autocomplete and switches to Map view', () => {
    // Start typing inside search box
    cy.get('input[placeholder="Search locations, building names..."]').type('Elec');
    
    // Suggestion box should appear, verify data structure mapping to MapTiler response mocks
    cy.contains('Electronic City Phase 1').should('be.visible').click();

    // The view should switch automatically to map view, MapContainer leaflet-container renders
    cy.get('.leaflet-container').should('exist');
  });

  it('renders property detail map with POI markers', () => {
    // Navigate straight to mock property
    cy.visit('http://localhost:5173/listings/1');

    cy.contains('Location & Neighborhood', { timeout: 10000 }).should('be.visible');

    // Ensure POI data appears from MapTiler Mock Provider Structure
    cy.contains('Metro Station Phase 1').should('exist');
    cy.contains('City General Hospital').should('exist');

    // Check Map Container injection
    cy.get('.leaflet-container').should('be.visible');
    
    // Assumes Leaflet mounted markers. The primary and nearby POIs.
    cy.get('.leaflet-marker-icon').should('have.length.greaterThan', 1);
  });
});
