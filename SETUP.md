# Setup — animated GitHub profile README

This repo is meant to become `github.com/Khokon0123/Khokon0123` (GitHub's
special "profile repo" — a repo named exactly after your username, whose
README renders at the top of your profile page).

## One-time setup

```bash
# 1. Create the profile repo (skip if it already exists)
gh repo create Khokon0123 --public --clone
cd Khokon0123
# then copy everything from this folder into it

# 2. Install the toolchain
python -m venv .venv && source .venv/bin/activate
pip install -r scripts/requirements.txt
```

## Add your portrait (do this once, and again whenever you change your photo)

```bash
python scripts/prep_photo.py your-photo.jpg          # -> source-prepped.png
python scripts/make_ascii_svg.py                      # -> khokon-ascii.svg
```

`prep_photo.py` needs `rembg`'s model weights the first time it runs — it
downloads them automatically, so the first run needs internet access and
takes a bit longer.

## Generate the info card

Edit the `ROWS` list at the top of `scripts/make_info_card.py` whenever your
role, stack, or highlights change, then:

```bash
python scripts/make_info_card.py                      # -> info-card.svg
```

## Generate the heatmap (this is what the daily Action re-runs)

```bash
python scripts/fetch_contributions.py Khokon0123       # -> data/contributions.json
python scripts/render_heatmap_svg.py                   # -> contrib-heatmap.svg
```

## Push it

```bash
git add -A
git commit -m "Animated profile README"
git push
```

Then go to the **Actions** tab on the repo and manually trigger
"Update profile art" once (`workflow_dispatch`) to confirm it runs and
commits a fresh heatmap on its own. After that it refreshes every day at
~06:17 UTC with no further action from you.

## Notes

- All three SVGs are self-contained — no `<script>`, no external CSS, no
  third-party stats service, no GitHub token. GitHub strips `<script>` tags
  and inline styles from READMEs, but it does render SVG `<img>` tags and
  plays their internal SMIL / CSS-keyframe animations.
- The portrait and info card are static — only regenerate them when your
  photo or bio details change. The Action only touches the heatmap.
- `khokon-ascii.svg` is already included, generated from the photo you sent.
  Regenerate it any time with a new photo via `prep_photo.py` + `make_ascii_svg.py`.
