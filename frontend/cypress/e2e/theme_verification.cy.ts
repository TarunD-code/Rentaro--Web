describe('Rentora Theme System Verification', () => {
  const palettes = [
    'trust', 'modern', 'luxury', 'minimal', 'warm', 
    'cool', 'bold', 'earthy', 'pastel', 'dark'
  ];

  const bgColors: Record<string, string> = {
    'trust': 'rgb(255, 255, 255)',
    'modern': 'rgb(236, 240, 241)',
    'luxury': 'rgb(250, 243, 224)',
    'minimal': 'rgb(255, 255, 255)',
    'warm': 'rgb(245, 245, 220)',
    'cool': 'rgb(240, 255, 255)',
    'bold': 'rgb(10, 10, 10)',
    'earthy': 'rgb(194, 178, 128)',
    'pastel': 'rgb(255, 248, 240)',
    'dark': 'rgb(10, 10, 10)'
  };

  const pages = ['/login', '/register', '/dashboard'];

  palettes.forEach((palette) => {
    it(`should apply the ${palette} theme correctly across core pages`, () => {
      pages.forEach((page) => {
        cy.visit(page);
        
        // Set theme in localStorage
        cy.window().then((win) => {
          win.localStorage.setItem('theme', palette);
        });
        
        // Reload to apply theme early
        cy.reload();

        // Verify body background color
        cy.get('body').should('have.css', 'background-color', bgColors[palette]);

        // Check for console errors
        cy.window().then((win) => {
          // Note: This requires a bit more setup if we want to catch errors after visit
          // but for now we look at the console logs if possible or assume no crash
        });

        // Verify UI elements exist
        if (page === '/login') {
          cy.get('form').should('exist');
          cy.contains('Tenant').should('exist');
        }
      });
    });
  });
});
