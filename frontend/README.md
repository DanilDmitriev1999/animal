# AI Learning UI

This is the frontend for the AI Learning platform, built with Next.js 15, React 19, and TypeScript. It features a custom "Glass UI" design system implemented with Tailwind CSS.

## Getting Started

1.  **Install dependencies:**
    ```bash
    pnpm install
    ```

2.  **Run the development server:**
    ```bash
    pnpm dev
    ```

3.  **Build for production:**
    ```bash
    pnpm build
    ```

4.  **Preview the production build:**
    ```bash
    pnpm preview
    ```

## Design System ("Glass UI")

The UI is built upon a custom design system with a glassmorphism aesthetic. The core of this system is a set of design tokens and utility classes.

### Token System

The single source of truth for the color palette is `src/tokens/colors.ts`.

To update the theme:

1.  Modify a HEX value in the `palette` object in `src/tokens/colors.ts`.
2.  Convert the new HEX value to its HSL equivalent (you can use an online tool for this).
3.  Update the corresponding CSS variable in `src/app/globals.css`. The file contains variables for both the light (`:root`) and dark (`.dark`) themes.

This manual step is required to keep the theme-switching mechanism provided by `shadcn/ui` intact while maintaining a single source of truth for the color values.

### Adjusting Glass Parameters

The "glass" effect on components like `GlassCard` is controlled by a few key styles in `tailwind.config.ts`:

-   **Shadow:** The `boxShadow.glass` utility controls the inner and outer shadows.
-   **Background Color:** The `colors.glass` value sets the semi-transparent background. This should have a corresponding value for the light theme when implemented.
-   **Blur:** The blur effect is applied directly in components using the `backdrop-blur-[20px]` utility class.
-   **Border Radius:** Card and input rounding can be adjusted via the `borderRadius.card` and `borderRadius.input` values.

## Running Tests

This project uses Playwright for end-to-end testing.

To run all tests:
```bash
pnpm exec playwright test
```

To run tests in UI mode:
```bash
pnpm exec playwright test --ui
```
