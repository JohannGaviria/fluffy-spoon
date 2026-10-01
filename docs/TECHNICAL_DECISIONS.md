# Technical Decisions - Fluffy Spoon

> Collects the technical and architectural decisions adopted for the system, expressed through Architecture Decision Records (ADRs), documenting the context, the alternatives evaluated, the decision taken, the trade-offs assumed and possible later evolutions.

---
## ADR-001: ON DELETE SET NULL to detach images when an album is deleted

### Context

An image can exist independently or be optionally associated with an album.

When a user deletes an album, the associated images must be preserved, along with their comments and ratings, but must stop belonging to the deleted album.

### Alternatives considered

- **`ON DELETE SET NULL`**: PostgreSQL automatically sets `images.album_id` to `NULL` when the album is deleted.
- **Event-Driven**: the album deletion publishes an event that is later processed to detach the images.

### Decision: `ON DELETE SET NULL`

For the MVP, `ON DELETE SET NULL` will be used in the relation between `images.album_id` and `albums.id`.

- PostgreSQL can guarantee referential integrity natively.
- Detaching the images happens automatically when the album is deleted.
- It does not require implementing producers, consumers, events or asynchronous processing.
- It keeps the operation simple and transactional.
- It is compatible with SQLAlchemy through `ondelete="SET NULL"`.
- Images, comments and ratings are preserved.
- It does not introduce eventual consistency: once the album deletion is confirmed, the images are immediately left unassociated.

> **Accepted trade-off:** the solution is coupled to the database and does not allow practising event-based processing during the MVP. The additional complexity of Event-Driven is not considered necessary for the current scope.

### Later evolution

In an iteration after the MVP, an **Event-Driven** approach may be evaluated, where the deletion of an album publishes an event such as `AlbumDeleted` so that a consumer detaches the images.

This would make it possible to later introduce concepts such as:

- Domain events.
- Asynchronous processing.
- Eventual consistency.
- Retries and idempotency.
- Decoupled communication between components.

Adopting this approach is out of MVP scope.

---

## ADR-002: `pending`/`confirmed` status in the `Images` table itself for the two-step S3 upload

### Context

Uploading an image happens in two steps (RF-308/RF-309): first a presigned S3 URL is requested and the upload intent is recorded; then the client uploads the file directly to S3 and confirms the upload so the system can create the definitive record.

Between both steps there is an image that technically has no file confirmed in S3 yet, but that already needs to be persisted to be validated in the second step (ownership, expiry, double-confirmation prevention).

### Alternatives considered

- **A. Status in the same `Images` table**: add `status ENUM('pending','confirmed')` and `expires_at` to `Images`, and make `url` nullable while the record is `pending`.
- **B. Separate `PendingUploads` table**: an independent table for the upload intent, which is deleted (or marked) once confirmed, leaving `Images` intact with all its fields `not null`.

### Decision: Option A — status in the same `Images` table

For the MVP, the image is persisted from the first step (RF-308) with `status = pending`, and RF-309 updates it to `status = confirmed` by completing its `url`.

- It avoids an extra table and model for a short-lived transient state (maximum 5 minutes, according to the `upload_url` `expires_in`).
- A single Alembic migration covers the image's entire lifecycle, instead of coordinating two tables.
- The RF-309 validations (ownership, expiry, double confirmation) are resolved with a single query by `storage_key` over `Images`, without joins.
- It is consistent with the rest of the system: no other Fluffy Spoon entity is modeled with a "draft" table separate from its definitive table.

> **Accepted trade-off:** `url` can no longer be `not null` in `Images`, and the `CHECK (status = 'pending' OR url IS NOT NULL)` constraint is added so the database keeps guaranteeing that no `confirmed` image is left without a `url`. Additionally, an abandoned upload request (never confirmed) remains as an expired `pending` row in `Images` instead of disappearing on its own — see the orphan cleanup limitation already recorded in "Known Limits and Assumptions" of `Architecture.md`.

### Later evolution

If a future iteration needs to more strongly distinguish between "upload intent" and "confirmed file" (for example, when introducing variants/thumbnails or an event-based processing pipeline), it will be possible to migrate to **Option B** or to an event-based approach (`ImageUploadRequested` / `ImageConfirmed`), separating the transient lifecycle from the definitive one. For MVP scope, that separation does not bring enough value compared to its additional complexity.

---
