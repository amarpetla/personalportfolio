# Personal Portfolio
# Personal Portfolio from Resume

This repo parses a PDF resume into JSON and renders a static portfolio site.

- Live site: https://amarpetla.github.io/personalportfolio/
- Parsed JSON (root): https://amarpetla.github.io/personalportfolio/parsed_resume.json

Regenerate data locally:

1. Put your PDF at `resume/staff_Amar_Petla.pdf` (or update `PDF_PATH` in `parse_resume.py`).
2. Run the parser: `python parse_resume.py`
3. Commit and push to trigger GitHub Pages deploy.

[![Publish (gh-pages branch)](https://github.com/amarpetla/personalportfolio/actions/workflows/gh-pages-branch.yml/badge.svg)](https://github.com/amarpetla/personalportfolio/actions/workflows/gh-pages-branch.yml)

- Live site: https://amarpetla.github.io/personalportfolio/


This repository contains a minimal, dark-themed, static personal portfolio site generated from a PDF resume.

## Structure
```
resume/                # Original resume PDF + generated text/JSON
site/                  # Static site assets (HTML/CSS/JS)
parse_resume.py        # Script to extract + heuristically structure resume content
requirements.txt       # Python dependency for PDF parsing
```

## Workflow
1. Put/update your resume PDF in `resume/` (currently: `staff_Amar_Petla.pdf`).
2. (Re)run the parser:
```bash
pip install -r requirements.txt
python parse_resume.py
```
3. Open `site/index.html` in a browser (or serve the `site/` folder) to see the portfolio pulling from `resume/parsed_resume.json`.

## Deploy to GitHub Pages

This repo ships with an automated Pages workflow (`.github/workflows/deploy.yml`).

Steps:
1. Ensure your default branch is `main` and the workflow file is committed.
2. Push changes to `main` – the workflow will:
	- Install dependencies
	- Run `parse_resume.py` to regenerate JSON
	- Copy the `site/` folder and generated JSON into a `public` artifact
	- Deploy to GitHub Pages
3. In the repo Settings > Pages, confirm "Build and deployment" is set to "GitHub Actions" (first run sets this automatically).
4. Your site will be available at: `https://<your-username>.github.io/<repository-name>/`.

Because the workflow copies `parsed_resume.json` and `json_resume.json` into the site root, the frontend fetch (`parsed_resume.json`) works under Pages.

To trigger a manual redeploy without code changes: use the "Run workflow" button in the Actions tab.

### Custom Domain (amarpetla.com)
1. Create a DNS A record for `@` pointing to GitHub Pages IPs:
	- 185.199.108.153
	- 185.199.109.153
	- 185.199.110.153
	- 185.199.111.153
2. (Optional) Add a `www` CNAME record pointing to `<username>.github.io.` or directly to `amarpetla.com`.
3. Ensure the `site/CNAME` file contains `amarpetla.com` (already present).
4. In repo Settings > Pages, add `amarpetla.com` as the custom domain and enable HTTPS (wait for certificate provisioning).
5. Future deploys will preserve the CNAME through the workflow (file is copied inside `site/`).

## Customization
Edit `site/index.html`, `site/styles.css`, or `site/script.js` for layout & design. Improve parsing rules in `parse_resume.py` if sections are mis-detected.

## Next Ideas
- Add a simple backend for a contact form.
- Export data to JSON Resume schema.
- Add dark/light theme toggle.
- Improve experience/company parsing heuristics.
- Add SEO meta tags & sitemap.
- Add print-friendly stylesheet / PDF export.

---
Generated scaffold. Adjust freely.