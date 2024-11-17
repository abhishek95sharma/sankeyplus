import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import bezier


class Params:
    title_space = 1
    corner_pad = 1
    node_height = 2
    node_width = 2
    flow_gap = 5
    node_height_gap = 1
    node_width_gap = 1
    figsize = (10, 5)
    fontsize_node = 6.0
    fontsize_flow = 4.5
    flow_alpha = 0.65
    curve = 0.65


def get_sankey_structure(df_nodes, df_layers, df_structure, params=Params()):
    df_structure = df_structure.merge(df_nodes, how="left", on="Node")
    df_structure = df_structure.merge(df_layers, how="left", on="Layer")
    df_structure = df_structure.sort_values(by=["Layer Order", "Node Order"])

    df_structure["Node number"] = df_structure.groupby(["Layer Order"])[
        "Node"
    ].cumcount()
    df_structure["Layer number"] = df_structure["Layer Order"].astype(int) - 1
    df_structure["Value"] = df_structure["Value"].astype(float)

    df_structure = df_structure.merge(
        (
            df_structure.groupby(["Layer number"]).agg(
                max_node_number=("Node number", "max")
            )
            + 1
        ).reset_index()
    )
    max_node_number = df_structure["max_node_number"].max()

    df_structure["X_min"] = df_structure["Layer number"] * (
        params.node_width + params.node_width_gap + params.flow_gap
    )
    df_structure["X_max"] = (
        df_structure["Layer number"]
        * (params.node_width + params.node_width_gap + params.flow_gap)
        + params.node_width
    )
    df_structure["Y_min"] = df_structure["Node number"] * (
        params.node_height + params.node_height_gap
    )
    df_structure["Y_max"] = (
        df_structure["Node number"] * (params.node_height + params.node_height_gap)
        + params.node_height
    )

    X_den = df_structure["X_max"].max() + 2 * params.corner_pad
    Y_den = df_structure["Y_max"].max() + 2 * params.corner_pad + params.title_space

    df_structure["X_min"] = (params.corner_pad + df_structure["X_min"]) / X_den
    df_structure["X_max"] = (params.corner_pad + df_structure["X_max"]) / X_den
    Y_pad = 0.5 * (1 - df_structure["max_node_number"] / max_node_number) * Y_den
    df_structure["Y_min"] = (params.corner_pad + df_structure["Y_min"] + Y_pad) / Y_den
    df_structure["Y_max"] = (params.corner_pad + df_structure["Y_max"] + Y_pad) / Y_den

    df_structure["Y_min"] = 1 - df_structure["Y_min"]
    df_structure["Y_max"] = 1 - df_structure["Y_max"]

    df_structure["X_delta"] = df_structure["X_max"] - df_structure["X_min"]
    df_structure["Y_delta"] = df_structure["Y_max"] - df_structure["Y_min"]

    return df_structure


def get_sankey_flows(df_structure, df_flows):
    df_flows["Value"] = df_flows["Value"].astype(float)

    df_flows = df_flows.merge(
        df_structure[["Layer", "Node", "Color"]],
        left_on=["Start Layer", "Start Node"],
        right_on=["Layer", "Node"],
        how="left",
    )
    del df_flows["Layer"]
    del df_flows["Node"]

    df_flows = df_flows.merge(
        df_structure[
            [
                "Layer",
                "Node",
                "Value",
                "X_max",
                "Y_min",
                "Y_max",
                "Node number",
                "Layer number",
            ]
        ].add_prefix("Start "),
        on=["Start Layer", "Start Node"],
        how="left",
    )
    df_flows.rename(
        columns={
            "Start X_max": "Start_X",
        },
        inplace=True,
    )

    df_flows = df_flows.merge(
        df_structure[
            [
                "Layer",
                "Node",
                "Value",
                "X_min",
                "Y_min",
                "Y_max",
                "Node number",
                "Layer number",
            ]
        ].add_prefix("End "),
        on=["End Layer", "End Node"],
        how="left",
    )
    df_flows.rename(
        columns={
            "End X_min": "End_X",
        },
        inplace=True,
    )

    df_flows = df_flows.sort_values(
        [
            "Start Layer number",
            "End Layer number",
            "Start Node number",
            "End Node number",
        ]
    )

    df_flows["Start Cum Value"] = df_flows.groupby(
        [
            "Start Layer number",
            "Start Node number",
        ]
    )["Value"].cumsum()
    df_flows["End Cum Value"] = df_flows.groupby(
        [
            "End Layer number",
            "End Node number",
        ]
    )["Value"].cumsum()

    df_flows["Start_Y_end"] = df_flows["Start Y_min"] - (
        (df_flows["Start Y_min"] - df_flows["Start Y_max"])
        * df_flows["Start Cum Value"]
        / df_flows["Start Value"]
    )
    df_flows["Start_Y_start"] = df_flows.groupby(
        [
            "Start Layer number",
            "Start Node number",
        ]
    )["Start_Y_end"].shift(1)
    df_flows["Start_Y_start"] = np.where(
        df_flows["Start_Y_start"].isna(),
        df_flows["Start Y_min"],
        df_flows["Start_Y_start"],
    )

    df_flows["End_Y_end"] = df_flows["End Y_min"] - (
        (df_flows["End Y_min"] - df_flows["End Y_max"])
        * df_flows["End Cum Value"]
        / df_flows["End Value"]
    )
    df_flows["End_Y_start"] = df_flows.groupby(
        [
            "End Layer number",
            "End Node number",
        ]
    )["End_Y_end"].shift(1)
    df_flows["End_Y_start"] = np.where(
        df_flows["End_Y_start"].isna(),
        df_flows["End Y_min"],
        df_flows["End_Y_start"],
    )

    df_flows["X_delta"] = df_flows["End_X"] - df_flows["Start_X"]
    df_flows["Start_Y"] = (df_flows["Start_Y_start"] + df_flows["Start_Y_end"]) / 2
    df_flows["Start_Y_band"] = (
        np.abs(df_flows["Start_Y_start"] - df_flows["Start_Y_end"]) / 2
    )
    df_flows["End_Y"] = (df_flows["End_Y_start"] + df_flows["End_Y_end"]) / 2
    df_flows["End_Y_band"] = np.abs(df_flows["End_Y_start"] - df_flows["End_Y_end"]) / 2
    df_flows["Y_delta"] = df_flows["End_Y"] - df_flows["Start_Y"]

    return df_flows


