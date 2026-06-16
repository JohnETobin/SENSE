############################################################################## 
#                         Substance Effect Network                           #
#   Last modified 11/25/2025                                                 #
#                                                                            #
#   To do:                                                                   #
#       make minimum edge count 5 or 10                                      #
#   Notes: This is currently displaying REAL data!!!!                        #
#   The code requires a parquet with the following variables:                #
#         substance                                                          #
#         effect                                                             #
#         count_sentences (# of co-occurrences)                              #
#         substance_count (# of total sentences with that substance)         #
#       #
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
import itertools
from pathlib import Path

# Build an absolute path to the project root, regardless of where the
# app is run from (local machine, Streamlit Cloud, etc.). This file lives
# in <root>/pages/, so the root is one level up.
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "Data" / "Clean"


###############################
# Page Setup                  #
###############################

st.set_page_config(page_title = "Substance Effect Network", layout = "wide")
st.title("Substance Effect Network")

random.seed(5)
np.random.seed(5)

###############################
# Import Data                 #
###############################

df = pd.read_parquet(DATA_DIR / "network.parquet", engine="fastparquet")

###############################
# Sidebar                     #
###############################

# ReadMe

with st.sidebar.expander("ReadMe", expanded=False):
    st.markdown(
        """
        The Substance-Effect Network visualizes Reddit users’ experiences with hallucinogenic substance use.

        From this data, we identified substances and effects using name-entity recognition (NER). A substance is connected to an effect if it appears in the 
        same sentences as that effect. 

        **Overview** 
        
        You can view all substances and effects in the data, or view individual substance and/or effects using the filters below. Hover on the (?) icon next 
        to each input for additional info.

        PPMI is a measure of association in natural language processing. It indicates the likelihood that a substance-effect pair will appear in the text, 
        relative to the probabilities that they appear on their own. A higher PPMI indicates a stronger association between the substance and effect. 

        **Filtering by Substance**
        
        If you filter by substance, you can view all of the substances connected to a single effect. For example, you can filter to "LSD" and see all the 
        effects people mention when they talk about LSD. 

        The data preview will update automatically when you filter by substance, so you can see the relative frequency with which each effect is reported. 

        **Filtering by Effect**
        
        If you filter by effect, you can view all of the substances connected to a single effect. For example, you can filter to "dizziness" and see all 
        substances mentioned with dizziness.

        The data preview will update automatically when you filter by effect, so you can see the relative frequency with which that effect co-occurs. 

        """,
        unsafe_allow_html=True,
    )

st.sidebar.subheader("Filter Substances or Effects")

# Substance filter 

selected_drug = st.sidebar.selectbox(
    "Filter by Substance",
    ["All"] + sorted(df["Substance"].unique()),
    help="Select a substance or view all."
)

# Effect filter 

selected_effect = st.sidebar.selectbox(
    "Filter by Effect",
    ["All"] + sorted(df["Effect"].unique()),
    help="Select an effect or view all."
)

# PPMI slider

st.sidebar.subheader("Filter by PPMI")

ppmi_min_val = float(df["PPMI"].min())
ppmi_max_val = float(df["PPMI"].max())

col1, col2 = st.sidebar.columns(2)

with col1:
    input_min = st.number_input(
        "Min",
        min_value=ppmi_min_val,
        max_value=ppmi_max_val,
        value=ppmi_min_val,
        step=0.01
    )

with col2:
    input_max = st.number_input(
        "Max",
        min_value=ppmi_min_val,
        max_value=ppmi_max_val,
        value=ppmi_max_val,
        step=0.01,
        help="PPMI, Positive Pointwise Mutual Information, is a measure of strength of association. PPMI is high when the probability of a substance and effect co-occurring is high relative to their individual probabilities of occurrence. A PPMI of 0 indicates that the probability of co-occurrence is either equal to or less than their individual probabilities of occurrence. PPMI is a good measure of comparison between substances and effects with different count frequencies.",

    )

ppmi_min, ppmi_max = st.sidebar.slider(
    "Select PPMI Range",
    min_value=ppmi_min_val,
    max_value=ppmi_max_val,
    value=(input_min, input_max), 
    step=0.01,
)

# Edge count slider

st.sidebar.subheader("Filter by Edge Count")

edge_min_val = 10
edge_max_val = int(df["edge_count"].max())

col1, col2 = st.sidebar.columns(2)

with col1:
    input_min = st.number_input(
        "Min",
        min_value=edge_min_val,
        max_value=edge_max_val,
        value=edge_min_val,
        step=1
    )

