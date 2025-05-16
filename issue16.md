## Description

There is currently no way to add sales tax to an invoice. Users need a "Sales Tax" button next to the "Add Note" button, which opens a dialog similar to "Add Labor" or "Add Item". The dialog should allow selection of a previously used sales tax rate or entry of a new rate. The user should be able to apply the tax to items only, labor only, or both. The selected tax should be added as a line to the invoice, between the subtotal and grand total.

## Current Behavior

- No sales tax button is present.
- No dialog for selecting or adding sales tax rates.
- No way to apply sales tax to invoice items.
- Users must manually calculate and add sales tax if needed.

## Expected Behavior

- A "Sales Tax" button appears next to the "Add Note" button.
- Clicking the button opens a dialog with a dropdown of existing sales tax rates and an option to add a new rate.
- User can select a rate or add a new one.
- User can choose to apply the tax to items only, labor only, or both.
- A "Sales Tax" line is added to the invoice, between the subtotal and grand total, with the correct calculation.
- The sales tax is calculated and displayed correctly based on the selection.

## Technical Details

- Implement a "Sales Tax" button in the invoice controls area.
- Create a dialog for selecting or adding sales tax rates.
- Store and retrieve previously used sales tax rates.
- Allow user to specify which items the tax applies to (items, labor, or both).
- Calculate the sales tax based on the selected rate and applicable items.
- Insert a "Sales Tax" line in the invoice summary, between subtotal and grand total.
- Ensure UI updates and backend persistence.
- Validate input and handle edge cases (e.g., duplicate rates, invalid input).

## Acceptance Criteria

- [ ] "Sales Tax" button is present next to "Add Note"
- [ ] Dialog allows selection or entry of sales tax rates
- [ ] User can specify which items the tax applies to
- [ ] "Sales Tax" line is added to the invoice in the correct position
- [ ] Sales tax is calculated and displayed correctly
- [ ] Rates are stored and can be reused
- [ ] UI and backend handle all edge cases and errors 