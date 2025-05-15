## Description

Currently, the application outputs invoices in XLSX format, which requires users to manually print the file to PDF if they need a non-editable version. This workflow is cumbersome and can lead to inconsistencies. The application should allow users to select the output format directly, choosing between a non-editable PDF or an editable XLSX file, depending on their needs. Additionally, the PDF version should be cryptographically signed to ensure that any tampering with the document is evident.

## Current Behavior

- Invoices are generated in XLSX format by default.
- Users must manually print the XLSX file to PDF to obtain a non-editable version.
- There is no option to select the output format within the application.
- The PDF version is not cryptographically signed, making it susceptible to tampering.

## Expected Behavior

- Users can select the desired output format (PDF or XLSX) before generating the invoice.
- The selected format is used to generate the invoice accordingly.
- The generated file is saved and can be downloaded or sent to the client.
- The application handles the conversion internally, eliminating the need for manual printing.
- The PDF version is cryptographically signed to ensure that any tampering is evident.

## Technical Details

- Implement a dropdown or radio button selection for output format in the invoice generation UI.
- Use appropriate libraries or tools to generate PDF and XLSX files.
- Ensure the generated files are correctly formatted and contain all necessary invoice details.
- Implement cryptographic signing for the PDF version to enhance security and integrity.

## Acceptance Criteria

- [ ] Users can select between PDF and XLSX output formats
- [ ] The selected format is used to generate the invoice
- [ ] The generated file is saved and can be downloaded
- [ ] The generated file contains all necessary invoice details
- [ ] The UI clearly indicates the selected output format
- [ ] The PDF version is cryptographically signed to prevent tampering