with col2:
    input_max = st.number_input(
        "Max",
        min_value=edge_min_val,
        max_value=edge_max_val,
        value=edge_max_val,
        step=1,
        help="Edge count is the number of times a substance and effect were mentioned together. Connections with high edge count are more frequently mentioned. Edge count frequency is not scale-invariant, so substances and effects that are more frequently mentioned in the data will likely naturally have a higher edge count when combined. Edge count is not a good measure of comparison between substances and effects with different count frequencies."

    )

edge_min, edge_max = st.sidebar.slider(
    "Select Edge Count Range",
    min_value=int(df["edge_count"].min()),
    max_value=int(df["edge_count"].max()),
    value=(input_min, input_max), 
    step=1, 
)

# Apply filters

filtered_df = df.copy()

if selected_drug != "All":
    filtered_df = filtered_df[filtered_df["Substance"] == selected_drug]

if selected_effect != "All":
    filtered_df = filtered_df[filtered_df["Effect"] == selected_effect]

filtered_df = filtered_df[
    (filtered_df["PPMI"].between(ppmi_min, ppmi_max)) &
    (filtered_df["edge_count"].between(edge_min, edge_max))
]

# Data preview

st.sidebar.subheader("Data Preview")

preview_df = filtered_df.rename(columns={"edge_count": "Edge Count"})[
    ["Substance", "Effect", "Edge Count", "PPMI"]
]

st.sidebar.dataframe(preview_df)
st.sidebar.write(f"Total edges: **{len(filtered_df)}**")

csv_data = preview_df.to_csv(index=False).encode('utf-8')
st.sidebar.download_button(
    label="Download as CSV",
    data=csv_data,
    file_name="filtered_network_data.csv",
    mime="text/csv"
)

###############################
# Plotly Graph                #
###############################

G = nx.Graph()
for drug in filtered_df["Substance"].unique():
    G.add_node(drug, type="drug")
for eff in filtered_df["Effect"].unique():
    G.add_node(eff, type="effect")

for _, row in filtered_df.iterrows():
    G.add_edge(row["Substance"], row["Effect"]) 

pos = nx.spring_layout(G, seed=42, k=0.5) if len(G.nodes) > 0 else {}

# Node hover text             

hover_texts = {}

substance_edge_sums = {
    s: filtered_df.loc[filtered_df["Substance"] == s, "edge_count"].sum()
    for s in filtered_df["Substance"].unique()
}

for node, data in G.nodes(data=True):

    if data["type"] == "drug":
        total_edge_sum = substance_edge_sums.get(node, 0)  # lookup once
        hover_texts[node] = (
            f"<b>{node}</b><br>"
            f"Type: Substance<br><br>"
            f"<b>Total Edge Count</b><br>{total_edge_sum}"
        )

    else:   
        connected_substances = [n for n in G.neighbors(node) if G.nodes[n]['type'] == 'drug']

        if connected_substances:
            total_edge_sum = filtered_df.loc[
                filtered_df["Effect"] == node, "edge_count"
            ].sum()

            info_lines = []
            for s in connected_substances:
                ppmi_val = filtered_df.loc[
                    (filtered_df["Substance"] == s) & (filtered_df["Effect"] == node),
                    "PPMI"
                ].values
                if len(ppmi_val) > 0:
                    info_lines.append(f"{s}: {ppmi_val[0]:.2f}")

            if info_lines:
                hover_texts[node] = (
                    f"<b>{node}</b><br>"
                    f"Type: Effect<br><br>"
                    f"<b>Total Edge Count</b><br>{total_edge_sum}<br><br>"
                    f"<b>PPMI</b><br>"
                    + "<br>".join(info_lines)
                )
            else:
                hover_texts[node] = (
                    f"<b>{node}</b><br>"
                    "Type: Effect<br>"
                    f"<b>Total Edge Count</b><br>{total_edge_sum}<br><br>"
                    "No connected substances"
                )
        else:
            hover_texts[node] = f"<b>{node}</b><br>Type: Effect<br>No connected substances"

# Effect node sizes based on total co-occurrences

effect_sizes = {}
max_count = filtered_df["edge_count"].max()

for effect in filtered_df["Effect"].unique():
    total_count = filtered_df.loc[filtered_df["Effect"] == effect, "edge_count"].sum()
    size = 8 + (total_count / max_count) * 12
    effect_sizes[effect] = size


 
 # Edge traces (opacity by PPMI)                 

edge_traces = []
max_ppmi = filtered_df["PPMI"].max() or 1 

