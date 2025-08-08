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

    # Moving averages chart
    df['Moving_Avg_1000'] = df['Values'].rolling(window=1000, min_periods=1).mean()
    df['Moving_Avg_5000'] = df['Values'].rolling(window=5000, min_periods=1).mean()
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=df['Timestamp'], y=df['Values'], mode='lines', name='Original Data',
        hovertemplate='Time: %{x}<br>Voltage: %{y:.2f} V'
    ))
    fig1.add_trace(go.Scatter(
        x=df['Timestamp'], y=df['Moving_Avg_1000'], mode='lines', name='MA 1000',
        hovertemplate='Time: %{x}<br>Voltage: %{y:.2f} V'
    ))
    fig1.add_trace(go.Scatter(
        x=df['Timestamp'], y=df['Moving_Avg_5000'], mode='lines', name='MA 5000',
        hovertemplate='Time: %{x}<br>Voltage: %{y:.2f} V'
    ))
    fig1.update_layout(
        title='Voltage Data with Moving Averages',
        xaxis_title="Time (s)",
        yaxis_title="Voltage (V)"
    )

    # Peaks and lows chart
    peaks, _ = find_peaks(df['Values'], prominence=5)
    lows, _ = find_peaks(-df['Values'], prominence=5)
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df['Timestamp'], y=df['Values'], mode='lines', name='Original Data',
        hovertemplate='Time: %{x}<br>Voltage: %{y:.2f} V'
    ))
    fig2.add_trace(go.Scatter(
        x=df.iloc[peaks]['Timestamp'], y=df.iloc[peaks]['Values'], mode='markers', name='Peaks',
        hovertemplate='Time: %{x}<br>Voltage: %{y:.2f} V'
    ))
    fig2.add_trace(go.Scatter(
        x=df.iloc[lows]['Timestamp'], y=df.iloc[lows]['Values'], mode='markers', name='Lows',
        hovertemplate='Time: %{x}<br>Voltage: %{y:.2f} V'
    ))
    fig2.update_layout(
        title='Voltage Data with Peaks and Lows',
        xaxis_title="Time (s)",
        yaxis_title="Voltage (V)"
    )

    # Below threshold chart
    threshold = 20
    below_threshold = df[df['Values'] < threshold]
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=df['Timestamp'], y=df['Values'], mode='lines', name='Original Data',
        hovertemplate='Time: %{x}<br>Voltage: %{y:.2f} V'
    ))
    fig3.add_trace(go.Scatter(
        x=below_threshold['Timestamp'], y=below_threshold['Values'], mode='markers', name=f'Below {threshold}',
        hovertemplate='Time: %{x}<br>Voltage: %{y:.2f} V'
    ))
    fig3.add_hline(y=threshold, line_dash='dash', annotation_text=f"Threshold {threshold}")
    fig3.update_layout(
        title=f'Voltage Data Below {threshold}',
        xaxis_title="Time (s)",
        yaxis_title="Voltage (V)"
    )

    # Downward acceleration points chart
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
    fig4.add_trace(go.Scatter(
        x=df['Timestamp'], y=df['Values'], mode='lines', name='Voltage',
        hovertemplate='Time: %{x}<br>Voltage: %{y:.2f} V'
    ))
    fig4.add_trace(go.Scatter(
        x=accel_df['Timestamp'], y=accel_df['Values'], mode='markers', name='Acceleration Points',
        hovertemplate='Time: %{x}<br>Voltage: %{y:.2f} V'
    ))
    fig4.update_layout(
        title='Voltage Data with Downward Acceleration Points',
        xaxis_title="Time (s)",
        yaxis_title="Voltage (V)"
    )

    return render_template(
        "index.html",
        chart1=to_html(fig1, full_html=False),
        chart2=to_html(fig2, full_html=False),
        chart3=to_html(fig3, full_html=False),
        chart4=to_html(fig4, full_html=False)
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
