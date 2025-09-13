
#***********************************************************************************************************
#*************************** WELCOME MESSAGE ****************************************************************
#***********************************************************************************************************

def neonball():
#  pip install mlxtend pandas openpyxl
#  pip install pandas scikit-learn openpyxl matplotlib
  print("**********************************************************")
  print("Welcome to use neonball *: text analysis tool")
  print()
  # print()
  # print()
  print("**********************************************************")

# ********************************************************************************************
# **************************** neonball ******************************************************
# ********************************************************************************************
# Two Colab-friendly functions:
#  - run_sentiment_excel_ui(): Upload Excel → pick sheet & column → VADER sentiment.
#  - run_label_classification_excel_ui(): Upload Excel → pick sheet & column → enter labels
#    (comma-separated) → semantic classification via SentenceTransformers.
#
# Usage in Colab:
#   !pip -q install pandas openpyxl ipywidgets matplotlib nltk sentence-transformers
#   import textla as tl
#   tl.run_sentiment_excel_ui()
#   tl.run_label_classification_excel_ui()
#
# Notes:
#  * Requires Google Colab (uses google.colab.files for upload/download).
#  * No network calls at import-time, models download on first run if needed.
#  * Charts use matplotlib defaults (no seaborn, no custom colors).
# ********************************************************************************************

__all__ = ["senti", "label"]

# ---------------------------------------------------------------------------------------------
# Internal helpers (kept lightweight and only used when a function is executed)
# ---------------------------------------------------------------------------------------------
def _require_colab():
    try:
        from google.colab import files as _files  # noqa: F401
    except Exception as e:
        raise RuntimeError(
            "textla functions require Google Colab (they use google.colab.files)."
        ) from e

def _upload_excel_bytes():
    import io
    from google.colab import files
    print("Upload your Excel file (.xlsx)…")
    uploaded = files.upload()
    if not uploaded:
        raise SystemExit("No file uploaded.")
    fname = next(iter(uploaded.keys()))
    return fname, io.BytesIO(uploaded[fname])

def _download_file(path):
    from google.colab import files
    files.download(path)

def _suggest_text_columns(df):
    # Heuristic: choose columns with average stripped length > 3; fallback to all columns
    import pandas as pd
    df = df.dropna(axis=1, how="all")
    candidates = []
    for c in df.columns:
        s = df[c].dropna().astype(str)
        if not len(s):
            continue
        avg_len = s.map(lambda x: len(x.strip())).mean()
        if avg_len >= 3:
            candidates.append(c)
    return candidates if candidates else list(df.columns)

def _make_sheet_picker(xl, status_text=""):
    import ipywidgets as w
    from IPython.display import display
    sheets = xl.sheet_names
    sheet_dd   = w.Dropdown(options=sheets, description="Sheet:", layout=w.Layout(width="360px"))
    col_dd     = w.Dropdown(options=[],    description="Text col:", layout=w.Layout(width="360px"))
    status_lbl = w.HTML(status_text or "<b>Status:</b> Pick a sheet")
    sample_out = w.Output()
    box = w.VBox([sheet_dd, col_dd, status_lbl, sample_out])
    display(box)
    return sheet_dd, col_dd, status_lbl, sample_out, box

