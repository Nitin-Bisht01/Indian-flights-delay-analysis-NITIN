import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ============================================================
# PAGE CONFIG + THEME
# ============================================================
st.set_page_config(
    page_title="Flight Operations Intelligence",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    /* Main canvas and readable typography */
    .stApp {
        background: linear-gradient(180deg, #f6f8fc 0%, #edf2f8 100%);
        color: #172b4d !important;
    }
    [data-testid="stAppViewContainer"] .main,
    [data-testid="stMain"] {
        color: #172b4d !important;
    }
    [data-testid="stAppViewContainer"] .main p,
    [data-testid="stAppViewContainer"] .main li,
    [data-testid="stAppViewContainer"] .main label,
    [data-testid="stAppViewContainer"] .main [data-testid="stCaptionContainer"] {
        color: #40516b;
    }
    [data-testid="stAppViewContainer"] .main h1,
    [data-testid="stAppViewContainer"] .main h2,
    [data-testid="stAppViewContainer"] .main h3,
    [data-testid="stAppViewContainer"] .main h4 {
        color: #142b4a !important;
        font-weight: 700;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #10243f 0%, #173b59 100%);
    }
    [data-testid="stSidebar"] * { color: #f4f8ff !important; }
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] [data-baseweb="select"] *,
    [data-testid="stSidebar"] [data-baseweb="tag"] {
        color: #172b4d !important;
    }

    /* Hero banner */
    .hero {
        padding: 1.35rem 1.6rem;
        border-radius: 18px;
        background: linear-gradient(115deg,#102747 0%,#176b87 55%,#35a6a0 100%);
        color: #ffffff !important;
        margin-bottom: 1rem;
        box-shadow: 0 8px 24px rgba(16,39,71,.14);
    }
    .hero h1 { color: #ffffff !important; margin: 0; font-size: 2rem; }
    .hero p { color: #e8f5fb !important; margin: .35rem 0 0 0; }

    /* KPI cards: force dark text on white cards */
    div[data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1px solid #dce5f0;
        padding: 14px 16px;
        border-radius: 14px;
        box-shadow: 0 3px 12px rgba(30,55,90,.06);
    }
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] [data-testid="stMetricLabel"],
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] * {
        color: #53647d !important;
        opacity: 1 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"],
    div[data-testid="stMetric"] [data-testid="stMetricValue"] * {
        color: #102b4e !important;
        opacity: 1 !important;
        font-weight: 750 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricDelta"],
    div[data-testid="stMetric"] [data-testid="stMetricDelta"] * {
        color: #087f70 !important;
    }

    /* Inputs, tables and supporting text */
    [data-testid="stDataFrame"] { border: 1px solid #dce5f0; border-radius: 10px; }
    [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea {
        color: #172b4d !important;
    }
    .section-note { color: #53647d !important; font-size: .9rem; }
    div[data-testid="stAlert"] p { color: #263b57 !important; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# DATA
# ============================================================
@st.cache_data(show_spinner="Loading flight operations data...")
def load_data(file_bytes=None, file_name=None):
    if file_bytes is not None:
        from io import BytesIO
        data = pd.read_csv(BytesIO(file_bytes))
    else:
        candidates = [
            Path("india_flight_delay_model_input.csv"),
            Path("india_flight_delay_model_input(1).csv"),
        ]
        candidates += sorted(Path(".").glob("india_flight_delay_model_input*.csv"))
        csv_path = next((p for p in candidates if p.exists()), None)
        if csv_path is None:
            return None
        data = pd.read_csv(csv_path)

    data.columns = data.columns.str.strip()
    if "Flight_Date" in data.columns:
        data["Flight_Date"] = pd.to_datetime(data["Flight_Date"], errors="coerce")
    if {"Scheduled_Departure_Hour", "Scheduled_Departure_Minute"}.issubset(data.columns):
        data["Departure_Time_Minutes"] = (
            data["Scheduled_Departure_Hour"] * 60
            + data["Scheduled_Departure_Minute"]
        )
        data["Departure_Time"] = (
            data["Scheduled_Departure_Hour"].astype(str).str.zfill(2)
            + ":"
            + data["Scheduled_Departure_Minute"].astype(str).str.zfill(2)
        )
        bins = [-1, 359, 599, 719, 839, 959, 1079, 1199, 1319, 1439]
        labels = ["00–05", "06–09", "10–11", "12–13", "14–15",
                  "16–17", "18–19", "20–21", "22–23"]
        data["Time_Block"] = pd.cut(
            data["Departure_Time_Minutes"], bins=bins, labels=labels
        )
    day_names = {0:"Monday",1:"Tuesday",2:"Wednesday",3:"Thursday",
                 4:"Friday",5:"Saturday",6:"Sunday"}
    month_names = {1:"January",2:"February",3:"March",4:"April",
                   5:"May",6:"June",7:"July",8:"August",
                   9:"September",10:"October",11:"November",12:"December"}
    if "Day_of_Week" in data:
        data["Day_Name"] = data["Day_of_Week"].map(day_names)
    if "Month" in data:
        data["Month_Name"] = data["Month"].map(month_names)
    if {"Origin_Airport", "Destination_Airport"}.issubset(data.columns):
        data["Route"] = data["Origin_Airport"].astype(str) + " → " + data["Destination_Airport"].astype(str)
    return data

uploaded = st.sidebar.file_uploader("Upload flight CSV (optional)", type=["csv"])
df = load_data(uploaded.getvalue(), uploaded.name) if uploaded else load_data()

if df is None:
    st.error("Dataset not found. Place `india_flight_delay_model_input.csv` in the same GitHub repository as `app.py`, or upload it using the sidebar.")
    st.stop()

required = {"Delay_Target", "Departure_Delay"}
missing_required = required - set(df.columns)
if missing_required:
    st.error(f"Required columns missing from dataset: {', '.join(sorted(missing_required))}")
    st.stop()

# ============================================================
# SIDEBAR FILTERS
# ============================================================
st.sidebar.markdown("## ✈️ Flight Intelligence")
st.sidebar.caption("Explore patterns across airlines, airports, routes and operations.")
st.sidebar.divider()

def options_for(col):
    return sorted(df[col].dropna().astype(str).unique().tolist()) if col in df.columns else []

filtered = df.copy()
if "Flight_Date" in filtered.columns and filtered["Flight_Date"].notna().any():
    min_date = filtered["Flight_Date"].min().date()
    max_date = filtered["Flight_Date"].max().date()
    date_value = st.sidebar.date_input("Flight date range", value=(min_date, max_date),
                                       min_value=min_date, max_value=max_date)
    if isinstance(date_value, tuple) and len(date_value) == 2:
        start_date, end_date = date_value
        filtered = filtered[
            filtered["Flight_Date"].between(pd.Timestamp(start_date), pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1))
        ]

filter_specs = [
    ("Airline", "Airline"),
    ("Origin airport", "Origin_Airport"),
    ("Destination airport", "Destination_Airport"),
    ("Weather", "Weather"),
]
for label, col in filter_specs:
    if col in filtered.columns:
        choices = options_for(col)
        selected = st.sidebar.multiselect(label, choices, default=[])
        if selected:
            filtered = filtered[filtered[col].astype(str).isin(selected)]

if "Delay_Target" in filtered.columns:
    delay_filter = st.sidebar.selectbox(
        "Delay status", ["All flights", "Delayed only", "Not delayed only"]
    )
    if delay_filter == "Delayed only":
        filtered = filtered[filtered["Delay_Target"] == 1]
    elif delay_filter == "Not delayed only":
        filtered = filtered[filtered["Delay_Target"] == 0]

st.sidebar.divider()
st.sidebar.caption(f"Showing **{len(filtered):,}** of **{len(df):,}** flights")
if st.sidebar.button("Reset all filters", use_container_width=True):
    st.rerun()

if filtered.empty:
    st.warning("No flights match the selected filters. Change or reset your filters.")
    st.stop()

# ============================================================
# HELPERS
# ============================================================
def delay_rate(series):
    return series.mean() * 100

def add_chart_note(text):
    st.markdown(f'<p class="section-note">{text}</p>', unsafe_allow_html=True)

def metric_row(data):
    total = len(data)
    delayed = int(data["Delay_Target"].sum())
    rate = delay_rate(data["Delay_Target"])
    avg_delay = data["Departure_Delay"].mean()
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Total flights", f"{total:,}")
    c2.metric("Delayed flights", f"{delayed:,}")
    c3.metric("Delay rate", f"{rate:.1f}%")
    c4.metric("Average departure delay", f"{avg_delay:.1f} min")

def bar_delay(data, category, title, top_n=20):
    stats = (data.groupby(category, dropna=False)
             .agg(Flights=("Delay_Target","size"),
                  Delay_Rate=("Delay_Target","mean"),
                  Avg_Delay=("Departure_Delay","mean"))
             .reset_index())
    stats["Delay_Rate"] *= 100
    stats = stats.sort_values("Delay_Rate", ascending=False).head(top_n)
    fig = px.bar(stats.sort_values("Delay_Rate"), x="Delay_Rate", y=category,
                 orientation="h", color="Delay_Rate",
                 color_continuous_scale="Tealgrn",
                 hover_data={"Flights":":,", "Avg_Delay":":.1f", "Delay_Rate":":.1f"},
                 title=title, labels={"Delay_Rate":"Delayed flights (%)", category:""})
    fig.update_layout(height=max(380, 28*len(stats)), coloraxis_showscale=False,
                      margin=dict(l=10,r=10,t=55,b=10))
    st.plotly_chart(fig, use_container_width=True)

def grouped_stats(data, col):
    return (data.groupby(col, dropna=False)
            .agg(Flights=("Delay_Target","size"),
                 Delay_Rate=("Delay_Target","mean"),
                 Avg_Delay=("Departure_Delay","mean"))
            .reset_index()
            .assign(Delay_Rate=lambda x:x["Delay_Rate"]*100))

# ============================================================
# HEADER + NAV
# ============================================================
st.markdown("""
<div class="hero">
  <h1>✈️ Flight Operations & Delay Intelligence</h1>
  <p>Interactive business intelligence dashboard · Indian aviation operations · Exploratory analysis</p>
</div>
""", unsafe_allow_html=True)

pages = [
    "Executive Overview", "Airline Intelligence", "Airport Intelligence",
    "Route Analysis", "Time & Calendar", "Weather Intelligence",
    "Operational Risk", "Correlation Studio", "Dataset Explorer"
]
page = st.sidebar.radio("DASHBOARD PAGES", pages, index=0)

# ============================================================
# 1. EXECUTIVE OVERVIEW
# ============================================================
if page == "Executive Overview":
    st.header("Executive Overview")
    metric_row(filtered)
    st.divider()
    left, right = st.columns([1,1])
    with left:
        counts = filtered["Delay_Target"].value_counts().reindex([0,1], fill_value=0)
        pie = px.pie(values=counts.values, names=["Not delayed","Delayed"],
                     hole=.62, title="Flight delay distribution",
                     color_discrete_sequence=["#35a6a0","#ef8354"])
        pie.update_traces(textinfo="percent+label")
        st.plotly_chart(pie, use_container_width=True)
    with right:
        delay_hist = px.histogram(filtered, x="Departure_Delay", nbins=35,
                                  color_discrete_sequence=["#176b87"],
                                  title="Departure delay distribution (minutes)")
        delay_hist.update_layout(xaxis_title="Departure delay (minutes)", yaxis_title="Flights")
        st.plotly_chart(delay_hist, use_container_width=True)

    st.subheader("Monthly flight activity and delay rate")
    if "Flight_Date" in filtered.columns:
        monthly = filtered.dropna(subset=["Flight_Date"]).groupby(
            filtered.dropna(subset=["Flight_Date"])["Flight_Date"].dt.to_period("M")
        ).agg(Flights=("Delay_Target","size"), Delay_Rate=("Delay_Target","mean")).reset_index()
        monthly["Flight_Date"] = monthly["Flight_Date"].astype(str)
        monthly["Delay_Rate"] *= 100
        fig = go.Figure()
        fig.add_trace(go.Bar(x=monthly["Flight_Date"], y=monthly["Flights"], name="Flights", opacity=.55))
        fig.add_trace(go.Scatter(x=monthly["Flight_Date"], y=monthly["Delay_Rate"],
                                 name="Delay rate (%)", yaxis="y2", mode="lines+markers"))
        fig.update_layout(title="Monthly flight volume vs delay rate",
                          yaxis=dict(title="Flights"),
                          yaxis2=dict(title="Delay rate (%)", overlaying="y", side="right"),
                          legend=dict(orientation="h", y=1.12), height=430)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Quick insights")
    a,b,c = st.columns(3)
    if "Airline" in filtered.columns:
        airline = grouped_stats(filtered, "Airline").sort_values("Delay_Rate", ascending=False)
        a.metric("Highest airline delay rate", airline.iloc[0]["Airline"],
                 f'{airline.iloc[0]["Delay_Rate"]:.1f}%')
    if "Weather" in filtered.columns:
        weather = grouped_stats(filtered, "Weather").sort_values("Delay_Rate", ascending=False)
        b.metric("Highest weather-category rate", str(weather.iloc[0]["Weather"]),
                 f'{weather.iloc[0]["Delay_Rate"]:.1f}%')
    if "Origin_Airport" in filtered.columns:
        airport = grouped_stats(filtered, "Origin_Airport").sort_values("Delay_Rate", ascending=False)
        c.metric("Highest origin rate", airport.iloc[0]["Origin_Airport"],
                 f'{airport.iloc[0]["Delay_Rate"]:.1f}%')

# ============================================================
# 2. AIRLINE INTELLIGENCE
# ============================================================
elif page == "Airline Intelligence":
    st.header("Airline Intelligence")
    if "Airline" not in filtered:
        st.info("Airline column not available.")
    else:
        stats = grouped_stats(filtered, "Airline").sort_values("Delay_Rate", ascending=False)
        left,right = st.columns([1.35,1])
        with left:
            fig = px.bar(stats.sort_values("Delay_Rate"), x="Delay_Rate", y="Airline",
                         orientation="h", color="Delay_Rate",
                         color_continuous_scale="Tealgrn",
                         hover_data={"Flights":":,", "Avg_Delay":":.1f"},
                         title="Delay rate by airline")
            fig.update_layout(coloraxis_showscale=False, height=430, xaxis_title="Delay rate (%)")
            st.plotly_chart(fig, use_container_width=True)
        with right:
            fig = px.scatter(stats, x="Flights", y="Delay_Rate", size="Avg_Delay",
                             color="Airline", hover_name="Airline",
                             title="Airline volume vs delay rate",
                             labels={"Flights":"Flight count","Delay_Rate":"Delay rate (%)"})
            fig.update_layout(height=430, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        st.subheader("Airline performance table")
        st.dataframe(stats.rename(columns={"Delay_Rate":"Delay rate (%)","Avg_Delay":"Average delay (min)"}),
                     use_container_width=True, hide_index=True)

# ============================================================
# 3. AIRPORT INTELLIGENCE
# ============================================================
elif page == "Airport Intelligence":
    st.header("Airport Intelligence")
    airport_type = st.radio("Airport view", ["Origin airports", "Destination airports"], horizontal=True)
    col = "Origin_Airport" if airport_type.startswith("Origin") else "Destination_Airport"
    if col in filtered:
        top_n = st.slider("Number of airports to display", 5, 30, 15)
        bar_delay(filtered, col, f"Highest delay rates · {airport_type.lower()}", top_n)
        stats = grouped_stats(filtered, col).sort_values("Flights", ascending=False).head(top_n)
        fig = px.scatter(stats, x="Flights", y="Delay_Rate", size="Avg_Delay",
                         color="Delay_Rate", hover_name=col,
                         color_continuous_scale="Tealgrn",
                         title="Airport traffic volume vs delay rate",
                         labels={"Flights":"Flight count","Delay_Rate":"Delay rate (%)"})
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(stats.rename(columns={col:"Airport","Delay_Rate":"Delay rate (%)",
                                           "Avg_Delay":"Average delay (min)"}),
                     use_container_width=True, hide_index=True)
    else:
        st.info(f"{col} column not available.")

# ============================================================
# 4. ROUTE ANALYSIS
# ============================================================
elif page == "Route Analysis":
    st.header("Route Analysis")
    if "Route" in filtered:
        routes = (filtered.groupby(["Origin_Airport","Destination_Airport","Route"])
                  .agg(Flights=("Delay_Target","size"),
                       Delay_Rate=("Delay_Target","mean"),
                       Avg_Delay=("Departure_Delay","mean")).reset_index())
        routes["Delay_Rate"] *= 100
        minimum = st.slider("Minimum flights per route", 1, 500, 50, 10)
        top_n = st.slider("Routes to display", 5, 30, 15)
        stable = routes[routes["Flights"] >= minimum]
        if stable.empty:
            st.warning("No routes meet this minimum flight count. Lower the threshold.")
        else:
            l,r = st.columns(2)
            with l:
                top_volume = stable.nlargest(top_n, "Flights").sort_values("Flights")
                fig = px.bar(top_volume, x="Flights", y="Route", orientation="h",
                             title="Busiest routes", color="Flights", color_continuous_scale="Blues")
                fig.update_layout(height=500, coloraxis_showscale=False)
                st.plotly_chart(fig, use_container_width=True)
            with r:
                top_delay = stable.nlargest(top_n, "Delay_Rate").sort_values("Delay_Rate")
                fig = px.bar(top_delay, x="Delay_Rate", y="Route", orientation="h",
                             title="Highest delay-rate routes", color="Delay_Rate",
                             color_continuous_scale="Tealgrn")
                fig.update_layout(height=500, coloraxis_showscale=False, xaxis_title="Delay rate (%)")
                st.plotly_chart(fig, use_container_width=True)
            st.dataframe(stable.sort_values("Flights", ascending=False).head(100),
                         use_container_width=True, hide_index=True)
    else:
        st.info("Origin_Airport and Destination_Airport columns are required.")

# ============================================================
# 5. TIME & CALENDAR
# ============================================================
elif page == "Time & Calendar":
    st.header("Time & Calendar Patterns")
    if "Scheduled_Departure_Hour" in filtered:
        hourly = (filtered.groupby("Scheduled_Departure_Hour")
                  .agg(Flights=("Delay_Target","size"), Delay_Rate=("Delay_Target","mean"),
                       Avg_Delay=("Departure_Delay","mean")).reset_index())
        hourly["Delay_Rate"] *= 100
        fig = go.Figure()
        fig.add_trace(go.Bar(x=hourly["Scheduled_Departure_Hour"], y=hourly["Flights"], name="Flights", opacity=.5))
        fig.add_trace(go.Scatter(x=hourly["Scheduled_Departure_Hour"], y=hourly["Delay_Rate"],
                                 name="Delay rate (%)", yaxis="y2", mode="lines+markers"))
        fig.update_layout(title="Hourly flight volume and delay rate", xaxis_title="Scheduled departure hour",
                          yaxis=dict(title="Flights"), yaxis2=dict(title="Delay rate (%)", overlaying="y", side="right"),
                          height=420)
        st.plotly_chart(fig, use_container_width=True)
    l,r = st.columns(2)
    if "Day_Name" in filtered:
        day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        day = grouped_stats(filtered, "Day_Name")
        day["Day_Name"] = pd.Categorical(day["Day_Name"], categories=day_order, ordered=True)
        day = day.sort_values("Day_Name")
        with l:
            fig = px.bar(day, x="Day_Name", y="Delay_Rate", color="Delay_Rate",
                         color_continuous_scale="Tealgrn", title="Delay rate by day of week")
            fig.update_layout(coloraxis_showscale=False, xaxis_title="", yaxis_title="Delay rate (%)")
            st.plotly_chart(fig, use_container_width=True)
    if "Month_Name" in filtered:
        month_order = ["January","February","March","April","May","June","July","August","September","October","November","December"]
        month = grouped_stats(filtered, "Month_Name")
        month["Month_Name"] = pd.Categorical(month["Month_Name"], categories=month_order, ordered=True)
        month = month.sort_values("Month_Name")
        with r:
            fig = px.line(month, x="Month_Name", y="Delay_Rate", markers=True,
                          title="Delay rate by month", hover_data=["Flights","Avg_Delay"])
            fig.update_traces(line_width=3)
            fig.update_layout(xaxis_title="", yaxis_title="Delay rate (%)")
            st.plotly_chart(fig, use_container_width=True)
    if "Peak_Hour" in filtered:
        peak = grouped_stats(filtered.assign(Peak_Period=filtered["Peak_Hour"].map({0:"Non-peak",1:"Peak"})), "Peak_Period")
        st.subheader("Peak vs non-peak comparison")
        st.dataframe(peak.rename(columns={"Delay_Rate":"Delay rate (%)","Avg_Delay":"Average delay (min)"}),
                     use_container_width=True, hide_index=True)

# ============================================================
# 6. WEATHER INTELLIGENCE
# ============================================================
elif page == "Weather Intelligence":
    st.header("Weather Intelligence")
    if "Weather" in filtered:
        weather = grouped_stats(filtered, "Weather").sort_values("Delay_Rate", ascending=False)
        l,r = st.columns(2)
        with l:
            fig = px.bar(weather, x="Weather", y="Delay_Rate", color="Delay_Rate",
                         color_continuous_scale="Tealgrn", title="Delay rate by weather condition")
            fig.update_layout(coloraxis_showscale=False, xaxis_title="", yaxis_title="Delay rate (%)")
            st.plotly_chart(fig, use_container_width=True)
        with r:
            fig = px.bar(weather, x="Weather", y="Flights", color="Flights",
                         color_continuous_scale="Blues", title="Flight volume by weather")
            fig.update_layout(coloraxis_showscale=False, xaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
    weather_numeric = [c for c in ["Temperature_C","Humidity_pct","Wind_Speed_kmh",
                                   "Visibility_km","Rainfall_mm","Cloud_Cover_pct"] if c in filtered]
    if weather_numeric:
        selected = st.selectbox("Explore a weather variable", weather_numeric)
        fig = px.box(filtered, x="Delay_Target", y=selected, color="Delay_Target",
                     points=False, title=f"{selected} distribution by delay status",
                     labels={"Delay_Target":"Delay status"})
        fig.update_layout(xaxis=dict(tickmode="array",tickvals=[0,1],ticktext=["Not delayed","Delayed"]))
        st.plotly_chart(fig, use_container_width=True)
        if len(weather_numeric) >= 2:
            corr = filtered[weather_numeric + ["Delay_Target"]].corr(numeric_only=True)["Delay_Target"].drop("Delay_Target").sort_values()
            fig = px.bar(x=corr.values, y=corr.index, orientation="h",
                         title="Weather variable correlation with delay target",
                         labels={"x":"Pearson correlation","y":"Weather variable"},
                         color=corr.values, color_continuous_scale="RdBu")
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 7. OPERATIONAL RISK
# ============================================================
elif page == "Operational Risk":
    st.header("Operational Risk Intelligence")
    risk_cols = [c for c in ["Origin_Congestion_Index","Turnaround_Risk_Index",
                             "Previous_Flight_Delay_Minutes"] if c in filtered]
    if risk_cols:
        selected = st.selectbox("Select operational risk indicator", risk_cols)
        sample = filtered.sample(min(12000, len(filtered)), random_state=42)
        fig = px.scatter(sample, x=selected, y="Departure_Delay", color="Delay_Target",
                         opacity=.55, title=f"{selected} vs departure delay",
                         labels={"Departure_Delay":"Departure delay (minutes)","Delay_Target":"Delayed flag"},
                         color_discrete_sequence=["#35a6a0","#ef8354"])
        st.plotly_chart(fig, use_container_width=True)
        # Quantile bands allow comparison without assuming a causal relationship.
        try:
            risk_data = filtered.copy()
            risk_data["Risk band"] = pd.qcut(risk_data[selected], q=4, duplicates="drop")
            risk_stats = grouped_stats(risk_data, "Risk band")
            fig = px.bar(risk_stats, x="Risk band", y="Delay_Rate", color="Delay_Rate",
                         color_continuous_scale="Tealgrn",
                         title=f"Delay rate across {selected} quartiles",
                         labels={"Delay_Rate":"Delay rate (%)"})
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.info("Not enough variation in this variable to form quartiles.")
    else:
        st.info("No operational risk columns were found.")

    if {"Origin_Congestion_Index","Turnaround_Risk_Index","Previous_Flight_Delay_Minutes"}.issubset(filtered.columns):
        st.subheader("Combined operational risk profile")
        risk = filtered.copy()
        risk["High congestion"] = risk["Origin_Congestion_Index"] >= risk["Origin_Congestion_Index"].quantile(.75)
        risk["High turnaround risk"] = risk["Turnaround_Risk_Index"] >= risk["Turnaround_Risk_Index"].quantile(.75)
        risk["Previous delay above median"] = risk["Previous_Flight_Delay_Minutes"] > risk["Previous_Flight_Delay_Minutes"].median()
        risk["Risk factor count"] = risk[["High congestion","High turnaround risk","Previous delay above median"]].sum(axis=1)
        risk_stats = grouped_stats(risk, "Risk factor count")
        fig = px.bar(risk_stats, x="Risk factor count", y="Delay_Rate", color="Delay_Rate",
                     color_continuous_scale="Tealgrn", title="Delay rate by number of elevated risk factors")
        fig.update_layout(coloraxis_showscale=False, yaxis_title="Delay rate (%)")
        st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 8. CORRELATION STUDIO
# ============================================================
elif page == "Correlation Studio":
    st.header("Correlation Studio")
    numeric = filtered.select_dtypes(include=np.number)
    numeric = numeric.loc[:, numeric.nunique() > 1]
    if numeric.shape[1] >= 2:
        selected_cols = st.multiselect("Choose numeric variables", numeric.columns.tolist(),
                                       default=numeric.columns.tolist()[:min(12,len(numeric.columns))])
        if len(selected_cols) >= 2:
            corr = numeric[selected_cols].corr()
            fig = px.imshow(corr, text_auto=".2f", aspect="auto",
                            color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                            title="Pearson correlation heatmap")
            fig.update_layout(height=max(500, 35*len(selected_cols)))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Select at least two variables.")
        if "Delay_Target" in numeric:
            st.subheader("Variables most correlated with delay target")
            target_corr = numeric.corr()["Delay_Target"].drop("Delay_Target")
            target_corr = target_corr.reindex(target_corr.abs().sort_values(ascending=False).index)
            fig = px.bar(x=target_corr.values, y=target_corr.index, orientation="h",
                         color=target_corr.values, color_continuous_scale="RdBu_r",
                         title="Correlation with Delay_Target")
            fig.update_layout(coloraxis_showscale=False, xaxis_title="Pearson correlation")
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Correlation describes association, not causation. Departure_Delay may be closely tied to the delay label, so interpret it carefully.")
    else:
        st.info("At least two varying numeric columns are required.")

# ============================================================
# 9. DATASET EXPLORER
# ============================================================
elif page == "Dataset Explorer":
    st.header("Dataset Explorer")
    tab1,tab2,tab3 = st.tabs(["Flight records","Data quality","Statistics"])
    with tab1:
        search = st.text_input("Search across visible text values")
        view = filtered
        if search:
            mask = view.astype(str).apply(lambda s:s.str.contains(search, case=False, na=False)).any(axis=1)
            view = view[mask]
        st.caption(f"{len(view):,} matching records")
        st.dataframe(view.head(500), use_container_width=True, hide_index=True)
        st.download_button("⬇️ Download filtered data as CSV",
                           data=view.to_csv(index=False).encode("utf-8"),
                           file_name="filtered_flight_delay_data.csv",
                           mime="text/csv")
    with tab2:
        quality = pd.DataFrame({
            "Column": filtered.columns,
            "Data type": filtered.dtypes.astype(str).values,
            "Missing values": filtered.isna().sum().values,
            "Missing (%)": (filtered.isna().mean().values*100).round(2),
            "Unique values": filtered.nunique().values,
        })
        st.dataframe(quality, use_container_width=True, hide_index=True)
        st.metric("Total missing values in filtered data", f"{filtered.isna().sum().sum():,}")
    with tab3:
        st.dataframe(filtered.describe(include="all").T, use_container_width=True)

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption("Airport Operations & Flight Delay Intelligence · Exploratory analysis of the supplied dataset")
st.caption("Note: This dashboard reports patterns in the dataset. Observed relationships should not be interpreted as proof of causation or as live flight-status information.")
