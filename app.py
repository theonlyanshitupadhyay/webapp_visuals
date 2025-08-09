import os
from flask import Flask, render_template
import pandas as pd
import plotly.graph_objs as go
from scipy.signal import find_peaks
from plotly.io import to_html

app = Flask(__name__)

@app.route("/")
def index():
    df = pd.read_csv(os.path.join(os.path.dirname(__file__), 'Sample_Data.csv'))
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%d-%m-%Y %H:%M')
    df = df.sort_values('Timestamp').reset_index(drop=True)

    # Create time in seconds from start
    df['Time_s'] = (df['Timestamp'] - df['Timestamp'].iloc[0]).dt.total_seconds()

    # Function to make all charts consistent
    def style_figure(fig, title):
        fig.update_layout(
            title=title,
            xaxis_title="Time (s)",
            yaxis_title="Voltage (V)",
            autosize=True,
            margin=dict(l=40, r=20, t=40, b=40),
            hovermode="x unified",
            template="plotly_white",
            legend=dict(x=0, y=1, bgcolor="rgba(255,255,255,0)"),
        )
        fig.update_layout(width=None, height=None)  # Responsive
        return fig

    # Chart 1: Moving averages
    df['Moving_Avg_1000'] = df['Values'].rolling(window=1000, min_periods=1).mean()
    df['Moving_Avg_5000'] = df['Values'].rolling(window=5000, min_periods=1).mean()
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df['Time_s'], y=df['Values'], mode='lines', name='Original Data',
                              hovertemplate='Time: %{x:.2f} s<br>Voltage: %{y:.2f} V'))
    fig1.add_trace(go.Scatter(x=df['Time_s'], y=df['Moving_Avg_1000'], mode='lines', name='MA 1000',
                              hovertemplate='Time: %{x:.2f} s<br>Voltage: %{y:.2f} V'))
    fig1.add_trace(go.Scatter(x=df['Time_s'], y=df['Moving_Avg_5000'], mode='lines', name='MA 5000',
                              hovertemplate='Time: %{x:.2f} s<br>Voltage: %{y:.2f} V'))
    fig1 = style_figure(fig1, 'Voltage Data with Moving Averages')

    # Chart 2: Peaks and Lows
    peaks, _ = find_peaks(df['Values'], prominence=5)
    lows, _ = find_peaks(-df['Values'], prominence=5)
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df['Time_s'], y=df['Values'], mode='lines', name='Original Data',
                              hovertemplate='Time: %{x:.2f} s<br>Voltage: %{y:.2f} V'))
    fig2.add_trace(go.Scatter(x=df.iloc[peaks]['Time_s'], y=df.iloc[peaks]['Values'], mode='markers', name='Peaks',
                              hovertemplate='Time: %{x:.2f} s<br>Voltage: %{y:.2f} V'))
    fig2.add_trace(go.Scatter(x=df.iloc[lows]['Time_s'], y=df.iloc[lows]['Values'], mode='markers', name='Lows',
                              hovertemplate='Time: %{x:.2f} s<br>Voltage: %{y:.2f} V'))
    fig2 = style_figure(fig2, 'Voltage Data with Peaks and Lows')

    # Chart 3: Below threshold
    threshold = 20
    below_threshold = df[df['Values'] < threshold]
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=df['Time_s'], y=df['Values'], mode='lines', name='Original Data',
                              hovertemplate='Time: %{x:.2f} s<br>Voltage: %{y:.2f} V'))
    fig3.add_trace(go.Scatter(x=below_threshold['Time_s'], y=below_threshold['Values'], mode='markers',
                              name=f'Below {threshold}', hovertemplate='Time: %{x:.2f} s<br>Voltage: %{y:.2f} V'))
    fig3.add_hline(y=threshold, line_dash='dash', annotation_text=f"Threshold {threshold}")
    fig3 = style_figure(fig3, f'Voltage Data Below {threshold}')

    # Chart 4: Downward acceleration points
    df['First_Deriv'] = df['Values'].diff()
    df['Second_Deriv'] = df['First_Deriv'].diff()
    downward_cycles = df[df['First_Deriv'] < 0].copy()
    downward_cycles['Cycle_ID'] = (downward_cycles['Timestamp'].diff() > pd.Timedelta('1h')).cumsum()
    acceleration_points = []
    for cycle_id, group in downward_cycles.groupby('Cycle_ID'):
        acceleration_candidates = group[group['Second_Deriv'] < 0]
        if not acceleration_candidates.empty:
            max_accel_point = acceleration_candidates.loc[acceleration_candidates['Second_Deriv'].idxmin()]
            acceleration_points.append(max_accel_point)
    accel_df = pd.DataFrame(acceleration_points)
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(x=df['Time_s'], y=df['Values'], mode='lines', name='Voltage',
                              hovertemplate='Time: %{x:.2f} s<br>Voltage: %{y:.2f} V'))
    fig4.add_trace(go.Scatter(x=accel_df['Time_s'], y=accel_df['Values'], mode='markers', name='Acceleration Points',
                              hovertemplate='Time: %{x:.2f} s<br>Voltage: %{y:.2f} V'))
    fig4 = style_figure(fig4, 'Voltage Data with Downward Acceleration Points')

    return render_template("index.html",
                           chart1=to_html(fig1, full_html=False, include_plotlyjs='cdn'),
                           chart2=to_html(fig2, full_html=False, include_plotlyjs=False),
                           chart3=to_html(fig3, full_html=False, include_plotlyjs=False),
                           chart4=to_html(fig4, full_html=False, include_plotlyjs=False)
                           )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
