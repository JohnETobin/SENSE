import pandas as pd
import numpy as np
import math
import itertools
from pathlib import Path

# This script is a one-time local data-prep step (raw -> clean parquet files).
# It is NOT run by the deployed Streamlit app; only Data/Clean needs to ship
# with the app. Run this manually whenever you regenerate the clean files.
ROOT_DIR = Path(__file__).resolve().parent
RAW_DIR = ROOT_DIR / "Data" / "Raw"
CLEAN_DIR = ROOT_DIR / "Data" / "Clean"

###############################
# Substance Effect Network    #
###############################

network = pd.read_parquet(RAW_DIR / "cooccurrence_df.parquet", engine="fastparquet")

# Making substance & effect variables proper case, renaming count_sentences to edge_count
network = network.rename(columns={
    "substance": "Substance",
    "effect": "Effect",
    "count_sentences": "edge_count"
})

network["Substance"] = network["Substance"].str.lower()

# Total count of each effect to calculate PPMI
effect_count = (
    network.groupby("Effect")["edge_count"]
      .sum()
      .reset_index()
      .rename(columns={"edge_count": "effect_count"})
)

network = network.merge(effect_count, on="Effect", how="left")

# Count of the total number of sentences containing any substance to calculate PPMI
total_sentences = network.drop_duplicates("Substance")["substance_count"].sum()

# Function to calculate PPMI
def ppmi(substance_count, effect_count, edge_count, total_sentences):
    """
    Compute positive PMI between a substance and an effect.
    
    Parameters
    ----------
    substance_count : int
        Number of sentences containing the substance (count of x)
    effect_count : int
        Number of sentences containing the substance and the effect (count of y)
    edge_count : int
        Number of sentences containing both the substance and effect (count of x,y)
    total_sentences : int
        Total number of sentences in the dataset (sum of substance_count)
        
    Returns
    -------
    float
        Positive Pointwise Mutual Information value
    """

    p_x = substance_count / total_sentences
    p_y = effect_count / total_sentences
    p_xy = edge_count / total_sentences

    if p_xy == 0 or p_x == 0 or p_y == 0:
        return 0.0

    pmi = math.log(p_xy / (p_x * p_y))

    return max(pmi, 0) 

# Applying PPMI function to the data
network["PPMI"] = network.apply(
    lambda row: ppmi(
        row["substance_count"],
        row["effect_count"],
        row["edge_count"],
        total_sentences
    ),
    axis=1
)

# Save Parquet
network.to_parquet(CLEAN_DIR / "network.parquet")

###############################
#  Sentiment Explorer         #
###############################

#### Longitudinal Data #### 
valence_df = pd.read_parquet(RAW_DIR / "valence.parquet", engine="fastparquet")

# Compute average change in sentiment score over time (KEEP)
trend_df = valence_df.groupby("Substance").apply(
    lambda df: (df["avg_valence"].iloc[-1] - df["avg_valence"].iloc[0]) / (df["Month"].iloc[-1] - df["Month"].iloc[0])
).reset_index(name="Average Change in Valence")

trend_df["Trend"] = np.where(
    trend_df["Average Change in Valence"] > 0, 
    "Positive", 
    "Negative"
)
valence_df = valence_df.merge(trend_df[["Substance", "Trend", "Average Change in Valence"]], on="Substance", how="left")

# Rename Variables 
valence_df = valence_df.rename(columns={
    "avg_valence": "Sentiment Score",
    "avg_arousal": "Arousal Score"
})

# Save Parquet
valence_df.to_parquet(CLEAN_DIR / "valence_df.parquet")

#### Emotion Labels #### 

# Import Parquet
df = pd.read_parquet(RAW_DIR / "GE_All.parquet", engine="fastparquet")

# Reshape Wide to Long
substance_cols = [
    'amanita', 'benzodiazepines', 'cannabis', 'dmt', 'dxm', 'fentanyl',
    'hallucinogens', 'ketamine', 'kratom', 'lsd', 'mdma', 'mescaline',
    'methamphetamine', 'nicotine vaping', 'opioids', 'psilocybin', 'salvia',
    'stimulants', 'tobacco products'
]

df_long = df.melt(
    id_vars=["emotion_label"],
    value_vars=substance_cols,
    var_name="Substance",
    value_name="Present"
)

# Keep only rows where substance is present
df_long = df_long[df_long["Present"] == 1]

# Count ofcomments for each substance-emotion pair
df_counts = (
    df_long
    .groupby(["Substance", "emotion_label"], as_index=False)
    .size()
    .rename(columns={"size": "count"})
)

all_combos = pd.DataFrame(
    list(itertools.product(substance_cols, df["emotion_label"].unique())),
    columns=["Substance", "emotion_label"]
)

df_emotions = (
    all_combos
    .merge(df_counts, on=["Substance", "emotion_label"], how="left")
    .fillna({"count": 0})
)

# Drop neutral
df_emotions = df_emotions[df_emotions["emotion_label"] != "neutral"]

# Percent of each emotion by substance
df_emotions["total_count"] = df_emotions.groupby("Substance")["count"].transform("sum")
df_emotions["Percent"] = (df_emotions["count"] / df_emotions["total_count"]) * 100

# Rename and drop columns
df_emotions["Emotion"] = df_emotions["emotion_label"]
df_emotions["Count"] = df_emotions["count"]

df_emotions = df_emotions.drop(columns=["total_count", "emotion_label", "count"])

# Reshape long to wide
heatmap_df = df_emotions.pivot(
    index="Emotion",     
    columns="Substance",  
    values="Percent"
)

count_df = df_emotions.pivot(
    index="Emotion",
    columns="Substance",
    values="Count" 
    )

# Save Parquets 
heatmap_df.to_parquet(CLEAN_DIR / "heatmap_df.parquet")
count_df.to_parquet(CLEAN_DIR / "count_df.parquet")