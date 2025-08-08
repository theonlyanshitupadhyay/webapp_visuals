from flask import Flask, render_template
import pandas as pd
import plotly.express as px
import plotly.io as pio

app = Flask(__name__)

# Load your CSV file
df = pd.read_csv("Sample_Data.csv")

# Create a function to style each chart
def create_voltage_chart(data, title, color):
    fig = px.line(data, x="Timestamp", y="Values", title=title, line_shape="linear")
    fig.update_layout(
        xaxis_title="Time (s)",
        yaxis_title="Voltage (V)"
    )
    fig.update_traces(
        line=dict(color=color),
        hovertemplate="Time: %{x}<br>Voltage: %{y} V<extra></extra>"
    )
    return pio.to_html(fig, full_html=False)

@app.route("/")
def index():
    chart1 = create_voltage_chart(df, "Voltage Over Time – Chart 1", "red")
    chart2 = create_voltage_chart(df, "Voltage Over Time – Chart 2", "blue")
    chart3 = create_voltage_chart(df, "Voltage Over Time – Chart 3", "green")
    chart4 = create_voltage_chart(df, "Voltage Over Time – Chart 4", "orange")

    return render_template("index.html",
                           chart1=chart1,
                           chart2=chart2,
                           chart3=chart3,
                           chart4=chart4)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
