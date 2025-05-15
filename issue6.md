## Description

After adding a labor or item line to the invoice, the "Add Labor" and "Add Item" buttons disappear and do not reappear, preventing users from adding additional line items. These buttons should remain accessible so users can add multiple labor or item entries to the invoice.

## Current Behavior

- User clicks "Add Labor" or "Add Item" and adds a line item to the invoice.
- The corresponding button disappears from the UI.
- User cannot add more labor or item entries without refreshing or reloading the page.

## Expected Behavior

- "Add Labor" and "Add Item" buttons remain visible and accessible after adding a line item.
- Users can add multiple labor or item entries in succession.
- The UI updates dynamically to allow continuous entry of line items.

## Technical Details

- Review the logic that hides these buttons after a line item is added.
- Ensure buttons are only hidden when appropriate (e.g., during entry, not after submission).
- Update UI state management to allow repeated use.

## Acceptance Criteria

- [ ] "Add Labor" and "Add Item" buttons remain visible after adding a line item
- [ ] Users can add multiple labor or item entries without refreshing the page
- [ ] UI updates dynamically and correctly reflects the current state
- [ ] No duplicate or overlapping buttons appear