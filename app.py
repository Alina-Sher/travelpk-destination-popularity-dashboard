"""Destination Popularity Dashboard for Travel.pk.

Uses a bundled SYNTHETIC demonstration dataset (data/destination_popularity.csv).
Nothing here represents actual Travel.pk bookings, customers or revenue.
"""
from html import escape
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA_PATH = Path(__file__).parent / "data" / "destination_popularity.csv"
REQUIRED_COLUMNS = [
    "destination", "province_or_region", "season", "traveler_type",
    "popularity_score", "estimated_trips", "data_type",
]
SEASONS = ["Spring", "Summer", "Autumn", "Winter"]
TRAVELERS = ["Solo", "Couple", "Family", "Group"]
ALL_SEASONS = "All Seasons"
ALL_TRAVELERS = "All Travelers"
SEASON_OPTIONS = [ALL_SEASONS] + SEASONS
TRAVELER_OPTIONS = [ALL_TRAVELERS] + TRAVELERS

NAVY, TEAL, SKY, INK, MUTED = "#0B2A4A", "#1B7F8C", "#6FA8DC", "#14213D", "#5B6B7F"

SYNTHETIC_NOTICE = (
    "Illustrative synthetic data. The figures below are demonstration values, "
    "not actual Travel.pk bookings, customers or market statistics."
)


# ---------------------------------------------------------------- data layer
@st.cache_data(show_spinner=False)
def load_data(path: str = str(DATA_PATH)) -> pd.DataFrame:
    """Load and validate the bundled CSV. Raises ValueError if it is malformed."""
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {', '.join(missing)}")
    if df.empty:
        raise ValueError("Dataset contains no rows.")
    if df[REQUIRED_COLUMNS].isna().any().any():
        raise ValueError("Dataset contains missing values.")
    if (df["popularity_score"] < 0).any() or (df["estimated_trips"] < 0).any():
        raise ValueError("popularity_score and estimated_trips must be non-negative.")
    if not df["season"].isin(SEASONS).all():
        raise ValueError(f"season must be one of {SEASONS}.")
    if not df["traveler_type"].isin(TRAVELERS).all():
        raise ValueError(f"traveler_type must be one of {TRAVELERS}.")
    return df


def apply_filters(df: pd.DataFrame, season: str, traveler: str) -> pd.DataFrame:
    out = df
    if season != ALL_SEASONS:
        out = out[out["season"] == season]
    if traveler != ALL_TRAVELERS:
        out = out[out["traveler_type"] == traveler]
    return out


def rank_destinations(df: pd.DataFrame) -> pd.DataFrame:
    """One row per destination, ranked by mean popularity score (desc).

    Ties are broken by total estimated trips, then by name, so ordering is stable.
    """
    if df.empty:
        return pd.DataFrame(
            columns=["destination", "province_or_region", "popularity_score", "estimated_trips"]
        )
    ranked = (
        df.groupby("destination", as_index=False)
        .agg(
            province_or_region=("province_or_region", "first"),
            popularity_score=("popularity_score", "mean"),
            estimated_trips=("estimated_trips", "sum"),
        )
        .sort_values(
            ["popularity_score", "estimated_trips", "destination"],
            ascending=[False, False, True],
        )
        .reset_index(drop=True)
    )
    ranked["popularity_score"] = ranked["popularity_score"].round(1)
    return ranked


def compute_kpis(df: pd.DataFrame) -> dict:
    ranked = rank_destinations(df)
    return {
        "destinations": int(df["destination"].nunique()),
        "top_destination": ranked.iloc[0]["destination"] if not ranked.empty else "No data",
        "total_trips": int(df["estimated_trips"].sum()),
        "avg_score": float(df["popularity_score"].mean()) if not df.empty else 0.0,
    }


def build_insights(df: pd.DataFrame, season: str, traveler: str) -> list[str]:
    """Up to three insights, each computed directly from the filtered rows."""
    ranked = rank_destinations(df)
    if ranked.empty:
        return []
    top = ranked.iloc[0]
    by_trips = ranked.sort_values("estimated_trips", ascending=False).iloc[0]
    insights = []

    if by_trips["destination"] == top["destination"]:
        insights.append(
            f"**{top['destination']}** ranks first with an average popularity score of "
            f"{top['popularity_score']:.1f} and also has the largest estimated trip count "
            f"({int(top['estimated_trips']):,})."
        )
    else:
        insights.append(
            f"**{top['destination']}** ranks first with an average popularity score of "
            f"{top['popularity_score']:.1f}."
        )
        insights.append(
            f"**{by_trips['destination']}** has the largest estimated trip count "
            f"({int(by_trips['estimated_trips']):,})."
        )

    total = df["estimated_trips"].sum()
    if season == ALL_SEASONS and total > 0:
        s = df.groupby("season")["estimated_trips"].sum().sort_values(ascending=False)
        insights.append(
            f"{s.index[0]} is the busiest season, with {s.iloc[0] / total:.0%} of estimated trips "
            f"for the selected travelers."
        )
    elif traveler == ALL_TRAVELERS and total > 0:
        t = df.groupby("traveler_type")["estimated_trips"].sum().sort_values(ascending=False)
        insights.append(
            f"{t.index[0]} travelers account for the largest share of estimated trips "
            f"({t.iloc[0] / total:.0%}) in {season}."
        )
    elif len(ranked) >= 2:
        gap = top["popularity_score"] - ranked.iloc[1]["popularity_score"]
        insights.append(
            f"For {season} {traveler.lower()} travel, {top['destination']} leads "
            f"{ranked.iloc[1]['destination']} by {gap:.1f} score points."
        )
    return insights[:3]


