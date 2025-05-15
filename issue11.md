## Description

Currently, when a logo is uploaded to the invoice, it may not be resized appropriately, leading to inconsistent appearances across different invoices. The application should automatically resize the uploaded logo to ensure a consistent and professional look.

## Current Behavior

- Uploaded logos are displayed at their original size.
- This can lead to inconsistencies in the invoice layout and appearance.
- Users have no control over the logo size after uploading.

## Expected Behavior

- The application automatically resizes the uploaded logo to a standard size.
- The resized logo maintains its aspect ratio to avoid distortion.
- The logo is displayed consistently across all invoices.
- Users can preview the logo after uploading to ensure it meets their expectations.

## Technical Details

- Implement image processing logic to resize the uploaded logo.
- Use appropriate libraries or tools to handle image resizing.
- Ensure the resized logo is stored and displayed correctly in the invoice.

## Acceptance Criteria

- [ ] Uploaded logos are automatically resized to a standard size
- [ ] The resized logo maintains its aspect ratio
- [ ] The logo is displayed consistently across all invoices
- [ ] Users can preview the logo after uploading
- [ ] The UI clearly indicates the expected logo size