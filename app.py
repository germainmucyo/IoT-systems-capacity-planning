"""
app.py — IoT Edge-Cloud Performance Explorer
Run: python app.py
Then open http://127.0.0.1:8050 in your browser.
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

# ── Load pre-computed simulation results ──────────────────────────────────────
df = pd.read_csv("simulation_results.csv")
M_OPTIONS = [int(m) for m in sorted(df["M"].unique())]
X_OPTIONS = [float(x) for x in sorted(df["x"].unique())]

# ── App setup ─────────────────────────────────────────────────────────────────
app = Dash(__name__)
app.title = "IoT Edge-Cloud Performance Explorer"

COLORS = {
    "bg":       "#0f1117",
    "card":     "#1a1d27",
    "border":   "#2e3250",
    "accent":   "#4f8ef7",
    "green":    "#36c98e",
    "orange":   "#f7a14f",
    "red":      "#f75f5f",
    "text":     "#e8eaf0",
    "subtext":  "#8b90a8",
}

CARD = {
    "backgroundColor": COLORS["card"],
    "border":          f"1px solid {COLORS['border']}",
    "borderRadius":    "10px",
    "padding":         "20px",
    "marginBottom":    "20px",
}

# ── Layout ────────────────────────────────────────────────────────────────────
app.layout = html.Div(style={"backgroundColor": COLORS["bg"], "minHeight": "100vh",
                              "fontFamily": "Inter, sans-serif", "color": COLORS["text"],
                              "padding": "30px"}, children=[

    # Header
    html.Div([
        html.H1("IoT Edge-Cloud Performance Explorer",
                style={"margin": 0, "fontSize": "26px", "fontWeight": "700"}),
        html.P("Interactive capacity planning tool for IoT gateway & edge-cloud systems",
               style={"margin": "6px 0 0", "color": COLORS["subtext"], "fontSize": "14px"}),
    ], style={"marginBottom": "28px"}),

    # ── Tabs ──────────────────────────────────────────────────────────────────
    dcc.Tabs(id="tabs", value="offload",
             colors={"border": COLORS["border"], "primary": COLORS["accent"],
                     "background": COLORS["card"]},
             children=[

        # ── Tab 1: Offloading Analysis ────────────────────────────────────────
        dcc.Tab(label="Offloading Analysis", value="offload",
                style={"color": COLORS["subtext"], "backgroundColor": COLORS["card"]},
                selected_style={"color": COLORS["text"], "backgroundColor": COLORS["bg"],
                                "borderTop": f"2px solid {COLORS['accent']}"},
                children=[html.Div(style={"padding": "20px 0"}, children=[

                    # Control
                    html.Div(style=CARD, children=[
                        html.Label("Select number of devices (M):",
                                   style={"fontWeight": "600", "marginBottom": "10px",
                                          "display": "block"}),
                        dcc.Slider(id="slider-M",
                                   min=min(M_OPTIONS), max=max(M_OPTIONS),
                                   step=None, value=M_OPTIONS[1],
                                   marks={m: str(m) for m in M_OPTIONS},
                                   tooltip={"placement": "bottom"}),
                    ]),

                    # KPI cards
                    html.Div(id="kpi-row", style={"display": "flex", "gap": "16px",
                                                   "marginBottom": "20px"}),

                    # Charts
                    html.Div(style={"display": "grid",
                                    "gridTemplateColumns": "1fr 1fr",
                                    "gap": "16px"}, children=[
                        html.Div(style=CARD, children=[dcc.Graph(id="fig-mean-delay")]),
                        html.Div(style=CARD, children=[dcc.Graph(id="fig-p95-delay")]),
                        html.Div(style={**CARD, "gridColumn": "1 / -1"},
                                 children=[dcc.Graph(id="fig-throughput")]),
                    ]),
                ])]),

        # ── Tab 2: Scaling Analysis ───────────────────────────────────────────
        dcc.Tab(label="Scaling Analysis", value="scaling",
                style={"color": COLORS["subtext"], "backgroundColor": COLORS["card"]},
                selected_style={"color": COLORS["text"], "backgroundColor": COLORS["bg"],
                                "borderTop": f"2px solid {COLORS['accent']}"},
                children=[html.Div(style={"padding": "20px 0"}, children=[

                    # Control
                    html.Div(style=CARD, children=[
                        html.Label("Select offloading ratio (x):",
                                   style={"fontWeight": "600", "marginBottom": "10px",
                                          "display": "block"}),
                        dcc.Slider(id="slider-x",
                                   min=0.0, max=1.0, step=None, value=0.2,
                                   marks={float(x): str(x) for x in X_OPTIONS},
                                   tooltip={"placement": "bottom"}),

                        html.Div(style={"marginTop": "20px"}),
                        html.Label("Delay threshold (s) — danger zone:",
                                   style={"fontWeight": "600", "marginBottom": "10px",
                                          "display": "block"}),
                        dcc.Slider(id="slider-threshold", min=50, max=1000,
                                   step=50, value=300,
                                   marks={v: str(v) for v in range(50, 1001, 150)},
                                   tooltip={"placement": "bottom"}),
                    ]),

                    html.Div(style={"display": "grid",
                                    "gridTemplateColumns": "1fr 1fr",
                                    "gap": "16px"}, children=[
                        html.Div(style=CARD, children=[dcc.Graph(id="fig-scale-mean")]),
                        html.Div(style=CARD, children=[dcc.Graph(id="fig-scale-p95")]),
                        html.Div(style={**CARD, "gridColumn": "1 / -1"},
                                 children=[dcc.Graph(id="fig-scale-tput")]),
                    ]),
                ])]),

        # ── Tab 3: Heatmap ────────────────────────────────────────────────────
        dcc.Tab(label="Operating Surface Heatmap", value="heatmap",
                style={"color": COLORS["subtext"], "backgroundColor": COLORS["card"]},
                selected_style={"color": COLORS["text"], "backgroundColor": COLORS["bg"],
                                "borderTop": f"2px solid {COLORS['accent']}"},
                children=[html.Div(style={"padding": "20px 0"}, children=[

                    html.Div(style=CARD, children=[
                        html.Label("Metric to display:",
                                   style={"fontWeight": "600", "marginBottom": "10px",
                                          "display": "block"}),
                        dcc.RadioItems(id="heatmap-metric",
                                       options=[
                                           {"label": "  Mean Delay", "value": "mean_delay"},
                                           {"label": "  P95 Delay",  "value": "p95_delay"},
                                           {"label": "  Throughput", "value": "throughput"},
                                       ],
                                       value="mean_delay",
                                       inline=True,
                                       labelStyle={"marginRight": "30px",
                                                   "color": COLORS["text"]}),
                    ]),

                    html.Div(style=CARD, children=[dcc.Graph(id="fig-heatmap")]),

                    html.Div(style=CARD, children=[
                        html.H4("Optimal Operating Point",
                                style={"margin": "0 0 10px", "color": COLORS["accent"]}),
                        html.Div(id="optimal-table"),
                    ]),
                ])]),
    ]),
])


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_line(x, y, name, color, ci_lo=None, ci_hi=None, dash="solid"):
    traces = []
    if ci_lo is not None and ci_hi is not None:
        traces.append(go.Scatter(
            x=list(x) + list(x)[::-1],
            y=list(ci_hi) + list(ci_lo)[::-1],
            fill="toself", fillcolor=color.replace(")", ",0.15)").replace("rgb", "rgba"),
            line=dict(width=0), showlegend=False, hoverinfo="skip"
        ))
    traces.append(go.Scatter(x=x, y=y, name=name, mode="lines+markers",
                              line=dict(color=color, width=2.5, dash=dash),
                              marker=dict(size=7)))
    return traces


def dark_layout(title, xlabel, ylabel):
    return dict(
        title=dict(text=title, font=dict(size=15, color=COLORS["text"])),
        xaxis=dict(title=xlabel, color=COLORS["subtext"],
                   gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
        yaxis=dict(title=ylabel, color=COLORS["subtext"],
                   gridcolor=COLORS["border"], zerolinecolor=COLORS["border"]),
        plot_bgcolor=COLORS["card"], paper_bgcolor=COLORS["card"],
        font=dict(color=COLORS["text"]),
        legend=dict(bgcolor=COLORS["card"]),
        margin=dict(l=50, r=20, t=50, b=50),
    )


def kpi_card(label, value, color):
    return html.Div(style={
        "backgroundColor": COLORS["card"], "border": f"1px solid {color}",
        "borderRadius": "10px", "padding": "16px 22px", "flex": "1",
        "borderLeft": f"4px solid {color}"
    }, children=[
        html.P(label, style={"margin": 0, "color": COLORS["subtext"], "fontSize": "12px"}),
        html.H3(value, style={"margin": "4px 0 0", "color": color, "fontSize": "22px"}),
    ])


# ── Callbacks: Offloading tab ─────────────────────────────────────────────────

@app.callback(
    Output("kpi-row",        "children"),
    Output("fig-mean-delay", "figure"),
    Output("fig-p95-delay",  "figure"),
    Output("fig-throughput", "figure"),
    Input("slider-M", "value"),
)
def update_offload(M):
    sub = df[df["M"] == M].sort_values("x")
    # Find optimal x: minimum mean delay, preferring interior points (x > 0)
    interior = sub[sub["x"] > 0.0]
    opt_interior = interior.loc[interior["mean_delay"].idxmin()]
    opt_full    = sub.loc[sub["mean_delay"].idxmin()]
    # Use interior optimum if it's within 5% of the global minimum
    if opt_interior["mean_delay"] <= opt_full["mean_delay"] * 1.05:
        opt = opt_interior
    else:
        opt = opt_full

    # KPI cards
    kpis = html.Div(style={"display": "flex", "gap": "16px", "width": "100%"}, children=[
        kpi_card("Optimal Offload Ratio (x*)", f"{opt['x']:.1f}", COLORS["accent"]),
        kpi_card("Min Mean Delay",  f"{opt['mean_delay']:.2f} s",  COLORS["green"]),
        kpi_card("P95 at Optimum",  f"{opt['p95_delay']:.2f} s",   COLORS["orange"]),
        kpi_card("Throughput",      f"{opt['throughput']:.2f} t/s", COLORS["text"]),
    ])

    def vline(x_val):
        return dict(type="line", x0=x_val, x1=x_val, yref="paper", y0=0, y1=1,
                    line=dict(color=COLORS["green"], width=1.5, dash="dot"))

    # Mean delay
    fig1 = go.Figure(
        make_line(sub["x"], sub["mean_delay"], "Mean Delay", COLORS["accent"],
                  sub["ci_mean_low"], sub["ci_mean_high"]))
    fig1.add_shape(vline(opt["x"]))
    fig1.add_annotation(x=opt["x"], y=opt["mean_delay"],
                        text=f"x*={opt['x']}", showarrow=True,
                        arrowcolor=COLORS["green"], font=dict(color=COLORS["green"]))
    fig1.update_layout(dark_layout(f"Mean Delay vs x  (M={M})", "Offloading Ratio x", "Delay (s)"))
    fig1.update_xaxes(range=[-0.05, 1.05])
    fig1.update_yaxes(rangemode="tozero")

    # P95 delay
    fig2 = go.Figure(
        make_line(sub["x"], sub["p95_delay"], "P95 Delay", COLORS["orange"],
                  sub["ci_p95_low"], sub["ci_p95_high"]))
    fig2.add_shape(vline(opt["x"]))
    fig2.update_layout(dark_layout(f"P95 Delay vs x  (M={M})", "Offloading Ratio x", "Delay (s)"))
    fig2.update_xaxes(range=[-0.05, 1.05])
    fig2.update_yaxes(rangemode="tozero")

    # Throughput
    fig3 = go.Figure(
        make_line(sub["x"], sub["throughput"], "Throughput", COLORS["green"]))
    fig3.update_layout(dark_layout(f"Throughput vs x  (M={M})", "Offloading Ratio x", "Tasks/sec"))

    return kpis, fig1, fig2, fig3


# ── Callbacks: Scaling tab ────────────────────────────────────────────────────

@app.callback(
    Output("fig-scale-mean", "figure"),
    Output("fig-scale-p95",  "figure"),
    Output("fig-scale-tput", "figure"),
    Input("slider-x",         "value"),
    Input("slider-threshold", "value"),
)
def update_scaling(x, threshold):
    sub = df[df["x"] == x].sort_values("M")

    def threshold_shape():
        return dict(type="line", x0=min(M_OPTIONS), x1=max(M_OPTIONS),
                    y0=threshold, y1=threshold,
                    line=dict(color=COLORS["red"], width=1.5, dash="dash"))

    # Find crossing point
    cross = sub[sub["mean_delay"] >= threshold]
    cross_note = ""
    if not cross.empty:
        cross_note = f" — danger zone at M≥{int(cross.iloc[0]['M'])}"

    fig1 = go.Figure(
        make_line(sub["M"], sub["mean_delay"], "Mean Delay", COLORS["accent"],
                  sub["ci_mean_low"], sub["ci_mean_high"]))
    fig1.add_shape(threshold_shape())
    fig1.update_layout(dark_layout(
        f"Mean Delay vs M  (x={x}){cross_note}", "Devices (M)", "Delay (s)"))

    fig2 = go.Figure(
        make_line(sub["M"], sub["p95_delay"], "P95 Delay", COLORS["orange"],
                  sub["ci_p95_low"], sub["ci_p95_high"]))
    fig2.update_layout(dark_layout(f"P95 Delay vs M  (x={x})", "Devices (M)", "Delay (s)"))

    fig3 = go.Figure(
        make_line(sub["M"], sub["throughput"], "Throughput", COLORS["green"]))
    fig3.update_layout(dark_layout(f"Throughput vs M  (x={x})", "Devices (M)", "Tasks/sec"))

    return fig1, fig2, fig3


# ── Callbacks: Heatmap tab ────────────────────────────────────────────────────

@app.callback(
    Output("fig-heatmap",   "figure"),
    Output("optimal-table", "children"),
    Input("heatmap-metric", "value"),
)
def update_heatmap(metric):
    metric_labels = {"mean_delay": "Mean Delay (s)", "p95_delay": "P95 Delay (s)",
                     "throughput": "Throughput (tasks/s)"}
    colorscale = "RdYlGn_r" if metric != "throughput" else "RdYlGn"

    m_vals = sorted(df["M"].unique())
    x_vals = sorted(df["x"].unique())
    x_strs = [f"{float(v):.1f}" for v in x_vals]
    m_strs = [str(int(v)) for v in m_vals]

    # Build z matrix
    z = []
    for m in m_vals:
        row = []
        for x in x_vals:
            val = df[(df["M"] == m) & (df["x"] == x)][metric].values
            row.append(float(val[0]) if len(val) > 0 else 0)
        z.append(row)

    import plotly.figure_factory as ff
    fig = px.imshow(
        z,
        x=x_strs,
        y=m_strs,
        color_continuous_scale=colorscale,
        labels=dict(x="Offloading Ratio x", y="Devices (M)",
                    color=metric_labels[metric]),
        aspect="auto",
    )

    fig.update_yaxes(autorange="reversed")
    for i, m in enumerate(m_vals):
        best_idx = z[i].index(min(z[i])) if metric != "throughput" else z[i].index(max(z[i]))
        fig.add_annotation(x=x_strs[best_idx], y=m_strs[i], text="★",
                           showarrow=False, font=dict(size=13, color="white"))

    fig.update_layout(
        title=dict(text=f"Operating Surface — {metric_labels[metric]}",
                   font=dict(size=15, color=COLORS["text"])),
        plot_bgcolor=COLORS["bg"],
        paper_bgcolor=COLORS["bg"],
        font=dict(color=COLORS["text"]),
        coloraxis_colorbar=dict(
            title=dict(text=metric_labels[metric], font=dict(color=COLORS["text"])),
            tickfont=dict(color=COLORS["text"]),
        ),
        margin=dict(l=60, r=20, t=60, b=60),
        height=520,
    )

    # Optimal table
    best_rows = []
    for m in sorted([int(v) for v in df["M"].unique()]):
        sub = df[df["M"] == m]
        opt = sub.loc[sub["mean_delay"].idxmin()]
        best_rows.append(html.Tr([
            html.Td(int(m),                    style={"padding": "6px 14px"}),
            html.Td(f"{opt['x']:.1f}",         style={"padding": "6px 14px",
                                                        "color": COLORS["accent"]}),
            html.Td(f"{opt['mean_delay']:.2f} s", style={"padding": "6px 14px"}),
            html.Td(f"{opt['p95_delay']:.2f} s",  style={"padding": "6px 14px"}),
            html.Td(f"{opt['throughput']:.2f}",   style={"padding": "6px 14px"}),
        ]))

    table = html.Table(style={"width": "100%", "borderCollapse": "collapse",
                               "fontSize": "13px"}, children=[
        html.Thead(html.Tr([
            html.Th(h, style={"textAlign": "left", "padding": "8px 14px",
                               "color": COLORS["subtext"], "borderBottom":
                               f"1px solid {COLORS['border']}"})
            for h in ["Devices (M)", "Optimal x*", "Min Mean Delay",
                       "P95 Delay", "Throughput"]
        ])),
        html.Tbody(best_rows),
    ])

    return fig, table


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)