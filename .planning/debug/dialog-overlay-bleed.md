---
status: diagnosed
trigger: "account wizard modal dialog doesn't properly obscure background content - background page elements bleed through"
created: 2026-02-13T00:00:00Z
updated: 2026-02-13T00:01:00Z
---

## Current Focus

hypothesis: CONFIRMED - Tailwind v4 @theme block missing --color-* registrations for custom semantic tokens
test: Built app CSS output, searched for .bg-background class
expecting: Class missing from output because --color-background not registered
next_action: Return diagnosis

## Symptoms

expected: Modal dialog overlay should darken background, making wizard content clearly readable
actual: Background page elements bleed through the overlay, making wizard content hard to read
errors: None (visual/CSS issue)
reproduction: Open account creation wizard
started: Since Tailwind v4 migration

## Eliminated

- hypothesis: Overlay (bg-black/80) missing or has wrong opacity
  evidence: bg-black/80 compiles correctly to background-color:#000c (rgba 0,0,0,0.8) in built CSS
  timestamp: 2026-02-13T00:00:30Z

- hypothesis: z-index stacking is incorrect
  evidence: Both overlay (z-50) and content (z-50) have correct z-index; overlay renders before content in DOM
  timestamp: 2026-02-13T00:00:30Z

## Evidence

- timestamp: 2026-02-13T00:00:10Z
  checked: dialog.tsx DialogOverlay component
  found: Uses class "bg-black/80" for overlay - this IS correctly generated in CSS output
  implication: Overlay darkening itself works fine

- timestamp: 2026-02-13T00:00:20Z
  checked: dialog.tsx DialogContent component
  found: Uses class "bg-background" for content panel background
  implication: If bg-background doesn't compile, content panel is transparent

- timestamp: 2026-02-13T00:00:30Z
  checked: globals.css @theme block
  found: Only --font-sans and --font-mono defined in @theme. NO --color-* variables registered.
  implication: Tailwind v4 cannot generate utility classes for custom colors

- timestamp: 2026-02-13T00:00:40Z
  checked: Built CSS output (dist/apps/web/assets/index-B929AP0I.css)
  found: .bg-background class DOES NOT EXIST in compiled CSS. .bg-black/80 DOES exist.
  implication: DialogContent has no background-color, making it transparent

- timestamp: 2026-02-13T00:00:45Z
  checked: All bg-* classes in compiled CSS
  found: Only built-in Tailwind colors (amber, blue, emerald, green, red, violet, transparent) present. Zero custom semantic tokens.
  implication: Every shadcn/ui component using theme tokens (bg-background, text-foreground, bg-accent, etc.) is broken

- timestamp: 2026-02-13T00:00:50Z
  checked: Full list of missing utility classes
  found: bg-background, bg-accent, text-muted-foreground, ring-offset-background, ring-ring, text-foreground, text-accent-foreground ALL MISSING
  implication: Widespread issue affecting 31 files (11 in libs/ui, 20 in apps/web)

- timestamp: 2026-02-13T00:00:55Z
  checked: CSS variable definitions in :root
  found: Variables use raw HSL values (e.g. --background: 0 0% 100%) without hsl() wrapper, and body uses hsl(var(--background)) explicitly
  implication: This is the Tailwind v3 / old shadcn pattern. Tailwind v4 needs @theme inline with --color-* mappings.

## Resolution

root_cause: globals.css defines custom color CSS variables (--background, --foreground, --primary, etc.) in :root but never registers them as Tailwind v4 theme colors via @theme --color-* variables. Tailwind v4 requires colors to be registered in the @theme block using the --color-<name> namespace. Without this, utility classes like bg-background, text-foreground, bg-accent are silently dropped from the compiled CSS, leaving DialogContent transparent (no bg-background) so background content bleeds through even though the overlay (bg-black/80) is correctly rendered.
fix:
verification:
files_changed: []