def make_rectangle(ax, x, y, width, height, color, border_color="none", linewidth=0.5):
    rect = patches.Rectangle(
        (x, y),
        width,
        height,
        linewidth=linewidth,
        edgecolor=border_color,
        facecolor=color,
    )
    ax.add_patch(rect)


def make_flow(
    x_start,
    x_end,
    y_start,
    y_end,
    y_start_band,
    y_end_band,
    color,
    alpha,
    curve,
    border_color="none",
):
    bezier_curve = bezier.Curve(
        np.asfortranarray(
            [
                [0.0, curve, 0.5, 1.0 - curve, 1.0],
                [0.0, 0.0, 0.5, 1.0, 1.0],
            ]
        ),
        degree=4,
    )
    n = 100
    bezier_curve_evaluated = bezier_curve.evaluate_multi(np.linspace(0, 1, n))
    import streamlit as st

    X = x_start + bezier_curve_evaluated[0] * ((x_end - x_start))
    Y = y_start + bezier_curve_evaluated[1] * ((y_end - y_start))
    Y_band = np.linspace(y_start_band, y_end_band, n)

    # st.write(X)
    # st.write(Y)
    # st.write(Y_upper)
    # st.write(Y_lower)
    # st.write([x_start, x_end])
    # st.write([y_start - y_start_band, y_end - y_end_band])
    # st.write([y_start + y_start_band, y_end + y_end_band])

    # st.write("dffdsfdfg")

    plt.fill_between(
        # [x_start, x_end],
        # [y_start - y_start_band, y_end - y_end_band],
        # [y_start + y_start_band, y_end + y_end_band],
        X,
        Y - Y_band,
        Y + Y_band,
        alpha=alpha,
        color=color,
        edgecolor=border_color,
    )


def write_text(
    text,
    x,
    y,
    width,
    height,
    fontsize,
    bold=False,
    color="black",
    ha="center",
    va="center",
):
    plt.text(
        x + width / 2,
        y + height / 2,
        text,
        fontsize=fontsize,
        fontweight="bold" if bold else "normal",
        color=color,
        ha=ha,
        va=va,
        # bbox=dict(facecolor="red", alpha=0.5),
    )


def make_sankey_diagram(df_structure, df_flows, params=Params()):
    fig, ax = plt.subplots(figsize=params.figsize, frameon=False)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    plt.rcParams["font.family"] = "monospace"
    plt.rcParams["font.monospace"] = ["Inconsolata"]
    ax.set_xticks([])
    ax.set_yticks([])
    plt.xlabel("")
    plt.ylabel("")
    plt.axis("off")

    for i, row in df_structure.iterrows():
        make_rectangle(
            ax,
            row["X_min"],
            row["Y_min"],
            row["X_delta"],
            row["Y_delta"],
            row["Color"],
        )

        write_node_text = lambda text, bold=False: write_text(
            text,
            row["X_min"],
            row["Y_min"],
            row["X_delta"],
            row["Y_delta"],
            fontsize=params.fontsize_node,
            bold=bold,
        )
        write_node_text(f'{row["Node"]}\n\n\n', True)
        write_node_text(f'\n\n{row["Line 1"]}\n')
        write_node_text(f'\n\n\n{row["Line 2"]}')

        write_text(
            row["Layer"],
            row["X_min"],
            1,
            row["X_delta"],
            0,
            fontsize=params.fontsize_node,
            bold=True,
        )

    for i, row in df_flows.iterrows():
        make_flow(
            row["Start_X"],
            row["End_X"],
            row["Start_Y"],
            row["End_Y"],
            row["Start_Y_band"],
            row["End_Y_band"],
            row["Color"],
            params.flow_alpha,
            params.curve,
        )

        write_flow_text = lambda text, bold=False: write_text(
            text,
            row["End_X"],
            row["End_Y"],
            0,
            0,
            fontsize=params.fontsize_flow,
            bold=bold,
            ha="right",
            va="center",
        )
        write_flow_text(f'{row["Start Node"]}->{row["End Node"]}\n', True)
        write_flow_text(f'\n{row["Line 1"]}, {row["Line 2"]}')

    return fig
