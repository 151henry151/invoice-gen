## Description

When adding a new labor item or regular item, after clicking "Save Labor Item" or "Save Item", the user is returned to the main page without the corresponding dialog open. For a smoother workflow, the main page should reload with the relevant dialog ("Add Labor Item" or "Add Item") already open, and the newly created item pre-selected in the dropdown, allowing the user to immediately add it to the invoice.

## Current Behavior

- User adds a new labor or regular item via the dialog.
- After saving, the user is returned to the main page.
- The "Add Labor Item" or "Add Item" dialog is not open.
- The newly created item is not pre-selected in the dropdown.
- User must manually reopen the dialog and find the new item.

## Expected Behavior

- After saving a new labor or regular item, the main page reloads with the relevant dialog open.
- The newly created item is pre-selected in the dropdown.
- The user can immediately proceed to add the item to the invoice.

## Technical Details

- Update the workflow after saving a new labor or regular item to pass state (e.g., via query params, session, or localStorage).
- On main page load, check for this state and open the appropriate dialog automatically.
- Pre-select the newly created item in the dropdown menu.
- Ensure the workflow is consistent for both labor and regular items.
- Handle edge cases (e.g., user navigates away or cancels action).

## Acceptance Criteria

- [ ] After saving a new labor or regular item, the main page reloads with the relevant dialog open
- [ ] The newly created item is pre-selected in the dropdown
- [ ] User can immediately add the item to the invoice
- [ ] Workflow is consistent for both labor and regular items
- [ ] Edge cases are handled gracefully 