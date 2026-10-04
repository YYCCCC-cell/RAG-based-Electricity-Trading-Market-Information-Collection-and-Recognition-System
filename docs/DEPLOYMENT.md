# Deployment and maintenance

## Canonical links

- [Public application](https://yycccc-cell.github.io/RAG-based-Electricity-Trading-Market-Information-Collection-and-Recognition-System/)
- [Source repository](https://github.com/YYCCCC-cell/RAG-based-Electricity-Trading-Market-Information-Collection-and-Recognition-System)
- [Deployment history](https://github.com/YYCCCC-cell/RAG-based-Electricity-Trading-Market-Information-Collection-and-Recognition-System/actions/workflows/pages.yml)
- [CI history](https://github.com/YYCCCC-cell/RAG-based-Electricity-Trading-Market-Information-Collection-and-Recognition-System/actions/workflows/ci.yml)

GitHub Pages hosts the public static application. Visitors do not need Python, an API key or access to the maintainer's computer. The site is a fixed-snapshot demonstration, not a hosted Python API, scheduled crawler or generative-model service.

## Publishing configuration

In **Settings → Pages → Build and deployment**, the source is **GitHub Actions**. Keep both workflow files in the repository:

| File | Responsibility | Trigger |
| --- | --- | --- |
| `.github/workflows/ci.yml` | Test; validate saved and regenerated results | Pushes and pull requests |
| `.github/workflows/pages.yml` | Test; build and validate `dist/`; publish Pages | Pushes or a manual run, restricted to the default branch |

The current default branch is `main`. The Pages build uploads only `dist/`, not the whole repository. The deploy job uses the `github-pages` environment, with `pages: write` and `id-token: write` permissions. See GitHub's [custom Pages workflow documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

The workflows are independent. The Pages workflow performs its own checks; it does not wait for the separate CI workflow. Review both runs for the same commit. There is no `schedule` trigger for notice collection.

## Make and publish an update

1. Start from the latest repository version so that manual uploads do not overwrite newer changes.
2. Edit the relevant source files. Interface changes belong in `web/`; Python logic belongs in `src/market_radar/`; explanatory material belongs in README or `docs/`.
3. If rules, labels or data changed, regenerate outputs with `python3 app.py run` and `python3 app.py evaluate`. Review the resulting errors and update affected metric statements. Do not run the label-preparation script over completed human reviews.
4. Build and check the release from the repository root:

   ```bash
   PYTHONPATH=src python3 -m unittest discover -s tests -v
   PYTHONPATH=src python3 scripts/build_static_site.py
   python3 scripts/check_repository.py
   ```

   On Windows PowerShell, set `$env:PYTHONPATH = "src"` first and use `py` in place of `python3`.

5. Preview with `python3 -m http.server 8000 --directory dist` and open `http://127.0.0.1:8000`. Do not rely on opening an HTML file with `file://`, because the page fetches `notices.json`.
6. Commit the edited sources, affected outputs and rebuilt `dist/` files together. For a browser upload, preserve the directory structure and upload the contents of the update folder, not its outer wrapper or ZIP. On macOS, `Command + Shift + .` shows hidden files.
7. Commit to `main`, or merge the reviewed branch into `main`. Check the newest **CI** and **Deploy website** runs for that commit; the latter should have successful `build` and `deploy` jobs.
8. Open the public URL in a fresh browser session. Confirm the snapshot loads, filters work and a question returns source links. A hard refresh may be needed if older assets are cached.

Editing only `dist/` is not a source update: the Pages build copies assets from `web/` and regenerates public data from the labelled snapshot. Conversely, editing only `web/` without rebuilding the checked-in `dist/` can fail CI's saved-asset check. Documentation-only edits do not require a data refresh.

## Required paths

```text
repository root/
├── .github/workflows/
│   ├── ci.yml
│   └── pages.yml
├── web/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── dist/                         generated, checked-in static assets
├── data/                         versioned source, labels and eval questions
├── outputs/                      saved predictions and metrics
├── src/market_radar/              Python application
├── scripts/
│   ├── build_static_site.py
│   └── check_repository.py
└── tests/
```

The rest of the repository, including README, package configuration and `docs/`, is also required for full reproducibility. Do not omit `web/` because `dist/` exists. Do not rename or relocate `.github/workflows/`.

## Troubleshooting

| Symptom | Check or correction |
| --- | --- |
| `FileNotFoundError` for `web/index.html` | Upload the entire `web/` directory at repository root; keep all three assets. |
| `missing required files: .github/workflows/ci.yml` | Add `ci.yml` inside `.github/workflows/`, beside `pages.yml`. A root-level copy does not satisfy the check. |
| `static asset differs from web source` | Rebuild with `build_static_site.py`, validate, and commit both sources and generated assets. |
| Saved metrics differ from recomputed results | Re-evaluate the intended snapshot, inspect the changes, and update affected documentation. Do not disable validation to force a pass. |
| Pages configuration or deployment permission error | Check Settings → Pages, Actions source, workflow permissions and the `github-pages` environment's branch rules. |
| CI is green but the site has not changed | Inspect `Deploy website` for the same commit. A non-default branch is not published; a README-only edit does not change the interface. |
| Page loads without notices | Check that `notices.json` was deployed with the assets and that asset URLs remain relative to the project subpath. |

After adding missing files, inspect the run triggered by the new commit. Re-running an old failed commit does not add the missing files to that commit. If a release needs to be undone, revert the relevant commit in GitHub or Git, then let the corrected default branch deploy again; preserve commit history.

## Data, privacy and operating limits

- The snapshot contains 100 records. Public classifications are computed during the build; browser retrieval uses JavaScript. Python evaluation results are not a separate browser benchmark.
- `dist/notices.json` excludes gold labels and label-status fields. The public source repository still contains the labelled dataset and its disclosed draft status; omission from the website is not a confidentiality boundary.
- The public search code does not send question text to a model API. GitHub Pages serves the assets, and following a source link contacts the official website. Hosting-level access logs may exist; do not claim that no visitor information is ever collected. See [About GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/about-github-pages).
- Never put passwords, API keys, private notices or internal trading information in the public repository or static bundle. Any future private API credentials belong on an authenticated backend, not in browser JavaScript.
- A new deployment does not mean new notices were crawled. Ingestion freshness, availability and hosting/maintenance cost are not measured by the current evaluator. Zero variable model cost is not a claim of zero total operating cost.

## Next stages

Continue interface, rule and evaluation development in this repository. A live notice feed would additionally need scheduled collection, parse-success and freshness monitoring, a reviewed promotion process and storage. A hosted generative service would also need a backend, authentication, request limits, cost controls and citation-quality evaluation. These are future additions, not capabilities provided by the current Pages deployment.
