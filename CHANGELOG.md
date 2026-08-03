# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.0-beta.14] - 2026-08-03

### Changed

- Assign invoice numbers automatically from each user's sequential counter and show them as read-only
- Default the invoice date to today while keeping date and due date editable
- Remove the invoice number/date confirm control from the create-invoice form

### Added

- Add `invoice_numbering` helpers and tests for sequential allocation that skips existing invoices and drafts
- Add `schema_migrate.ensure_invoice_draft_schema` and an `invoice_number` column on `InvoiceDraft` to reserve numbers for drafts

## [0.9.0-beta.13] - 2026-08-03

### Fixed

- Load Google Maps Places autocomplete on client details by injecting `GOOGLE_MAPS_API_KEY` into that template (previously only business details received the key)
- Resolve the Maps API key from `GOOGLE_MAPS_API_KEY` or `credentials.ini` via `get_google_maps_api_key()`

### Added

- Add tests for Maps API key resolution and client-details key embedding

## [0.9.0-beta.12] - 2026-08-03

### Fixed

- Persist client address from the address-picker fields on create and edit instead of reading a missing `address` form key that cleared the stored address
- Parse stored addresses from the trailing country/ZIP/state/city so a missing address line 2 no longer mis-fills the edit form
- Preserve `from_create_invoice` when opening client details from the invoice editor and return to create-invoice on cancel

### Added

- Add `address_utils` helpers and regression tests for client address save/restore

## [0.9.0-beta.11] - 2026-08-03

### Added

- Add `phone_utils` helpers and a reusable phone input (country dial code + progressive national formatting) for client and business detail forms
- Add `static/js/phone_input.js` so mobile users can enter NANP numbers without typing parentheses or dashes

### Changed

- Widen client and business `phone` columns from 20 to 40 characters to store formatted international values

## [0.9.0-beta.10] - 2026-05-31

### Fixed

- Change the invoice submit handler from `fetch(redirect: 'manual')` to `redirect: 'follow'` and treat `response.ok`/`response.redirected`/`response.url` as success, so a successful save no longer shows the "Could not generate invoice" alert (the manual redirect produced an opaque response with `status === 0`)

### Changed

- Reword the submit failure alert to "Could not save the invoice." and navigate to `response.url` after a successful save

### Added

- Add `tests/test_edit_invoice_submit.py` asserting the edit POST persists changes and redirects to `invoice_list` with a relative Location

## [0.9.0-beta.9] - 2026-05-31

### Fixed

- Remove the duplicate `confirmInvoiceBtn` click handler in `components/invoice_fields.html` that unconditionally re-set the date/due-date/invoice-number fields to `readOnly` on every click, which prevented editing the invoice number after confirming

### Changed

- Toggle the due-date `readOnly` state and the confirm button color (`btn-success`/`btn-warning`) inside the authoritative `confirmInvoiceBtn` handler and `applyInvoicePayload` in `create_invoice.html`, preserving the behavior previously provided by the removed component handler

## [0.9.0-beta.8] - 2026-05-31

### Added

- Embed a pristine JSON snapshot (`INVOICE_SNAPSHOT`) of the saved invoice and the edit POST URL (`EDIT_POST_URL`) in the edit-invoice page via `edit_invoice` GET
- Add a `discardInvoiceEdits` handler and a "Discard changes" button (edit mode only) that restores the invoice to its last saved state and resets the autosave draft
- Add `tests/test_edit_invoice_cancel.py` covering snapshot embedding, the discard control, and line-item round-tripping

### Changed

- Seed the create-invoice page from `INVOICE_SNAPSHOT` when in edit mode (ignoring stale create drafts) and point the form `action` at `EDIT_POST_URL`, instead of restoring the create draft
- Extract `finalizeBusinessClientSelection` from the `DOMContentLoaded` handler and reuse it for the edit-seed and discard paths
- Label the submit button "Save Changes" in edit mode (was "Generate Invoice")