# ------------------------------------------------------------------ UI layer
def stretch_kwargs() -> dict:
    """Streamlit >=1.49 uses width='stretch'; older versions use use_container_width."""
    try:
        major, minor = (int(p) for p in st.__version__.split(".")[:2])
    except (ValueError, AttributeError):
        return {"use_container_width": True}
    return {"width": "stretch"} if (major, minor) >= (1, 49) else {"use_container_width": True}


CSS = f"""
<style>
.block-container {{ padding-top: 2rem; max-width: 1200px; }}
[data-testid="stSidebar"] {{ background: #F2F6FA; }}
.brand {{ color: {TEAL}; font-weight: 700; font-size: 0.95rem; letter-spacing: 0.02em; margin: 0; }}
.page-title {{ color: {NAVY}; font-size: 2.1rem; font-weight: 700; line-height: 1.15; margin: 0.1rem 0 0.4rem; }}
.page-sub {{ color: {MUTED}; font-size: 1.02rem; max-width: 46rem; margin: 0 0 0.9rem; }}
.notice {{ background: #FFF8E6; border: 1px solid #F0D99A; color: #5C4A10; border-radius: 8px;
           padding: 0.6rem 0.9rem; font-size: 0.9rem; margin-bottom: 1.2rem; }}
.kpi {{ background: #fff; border: 1px solid #DCE4EE; border-left: 4px solid {NAVY};
        border-radius: 8px; padding: 0.85rem 1rem; height: 100%; margin-bottom: 0.5rem; }}
.kpi-label {{ color: {MUTED}; font-size: 0.85rem; margin: 0; }}
.kpi-value {{ color: {NAVY}; font-size: 1.6rem; font-weight: 700; margin: 0.1rem 0 0; line-height: 1.2; overflow-wrap: anywhere; }}
h2, h3 {{ color: {NAVY}; }}
</style>
"""


def kpi_card(label: str, value: str) -> str:
    return (
        f'<div class="kpi"><p class="kpi-label">{escape(label)}</p>'
        f'<p class="kpi-value">{escape(value)}</p></div>'
    )


def reset_filters() -> None:
    st.session_state["season_filter"] = ALL_SEASONS
    st.session_state["traveler_filter"] = ALL_TRAVELERS


def ranking_chart(ranked: pd.DataFrame, season: str, traveler: str) -> go.Figure:
    top = ranked.head(10)
    colors = [TEAL] + [NAVY] * (len(top) - 1)
    fig = go.Figure(
        go.Bar(
            x=top["popularity_score"],
            y=top["destination"],
            orientation="h",
            marker_color=colors,
            customdata=top[["province_or_region", "estimated_trips"]].values,
            hovertemplate=(
                "<b>%{y}</b><br>Region: %{customdata[0]}<br>"
                "Popularity score: %{x:.1f}<br>"
                "Estimated trips: %{customdata[1]:,}<extra></extra>"
            ),
        )
    )
    fig.update_layout(
        title=f"Top destinations by popularity score ({season}, {traveler})",
        xaxis_title="Popularity score (illustrative, 0-100)",
        yaxis_title="Destination",
        yaxis=dict(autorange="reversed"),  # first row (highest) drawn at the top
        height=max(320, 46 * len(top) + 130),
        margin=dict(l=10, r=10, t=60, b=40),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color=INK),
    )
    fig.update_xaxes(gridcolor="#E6ECF2", rangemode="tozero")
    return fig


