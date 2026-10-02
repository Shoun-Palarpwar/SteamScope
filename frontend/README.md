# SteamScope frontend

A React + Vite interface using the local FastAPI backend. The design uses ink-purple
backgrounds, acid-lime accents, lavender panels, oversized editorial typography,
and real game artwork. The discovery screen combines a cinematic spotlight with
a personalized recommendations panel. Shared cards carry the visual identity
through collections, recommendations, rankings, and analytics.

`src/styles.css` contains the base layout and components; `src/identity.css`
defines the visual theme and responsive adjustments. Desktop (1440px) and phone
(390px) layouts have been visually checked, including discovery and analytics.

## Run locally

Start MySQL and the backend as described in `../backend/README.md`. Then:

```sh
cd /Users/shounpalarpwar/Downloads/SteamScope/SteamScope-main/frontend
npm install
npm run dev
```

Open http://127.0.0.1:5173. Vite proxies `/api` requests to port 8000. Keep both
servers running. `npm run build` checks and bundles the frontend; production
hosting must route `/api` to FastAPI (the development proxy is not bundled).

## Try it

- Discover: search/filter/sort games and open game details.
- Add a game to your library or wishlist in the details dialog.
- Favorite owned games using the heart on their card or the detail view.
- For you: recommendations include a matching reason and update after edits.
- Switch demo profiles using the top-right picker; search to find any of the
  3,000 profiles. The selected profile is remembered on this browser.
- Rankings distinguish stored Steam metrics from simulated community data.
- Analytics displays genre, platform, and release-year summaries.

Collection actions persist to MySQL. No login is required for this local demo.
Empty, loading, error, and missing-artwork states are included. Game descriptions
are displayed as plain text; HTML from the catalog is never injected into React.
Images come from catalog URLs; fonts have local fallbacks if Google Fonts is
unavailable. Layout adapts from a desktop sidebar to horizontally scrollable
navigation on narrow screens.
