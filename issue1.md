## Description

Currently, when a new business is added through the form, it is not appearing in the business selection dropdown menu, even after page refresh. This indicates a potential issue with either the database storage or the data retrieval process.

## Current Behavior

- User adds a new business through the form
- Form submission appears successful
- New business is not visible in the dropdown menu
- Issue persists even after page refresh
- No error messages are displayed to the user

## Expected Behavior

- After successful business creation, the new business should appear in the dropdown menu
- The dropdown should update immediately after creation
- The business should remain in the dropdown after page refresh

## Technical Details

- Need to verify database insertion is successful
- Check the query that populates the dropdown menu
- Ensure proper session handling and data persistence
- Verify the business data is being properly formatted for the dropdown

## Acceptance Criteria

- [ ] New business appears in dropdown menu immediately after creation
- [ ] New business remains in dropdown after page refresh
- [ ] All business details are correctly displayed in the dropdown
- [ ] Proper error handling if business creation fails