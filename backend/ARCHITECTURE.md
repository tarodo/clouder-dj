# ClouderApp Backend Architecture

This document outlines the proposed backend architecture for the ClouderApp MVP, based on the initial project description. It builds upon the existing foundation of user authentication, core music entities, and a service-oriented structure.

## 1. Core Concepts & Data Flow

The application's main purpose is to help DJs sort new music into personal playlists. This workflow is structured into three "layers":

-   **Bronze Layer**: A temporary, weekly playlist of all new tracks in a specific genre. This is the source for curation.
-   **Silver Layer**: A set of temporary, weekly playlists corresponding to the user's personal categories (e.g., "Warm-up", "Peak Time"). Tracks are moved from Bronze to Silver.
-   **Golden Layer**: A set of permanent, "master" playlists for each category. Tracks are promoted from Silver to Golden.

## 2. Data Ingestion & Enrichment (MVP Points 1-3)

The existing `ExternalData` model is well-suited for this. The process will be:

1.  **Scraping Service**: A background service (e.g., using Taskiq, which is already in `requirements.txt`) will periodically fetch new releases from Beatport by genre.
2.  **Internal Database Registration**:
    -   For each new track, the service will check if the `Artist`, `Label`, `Release`, and `Track` already exist in our database.
    -   If not, new entries are created with a ClouderApp internal ID.
    -   An `ExternalData` entry is created to link our internal `Track` ID to its Beatport ID and store raw data.
3.  **Spotify Enrichment**:
    -   Another background task will take our internal entities (Tracks, Artists, etc.) and search for them on Spotify.
    -   When a match is found, another `ExternalData` entry is created with `provider='SPOTIFY'` and the Spotify ID/URI. This is crucial for playback and playlist management.

## 3. New Database Models

To support the user-facing curation workflow (MVP Points 4-12), the following new database models are proposed.

### `Style`

Represents a music genre/style that users can work with. This could be a pre-populated table.

-   `id` (PK)
-   `name` (String, unique, e.g., "Techno", "House")

### `UserCategory` (Golden Layer)

Represents a user's custom category for a given style. This is the definition for both Golden and Silver layer playlists.

-   `id` (PK)
-   `user_id` (FK to `users.id`)
-   `style_id` (FK to `styles.id`)
-   `name` (String, e.g., "Warm Up", "Peak Time")
-   `spotify_playlist_id` (String): The ID of the permanent "Golden Layer" Spotify playlist.
-   `is_trash` (Boolean, default=False): A flag to identify the special "Trash" category.

*A unique constraint on `(user_id, style_id, name)` is recommended.*

### `CurationPeriod` (Bronze Layer)

Represents a user's curation session for a specific style and time period.

-   `id` (PK)
-   `user_id` (FK to `users.id`)
-   `style_id` (FK to `styles.id`)
-   `year` (Integer)
-   `week` (Integer)
-   `status` (Enum: `IN_PROGRESS`, `SORTED`): The status of the overall Bronze layer playlist for this period.
-   `bronze_spotify_playlist_id` (String): The ID of the temporary "Bronze Layer" Spotify playlist.

*A unique constraint on `(user_id, style_id, year, week)` is recommended.*

### `PeriodPlaylist` (Silver Layer)

An intermediary table that represents a "Silver Layer" playlist for a specific `CurationPeriod` and `UserCategory`.

-   `id` (PK)
-   `curation_period_id` (FK to `curation_periods.id`)
-   `user_category_id` (FK to `user_categories.id`)
-   `spotify_playlist_id` (String): The ID of the temporary "Silver Layer" Spotify playlist.

### `CurationTrack`

Tracks the status of an individual track within a `CurationPeriod`.

-   `id` (PK)
-   `curation_period_id` (FK to `curation_periods.id`)
-   `track_id` (FK to `tracks.id`)
-   `status` (Enum: `UNSORTED`, `SORTED`): The status of the track within the Bronze layer.
-   `current_silver_playlist_id` (FK to `period_playlists.id`, nullable): Tracks which Silver playlist the track currently resides in.

*A unique constraint on `(curation_period_id, track_id)` is recommended.*

## 4. API Endpoints & Services

New services and API endpoints will be required to manage this logic.

-   **`StyleService` & `/styles` endpoint**: To list available music styles.
-   **`CurationService` & `/curation` endpoints**: This will be the main service to handle the user workflow.
    -   `GET /curation/periods`: List a user's curation periods (e.g., by style).
    -   `POST /curation/periods`: Start a new curation period for a style, year, and week. This will trigger:
        -   Creation of `CurationPeriod`, `PeriodPlaylist` records.
        -   Creation of the actual Bronze and Silver playlists on Spotify via their API.
        -   Populating the Bronze playlist with new tracks.
    -   `GET /curation/periods/{period_id}/tracks`: Get tracks for a curation period (the Bronze playlist contents).
    -   `POST /curation/tracks/{curation_track_id}/move`: The core action. Moves a track from Bronze to a Silver playlist. This updates the `CurationTrack` status and uses the Spotify API to move the track between playlists.
    -   `POST /curation/tracks/{track_id}/promote`: Moves a track from a Silver playlist to the corresponding Golden playlist.

## 5. User Workflow Implementation Steps

1.  **User Login**: (Already implemented).
2.  **Select Style**: User selects a style from `/styles`.
3.  **Setup Categories**: If it's the first time for this style, the user is prompted to create `UserCategory` entries. The backend creates the corresponding "Golden" playlists on Spotify.
4.  **Select Period**: User selects a year and week. The client calls `POST /curation/periods`.
5.  **Curation (Bronze -> Silver)**: The user listens to the Bronze playlist. The UI shows buttons for each category. Clicking a button calls `POST /curation/tracks/{...}/move` with the target `PeriodPlaylist` (Silver).
6.  **Review (Silver -> Golden)**: Once the Bronze playlist is fully sorted (`status=SORTED`), the user can review the Silver playlists. The UI will have a "promote to golden" button, which calls `POST /curation/tracks/{...}/promote`.

This architecture provides a scalable and maintainable structure to build the ClouderApp features.
