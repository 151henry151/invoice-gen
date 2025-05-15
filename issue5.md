## Description

Currently, there is no way to edit or remove individual line items once they have been added to the invoice. Users should be able to modify or delete any line item directly from the invoice interface.

## Current Behavior

- Line items are added to the invoice and displayed in a list.
- There are no "Edit" or "Remove" buttons for individual line items.
- Users cannot change or delete a line item after it has been added.

## Expected Behavior

- Each line item on the invoice displays "Edit" and "Remove" buttons.
- Clicking "Edit" allows the user to modify the details of the line item (e.g., description, quantity, rate).
- Clicking "Remove" deletes the line item from the invoice.
- The invoice total updates automatically after editing or removing a line item.
- UI provides clear feedback for successful edits or removals.

## Technical Details

- Add "Edit" and "Remove" buttons to each line item in the invoice UI.
- Implement logic to update or delete line items in the frontend and backend.
- Ensure invoice total recalculates after changes.
- Provide confirmation dialog for removals to prevent accidental deletion.

## Acceptance Criteria

- [ ] "Edit" and "Remove" buttons are present for each line item
- [ ] Editing a line item updates its details and the invoice total
- [ ] Removing a line item deletes it and updates the invoice total
- [ ] Confirmation dialog appears before removal
- [ ] UI feedback for successful edits and removals
- [ ] Changes are persisted and reflected in the output