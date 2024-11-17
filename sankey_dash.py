import numpy as np
import streamlit as st
import pandas as pd
from sankey import *


st.set_page_config(
    layout="wide", page_title="SankeyPlus", page_icon=":chart_with_upwards_trend:"
)

df_layers = pd.read_csv("layers.csv", dtype=str)
df_nodes = pd.read_csv("nodes.csv", dtype=str)
df_structure = pd.read_csv("structure.csv", dtype=str)
df_flows = pd.read_csv("flows.csv", dtype=str)

st.subheader("Sankey Diagram Inputs:")

with st.form("data_editor"):
    st_tab_layers, st_tab_nodes, st_tab_structure, st_tab_flows = st.tabs(
        ["Layers", "Nodes", "Structure", "Flows"]
    )

    with st_tab_layers:
        st.data_editor(df_layers, use_container_width=True, hide_index=True)

    with st_tab_nodes:
        st.data_editor(df_nodes, use_container_width=True, hide_index=True)

    with st_tab_structure:
        st.data_editor(df_structure, use_container_width=True, hide_index=True)

    with st_tab_flows:
        st.data_editor(df_flows, use_container_width=True, hide_index=True)

    submit_button = st.form_submit_button("Submit")

# ---
st.subheader("Sankey Diagram Parameters:")

cols = st.columns(4)
with cols[0]:
    st.markdown("**Size**")
    figsize_x = st.number_input("Width", 1, 10, Params.figsize[0], 1)
    figsize_y = st.number_input("Height", 1, 6, Params.figsize[1], 1)
    figsize = (figsize_x, figsize_y)
    corner_pad = st.number_input("Outer padding", 1, 3, Params.corner_pad, 1)


with cols[1]:
    st.markdown("**Structure | Nodes**")
    title_space = st.number_input("Title space", 0.1, 10.0, Params.title_space, 0.1)
    node_height = st.number_input(
        "Node | Height Multiplier", 0.5, 10.0, Params.node_height, 0.1
    )
    node_width = st.number_input("Node | Width", 0.5, 10.0, Params.node_width, 0.1)
    node_height_gap = st.number_input(
        "Node | Vertical Spacing", 0.1, 10.0, Params.node_height_gap, 0.1
    )
    node_width_gap = st.number_input(
        "Node | Horizontal Spacing", 0.1, 10.0, Params.node_width_gap, 0.1
    )

with cols[2]:
    st.markdown("**Structure | Flows**")
    flow_gap = st.number_input("Flow | Width", 1.0, 8.0, Params.flow_gap, 0.1)
    flow_alpha = st.number_input(
        "Flow | Transparency", 0.3, 0.9, Params.flow_alpha, 0.05, format="%0.2f"
    )
    curve = st.number_input(
        "Flow | Curvature", 0.0, 1.0, Params.curve, 0.05, format="%0.2f"
    )

with cols[3]:
    st.markdown("**Font Size**")
    fontsize_node = st.number_input(
        "Node | Font size", 4.0, 12.0, Params.fontsize_node, 0.5, format="%0.1f"
    )
    fontsize_flow = st.number_input(
        "Flow | Font size", 4.0, 12.0, Params.fontsize_flow, 0.5, format="%0.1f"
    )


class Params:
    title_space = title_space
    corner_pad = corner_pad
    node_height = node_height
    node_width = node_width
    flow_gap = flow_gap
    node_height_gap = node_height_gap
    node_width_gap = node_width_gap
    figsize = figsize
    fontsize_node = fontsize_node
    fontsize_flow = fontsize_flow
    flow_alpha = flow_alpha
    curve = curve


params = Params()

st.subheader("Sankey Diagram Output:")

df_structure = get_sankey_structure(df_nodes, df_layers, df_structure, params)
df_flows = get_sankey_flows(df_structure, df_flows)
fig = make_sankey_diagram(df_structure, df_flows, params)

st.pyplot(fig, use_container_width=False)