def render_assumptions() -> None:
    with st.expander("Data Sources & Assumptions", expanded=False):
        st.markdown(
            """
1. **Data source.** A locally bundled **synthetic demonstration dataset**
   (`data/destination_popularity.csv`, 192 rows: 12 destinations × 4 seasons × 4 traveler types).
   It was not scraped, purchased, or collected from actual customers, and every row is tagged
   `data_type = synthetic_illustrative`.
2. **Why synthetic.** Verified Travel.pk booking or search data was not available for this
   project. The dataset only demonstrates how the dashboard works.
3. **`popularity_score`.** A simple, unofficial 0–100 index:
   `round(100 × estimated_trips ÷ highest estimated_trips in the dataset, 1)`.
   It is **not** an official Travel.pk metric.
4. **`estimated_trips`.** An assumed, illustrative trip count for one destination–season–traveler
   segment. It is not a real booking count.
5. **Seasons and traveler types.** Assigned by the author from general assumptions about
   Pakistan's climate and travel patterns (e.g., northern valleys peak in Summer, Murree and
   Gwadar are stronger in Winter, cities draw more Family trips). Every destination has a row
   for each of the 16 season × traveler combinations. Seasons: Spring, Summer, Autumn, Winter.
6. **Ranking.** Destinations are ranked by their **mean popularity score** across the rows that
   match the selected filters (highest first). Ties are broken by total estimated trips. Because
   every destination has the same set of segments, this matches ranking by total estimated trips.
7. **Limitations.** Values are assumptions, not market statistics. They ignore price, capacity,
   events, year-to-year change and booking channel. Use verified booking or search data
   before making any real business decision.
"""
        )


def main() -> None:
    st.set_page_config(page_title="Destination Popularity Dashboard | Travel.pk",
                       page_icon="🧭", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)

    try:
        df = load_data()
    except FileNotFoundError:
        st.error("Dataset not found. Expected file: data/destination_popularity.csv")
        st.stop()
    except ValueError as exc:
        st.error(f"The dataset could not be used: {exc}")
        st.stop()

    # Sidebar filters (session_state keys let the reset button restore defaults)
    st.session_state.setdefault("season_filter", ALL_SEASONS)
    st.session_state.setdefault("traveler_filter", ALL_TRAVELERS)
    with st.sidebar:
        st.markdown("### Filters")
        season = st.selectbox("Season", SEASON_OPTIONS, key="season_filter")
        traveler = st.selectbox("Traveler type", TRAVELER_OPTIONS, key="traveler_filter")
        st.button("Reset Filters", on_click=reset_filters)
        st.caption(SYNTHETIC_NOTICE)

    # Header
    st.markdown('<p class="brand">Travel.pk</p>', unsafe_allow_html=True)
    st.markdown('<h1 class="page-title">Destination Popularity Dashboard</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="page-sub">Explore which destinations across Pakistan are most popular, '
        "and how that changes by season and traveler type.</p>",
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="notice"><b>Data notice:</b> {SYNTHETIC_NOTICE}</div>',
                unsafe_allow_html=True)

    filtered = apply_filters(df, season, traveler)
    if filtered.empty:
        st.info("No destinations match these filters. Choose different options or press "
                "**Reset Filters** in the sidebar.")
        render_assumptions()
        st.stop()

    # KPIs
    k = compute_kpis(filtered)
    cols = st.columns(4)
    cards = [
        ("Destinations in results", f"{k['destinations']:,}"),
        ("Top-ranked destination", k["top_destination"]),
        ("Total estimated trips", f"{k['total_trips']:,}"),
        ("Average popularity score", f"{k['avg_score']:.1f}"),
    ]
    for col, (label, value) in zip(cols, cards):
        col.markdown(kpi_card(label, value), unsafe_allow_html=True)

    # Ranking chart
    ranked = rank_destinations(filtered)
    st.subheader("Top destinations")
    st.plotly_chart(ranking_chart(ranked, season, traveler), **stretch_kwargs())

    # Insights
    st.subheader("Key insights")
    for text in build_insights(filtered, season, traveler):
        st.markdown(f"- {text}")
    st.caption("Insights come from the illustrative synthetic dataset and are not real booking findings.")

    # Details table
    st.subheader("Destination details")
    table = (
        filtered.sort_values(["popularity_score", "estimated_trips", "destination"],
                             ascending=[False, False, True])
        [["destination", "province_or_region", "season", "traveler_type",
          "popularity_score", "estimated_trips"]]
        .rename(columns={
            "destination": "Destination", "province_or_region": "Region",
            "season": "Season", "traveler_type": "Traveler type",
            "popularity_score": "Popularity score", "estimated_trips": "Estimated trips",
        })
    )
    st.caption(f"{len(table)} rows, sorted by popularity score (highest first).")
    st.dataframe(
        table, hide_index=True,
        column_config={
            "Popularity score": st.column_config.ProgressColumn(
                "Popularity score", min_value=0, max_value=100, format="%.1f"),
            "Estimated trips": st.column_config.NumberColumn("Estimated trips", format="%d"),
        },
        **stretch_kwargs(),
    )

    render_assumptions()
    st.caption("Travel.pk Destination Popularity Dashboard · synthetic demonstration data")


if __name__ == "__main__":
    main()
