# Screenshot Capture

## Required screenshots

- `assets/screenshots/interface_home.png`
- `assets/screenshots/report_generation.png`
- `assets/screenshots/knowledge_graph.png`

## Safety checklist

Before committing a screenshot, confirm it does not show:

- secrets, tokens, API keys, cookies, or passwords
- real user data or real business material
- local sensitive paths
- private IP addresses
- backend disconnected banners
- debug panels
- dry-run labels
- Runtime Manifest screens
- raw internal scoring or AutoJudge details

## Manual fallback

1. Start backend and frontend with `scripts/local_demo_start.md`.
2. Open `http://127.0.0.1:5173/`.
3. Capture only product-facing screens.
4. Save files under `assets/screenshots/`.
5. Re-run `scripts/sanitize_check.ps1` and inspect the README image links.
