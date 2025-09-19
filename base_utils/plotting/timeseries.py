from typing import List
import plotly.graph_objs as go
import pandas as pd
import plotly.io as pio


HORIZONTAL_LEGEND = dict(
    orientation="h",
    yanchor="bottom",
    y=-0.2,  # Move below plot
    xanchor="center",
    x=0.5,   # Center horizontally
)

# Set a global default template
pio.templates.default = (
    "plotly_white"  # other good options: "simple_white", "seaborn", "ggplot2"
)


def plot_timeseries(
    df: pd.DataFrame,
    bold_series: str | list = [],
    secondary_y_axis_cols: list[str] = [],
    mode: str = "lines",
    title: str = "Timeseries Plot",
    legend_dict: dict = HORIZONTAL_LEGEND,
    add_monthly_v_line: None | int | List[int] = None,
    add_vline_today: bool = False,
) -> go.Figure:
    """
    Plots the timeseries data from a DataFrame using Plotly.

    Parameters:
    - df: pandas DataFrame containing the timeseries data.
    - bold_series: A string or list of strings representing the column names to be highlighted in bold.
    - secondary_y_axis_cols: List of column names to plot on a secondary y-axis.
    - mode: Plot mode, e.g. 'lines', 'markers', 'lines+markers'.
    - legend_dict: Dict of legend properties (default = HORIZONTAL_LEGEND).
    """

    # normalize inputs
    if not isinstance(bold_series, list):
        bold_series = [bold_series]

    traces = []
    for col in df.columns.tolist():
        # assign which y-axis to use
        yaxis = "y2" if col in secondary_y_axis_cols else "y"

        # line style
        if col in bold_series:
            line_style = dict(width=4, color="black")
        else:
            line_style = dict(width=1)

        traces.append(
            go.Scatter(
                x=df.index,
                y=df[col],
                mode=mode,
                name=str(col),
                line=line_style,
                yaxis=yaxis,
            )
        )

    # Layout with secondary axis definition
    layout = go.Layout(
        title=title,
        xaxis=dict(title="Time"),
        yaxis=dict(title="Primary Axis"),
        yaxis2=dict(
            title="Secondary Axis", overlaying="y", side="right", showgrid=False
        ),
        showlegend=True,
        # legend=legend_dict,

    )


    fig = go.Figure(data=traces, layout=layout)

    if add_monthly_v_line:
        if isinstance(add_monthly_v_line, int):
            v_lines = list(range(add_monthly_v_line, 13))  # from given month through Dec
        elif isinstance(add_monthly_v_line, (list, tuple, set)):
            v_lines = list(add_monthly_v_line)             # explicit months like [8,9,10,11]
        else:
            v_lines = list(range(1, 13))                   # truthy sentinel -> all months

        # First day of each month in the data span
        month_starts = pd.date_range(
            df.index.min().to_period("M").to_timestamp(),
            df.index.max().to_period("M").to_timestamp(),
            freq="MS"
        )

        for ts in month_starts:
            if ts.month in v_lines:
                fig.add_vline(x=ts, line_dash="dot", line_color="gray", opacity=0.4)

    if add_vline_today:
        fig.add_vline(x=pd.Timestamp.today(), line_dash="dash", line_color="red", opacity=0.7)
    return fig