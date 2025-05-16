## Description

Currently, the invoice details section lists all line items but does not display a subtotal or grand total at the bottom. Users need a clear summary of the invoice's subtotal (sum of all line items) and a grand total (including any additional charges, such as sales tax).

## Current Behavior

- Line items are listed in the invoice details section.
- No subtotal is displayed below the line items.
- No grand total is displayed.
- Users must manually calculate totals if needed.

## Expected Behavior

- An "Invoice Subtotal" is displayed below the list of line items, showing the sum of all line items (labor and regular items).
- A "Grand Total" is displayed below the subtotal, reflecting the subtotal plus any additional charges (e.g., sales tax).
- Both values update dynamically as line items are added, edited, or removed.

## Technical Details

- Calculate subtotal as the sum of all line items (labor and regular items).
- Calculate grand total as subtotal plus any additional charges (e.g., sales tax, if present).
- Update the UI to display both values at the bottom of the invoice details section.
- Ensure calculations are accurate and update in real time as items change.
- Ensure accessibility and responsive design for the new summary section.

## Acceptance Criteria

- [ ] "Invoice Subtotal" is displayed below the line items
- [ ] "Grand Total" is displayed below the subtotal
- [ ] Both values update dynamically as line items are modified
- [ ] Calculations are accurate and reflect all current line items and charges
- [ ] UI is clear, accessible, and responsive 