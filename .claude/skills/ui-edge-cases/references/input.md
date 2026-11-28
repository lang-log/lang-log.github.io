# Input: touch, mouse, keyboard, timing

## Touch

- After a tap, no control stays in its pressed or hover look (seen: map buttons and the key's Next button stayed pressed on a phone). Hover styles are inside `@media (hover: hover)`, and no `:focus` style looks like a pressed state.
- Every control is at least 44 px high on a touch screen.
- Pinch and drag on the map, and swipes beside it: the map and the page each move as intended, and the page never gets stuck (`touch-action`, `overscroll-behavior`).
- A double tap does not zoom the page by mistake on a control.
- Text fields have a font of 16 px or more, so iOS Safari does not zoom into them.

## Mouse

- Hover shows the same thing as a tap or a focus would (no information only on hover).
- Pressing and holding, then dragging off a button, leaves no pressed state.
- The mouse wheel over the map zooms the map; over the rest of the page it scrolls.

## Keyboard and assistive technology

- Every control can be reached with Tab and used with Enter or Space, in a sensible order, and the focus ring is visible in both themes.
- Escape closes an open menu or popup, and the focus goes back to the control that opened it.
- Toggle buttons have `aria-pressed`, symbol-only buttons an `aria-label`, groups `role="group"` (`ui-design.md`), in every interface language.
- With `prefers-reduced-motion: reduce`, nothing animates.

## Timing

- Pressing a control before the page's script, the data or the map has finished loading: nothing breaks and no error appears (seen: a click on the map before its points were drawn failed in Firefox in CI).
- Pressing fast and many times (double press, press during an animation): the end state matches the last press.
- Going back and forward in the browser history, and reloading, restore the state in the query string (`docs/urls.md`).
- A page opened from the browser's back-forward cache shows the right state (menus closed, buttons not pressed).