# ********************************************************************************************
# *************************** Sentiment (VADER) **********************************************
# ********************************************************************************************
def senti():
    """
    Open a Colab widget flow to:
      1) Upload an Excel file (.xlsx)
      2) Pick a sheet & text column
      3) Run VADER sentiment analysis
      4) Preview results, view a simple distribution chart, and download CSV
    """
    _require_colab()

    # Lazy imports (only when function runs)
    import pandas as pd
    import matplotlib.pyplot as plt
    import ipywidgets as w
    from IPython.display import display, clear_output

    # NLTK / VADER
    import nltk
    nltk.download("vader_lexicon", quiet=True)
    from nltk.sentiment import SentimentIntensityAnalyzer
    sia = SentimentIntensityAnalyzer()

    # Upload & read Excel
    fname, bio = _upload_excel_bytes()
    try:
        xl = pd.ExcelFile(bio, engine="openpyxl")
    except Exception as e:
        raise SystemExit(f"Could not read Excel file. Details: {e}")

    # UI
    sheet_dd, col_dd, status_lbl, sample_out, _ = _make_sheet_picker(xl)
    analyze_btn  = w.Button(description="Run Sentiment Analysis", button_style="success")
    download_btn = w.Button(description="Download CSV")
    display(w.HBox([analyze_btn, download_btn]))

    # State
    df_current = {"df": None}
    result_df  = {"df": None}

    def _on_sheet_change(_):
        with sample_out:
            clear_output()
        status_lbl.value = "<b>Status:</b> Loading sheet preview…"
        try:
            df = xl.parse(sheet_dd.value, dtype=str)  # strings safer for text columns
        except Exception as e:
            status_lbl.value = f"<b>Status:</b> ❌ Failed to read sheet: {e}"
            col_dd.options = []
            df_current["df"] = None
            return

        df = df.dropna(axis=1, how="all")
        df_current["df"] = df
        options = _suggest_text_columns(df)
        col_dd.options = options
        col_dd.value   = options[0] if options else None

        with sample_out:
            clear_output()
            print("Sheet preview (first 8 rows):")
            display(df.head(8))
        status_lbl.value = "<b>Status:</b> Pick a column, then click “Run Sentiment Analysis”."

    sheet_dd.observe(_on_sheet_change, names="value")
    _on_sheet_change(None)

    def _run(_):
        df = df_current["df"]
        if df is None or df.empty:
            status_lbl.value = "<b>Status:</b> ❌ No data in the selected sheet."
            return
        col = col_dd.value
        if not col:
            status_lbl.value = "<b>Status:</b> ❌ Please choose a column."
            return

        text = df[col].astype(str).fillna("").map(lambda s: s.strip())
        mask = text.str.len() > 0
        text_nonempty = text[mask]
        if text_nonempty.empty:
            status_lbl.value = "<b>Status:</b> ❌ No non-empty text in that column."
            return

        scores = text_nonempty.apply(sia.polarity_scores).apply(pd.Series)
        def _label(c):
            if c >= 0.05: return "Positive"
            if c <= -0.05: return "Negative"
            return "Neutral"
        labels = scores["compound"].apply(_label)

        out = pd.DataFrame({
            "sheet": sheet_dd.value,
            "column": col,
            "row_index": text_nonempty.index,
            "text": text_nonempty,
            "compound": scores["compound"],
            "positive_ratio": scores["pos"],
            "neutral_ratio": scores["neu"],
            "negative_ratio": scores["neg"],
            "label": labels
        }).reset_index(drop=True)

        result_df["df"] = out

        pos = (out["label"] == "Positive").sum()
        neg = (out["label"] == "Negative").sum()
        neu = (out["label"] == "Neutral").sum()
        avg = out["compound"].mean()

        status_lbl.value = (f"<b>Status:</b> ✅ Analyzed {len(out)} rows → "
                            f"{pos} positive, {neu} neutral, {neg} negative. "
                            f"Avg compound: {avg:.3f}")

        with sample_out:
            clear_output()
            print("Results preview (first 15 rows):")
            display(out.head(15))

            plt.figure(figsize=(6,4))
            plt.bar(["Positive","Neutral","Negative"], [pos, neu, neg])
            plt.title("Sentiment distribution")
            plt.ylabel("Count")
            plt.xlabel("Sentiment")
            plt.show()

    def _download(_):
        out = result_df["df"]
        if out is None or out.empty:
            status_lbl.value = "<b>Status:</b> ⚠️ Nothing to download yet."
            return
        out_name = f"sentiment_results_{sheet_dd.value}_{col_dd.value}.csv".replace(" ", "_")
        out.to_csv(out_name, index=False)
        _download_file(out_name)

    analyze_btn.on_click(_run)
    download_btn.on_click(_download)


# ********************************************************************************************
# *************************** Custom Label Classification ************************************
# ********************************************************************************************
_cached_model = None