for u, v in G.edges():
    x0, y0 = pos[u]
    x1, y1 = pos[v]

    ppmi_val = filtered_df.loc[
        (filtered_df["Substance"] == u) & (filtered_df["Effect"] == v), "PPMI"
    ].values
    if len(ppmi_val) == 0:
        ppmi_val = filtered_df.loc[
            (filtered_df["Substance"] == v) & (filtered_df["Effect"] == u), "PPMI"
        ].values
    ppmi_val = ppmi_val[0] if len(ppmi_val) > 0 else 0

    opacity = 0.3 + (1.0 - 0.15) * (ppmi_val / max_ppmi)
    opacity = max(0.15, min(opacity, 1.0))  

    edge_traces.append(
        go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode="lines",
            line=dict(width=2, color=f"rgba(170,170,170,{opacity})"),  
            hoverinfo="text",
            text=f"{u} — {v}",
            showlegend=False,
            textfont=dict(color="#444444")
        )
    )

# Node traces                

drug_x, drug_y, drug_hover = [], [], []
effect_x, effect_y, effect_hover = [], [], []

drug_nodes = []
effect_nodes = []

for node, data in G.nodes(data=True):
    x, y = pos[node]

    if data["type"] == "drug":
        drug_nodes.append(node)
        drug_x.append(x)
        drug_y.append(y)
        drug_hover.append(hover_texts[node])
    else:
        effect_nodes.append(node)
        effect_x.append(x)
        effect_y.append(y)
        effect_hover.append(hover_texts[node])

# Substance trace 

drug_trace = go.Scatter(
    x=drug_x, y=drug_y,
    mode="markers+text",
    name="Substances",
    legendgroup="Substances",
    text=drug_nodes,    
    textposition="top center",
    hovertext=drug_hover,
    hoverinfo="text",
    marker=dict(
        color="#015293",
        size=18,
        line_width=0
    ),
    textfont=dict(color="#444444")
)

# Effect trace

effect_trace = go.Scatter(
    x=effect_x, y=effect_y,
    mode="markers+text",
    name="Effects",
    legendgroup="Effects",
    text=effect_nodes,     
    textposition="top center",
    hovertext=effect_hover,
    hoverinfo="text",
    marker=dict(
        color="#87a4d3",
        size=[effect_sizes[n] for n in effect_nodes],  
        line_width=0,
        opacity=1
    ),
    textfont=dict(color="#444444")
)

# Combine into plotly figure 

fig = go.Figure(
    data=edge_traces + [drug_trace, effect_trace],
    layout=go.Layout(
        showlegend=True,
        legend=dict(
            orientation="v",
            xanchor="left",
            x=1.02,
            yanchor="top",
            y=1,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="lightgray",
            borderwidth=1,
            font=dict(size=12)
        ),
        annotations=[
            dict(
                text="<b>Notes</b><br>Edge opacity is based on <br>PPMI. Higher opacity <br>indicates higher PPMI.<br><br>Effect node size is based<br>on total edge count<br>with any substance.",
                xref="paper", yref="paper",
                x=1.02, y=0.0,  
                xanchor="left", yanchor="bottom",
                showarrow=False,
                font=dict(size=11, color="gray", family="Helvetica, sans-serif"),
                align="left"
            )
        ],
        hovermode="closest",
        margin=dict(b=40, l=40, r=200, t=60),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=550
    )
)

config = {
    "scrollZoom": True,
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d", "toggleSpikelines"],
}

st.plotly_chart(fig, use_container_width=True, config=config)

###############################
# Main Page Text              #
###############################

# Text below graph

if selected_drug != "All":
    connected_effects = list(G.neighbors(selected_drug)) if selected_drug in G.nodes else []
    st.success(f"**{selected_drug}** is associated with: {', '.join(connected_effects)}")
elif selected_effect != "All":
    connected_substances = list(G.neighbors(selected_effect)) if selected_effect in G.nodes else []
    st.success(f"**{selected_effect}** is associated with: {', '.join(connected_substances)}")
else:
    st.info("Select a substance or effect from the sidebar to filter.")

st.markdown("---") 

# Footer text 

st.markdown(
    """
    <div style='text-align: center; font-size: 14px; color: gray;'>
        This is an open-source project. The code base is housed on GitHub.
    </div>
    """,
    unsafe_allow_html=True
)

###############################
# Styling                     #
###############################

st.markdown(
    """
    <style>
    html, body, [class*="css"]  {
        font-family: "Helvetica", sans-serif !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

fig.update_layout(
    font=dict(family="Helvetica, sans-serif")
)
