## Description

Currently, the "Notes" field is always visible on the invoice, regardless of whether the user has added any notes. This can clutter the interface and distract users. The "Notes" field should only appear after the user clicks an "Add note" button, allowing for a cleaner and more intuitive user experience. Once the notes field is revealed, an "Add note to invoice" button should appear, which, when clicked, adds the note to the invoice like a line item. The added note should then have "Edit" and "Delete" buttons for further management.

## Current Behavior

- The "Notes" field is always displayed on the invoice.
- There is no "Add note" button to trigger the visibility of the notes field.
- There are no options to edit or delete notes once they are added.

## Expected Behavior

- The "Notes" field is hidden by default.
- An "Add note" button is available for users to click when they want to add notes.
- Clicking the "Add note" button reveals the notes field, allowing the user to enter their notes.
- An "Add note to invoice" button appears with the notes field.
- Clicking "Add note to invoice" adds the note to the invoice like a line item.
- Once a note is added, it displays "Edit" and "Delete" buttons for further management.
- Users can edit or delete the note as needed, and the changes are reflected in the invoice.

## Technical Details

- Implement an "Add note" button in the invoice UI.
- Use JavaScript to toggle the visibility of the notes field based on user interaction.
- Ensure the notes field is properly styled and integrated into the invoice layout.
- Implement an "Add note to invoice" button that appears with the notes field.
- Implement "Edit" and "Delete" buttons for each note.
- Persist the notes data when the invoice is saved.

## Acceptance Criteria

- [ ] "Notes" field is hidden by default
- [ ] "Add note" button is present and functional
- [ ] Clicking "Add note" reveals the notes field
- [ ] "Add note to invoice" button appears with the notes field
- [ ] Clicking "Add note to invoice" adds the note to the invoice like a line item
- [ ] Once a note is added, it displays "Edit" and "Delete" buttons
- [ ] Users can edit or delete notes as needed
- [ ] Notes data is persisted when the invoice is saved