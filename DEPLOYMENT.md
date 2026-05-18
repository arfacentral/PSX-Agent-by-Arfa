# Deploying PSX Agent by Arfa

This app can be shared with family. It is not limited to your computer.

The easiest deployment is **Streamlit Community Cloud** because the GUI can run the screener directly without the separate FastAPI backend.

## Recommended: Streamlit Community Cloud

Use this if you want a simple web link for family members.

### 1. Put This Folder On GitHub

Create a GitHub repository and upload the project files.

Do not upload:

- `.venv/`
- `.env`
- `data/cache/`
- `reports/`

The `.gitignore` file already excludes those.

### 2. Create The Streamlit App

Go to:

```text
https://share.streamlit.io/
```

Choose:

- Repository: your PSX agent repository
- Branch: `main`
- Main file path:

```text
app.py
```

### 3. Share The Link

Streamlit will give you a public URL. Send that URL to your family.

The app will run in `Local engine` mode, which means the Streamlit app itself fetches PSX Terminal data and builds the recommendations.

## Current Fast Mode

The deployed app is configured for a fast pre-market workflow:

- 20 watched tickers
- no API key
- no heavy historical candle calls
- target load time under 30 seconds
- recommendations are labelled as screening ideas

Edit `WATCHLIST` in `.env.example` or in hosting environment settings if you want different tickers.

## Option: Private Deployment

If you do not want a public link, use a private host such as:

- Render
- Railway
- Fly.io
- a small VPS

For Docker-style hosts, use:

```text
Dockerfile
```

and run:

```bash
streamlit run gui/app.py --server.address 0.0.0.0 --server.port 8501
```

## Option: Share From Your Own Computer

This is less reliable because your computer must stay on.

You can use a tunnel service like Cloudflare Tunnel or Tailscale Funnel to expose the local app. Only do this if you are comfortable managing access.

## Morning Usage

Family members can open the deployed link before the PSX market opens.

They should treat the output as a screener:

- check the symbol in their broker terminal
- verify price and volume
- confirm spread/liquidity
- never trade only because the app says `BUY WATCH`