def label(model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
    """
    Open a Colab widget flow to:
      1) Upload an Excel file (.xlsx)
      2) Pick a sheet & text column
      3) Enter comma-separated labels (e.g., "expensive, inexpensive, neutral")
      4) Classify each row to the closest label using sentence embeddings
      5) Preview results, view a chart, and download CSV

    Parameters
    ----------
    model_name : str
        SentenceTransformers model to use (default: "sentence-transformers/all-MiniLM-L6-v2").
    """
    _require_colab()

    # Lazy imports
    import pandas as pd
    import matplotlib.pyplot as plt
    import ipywidgets as w
    from IPython.display import display, clear_output

    # Load / cache model
    global _cached_model
    if _cached_model is None:
        from sentence_transformers import SentenceTransformer
        _cached_model = SentenceTransformer(model_name)
    model = _cached_model

    # Upload & read Excel
    fname, bio = _upload_excel_bytes()
    try:
        xl = pd.ExcelFile(bio, engine="openpyxl")
    except Exception as e:
        raise SystemExit(f"Could not read Excel file. Details: {e}")

    # UI
    sheet_dd, col_dd, status_lbl, sample_out, _ = _make_sheet_picker(xl, status_text="<b>Status:</b> Pick a sheet")
    labels_tb = w.Text(
        value="expensive, inexpensive",
        description="Labels:",
        placeholder="Comma-separated (e.g. expensive, inexpensive, neutral)",
        layout=w.Layout(width="560px")
    )
    threshold_sl = w.FloatSlider(
        value=0.35, min=0.0, max=0.9, step=0.01,
        description="Uncertain if <",
        readout_format=".2f",
        layout=w.Layout(width="560px")
    )
    batch_sz_sl = w.IntSlider(
        value=512, min=64, max=2048, step=64,
        description="Batch size",
        layout=w.Layout(width="560px")
    )
    analyze_btn  = w.Button(description="Run Classification", button_style="success")
    download_btn = w.Button(description="Download CSV")
    display(w.VBox([labels_tb, threshold_sl, batch_sz_sl, w.HBox([analyze_btn, download_btn])]))

    # State
    df_current = {"df": None}
    result_df  = {"df": None}

    def _on_sheet_change(_):
        with sample_out:
            clear_output()
        status_lbl.value = "<b>Status:</b> Loading sheet preview…"
        try:
            df = xl.parse(sheet_dd.value, dtype=str)
        except Exception as e:
            status_lbl.value = f"<b>Status:</b> ❌ Failed to read sheet: {e}"
            col_dd.options = []
            df_current["df"] = None
            return
        df = df.dropna(axis=1, how="all")
        df_current["df"] = df
        options = _suggest_text_columns(df)
        col_dd.options = options
        col_dd.value   = options[0] if options else None
        with sample_out:
            clear_output()
            print("Sheet preview (first 8 rows):")
            display(df.head(8))
        status_lbl.value = "<b>Status:</b> Enter labels, pick a column, then click “Run Classification”."

    sheet_dd.observe(_on_sheet_change, names="value")
    _on_sheet_change(None)

    def _clean_labels(raw: str):
        parts = [p.strip() for p in raw.split(",")]
        parts = [p for p in parts if p]
        seen = set()
        uniq = []
        for p in parts:
            low = p.lower()
            if low not in seen:
                uniq.append(p)
                seen.add(low)
        return uniq

    def _run(_):
        from sentence_transformers import util
        df = df_current["df"]
        if df is None or df.empty:
            status_lbl.value = "<b>Status:</b> ❌ No data in the selected sheet."
            return
        col = col_dd.value
        if not col:
            status_lbl.value = "<b>Status:</b> ❌ Please choose a column."
            return

        labels = _clean_labels(labels_tb.value)
        if len(labels) < 2:
            status_lbl.value = "<b>Status:</b> ❌ Please provide at least two labels (comma-separated)."
            return

        text = df[col].astype(str).fillna("").map(lambda s: s.strip())
        mask = text.str.len() > 0
        text_nonempty = text[mask]
        if text_nonempty.empty:
            status_lbl.value = "<b>Status:</b> ❌ No non-empty text in that column."
            return

        thr   = float(threshold_sl.value)
        batch = int(batch_sz_sl.value)

        # Embed labels once
        label_emb = model.encode(labels, convert_to_tensor=True, normalize_embeddings=True)

        idxs = text_nonempty.index.to_list()
        texts = text_nonempty.to_list()
        assigned_labels = []
        confidences = []

        for start in range(0, len(texts), batch):
            end = min(start + batch, len(texts))
            chunk = texts[start:end]
            text_emb = model.encode(chunk, convert_to_tensor=True, normalize_embeddings=True)
            sims = util.cos_sim(text_emb, label_emb).cpu().numpy()
            best_idx = sims.argmax(axis=1)
            best_val = sims.max(axis=1)
            for i in range(len(chunk)):
                if best_val[i] < thr:
                    assigned_labels.append("Uncertain")
                else:
                    assigned_labels.append(labels[int(best_idx[i])])
                confidences.append(float(best_val[i]))

        out = pd.DataFrame({
            "sheet": sheet_dd.value,
            "column": col,
            "row_index": idxs,
            "text": texts,
            "predicted_label": assigned_labels,
            "confidence_cosine": confidences
        })
        result_df["df"] = out

        counts = out["predicted_label"].value_counts().sort_values(ascending=False)

        with sample_out:
            clear_output()
            print("Results preview (first 15 rows):")
            display(out.head(15))

            plt.figure(figsize=(7,4))
            plt.bar(counts.index.astype(str), counts.values)
            plt.title("Label distribution")
            plt.ylabel("Count")
            plt.xlabel("Label")
            plt.xticks(rotation=20)
            plt.show()

        top_k = ", ".join([f"{k}: {v}" for k, v in counts.head(5).items()])
        status_lbl.value = (f"<b>Status:</b> ✅ Classified {len(out)} rows. "
                            f"Top counts → {top_k} "
                            f"(Uncertain threshold: {thr:.2f})")

    def _download(_):
        out = result_df["df"]
        if out is None or out.empty:
            status_lbl.value = "<b>Status:</b> ⚠️ Nothing to download yet."
            return
        out_name = f"classification_results_{sheet_dd.value}_{col_dd.value}.csv".replace(" ", "_")
        out.to_csv(out_name, index=False)
        _download_file(out_name)

    analyze_btn.on_click(_run)
    download_btn.on_click(_download)



