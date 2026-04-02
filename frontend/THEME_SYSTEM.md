# Rentora Theme System

This project implements a premium, 10-palette global theme system with zero "white flash" on refresh and seamless CSS variable synchronization.

## 🎨 Available Palettes

| Name | Theme Feel | Primary Color |
| :--- | :--- | :--- |
| **Trust** | Professional & Classic | #0A3D62 |
| **Modern** | Vibrant & Energetic | #3F51B5 |
| **Luxury** | Elegant & Premium | #001F3F |
| **Minimal** | Content-First & Clean | #000000 |
| **Warm** | Cozy & Approachable | #228B22 |
| **Cool** | Serene & Calm | #191970 |
| **Bold** | High-Impact & Nightlife | #DC143C |
| **Earthy** | Organic & Grounded | #808000 |
| **Pastel** | Gentle & Friendly | #FFB6C1 |
| **Dark** | High-Contrast & Night mode | #0A0A0A |

## 🚀 How it Works

1. **Early Bootstrap**: A small script in `index.html` reads `localStorage` and applies the background color before React hydrates.
2. **CSS Variables**: `ThemeContext.tsx` syncs the active palette to `:root` variables (`--bg-default`, `--color-primary`, etc.).
3. **MUI Integration**: `getTheme()` in `theme.ts` generates a full MUI `createTheme` object based on the selected variant.
4. **Selector UI**: The Header in `Layout.tsx` provides 10-swatch circular selectors on desktop and an overflow menu on mobile.

## ➕ Adding a New Palette

To add a new palette, update `src/theme.ts`:
1. Add the variant name to `PaletteVariant`.
2. Add the HEX tokens to the `palettes` object.
3. Update the `bgMap` in `index.html` to support zero-flash for the new palette.

## 🧪 Verification

To run the automated theme verification:
1. Ensure the dev server is running: `npm run dev`
2. Run Cypress: `npx cypress run` (or `npx cypress open` for UI mode)

The verification script iterates through all 10 themes and ensures:
- The body background color matches the palette.
- No console errors are present on Login, Register, and Dashboard pages.
