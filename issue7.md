## Description

When the user refreshes or reloads the page, any line items that have been added to the invoice are erased. This behavior prevents users from maintaining their work and forces them to re-enter all line items after a refresh.

## Current Behavior

- User adds line items to the invoice.
- Upon refreshing or reloading the page, all previously added line items are lost.
- No warning or confirmation is provided before the data is erased.

## Expected Behavior

- Line items added to the invoice persist after a page refresh or reload.
- Users can refresh the page without losing their work.
- If a refresh is necessary, a warning or confirmation dialog should be provided to prevent accidental data loss.

## Technical Details

- Review the state management and persistence logic for line items.
- Ensure line items are stored in a persistent state (e.g., local storage, session storage, or backend).
- Implement logic to restore line items after a page refresh.

## Acceptance Criteria

- [ ] Line items persist after refreshing or reloading the page
- [ ] Users can refresh the page without losing their work
- [ ] A warning or confirmation dialog is provided if refreshing will cause data loss
- [ ] UI correctly reflects the restored line items