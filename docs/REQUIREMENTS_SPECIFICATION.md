# Requirements Specification - Fluffy Spoon

> Defines the functionality offered by the system, organized by module and expressed through functional requirements and their corresponding user stories, establishing the expected behavior of the application from the business perspective.

## Table of Contents

- [Project Summary](#project-summary)
- [System Requirements](#system-requirements)
    - [Functional Requirements](#functional-requirements)
- [User Stories](#user-stories)
- [Data Models](#data-models)
    - [Persistent Models](#persistent-models)
    - [Cache Structures - Redis](#cache-structures---redis)

---

## Project Summary

- **Project name:** Fluffy Spoon

- **Short description:** REST API to manage an image gallery with light social interaction. Users can upload images individually or group them into albums, while other users can interact with the content through ratings from 1 to 5 and comments.

- **Detailed description:** Fluffy Spoon is a backend system designed to manage an image gallery in a simple and secure way. The application allows registering users, managing images and albums, and handling user interactions through ratings and comments.

    The domain focuses on applying business rules such as ownership of images and albums, prevention of duplicate ratings, assignment of scores between 1 and 5, comment management and integrity of the relations between users and content. The project aims to serve as a practical implementation of a layered architecture, keeping a clear separation between domain rules and the technologies used for its infrastructure.

- **Involved actors:**

    - **User:** creates albums, uploads images, comments on and likes other users' images, manages their profile.
- **Architecture type:** Monolith with Layered Architecture.

- **Initial technology stack:**

    - Language: Python
    - Framework: FastAPI
    - Database: PostgreSQL
    - Others: SQLAlchemy · Alembic · Redis · PyJWT · Argon2 · Structlog · Ruff · Mypy · Pytest · Pytest-Asyncio · Docker · Docker Compose · GitHub Actions · Cloud · Boto3

---

## System Requirements

### Functional Requirements

#### Module 1 - Authentication:

- **RF-101:** The system must allow a new user to register with valid credentials.
- **RF-102:** The system must allow a registered user to log in with their credentials.
- **RF-103**: The system must allow an authenticated user to log out and invalidate their current `access token`.

#### Module 2 - Albums:

- **RF-204:** The system must allow an authenticated user to create an album and set it as their own.
- **RF-205:** The system must allow querying albums and filtering the results by their owner.
- **RF-206:** The system must allow only the owner of an album to modify its information.
- **RF-207:** The system must allow only the owner of an album to delete it.

#### Module 3 - Images:

- **RF-308:** The system must allow an authenticated user to request a presigned S3 URL to upload a new image, validating the file metadata (type and size) and generating a unique `storage_key`.
- **RF-309:** The system must allow an authenticated user to confirm the file upload to S3, verifying that the object exists and creating the definitive image record.
- **RF-310:** The system must allow querying the available images and filtering them by different criteria.
- **RF-311:** The system must allow only the owner of an image to modify its information.
- **RF-312:** The system must allow only the owner of an image to delete it.

#### Module 4 - Comments:

- **RF-413:** The system must allow an authenticated user to publish a comment on an image.
- **RF-414:** The system must allow querying the comments associated with an image.
- **RF-415:** The system must allow only the author of a comment to modify its content.
- **RF-416:** The system must allow the author of a comment to delete it.

#### Modules 5 - Ratings:

- **RF-517:** The system must allow an authenticated user to rate an image with a score between 1 and 5.
- **RF-518:** The system must allow querying the number of ratings received and the average rating of an image.
- **RF-519:** The system must allow an authenticated user to modify the rating they have made on an image.
- **RF-520:** The system must allow an authenticated user to delete their rating of an image.

---

## User Stories

### Module 1 - Authentication:

#### US-RF-101: User Registration

**As** an unauthenticated visitor,

**I want** to register in the system,

**So that** I can access the gallery features.

**Endpoint:** `HTTP` - `POST /api/v1/auth/register`

**Priority:** High (P0)

**Size**: L

**Estimate**: 2

**Acceptance criteria:**

- [ ] The user must provide a `name`, an `email` and a `password`.
- [ ] The `name` must not be empty and must be between 3 and 100 characters.
- [ ] The `email` must have a valid format.
- [ ] The `email` must not be previously registered.
- [ ] The `password` is handled as a secret; it is never exposed in logs or tracebacks.
- [ ] The `password` must be between 8 and 16 characters long and include at least one uppercase letter, one lowercase letter, one number and one special character.
- [ ] The `password` must be stored using Argon2.
- [ ] The system must log the successful and failed executions of the process.
- [ ] A `201 Created` code is returned with the `id`, `name`, `email`, `created_at`, `updated_at` data of the created user if the registration was successful.
- [ ] A `400 Bad Request` code is returned if any field does not meet the format validations.
- [ ] A `409 Conflict` code is returned if the `email` is already registered.
- [ ] A `422 Unprocessable Entity` code is returned if any required field is missing or malformed.
- [ ] A `500 Internal Server Error` code is returned if any unexpected error occurs.

#### US-RF-102: Login

**As** a registered user,

**I want** to log in with my credentials,

**So that** I can access the gallery features that require authentication.

**Endpoint:** `HTTP` - `POST /api/v1/auth/login`

**Cache:** `cache:login:attempts:{email}:{ip}` - `cache:login:lock:{email}:{ip}`

**Priority:** High (P0)

**Size**: L

**Estimate**: 3

**Acceptance criteria:**

- [ ] The user must provide an `email` and a `password`.
- [ ] The `email` must have a valid format.
- [ ] The `email` must be normalized before performing authentication.
- [ ] The `password` is handled as a secret and must not be exposed in logs or tracebacks.
- [ ] The system must verify the `password` using the user's stored hash.
- [ ] Invalid credentials must be rejected without revealing whether the `email` or the `password` is incorrect.
- [ ] The system must record failed authentication attempts associated with the `email` and `IP` combination through `cache:login:attempts:{email}:{ip}`.
- [ ] The failed-attempt counter must have a **15-minute** window.
- [ ] The system must temporarily block authentication for the `email` and `IP` combination after **5 consecutive failed attempts**.
- [ ] The lockout must be stored through `cache:login:lock:{email}:{ip}` and last **15 minutes**.
- [ ] The failed-attempt counter must be reset when authentication succeeds.
- [ ] The system must use atomic operations to update the attempt counter and avoid race conditions.
- [ ] The system must generate a `JWT Access Token` when the credentials are valid.
- [ ] The `Access Token` must contain the `sub`, `jti`, `iat` and `exp` claims.
    - The `sub` claim must contain the user identifier.
    - The `jti` claim must contain a unique identifier of the `Access Token`.
    - The `Access Token` must have a maximum duration of **15 minutes**.
- [ ] The system must log successful and failed authentication attempts without logging passwords, tokens or secrets.
- [ ] A `200 OK` code is returned with the `id`, `name`, `email`, `created_at`, `updated_at`, `access_token` and `exp` data when authentication is successful.
- [ ] A `401 Unauthorized` code is returned if the provided credentials are invalid.
- [ ] A `422 Unprocessable Entity` code is returned if any required field is missing or does not meet the input schema.
- [ ] A `429 Too Many Requests` code is returned if the `email` and `IP` combination is temporarily locked.
- [ ] A `500 Internal Server Error` code is returned if any unexpected error occurs.

#### US-RF-103: Logout

**As** an authenticated user,

**I want** to log out,

**So that** my current `access_token` is invalidated and cannot be used anymore, forcing me to log in again.

**Endpoint:** `HTTP` - `POST /api/v1/auth/logout`

**Requires Authentication:** ✅

**Cache:** `cache:access_token:revoked:{jti}`

**Priority:** High (P0)

**Size:** S

**Estimate:** 2

**Acceptance criteria:**

- [ ] The system must verify the signature and expiry of the `access_token`.
- [ ] The system must extract the `jti` claim from the `access_token` and use it as the blacklist identifier.
- [ ] The system must store the `access_token` `jti` in `cache:access_token:revoked:{jti}` in Redis.
- [ ] The blacklist entry must have a TTL equal to the remaining expiry time of the `access_token`.
- [ ] Once added to the blacklist, the `access_token` must not grant access to the API's protected endpoints.
- [ ] The system must reject any request presenting an `access_token` that is on the blacklist.
- [ ] The system must log the successful logout and the failed attempts without logging tokens or secrets.
- [ ] A `204 No Content` code is returned if the logout is successful.
- [ ] A `401 Unauthorized` code is returned if the `access_token` is invalid or expired.
- [ ] A `422 Unprocessable Entity` code is returned if the required access credential is missing or does not meet the input schema.
- [ ] A `500 Internal Server Error` code is returned if any unexpected error occurs.

### Module 2 - Albums:

#### Visibility Truth Table - Albums

|Resource / context|Owner|Album|Visible?|Condition|
|---|---|---|---|---|
|Album|Own|public|Yes|The owner can always query their albums.|
|Album|Own|private|Yes|The owner can always query their albums.|
|Album|Another user|public|Yes|Public albums are visible.|
|Album|Another user|private|No|Private albums are only visible to their owner.|

#### US-RF-204: Album Creation

**As** an authenticated user,

**I want** to create an album and set it as my own,

**So that** I can group and organize my images.

**Endpoint:** `HTTP` - `POST /api/v1/albums`

**Requires Authentication:** ✅

**Cache:** `cache:albums:list`

**Priority:** High (P0)

**Size:** M

**Estimate:** 2

**Acceptance criteria:**

- [ ] The user must provide a `title`, an optional `description` and a `visibility` to define the album's visibility as `public` or `private`.
- [ ] The `title` must not be empty and must be between 1 and 100 characters.
- [ ] The `description` must not exceed 500 characters.
- [ ] The `visibility` must only accept the values `public` or `private`.
- [ ] The system must associate the album with the authenticated user through the `sub` claim.
- [ ] After creating the album, the system must invalidate the cache by deleting the keys matching the `cache:albums:list` pattern.
- [ ] The system must log the successful and failed executions of the process.
- [ ] A `201 Created` code is returned with the `id`, `title`, `description`, `owner_id`, `visibility`, `created_at`, `updated_at` data of the created album.
- [ ] A `401 Unauthorized` code is returned if the `access_token` is invalid or expired.
- [ ] A `422 Unprocessable Entity` code is returned if any required field is missing or does not meet the input schema.
- [ ] A `500 Internal Server Error` code is returned if any unexpected error occurs.

#### US-RF-205: Album Query and Filtering

**As** an authenticated user,

**I want** to query and filter the available albums,

**So that** I can explore other users' public content and manage or query my own albums.

**Endpoint:** `HTTP` - `GET /api/v1/albums`

**Requires Authentication:** ✅

**Cache:** `cache:albums:list:{query_hash}`

**Priority:** High (P0)

**Size:** L

**Estimate:** 3

**Acceptance criteria:**

- [ ] The query must allow filtering albums by `title`, performing a partial search on the title.
- [ ] The system must allow filtering albums by owner through `owner_id`.
- [ ] The system must allow filtering the results by `visibility`, accepting only the values `public` and `private`.
- [ ] The system must allow querying only the user's own albums through a filter that represents resource ownership.
- [ ] The returned albums must comply with the visibility rules defined in the album visibility truth table.
- [ ] The `private` value in the `visibility` filter may only produce results corresponding to albums of the authenticated user.
- [ ] Applying the filters must not grant access to albums that would not be visible to the authenticated user.
- [ ] The filters must be combinable, for example `title` + `owner_id` or `title` + `visibility`.
- [ ] When filters are combined, the results must simultaneously satisfy the conditions of all filters and the visibility rules defined in the album visibility truth table.
- [ ] The system must allow sorting the results by `created_at` or `title`.
    - Sorting must accept the ascending (`asc`) and descending (`desc`) directions.
- [ ] The system must allow paginating the results through the `page` and `page_size` parameters.
- [ ] The system must build a `query_hash` from the query parameters (`title`, `owner_id`, `visibility`, sorting and pagination) and use it as the `cache:albums:list:{query_hash}` key.
- [ ] Before querying the database, the system must check in Redis whether the `cache:albums:list:{query_hash}` key exists.
- [ ] On a **cache hit**, the system must return the stored response without querying the database.
- [ ] On a **cache miss**, the system must query the database and store the response in `cache:albums:list:{query_hash}` with a TTL of **5 minutes**.
- [ ] The responses stored in the cache must include the album list and the pagination metadata.
- [ ] The system must log the successful and failed executions of the process without logging sensitive information.
- [ ] A `200 OK` code is returned with the album list and its data: `id`, `title`, `description`, `owner_id`, `visibility`, `created_at` and `updated_at`, together with the pagination metadata (`page`, `page_size`, `total`, `total_pages`, `has_next`).
- [ ] An empty list with a `200 OK` code is returned when no albums match the provided filters, or when the visibility rules defined in the album visibility truth table prevent any visible results from existing.
- [ ] A `401 Unauthorized` code is returned if the `access_token` is invalid or expired.
- [ ] A `422 Unprocessable Entity` code is returned if the query parameters do not meet the expected schema.
- [ ] A `500 Internal Server Error` code is returned if any unexpected error occurs.

#### US-RF-206: Album Update

**As** an authenticated user,

**I want** to modify the information of an album that belongs to me,

**So that** I can keep its content up to date.

**Endpoint:** `HTTP` - `PATCH /api/v1/albums/{album_id}`

**Requires Authentication:** ✅

**Cache:** `cache:albums:list`

**Priority:** Medium (P1)

**Size:** S

**Estimate:** 2

**Acceptance criteria:**

- [ ] The system must verify that the authenticated user is the owner of the album.
- [ ] The system must allow updating the album's `title`, `description` and `visibility`.
- [ ] The `title` must not be empty and must be between 1 and 100 characters.
- [ ] The `description` must not exceed 500 characters.
- [ ] The `visibility` must only accept the values `public` or `private`
- [ ] The album's `updated_at` must be updated at the moment of the modification.
- [ ] After modifying the album, the system must invalidate the cache by deleting the keys matching the `cache:albums:list` pattern.
- [ ] The system must log the successful and failed executions of the process.
- [ ] A `200 OK` code is returned with the album's updated data.
- [ ] A `401 Unauthorized` code is returned if the `access_token` is invalid or expired.
- [ ] A `403 Forbidden` code is returned if the authenticated user is not the owner of the album.
- [ ] A `404 Not Found` code is returned if the album does not exist.
- [ ] A `422 Unprocessable Entity` code is returned if any required field is missing or does not meet the input schema.
- [ ] A `500 Internal Server Error` code is returned if any unexpected error occurs.

#### US-RF-207: Album Deletion

**As** an authenticated user,

**I want** to delete an album that belongs to me,

**So that** I can remove it from the gallery.

**Endpoint:** `HTTP` - `DELETE /api/v1/albums/{album_id}`

**Requires Authentication:** ✅

**Cache:** `cache:albums:list`

**Priority:** Low P2

**Size:** XS

**Estimate:** 1

**Acceptance criteria:**

- [ ] The system must verify that the authenticated user is the owner of the album.
- [ ] The system must delete the album from the database.
- [ ] After deleting the album, the system must invalidate the cache by deleting the keys matching the `cache:albums:list` pattern.
- [ ] The system must log the successful and failed executions of the process.
- [ ] A `204 No Content` code is returned if the album was deleted successfully.
- [ ] A `401 Unauthorized` code is returned if the `access_token` is invalid or expired.
- [ ] A `403 Forbidden` code is returned if the authenticated user is not the owner of the album.
- [ ] A `404 Not Found` code is returned if the album does not exist.
- [ ] A `500 Internal Server Error` code is returned if any unexpected error occurs.

### Module 3 - Images:

#### Visibility Truth Table - Images

|Resource / context|Owner|Album|Image|Visible?|Condition|
|---|---|---|---|---|---|
|Image without album|Own|—|public|Yes|The owner can query their images.|
|Image without album|Own|—|private|Yes|The owner can query their images.|
|Image without album|Another user|—|public|Yes|Public images without an album are visible.|
|Image without album|Another user|—|private|No|Private images are not visible to third parties.|
|Image with album|Own|public|public|Yes|The owner can query their images.|
|Image with album|Own|public|private|Yes|The owner can query their images.|
|Image with album|Own|private|public|Yes|The owner can query their images.|
|Image with album|Own|private|private|Yes|The owner can query their images.|
|Image with album|Another user|public|public|Yes|Visible only through a query with `album_id`.|
|Image with album|Another user|public|private|No|The private image is not visible.|
|Image with album|Another user|private|public|No|The private album is not visible.|
|Image with album|Another user|private|private|No|The private album is not visible.|

> **General rule:** The owner can query their own albums and images regardless of their visibility. Other users can only query public resources. For an image associated with an album, both the album and the image must be public in order to be queried by third parties. Images associated with an album require specifying `album_id` in third-party queries, so they do not appear in general queries.

#### US-RF-308: Upload URL Request

**As** an authenticated user,

**I want** to request a presigned S3 URL to upload a new image,

**So that** I can upload it directly to object storage without it going through the API server.

**Endpoint:** `HTTP` - `POST /api/v1/images/upload-url`

**Requires Authentication:** ✅

**Priority:** High (P0)

**Size:** L

**Estimate:** 4

**Acceptance criteria:**

- [ ] The user must provide the file metadata (`file_name`, `content_type` and `file_size`) together with a `title`.
- [ ] The user must optionally be able to provide a `description`, an `album_id` and the image's `visibility` as `public` or `private`.
- [ ] The `title` must not be empty and must be between 1 and 100 characters.
- [ ] The `description` must not exceed 500 characters.
- [ ] The `visibility` must only accept the values `public` or `private`.
    - The image's `visibility` must be independent of the visibility of the album it is associated with.
- [ ] The `album_id` must correspond to an existing album of the authenticated user.
- [ ] The system must validate the `content_type` and the `file_size` against the formats and maximum size allowed by the system.
- [ ] The system must generate a unique `storage_key` for the file, avoiding collisions with other files.
- [ ] The system must create the image record with `status = pending` (without `url`), associating the `storage_key` with the validated metadata (`title`, `description`, `album_id`, `visibility`), with the authenticated user through the `sub` claim, and with an expiration date (`expires_at`) equal to the `upload_url` `expires_in` (see the `Images` model, section 4).
- [ ] The system must generate a presigned S3 URL (`upload_url`) to upload the file via `PUT`, restricted to the generated `storage_key`.
- [ ] The `upload_url` must expire within a short time (5 minutes) from its generation.
- [ ] The system must log the successful and failed executions of the process without logging sensitive information.
- [ ] A `201 Created` code is returned with the `storage_key`, `upload_url` and `expires_in` (300 seconds) data.
- [ ] A `401 Unauthorized` code is returned if the `access_token` is invalid or expired.
- [ ] A `404 Not Found` code is returned if the provided `album_id` does not correspond to an existing album of the authenticated user.
- [ ] A `415 Unsupported Media Type` code is returned if the file's `content_type` is not valid.
- [ ] A `422 Unprocessable Entity` code is returned if the `file_size` exceeds the maximum allowed size, or if any required field is missing or does not meet the input schema.
- [ ] A `500 Internal Server Error` code is returned if any unexpected error occurs.

#### US-RF-309: Upload Confirmation

**As** an authenticated user,

**I want** to confirm that I completed the file upload to S3,

**So that** the system verifies the object and creates the definitive image record in the gallery.

**Endpoint:** `HTTP` - `POST /api/v1/images/confirm`

**Requires Authentication:** ✅

**Cache:** `cache:images:list`

**Priority:** High (P0)

**Size:** L

**Estimate:** 4

**Acceptance criteria:**

- [ ] The user must provide the `storage_key` returned by the upload URL request (US-RF-308).
- [ ] The system must look up the image with `status = pending` associated with the `storage_key`.
- [ ] The system must validate that the `pending` image belongs to the authenticated user through the `sub` claim.
- [ ] The system must validate that the `pending` image has not expired (`expires_at`).
- [ ] The system must validate that the image does not already have `status = confirmed`.
- [ ] The system must verify that the object corresponding to the `storage_key` exists in object storage (S3).
- [ ] The system must build the image access `url` from the `storage_key` and the bucket/CDN configuration.
- [ ] The system must complete the image's `url` field and update its `status` to `confirmed`.
- [ ] If an error occurs during object verification or image update, the system must avoid leaving the image in an inconsistent state (e.g. `url` completed but `status` still `pending`, or vice versa).
- [ ] After confirming the upload, the system must invalidate the cache by deleting the keys matching the `cache:images:list` pattern.
- [ ] The system must log the successful and failed executions of the process without logging sensitive information.
- [ ] A `201 Created` code is returned with the `id`, `title`, `description`, `url`, `visibility`, `album_id`, `owner_id`, `created_at`, `updated_at` data of the created image.
- [ ] A `401 Unauthorized` code is returned if the `access_token` is invalid or expired.
- [ ] A `403 Forbidden` code is returned if the `pending` record associated with the `storage_key` belongs to another user.
- [ ] A `404 Not Found` code is returned if the `storage_key` does not correspond to any `pending` record.
- [ ] A `409 Conflict` code is returned if the object does not yet exist in object storage, or if the `pending` record was already confirmed previously.
- [ ] A `410 Gone` code is returned if the `pending` record associated with the `storage_key` expired before confirmation.
- [ ] A `422 Unprocessable Entity` code is returned if the `storage_key` is missing or does not meet the input schema.
- [ ] A `500 Internal Server Error` code is returned if any unexpected error occurs.

#### US-RF-310: Image Query and Filtering

**As** an authenticated user,

**I want** to query the available images and filter them by different criteria,

**So that** I can explore other users' public content and manage or query my own images.

**Endpoint:** `HTTP` - `GET /api/v1/images`

**Requires Authentication:** ✅

**Cache:** `cache:images:list:{query_hash}`

**Priority:** High (P0)

**Size:** XL

**Estimate:** 3

**Acceptance criteria:**

- [ ] The query must allow filtering images by `title`, performing a partial search on the title.
- [ ] The system must allow filtering images by owner through `owner_id`.
- [ ] The system must allow filtering images by album through `album_id`.
- [ ] The system must allow filtering the results by `visibility`, accepting only the values `public` and `private`.
- [ ] The system must allow querying only the user's own images through a filter that represents resource ownership.
- [ ] The returned images must comply with the visibility rules defined in the image visibility truth table.
- [ ] The `private` value in the `visibility` filter may only be used to query images of the authenticated user.
- [ ] For users who are not the owners, images associated with an album may only be included in the results when `album_id` is specified, according to the visibility rules defined in the image visibility truth table.
- [ ] The filters must be combinable, for example `title` + `owner_id`, `album_id` + `visibility` or `title` + `album_id`.
- [ ] When filters are combined, the results must simultaneously satisfy the filtering conditions and the visibility rules defined in the image visibility truth table.
- [ ] Applying a filter must not grant access to images that would not be visible without that filter.
- [ ] The system must allow sorting the results by `created_at` or `title`.
    - Sorting must accept the ascending (`asc`) and descending (`desc`) directions.
- [ ] The system must allow paginating the results through the `page` and `page_size` parameters.
- [ ] The system must build a `query_hash` from the query parameters (`title`, `owner_id`, `album_id`, `visibility`, sorting and pagination) and use it as the `cache:images:list:{query_hash}` key.
- [ ] Before querying the database, the system must check in Redis whether the `cache:images:list:{query_hash}` key exists.
- [ ] On a **cache hit**, the system must return the stored response without querying the database.
- [ ] On a **cache miss**, the system must query the database and store the response in `cache:images:list:{query_hash}` with a TTL of **5 minutes**.
- [ ] The responses stored in the cache must include the image list and the pagination metadata.
- [ ] The system must log the successful and failed executions of the process without logging sensitive information.
- [ ] A `200 OK` code is returned with the image list and its data: `id`, `title`, `description`, `url`, `visibility`, `album_id`, `owner_id`, `created_at` and `updated_at`, together with the pagination metadata (`page`, `page_size`, `total`, `total_pages`, `has_next`).
- [ ] An empty list with a `200 OK` code is returned when no images match the provided filters.
- [ ] A `401 Unauthorized` code is returned if the `access_token` is invalid or expired.
- [ ] A `422 Unprocessable Entity` code is returned if the query parameters do not meet the expected schema.
- [ ] A `500 Internal Server Error` code is returned if any unexpected error occurs.

#### US-RF-311: Image Update

**As** an authenticated user,

**I want** to modify the information of an image that belongs to me,

**So that** I can keep its content up to date.

**Endpoint:** `HTTP` - `PATCH /api/v1/images/{image_id}`

**Requires Authentication:** ✅

**Cache:** `cache:images:list`

**Priority:** Medium (P1)

**Size:** S

**Estimate:** 2

**Acceptance criteria:**

- [ ] The system must verify that the authenticated user is the owner of the image.
- [ ] The system must allow updating the image's `title`, `description`, `visibility` and `album_id`.
- [ ] The `title` must not be empty and must be between 1 and 100 characters.
- [ ] The `description` must not exceed 500 characters.
- [ ] The `visibility` must only accept the values `public` or `private`.
- [ ] The `album_id` must correspond to an existing album of the authenticated user.
- [ ] The image's `updated_at` must be updated at the moment of the modification.
- [ ] After modifying the image, the system must invalidate the cache by deleting the keys matching the `cache:images:list` pattern.
- [ ] The system must log the successful and failed executions of the process.
- [ ] A `200 OK` code is returned with the image's updated data.
- [ ] A `401 Unauthorized` code is returned if the `access_token` is invalid or expired.
- [ ] A `403 Forbidden` code is returned if the authenticated user is not the owner of the image.
- [ ] A `404 Not Found` code is returned if the image does not exist, or if the provided `album_id` does not correspond to an existing album of the authenticated user.
- [ ] A `422 Unprocessable Entity` code is returned if any required field is missing or does not meet the input schema.
- [ ] A `500 Internal Server Error` code is returned if any unexpected error occurs.

#### US-RF-312: Image Deletion

**As** an authenticated user,

**I want** to delete an image that belongs to me,

**So that** I can remove it from the gallery.

**Endpoint:** `HTTP` - `DELETE /api/v1/images/{image_id}`

**Requires Authentication:** ✅

**Cache:** `cache:images:list`

**Priority:** Low (P2)

**Size:** XS

**Estimate:** 1

**Acceptance criteria:**

- [ ] The system must verify that the authenticated user is the owner of the image.
- [ ] The system must delete the image record and its file from object storage.
- [ ] The comments and ratings associated with the image must be deleted along with the image.
- [ ] After deleting the image, the system must invalidate the cache by deleting the keys matching the `cache:images:list` pattern.
- [ ] The system must log the successful and failed executions of the process.
- [ ] A `204 No Content` code is returned if the image was deleted successfully.
- [ ] A `401 Unauthorized` code is returned if the `access_token` is invalid or expired.
- [ ] A `403 Forbidden` code is returned if the authenticated user is not the owner of the image.
- [ ] A `404 Not Found` code is returned if the image does not exist.
- [ ] A `500 Internal Server Error` code is returned if any unexpected error occurs.

### Module 4 - Comments:

> **Visibility summary:** Comments depend on the image they are associated with. They can only be created (US-RF-413) and queried (US-RF-414) when the image is visible to the authenticated user, according to the visibility rules defined in the image visibility truth table (Module 3). Updating (US-RF-415) and deleting (US-RF-416) a comment is restricted to its author.

#### US-RF-413: Comment Creation

**As** an authenticated user,

**I want** to publish a comment on an image,

**So that** I can share my opinion with other users.

**Endpoint:** `HTTP` - `POST /api/v1/images/{image_id}/comments`

**Requires Authentication:** ✅

**Cache:** `cache:comments:list:{image_id}`

**Priority:** High (P0)

**Size:** S

**Estimate:** 2

**Acceptance criteria:**

- [ ] The user must provide a valid `access_token` through the authentication mechanism defined by the API.
- [ ] The user must provide the comment's `content`.
- [ ] The `content` must not be empty and must be between 1 and 500 characters.
- [ ] The image being commented on must exist.
- [ ] The system must associate the comment with the authenticated user through the `sub` claim.
- [ ] After creating the comment, the system must invalidate the cache by deleting the keys matching the `cache:comments:list:{image_id}` pattern.
- [ ] The system must log the successful and failed executions of the process.
- [ ] A `201 Created` code is returned with the `id`, `content`, `image_id`, `author_id`, `created_at`, `updated_at` data of the created comment.
- [ ] A `401 Unauthorized` code is returned if the `access_token` is invalid or expired.
- [ ] A `404 Not Found` code is returned if the image does not exist.
- [ ] A `422 Unprocessable Entity` code is returned if any required field is missing or does not meet the input schema.
- [ ] A `500 Internal Server Error` code is returned if any unexpected error occurs.

#### US-RF-414: Comment Query

**As** an authenticated user,

**I want** to query the comments associated with an image,

**So that** I can see what other users think about it.

**Endpoint:** `HTTP` - `GET /api/v1/images/{image_id}/comments`

**Requires Authentication:** ✅

**Cache:** `cache:comments:list:{image_id}:{query_hash}`

**Priority:** High (P0)

**Size:** S

**Estimate:** 2

**Acceptance criteria:**

- [ ] The system must return only the comments of the image specified by `image_id`.
- [ ] The image must be visible to the authenticated user according to the visibility rules defined in the image visibility truth table.
- [ ] The system must allow paginating the results through the `page` and `page_size` parameters.
- [ ] The system must allow sorting the results by `created_at`.
    - Sorting must accept the ascending (`asc`) and descending (`desc`) directions.
- [ ] The system must build a `query_hash` from the pagination and sorting and use it as part of the `cache:comments:list:{image_id}:{query_hash}` key.
- [ ] Before querying the database, the system must check in Redis whether the `cache:comments:list:{image_id}:{query_hash}` key exists.
- [ ] On a **cache hit**, the system must return the stored response without querying the database.
- [ ] On a **cache miss**, the system must query the database and store the response in `cache:comments:list:{image_id}:{query_hash}` with a TTL of **5 minutes**.
- [ ] The responses stored in the cache must include the comment list and the pagination metadata.
- [ ] The system must log the successful and failed executions of the process without logging sensitive information.
- [ ] A `200 OK` code is returned with the comment list and its data: `id`, `content`, `image_id`, `author_id`, `created_at`, `updated_at`, together with the pagination metadata (`page`, `page_size`, `total`, `total_pages`, `has_next`).
- [ ] An empty list with a `200 OK` code is returned when the image has no comments.
- [ ] A `401 Unauthorized` code is returned if the `access_token` is invalid or expired.
- [ ] A `404 Not Found` code is returned if the image does not exist or is not visible to the authenticated user.
- [ ] A `422 Unprocessable Entity` code is returned if the query parameters do not meet the expected schema.
- [ ] A `500 Internal Server Error` code is returned if any unexpected error occurs.

#### US-RF-415: Comment Update

**As** an authenticated user,

**I want** to modify the content of a comment I have published,

**So that** I can correct or update my opinion.

**Endpoint:** `HTTP` - `PATCH /api/v1/comments/{comment_id}`

**Requires Authentication:** ✅

**Cache:** `cache:comments:list:{image_id}`

**Priority:** Medium (P1)

**Size:** S

**Estimate:** 1

**Acceptance criteria:**

- [ ] The system must verify that the authenticated user is the author of the comment.
- [ ] The user must be able to update the comment's `content`.
- [ ] The `content` must not be empty and must be between 1 and 500 characters.
- [ ] The comment's `updated_at` must be updated at the moment of the modification.
- [ ] After modifying the comment, the system must invalidate the cache by deleting the keys matching the `cache:comments:list:{image_id}` pattern.
- [ ] The system must log the successful and failed executions of the process.
- [ ] A `200 OK` code is returned with the comment's updated data.
- [ ] A `401 Unauthorized` code is returned if the `access_token` is invalid or expired.
- [ ] A `403 Forbidden` code is returned if the authenticated user is not the author of the comment.
- [ ] A `404 Not Found` code is returned if the comment does not exist.
- [ ] A `422 Unprocessable Entity` code is returned if any required field is missing or does not meet the input schema.
- [ ] A `500 Internal Server Error` code is returned if any unexpected error occurs.

#### US-RF-416: Comment Deletion

**As** an authenticated user,

**I want** to delete a comment I have published,

**So that** I can remove my opinion from the image.

**Endpoint:** `HTTP` - `DELETE /api/v1/comments/{comment_id}`

**Requires Authentication:** ✅

**Cache:** `cache:comments:list:{image_id}`

**Priority:** Low (P2)

**Size:** XS

**Estimate:** 1

**Acceptance criteria:**

- [ ] The user must provide a valid `access_token` through the authentication mechanism defined by the API.
- [ ] The system must verify that the authenticated user is the author of the comment.
- [ ] The system must delete the comment from the database.
- [ ] After deleting the comment, the system must invalidate the cache by deleting the keys matching the `cache:comments:list:{image_id}` pattern.
- [ ] The system must log the successful and failed executions of the process.
- [ ] A `204 No Content` code is returned if the comment was deleted successfully.
- [ ] A `401 Unauthorized` code is returned if the `access_token` is invalid or expired.
- [ ] A `403 Forbidden` code is returned if the authenticated user is not the author of the comment.
- [ ] A `404 Not Found` code is returned if the comment does not exist.
- [ ] A `500 Internal Server Error` code is returned if any unexpected error occurs.

### Module 5 - Ratings:

> **Visibility summary:** Ratings depend on the image they are associated with. They can only be created (US-RF-517) and have their aggregates queried (US-RF-518) when the image is visible to the authenticated user, according to the visibility rules defined in the image visibility truth table (Module 3). Updating (US-RF-519) and deleting (US-RF-520) a rating is restricted to its author.

#### US-RF-517: Rating Creation

**As** an authenticated user,

**I want** to rate an image with a score between 1 and 5,

**So that** I can indicate how much I like it.

**Endpoint:** `HTTP` - `POST /api/v1/images/{image_id}/ratings`

**Requires Authentication:** ✅

**Cache:** `cache:image:ratings:{image_id}`

**Priority:** High (P0)

**Size:** S

**Estimate:** 2

**Acceptance criteria:**

- [ ] The user must provide a `score` with an integer value between 1 and 5.
- [ ] The image being rated must exist.
- [ ] The system must prevent a user from rating the same image twice.
- [ ] The system must associate the rating with the authenticated user through the `sub` claim.
- [ ] After creating the rating, the system must invalidate the cache by deleting the `cache:image:ratings:{image_id}` key.
- [ ] The system must log the successful and failed executions of the process.
- [ ] A `201 Created` code is returned with the `id`, `score`, `image_id`, `user_id`, `created_at`, `updated_at` data of the created rating.
- [ ] A `401 Unauthorized` code is returned if the `access_token` is invalid or expired.
- [ ] A `404 Not Found` code is returned if the image does not exist.
- [ ] A `409 Conflict` code is returned if the user has already rated the image.
- [ ] A `422 Unprocessable Entity` code is returned if any required field is missing or does not meet the input schema.
- [ ] A `500 Internal Server Error` code is returned if any unexpected error occurs.

#### US-RF-518: Querying an Image's Ratings

**As** an authenticated user,

**I want** to query the number of ratings received and the average rating of an image,

**So that** I can know the general opinion about it.

**Endpoint:** `HTTP` - `GET /api/v1/images/{image_id}/ratings`

**Requires Authentication:** ✅

**Cache:** `cache:image:ratings:{image_id}`

**Priority:** High (P0)

**Size:** S

**Estimate:** 2

**Acceptance criteria:**

- [ ] The image must be visible to the authenticated user according to the visibility rules defined in the image visibility truth table.
- [ ] The system must compute the total number of ratings received (`rating_count`) and the average rating (`rating_avg`) of the image.
- [ ] The `rating_avg` must be computed precisely from the `score` of the existing ratings.
- [ ] Before querying the database, the system must check in Redis whether the `cache:image:ratings:{image_id}` key exists.
- [ ] On a **cache hit**, the system must return the stored response without querying the database.
- [ ] On a **cache miss**, the system must query the database and store the response in `cache:image:ratings:{image_id}` with a TTL of **5 minutes**.
- [ ] The system must log the successful and failed executions of the process without logging sensitive information.
- [ ] A `200 OK` code is returned with the `image_id`, `rating_count` and `rating_avg` data.
- [ ] A `200 OK` code is returned with `rating_count` as `0` and `rating_avg` as `null` when the image has no ratings.
- [ ] A `401 Unauthorized` code is returned if the `access_token` is invalid or expired.
- [ ] A `404 Not Found` code is returned if the image does not exist or is not visible to the authenticated user.
- [ ] A `500 Internal Server Error` code is returned if any unexpected error occurs.

#### US-RF-519: Rating Update

**As** an authenticated user,

**I want** to modify the rating I have made on an image,

**So that** I can update my score.

**Endpoint:** `HTTP` - `PATCH /api/v1/ratings/{rating_id}`

**Requires Authentication:** ✅

**Cache:** `cache:image:ratings:{image_id}`

**Priority:** Medium (P1)

**Size:** S

**Estimate:** 1

**Acceptance criteria:**

- [ ] The user must provide a valid `access_token` through the authentication mechanism defined by the API.
- [ ] The system must verify that the authenticated user is the author of the rating.
- [ ] The user must be able to update the rating's `score`.
- [ ] The `score` must only accept integer values between 1 and 5.
- [ ] The rating's `updated_at` must be updated at the moment of the modification.
- [ ] After modifying the rating, the system must invalidate the cache by deleting the `cache:image:ratings:{image_id}` key.
- [ ] The system must log the successful and failed executions of the process.
- [ ] A `200 OK` code is returned with the rating's updated data.
- [ ] A `401 Unauthorized` code is returned if the `access_token` is invalid or expired.
- [ ] A `403 Forbidden` code is returned if the authenticated user is not the author of the rating.
- [ ] A `404 Not Found` code is returned if the rating does not exist.
- [ ] A `422 Unprocessable Entity` code is returned if any required field is missing or does not meet the input schema.
- [ ] A `500 Internal Server Error` code is returned if any unexpected error occurs.

#### US-RF-520: Rating Deletion

**As** an authenticated user,

**I want** to delete the rating I have made on an image,

**So that** I can withdraw my score.

**Endpoint:** `HTTP` - `DELETE /api/v1/ratings/{rating_id}`

**Requires Authentication:** ✅

**Cache:** `cache:image:ratings:{image_id}`

**Priority:** Low (P2)

**Size:** XS

**Estimate:** 1

**Acceptance criteria:**

- [ ] The system must verify that the authenticated user is the author of the rating.
- [ ] The system must delete the rating from the database.
- [ ] After deleting the rating, the system must invalidate the cache by deleting the `cache:image:ratings:{image_id}` key.
- [ ] The system must log the successful and failed executions of the process.
- [ ] A `204 No Content` code is returned if the rating was deleted successfully.
- [ ] A `401 Unauthorized` code is returned if the `access_token` is invalid or expired.
- [ ] A `403 Forbidden` code is returned if the authenticated user is not the author of the rating.
- [ ] A `404 Not Found` code is returned if the rating does not exist.
- [ ] A `500 Internal Server Error` code is returned if any unexpected error occurs.

---

## Data Models

### Persistent Models

#### Module 1 - Authentication:

##### `Users` data model - (PostgreSQL)

|Field|Type|Constraints|Description|
|---|---|---|---|
|`id`|`UUID`|Primary key, not null|Unique user identifier.|
|`name`|`VARCHAR(100)`|Not null|User name. Must contain between 3 and 100 characters.|
|`email`|`VARCHAR(255)`|Unique, not null|Email address used to identify the user and log in.|
|`password_hash`|`VARCHAR(255)`|Not null|Password hash generated through Argon2. The password is never stored in plain text.|
|`created_at`|`TIMESTAMP WITH TIME ZONE`|Not null, default `CURRENT_TIMESTAMP`|Date and time when the user was created.|
|`updated_at`|`TIMESTAMP WITH TIME ZONE`|Not null, default `CURRENT_TIMESTAMP`|Date and time of the user's last modification.|

#### Module 2 - Albums:

##### `Albums` data model - (PostgreSQL)

|Field|Type|Constraints|Description|
|---|---|---|---|
|`id`|`UUID`|Primary key, not null|Unique album identifier.|
|`owner_id`|`UUID`|Foreign key → `users.id`, not null|User who owns the album.|
|`title`|`VARCHAR(100)`|Not null|Album title. Must contain between 1 and 100 characters.|
|`description`|`VARCHAR(500)`|Nullable|Optional album description. Must not exceed 500 characters.|
|`visibility`|`ENUM('public','private')`|Not null, default `private`|Album visibility. Only accepts the values `public` or `private`.|
|`created_at`|`TIMESTAMP WITH TIME ZONE`|Not null, default `CURRENT_TIMESTAMP`|Date and time when the album was created.|
|`updated_at`|`TIMESTAMP WITH TIME ZONE`|Not null, default `CURRENT_TIMESTAMP`, updated on modification|Date and time of the album's last modification.|

#### Module 3 - Images:

##### `Images` data model - (PostgreSQL)

|Field|Type|Constraints|Description|
|---|---|---|---|
|`id`|`UUID`|Primary key, not null|Unique image identifier.|
|`owner_id`|`UUID`|Foreign key → `users.id`, not null|User who owns the image.|
|`album_id`|`UUID`|Foreign key → `albums.id`, nullable, `ON DELETE SET NULL`|Album the image is associated with, if any.|
|`title`|`VARCHAR(100)`|Not null|Image title. Must contain between 1 and 100 characters.|
|`description`|`VARCHAR(500)`|Nullable|Optional image description. Must not exceed 500 characters.|
|`visibility`|`ENUM('public','private')`|Not null, default `private`|Image visibility. Only accepts the values `public` or `private`.|
|`status`|`ENUM('pending','confirmed')`|Not null, default `pending`|Upload state. `pending` while awaiting S3 confirmation (RF-308); it becomes `confirmed` in RF-309 and can no longer change.|
|`storage_key`|`VARCHAR(255)`|Unique, not null|Unique file identifier in object storage.|
|`url`|`VARCHAR(500)`|Nullable|File access URL. Null while `status = pending`; completed when the upload is confirmed (RF-309).|
|`expires_at`|`TIMESTAMP WITH TIME ZONE`|Not null|Point from which a `pending` record is no longer valid for confirmation (RF-309, `410 Gone`). No effect once `status = confirmed`.|
|`created_at`|`TIMESTAMP WITH TIME ZONE`|Not null, default `CURRENT_TIMESTAMP`|Date and time when the image upload was requested.|
|`updated_at`|`TIMESTAMP WITH TIME ZONE`|Not null, default `CURRENT_TIMESTAMP`, updated on modification|Date and time of the image's last modification.|

**Additional constraint:** `CHECK (status = 'pending' OR url IS NOT NULL)` — guarantees at the database level that no `confirmed` image can be left without a `url`, even if the application layer had a bug.

#### Module 4 - Comments:

##### `Comments` data model - (PostgreSQL)

|Field|Type|Constraints|Description|
|---|---|---|---|
|`id`|`UUID`|Primary key, not null|Unique comment identifier.|
|`content`|`VARCHAR(500)`|Not null|Comment content. Must be between 1 and 500 characters.|
|`image_id`|`UUID`|Foreign key → `images.id`, not null, `ON DELETE CASCADE`|Image the comment is published on.|
|`author_id`|`UUID`|Foreign key → `users.id`, not null|User who authored the comment.|
|`created_at`|`TIMESTAMP WITH TIME ZONE`|Not null, default `CURRENT_TIMESTAMP`|Date and time when the comment was created.|
|`updated_at`|`TIMESTAMP WITH TIME ZONE`|Not null, default `CURRENT_TIMESTAMP`, updated on modification|Date and time of the comment's last modification.|

#### Module 5 - Ratings:

##### `Ratings` data model - (PostgreSQL)

|Field|Type|Constraints|Description|
|---|---|---|---|
|`id`|`UUID`|Primary key, not null|Unique rating identifier.|
|`score`|`SMALLINT`|Not null, `CHECK (score BETWEEN 1 AND 5)`|Score given to the image. Must be an integer between 1 and 5.|
|`image_id`|`UUID`|Foreign key → `images.id`, not null, `ON DELETE CASCADE`|Rated image.|
|`user_id`|`UUID`|Foreign key → `users.id`, not null|User who made the rating.|
|`created_at`|`TIMESTAMP WITH TIME ZONE`|Not null, default `CURRENT_TIMESTAMP`|Date and time when the rating was created.|
|`updated_at`|`TIMESTAMP WITH TIME ZONE`|Not null, default `CURRENT_TIMESTAMP`, updated on modification|Date and time of the rating's last modification.|

**Uniqueness constraint:** the `(image_id, user_id)` combination must be unique, guaranteeing a single rating per user and image.

### Cache Structures - Redis

|Key|Type|Value|TTL|Purpose|
|---|---|---|---|---|
|`cache:login:attempts:{email}:{ip}`|String|Failed attempt counter|15 minutes|Record failed authentication attempts.|
|`cache:login:lock:{email}:{ip}`|String|Lockout marker|15 minutes|Temporarily block authentication after **5 consecutive failed attempts**.|
|`cache:access_token:revoked:{jti}`|String|Identifier of the revoked `access_token`|Remaining expiry time of the `access_token` (max. 15 minutes)|Blacklist of `access_token`s invalidated during logout.|
|`cache:albums:list:{query_hash}`|JSON|Paginated response of the album query|5 minutes|Store album query results and speed up searches (hit/miss).|
|`cache:images:list:{query_hash}`|JSON|Paginated response of the image query|5 minutes|Store image query results and speed up searches (hit/miss).|
|`cache:comments:list:{image_id}:{query_hash}`|JSON|Paginated response of an image's comments|5 minutes|Store an image's comments and speed up queries (hit/miss).|
|`cache:image:ratings:{image_id}`|JSON|Rating count and average of an image|5 minutes|Store an image's rating aggregates and speed up queries (hit/miss).|
