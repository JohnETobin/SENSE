############################################################################## 
#                        Longitudinal Sentiment Analysis                     #
#   Last modified 3/19/2026                                                  #
#                                                                            #  
#   Notes:                                                                   #
#       This is currently displaying REAL data to act as a placeholder       #
#       The code requires 2 parquets                                         #
#       Parquet 1 (valence score)                                            #
#           "Substance"                                                      #
#           "Month"                                                          #
#           "Sentiment Score" (average valence)                              #
#       Parquet 2 (go emotion)                                               #
#           "Substance"                                                      #
#           "Emotion" (1 observation for each of the time 5 emotions)        #
#           "Percent" (percents of top 5 sum to 1)                           #
#                                                                            #     
##############################################################################

import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import plotly.graph_objects as go
import random
import plotly.express as px
import math
from pathlib import Path

# Build an absolute path to the project root, regardless of where the
# app is run from (local machine, Streamlit Cloud, etc.). This file lives
# in <root>/pages/, so the root is one level up.
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "Data" / "Clean"

###############################
# Page Setup                  #
###############################

st.set_page_config(page_title = "Sentiment Explorer", layout = "wide")
st.title("Sentiment Explorer")

random.seed(5)
np.random.seed(5)

###############################
# Emotion Data                #
###############################

heatmap_df = pd.read_parquet(DATA_DIR / "heatmap_df.parquet", engine="fastparquet")
count_df = pd.read_parquet(DATA_DIR / "count_df.parquet", engine="fastparquet")
valence_df = pd.read_parquet(DATA_DIR / "valence_df.parquet", engine="fastparquet")

###############################
# Sidebar                     #
###############################

# ReadMe
with st.sidebar.expander("ReadMe", expanded=False):
    st.markdown(
        """
        The Sentiment Explorer visualizes changes in Reddit users' feeling of hallucinogenic substances over time, as well as emotions identified in 
        posts related to selected substances. 

        **Sentiment Change Over Tenure by Substance** 

        Sentiment scores range from -1 to 1, capturing both direction and intensity. Values closer to -1 or 1 indicate stronger sentiment, while those near 0 reflect more neutral feelings.

        **Emotion Distribution by Substance**

        User comments are classified by emotion using GoEmotion, identified by the words present in the text. There are 27 possible emotions, 
        plus neutral<sup>1</sup>. The Emotion Distribution by Substance chart displays the top five emotions present in posts related to the selected 
        substance, and the percent of those posts identified as each semotion. Percents sum to 100.

        **Filtering by Substance** 

        You can filter by substance, selecting one or more to view simultaneously. 

        **Filtering by Trend** 

        You can filter by trend direction. We classify trend, defined as the average change in sentiment over time, as positive or negative. 

        <sup>1</sup> Emotions include admiration, adoration, aesthetic appreciation,  amusement, anger, anxiety, awe, awkwardness, boredom,  calmness, confusion,
        craving, disgust, empathic pain,  entrancement, excitement, fear, horror, interest, joy, nostalgia,  relief, romance, sadness, satisfaction, sexual desire,
        surprise, and neutral. 

        """,
        unsafe_allow_html=True,
    )

# Filter mode selector

st.sidebar.subheader("Filter by Substance or Trend")

filter_mode = st.sidebar.radio(
    "Filter by:",
    options=["Substances", "Trend"]
)

# Apply filtering based on mode
if filter_mode == "Substances":
    selected_drugs = st.sidebar.multiselect(
        "Select one or more substances:",
        options=sorted(valence_df["Substance"].unique()),
        default=[],
        help="Choose a substances to display in the chart."
    )
    
    # Filter dataframe
    if selected_drugs:
        filtered_df = valence_df[valence_df["Substance"].isin(selected_drugs)]
    else:
        filtered_df = valence_df.iloc[0:0]  

elif filter_mode == "Trend":
    selected_trend = st.sidebar.multiselect(
        "Select trend direction:",
        options=["Positive", "Negative"],
        default=[],
        help="Filter substances by average change in sentiment."
    )
    
    if selected_trend:
        filtered_df = valence_df[valence_df["Trend"].isin(selected_trend)]
    else:
        filtered_df = valence_df.iloc[0:0] 

selected_substances = filtered_df["Substance"].unique()

# Data preview in sidebar
preview_df = filtered_df[["Month", "Substance", "Sentiment Score", "Average Change in Valence", "Trend", "Comments"]]
if preview_df.empty:
    st.sidebar.info("Select filter options to preview data.")
else:
    st.sidebar.dataframe(preview_df)

# Download Trend button
trend_csv_data = preview_df.to_csv(index=False).encode("utf-8")
st.sidebar.download_button(
    label="Download Trend Data",
    data=trend_csv_data,
    file_name="filtered_valence_scores.csv",
    mime="text/csv"
)

# Download Emotion button
heatmap_csv_data = heatmap_df.to_csv(index=True).encode("utf-8")
st.sidebar.download_button(
    label="Download Emotion Distribution Data",
    data=heatmap_csv_data,
    file_name="emotion_distribution.csv",
    mime="text/csv"
)

###############################
# Valence Plotly Graph        #
###############################

st.subheader(
    "Change Over Tenure in Emotional Valence",
    help="Average change in user sentiment over their tenure commenting by substance."
)

# Placeholder for the empty chart
chart_placeholder = st.empty()

# Show chart if there is datas
fig = px.line(
    filtered_df,
    x="Month",
    y="Sentiment Score",
    color="Substance",
    markers=True,
    line_shape="spline"
)

fig.update_traces(line=dict(shape="spline", smoothing=1.3),
                  customdata=filtered_df[["Comments"]],
    hovertemplate=(
        "Substance: %{fullData.name}<br>"
        "Month: %{x}<br>"
        "Sentiment: %{y:.2f}<br>"
        "Comments: %{customdata[0]}<extra></extra>")
)

fig.update_layout(
    yaxis=dict(range=[-1.1, 1.1]),
    template="plotly_white",
    legend_title="Substance"
)

chart_placeholder.plotly_chart(fig, use_container_width=True)

###############################
#  Emotion Heat Map           #
###############################

st.subheader(
    "Emotion Distribution by Substance",
    help=" < help text here >"
)

fig = px.imshow(
    heatmap_df,
    color_continuous_scale="Blues",
    aspect="auto"
)

# Custom hover with Count
fig.update_traces(
    customdata=count_df.values,
    hovertemplate=(
        "Emotion: %{y}<br>"
        "Substance: %{x}<br>"
        "Percent: %{z:.1f}%<br>"
        "Count: %{customdata}<extra></extra>"
    )
)

fig.update_layout(
    xaxis_title="Substance",
    yaxis_title="Effect",
    height=700,
   coloraxis_colorbar=dict(
        title="Percent",
        tickformat=".1f"  
   )
)

st.plotly_chart(fig, use_container_width=True)

###############################
# Main Page Text              #
###############################

# Footer text 
st.markdown("---") 

st.markdown(
    """
    <div style='text-align: center; font-size: 14px; color: gray;'>
        This is an open-source project. The code base is housed on GitHub.
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style='text-align: center; font-size: 14px; color: gray;'>
        This project uses the ki-elements/multilingual_va_prediction model available on Hugging Face, licensed under the MIT License.

    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style='text-align: center; font-size: 14px; color: gray;'>
        This project uses the SamLowe/roberta-base-go_emotions model available on Hugging Face, licensed under the MIT License.

    </div>
    """,
    unsafe_allow_html=True
)
