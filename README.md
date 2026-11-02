# Tech Today

Free mobile-first static news reader for GitHub Pages. The page fetches the latest committed `news.json` on launch and when either Refresh button is tapped. Headlines are newest first and link directly to publishers.

## Prepublication state

This repository is staged only. GitHub Pages must **not** be enabled without separate owner approval. The news workflow is **manual only** until publication approval. The initial feed is empty.

## Test collector

Run `python update_news.py` with internet access, then inspect `news.json`. In GitHub Actions, run `Refresh Tech Today` manually. After checking results and obtaining separate publication approval, enable GitHub Pages and optionally add a scheduled trigger to the workflow.

## Limitations

RSS feeds are not independent verification of every claim. Feed collection requires GitHub Actions or a local Python run. iOS Home Screen behavior needs real-device testing. Some publishers do not supply article images.
