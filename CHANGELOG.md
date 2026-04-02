# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.9.0-beta.6]: https://github.com/151henry151/invoice-gen
[0.9.0-beta.5]: https://github.com/151henry151/invoice-gen
[0.9.0-beta.4]: https://github.com/151henry151/invoice-gen
[0.9.0-beta.3]: https://github.com/151henry151/invoice-gen
[0.9.0-beta.2]: https://github.com/151henry151/invoice-gen
[0.9.0-beta.1]: https://github.com/151henry151/invoice-gen