## [0.9.0-beta.7] - 2026-04-02

### Fixed

- Fix labor line restore in `applyInvoicePayload` on create-invoice page: use `item.hours` / `item.minutes` for display (was undefined `hours` / `minutes`, throwing on restore and clearing line items after navigation)
- Skip server draft merge when server has fewer line items than local draft (partial server snapshot)

## [0.9.0-beta.6] - 2026-04-02

### Fixed

- Skip applying server invoice draft over localStorage when the server snapshot has no line items but local draft has items (prevents reload from wiping in-progress invoices after a stale or partial autosave)

## [0.9.0-beta.5] - 2026-04-02

### Fixed

- Emit relative URLs from `url_for_with_prefix` so HTTPS deployments expose `Location` to `fetch(..., redirect: 'manual')` after generating an invoice (avoid opaque redirects from absolute `http://` redirects)
- Use `response.url` when `Location` header is missing on redirect responses in create-invoice submit handler

### Added

- Add `tests/test_create_invoice_submit.py` asserting successful invoice POST returns a non-absolute redirect

## [0.9.0-beta.4] - 2026-04-02

### Fixed

- Replace raw SQL in `update_item` and `update_labor` with ORM writes so SQLAlchemy 2.x no longer raises on `session.execute()` for plain strings; map form price to `Item.unit_price` (legacy SQL used non-existent column `price`)

### Changed

- Align `tests/test_items.py` success assertions with flash text `Item saved successfully` / `Labor item saved successfully`

## [0.9.0-beta.3] - 2026-03-22

### Fixed

- Set docker-compose `web` `command` to `/app/entrypoint.sh` so the app starts when `.:/app` hides image-only `/app/start.sh`
- Restore `README.md` body after accidental truncation in the same release commit

## [0.9.0-beta.2] - 2026-03-22

### Merged

- Merge remote `master` (app factory, templates, tests, Docker dev tooling) into this release branch

### Added

- Add `InvoiceDraft` model and `GET`/`PUT`/`DELETE` `/api/invoice-draft` (and `/invoice/api/invoice-draft`) for server-side autosave of the create-invoice form
- Add unit tests for the invoice draft API under `tests/`
- Register `/invoice/get_client/<id>` alongside `/get_client/<id>` for consistent proxy paths

### Changed

- Replace apt package `libgdk-pixbuf2.0-0` with `libgdk-pixbuf-2.0-0` for compatibility with current Debian-based `python:3.9-slim` images
- Update create-invoice client preview to fill all client detail slots (including mobile accordion) via `data-client-preview` and `setClientPreviewFields`
- Point client-detail fetch at `/invoice/get_client/` to match company API path style
- Add `id="client_id"` on the hidden client field and persist selection in `selectionData` localStorage when saving business/client
- Replace default form POST with `fetch` and `redirect: manual` so local and server drafts clear only after a successful redirect to the invoice list
- Extend draft payload with due date, business and client ids, pending notes text, optional item line date, and `savedAt` for merge ordering
- Debounce server draft `PUT` after local saves (1.5s); merge server draft on load when newer than local `savedAt`
- Delete server draft row when an invoice is committed successfully (in addition to client-side clear on success)

## [0.9.0-beta.1] - 2025 (baseline)

### Added

- Initial beta release with core invoice generation functionality (see README)

[0.9.0-beta.7]: https://github.com/151henry151/invoice-gen
[0.9.0-beta.6]: https://github.com/151henry151/invoice-gen
[0.9.0-beta.5]: https://github.com/151henry151/invoice-gen
[0.9.0-beta.4]: https://github.com/151henry151/invoice-gen
[0.9.0-beta.3]: https://github.com/151henry151/invoice-gen
[0.9.0-beta.2]: https://github.com/151henry151/invoice-gen
[0.9.0-beta.1]: https://github.com/151henry151/invoice-gen
