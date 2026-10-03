# SteamScope — teammate access

**Simplest option: use the app running on the host's Mac.** Everyone connects
to the same trusted Wi-Fi/LAN. Teammates need only a browser—no Git clone,
Python, Node.js, MySQL, or dataset downloads.

## Host: start the app

**1. Start MySQL** in Terminal:

```sh
brew services start mysql
```

Use the existing populated `steamscope` database. Do not rerun imports.

**2. Start the backend** in one terminal. This assumes the environment has
already been installed and `backend/.env` contains working MySQL credentials.

```sh
cd ~/Downloads/SteamScope/SteamScope-main/backend
source .venv/bin/activate
python3 -m uvicorn app.main:app --env-file .env --host 127.0.0.1 --port 8000
```

**3. Start the frontend for the local network** in another terminal. If a
frontend is already running on port 5173, stop it with Ctrl+C first.

```sh
cd ~/Downloads/SteamScope/SteamScope-main/frontend
npx vite --host 0.0.0.0
```

Copy the **Network** URL printed by Vite, for example
`http://192.168.1.25:5173/`, and send it to your teammates. The address above is
an example; use the one shown on your Mac. Keep both terminals open and the
Mac awake. Ctrl+C stops each server after the session.

## Teammates: open and explore

1. Join the same Wi-Fi/LAN and open the host's Network URL in your browser.
   Do not use `localhost` or `127.0.0.1`; those refer to your own computer.
2. Choose a demo profile. Use different profiles to avoid changing each
   other's collections. Everyone is using the same database; edits persist.
3. Explore Discover, game details, For you, My library, Wishlist, Favorites,
   Rankings, Analytics, and Behind SteamScope.

## If it does not open

- **Cannot reach the page:** check the host is awake, both computers share the
  network, and Vite is running with `--host 0.0.0.0`. Allow Node/Vite through
  the Mac firewall on this trusted network if prompted. Guest/campus Wi-Fi
  may block communication between devices.
- **Page loads but data fails:** the host should open
  `http://127.0.0.1:8000/health/ready` and check MySQL, `.env`, and backend logs.
- **Different networks:** this local address will not work. Arrange a shared
  network or a separate private remote-access setup; no internet deployment
  is configured. Do not expose MySQL or forward router ports for this demo.

**Demo limits:** profile selection is not login, so share only with trusted
teammates. The frontend forwards API requests to the host's local backend;
teammates do not need the database password. The presentation PDF download
is still unfinished. Access from a second physical computer has not yet been
verified.
