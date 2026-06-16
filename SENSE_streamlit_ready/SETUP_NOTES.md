# SENSE Streamlit App — Deployment-Ready

This folder is your original SENSE app, fixed so it will run on Streamlit
Community Cloud instead of only on a specific local machine. Changes made:

1. Removed the hardcoded `os.chdir('/Users/delaneyblack/...')` lines from
   `data_prep.py`, `pages/1_Substance_Effect_Network.py`, and
   `pages/2_Sentiment_Explorer.py`. Paths are now built relative to each
   file's own location using `pathlib`, so they work no matter who runs
   the app or from where.
2. Renamed `Pages/` to `pages/` (lowercase). Streamlit's automatic
   multi-page detection specifically requires a lowercase `pages` folder.
   This worked on a Mac because macOS ignores case in filenames, but
   Streamlit Cloud runs on Linux, which does NOT ignore case — so the
   pages would have silently failed to appear.
3. Added `requirements.txt` listing the packages the app needs
   (streamlit, pandas, numpy, networkx, plotly, fastparquet).
4. Added `.gitignore` to keep `.DS_Store` and other junk out of the repo.

## What YOU need to do before deploying

Drop your real parquet files into `Data/Clean/`:
- network.parquet
- valence_df.parquet
- heatmap_df.parquet
- count_df.parquet

These are the only files the live app actually reads. You do not need to
upload anything into `Data/Raw/` — that's only used by `data_prep.py`,
which you'd run locally if you ever need to regenerate the clean files.

See the chat instructions for the full step-by-step deployment guide.
