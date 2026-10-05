# Portfolio site

Static portfolio with a demo options-trading dashboard (sample data only).

## Files
- `index.html` – home page (edit the text, links, and project cards)
- `dashboard.html` + `dashboard.js` – demo dashboard; trades live in the `trades` array at the top of `dashboard.js`
- `style.css` – shared styles (light/dark follows the visitor's system setting)

## Publish on GitHub Pages
1. On github.com, create a new **public** repository. For a root URL like `https://<username>.github.io`, name it exactly `<username>.github.io`. Any other name works too and is served at `https://<username>.github.io/<repo-name>/`.
2. Upload all files to the repo (**Add file → Upload files**, then commit).
3. Go to **Settings → Pages**. Under **Build and deployment**, set Source to **Deploy from a branch**, pick `main` and `/ (root)`, then Save.
4. Wait a minute or two, then open the URL shown at the top of the Pages settings.

## Before you go live
- Replace the placeholder email, LinkedIn, and GitHub links in `index.html`.
- Keep the dashboard on synthetic data. Never commit real account numbers, balances, or brokerage exports to a public repo.
