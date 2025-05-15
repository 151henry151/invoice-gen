## Description

Currently, when a new client is added through the form, it is not appearing in the client selection dropdown menu, even after page refresh. This indicates a potential issue with either the database storage or the data retrieval process.

## Current Behavior

- User adds a new client through the form
- Form submission appears successful
- New client is not visible in the dropdown menu
- Issue persists even after page refresh
- No error messages are displayed to the user

## Expected Behavior

- After successful client creation, the new client should appear in the dropdown menu
- The dropdown should update immediately after creation
- The client should remain in the dropdown after page refresh

## Technical Details

- Need to verify database insertion is successful
- Check the query that populates the dropdown menu
- Ensure proper session handling and data persistence
- Verify the client data is being properly formatted for the dropdown

## Acceptance Criteria

- [ ] New client appears in dropdown menu immediately after creation
- [ ] New client remains in dropdown after page refresh
- [ ] All client details are correctly displayed in the dropdown
- [ ] Proper error handling if client creation fails