## Description

The invoice date and invoice number fields exist and are reflected on the outputted invoice, but the workflow for confirming and editing these fields is missing. Users should be able to enter these values, then click an "Add to invoice" button to confirm them. Once confirmed, the fields should become non-editable and display as finalized values at the top of the invoice. An "Edit" button should allow users to re-enable editing if changes are needed. Additionally, the invoice number should be automatically populated with the next sequential number, but users can manually enter a different number if desired. The next invoice will increment by one from the last manually entered invoice number. Duplicate invoice numbers are allowed, but a warning alert should be displayed to the user if the entered invoice number is not unique.

## Current Behavior

- Invoice date and invoice number fields are present and accept input.
- There is no "Add to invoice" button to confirm and finalize these fields.
- There is no "Edit" button to allow changes after confirmation.
- Fields remain editable at all times, or their state is unclear.
- Invoice number is not automatically populated with the next sequential number.
- No warning is provided if the invoice number is not unique.

## Expected Behavior

- Users can enter invoice date and invoice number.
- The invoice number is automatically populated with the next sequential number.
- Users can manually enter a different invoice number if needed.
- Clicking "Add to invoice" disables text entry and displays the values as finalized at the top of the invoice.
- An "Edit" button appears, allowing users to re-enable editing if needed.
- The workflow is consistent with how line items are added and edited.
- The next invoice will increment by one from the last manually entered invoice number.
- If the entered invoice number is not unique, a warning alert is displayed to the user, but the user can still proceed.

## Technical Details

- Implement "Add to invoice" button for both fields.
- After confirmation, fields become non-editable and display as static text.
- Implement "Edit" button to allow further changes.
- Ensure UI updates and backend persistence.
- Validate input (e.g., date format).
- Implement logic to automatically populate the invoice number with the next sequential number.
- Implement a warning alert for non-unique invoice numbers.

## Acceptance Criteria

- [ ] "Add to invoice" button confirms and finalizes invoice date and number
- [ ] Fields become non-editable after confirmation
- [ ] "Edit" button allows further changes
- [ ] Finalized values display at the top of the invoice
- [ ] Invoice number is automatically populated with the next sequential number
- [ ] Users can manually enter a different invoice number
- [ ] The next invoice increments by one from the last manually entered invoice number
- [ ] A warning alert is displayed if the entered invoice number is not unique
- [ ] Changes are saved and reflected in the UI and output
- [ ] Proper validation and error handling