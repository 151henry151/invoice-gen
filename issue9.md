## Description

Currently, there is no way for users to preview the invoice before finalizing it. A "Preview invoice" feature should be implemented to allow users to see how the invoice will look before it is generated or sent. This will help users catch any errors or make adjustments as needed.

## Current Behavior

- Users cannot preview the invoice before finalizing it.
- There is no way to see how the invoice will appear in its final form.

## Expected Behavior

- A "Preview invoice" button is available on the invoice creation page.
- Clicking the "Preview invoice" button opens a modal or new tab showing a preview of the invoice.
- The preview should accurately reflect the final invoice, including all line items, notes, and formatting.
- Users can close the preview and return to editing the invoice if changes are needed.

## Technical Details

- Implement a "Preview invoice" button in the invoice UI.
- Use JavaScript to generate a preview of the invoice based on the current state.
- Ensure the preview accurately reflects the final invoice layout and content.
- Provide a way to close the preview and return to the invoice creation page.

## Acceptance Criteria

- [ ] "Preview invoice" button is present and functional
- [ ] Clicking the button opens a preview of the invoice
- [ ] The preview accurately reflects the final invoice
- [ ] Users can close the preview and return to editing the invoice
- [ ] The preview is styled consistently with the final invoice