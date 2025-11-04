import streamlit as st
import pandas as pd
import numpy as np
from textwrap import dedent

st.set_page_config(
    page_title="AML Rule Design Agent",
    page_icon="🛡️",
    layout="wide",
)

RISK_LEVELS = ["Low", "Medium", "High", "Very High"]
RISK_LEVEL_MAP = {level: idx for idx, level in enumerate(RISK_LEVELS, start=1)}

COUNTRY_DISTRIBUTION = {
    "United States": 22,
    "United Kingdom": 12,
    "Canada": 8,
    "Germany": 8,
    "France": 5,
    "European Union": 6,
    "United Arab Emirates": 5,
    "Singapore": 5,
    "Hong Kong": 4,
    "Turkey": 4,
    "Russia": 4,
    "Belarus": 2,
    "China": 4,
    "Brazil": 3,
    "Mexico": 3,
    "Nigeria": 2,
    "India": 4,
    "South Africa": 2,
    "Iran": 1,
    "Syria": 1,
    "North Korea": 0.5,
    "Myanmar": 0.5,
    "Philippines": 2,
}

COUNTRY_OPTIONS = list(COUNTRY_DISTRIBUTION.keys())

DEFAULT_HIGH_RISK_COUNTRIES = [
    "Russia",
    "Belarus",
    "Iran",
    "North Korea",
    "Syria",
    "Myanmar",
    "Turkey",
]

CHANNELS = [
    "Wire",
    "ACH / SEPA",
    "International Remittance",
    "Crypto Transfer",
    "Cash Deposit",
    "Card Purchase",
]

BASE_RECOMMENDATIONS = {
    "Conservative": {
        "amount": 10000,
        "velocity": 3,
        "behaviour_multiplier": 1.8,
        "account_age": 18,
        "require_pep": True,
        "adverse_media": True,
        "min_customer_risk_level": "High",
    },
    "Balanced": {
        "amount": 20000,
        "velocity": 5,
        "behaviour_multiplier": 2.4,
        "account_age": 12,
        "require_pep": False,
        "adverse_media": True,
        "min_customer_risk_level": "High",
    },
    "Aggressive": {
        "amount": 35000,
        "velocity": 7,
        "behaviour_multiplier": 3.2,
        "account_age": 9,
        "require_pep": False,
        "adverse_media": False,
        "min_customer_risk_level": "Very High",
    },
}

BUSINESS_ADJUSTMENTS = {
    "Retail Banking": {
        "amount": 15000,
        "account_age": 12,
    },
    "Corporate Banking": {
        "amount": 50000,
        "velocity": 3,
        "behaviour_multiplier": 2.6,
        "min_customer_risk_level": "Very High",
    },
    "Fintech / Neobank": {
        "amount": 12000,
        "behaviour_multiplier": 2.0,
        "account_age": 9,
    },
    "Crypto Exchange": {
        "velocity": 8,
        "behaviour_multiplier": 2.9,
        "min_customer_risk_level": "High",
        "high_risk_countries": [
            "Russia",
            "Belarus",
            "Philippines",
            "Turkey",
            "United Arab Emirates",
            "Hong Kong",
        ],
        "adverse_media": True,
    },
    "Money Services / Remittance": {
        "amount": 9000,
        "velocity": 8,
        "behaviour_multiplier": 2.2,
        "high_risk_countries": [
            "Mexico",
            "Brazil",
            "Philippines",
            "Nigeria",
            "Turkey",
            "Russia",
        ],
    },
}


def format_currency(value: float) -> str:
    return f"${value:,.0f}"


def get_recommended_thresholds(risk_posture: str, business_unit: str) -> dict:
    base = BASE_RECOMMENDATIONS[risk_posture].copy()
    adjustments = BUSINESS_ADJUSTMENTS.get(business_unit, {})

    for key, value in adjustments.items():
        if isinstance(value, list):
            base[key] = list(dict.fromkeys(value))
        elif isinstance(value, (int, float)):
            existing = base.get(key, value)
            base[key] = round((existing + value) / 2, 1 if isinstance(value, float) else 0)
        else:
            base[key] = value

    base.setdefault("high_risk_countries", DEFAULT_HIGH_RISK_COUNTRIES)
    base["high_risk_countries"] = list(dict.fromkeys(base["high_risk_countries"]))
    base["amount"] = int(base.get("amount", 20000))
    base["velocity"] = int(base.get("velocity", 5))
    base["behaviour_multiplier"] = float(base.get("behaviour_multiplier", 2.5))
    base["account_age"] = int(base.get("account_age", 12))
    base["require_pep"] = bool(base.get("require_pep", risk_posture == "Conservative"))
    base["adverse_media"] = bool(base.get("adverse_media", risk_posture != "Aggressive"))
    base["min_customer_risk_level"] = base.get(
        "min_customer_risk_level",
        "High" if risk_posture != "Aggressive" else "Very High",
    )
    return base


def update_state_with_defaults(defaults: dict) -> None:
    st.session_state["amount_enabled"] = True
    st.session_state["velocity_enabled"] = True
    st.session_state["geo_enabled"] = True
    st.session_state["risk_enabled"] = True
    st.session_state["pep_enabled"] = defaults["require_pep"]
    st.session_state["behavior_enabled"] = True
    st.session_state["account_age_enabled"] = True
    st.session_state["adverse_media_enabled"] = defaults["adverse_media"]
    st.session_state["channel_focus_enabled"] = True
    st.session_state["amount_threshold"] = int(defaults["amount"])
    st.session_state["velocity_threshold"] = int(defaults["velocity"])
    st.session_state["behaviour_multiplier"] = float(defaults["behaviour_multiplier"])
    st.session_state["account_age_threshold"] = int(defaults["account_age"])
    st.session_state["min_customer_risk_level"] = defaults["min_customer_risk_level"]
    st.session_state["high_risk_country_selection"] = list(defaults["high_risk_countries"])


def ensure_state_defaults(defaults: dict) -> None:
    fallback_state = {
        "amount_enabled": True,
        "velocity_enabled": True,
        "geo_enabled": True,
        "risk_enabled": True,
        "pep_enabled": defaults["require_pep"],
        "behavior_enabled": True,
        "account_age_enabled": True,
        "adverse_media_enabled": defaults["adverse_media"],
        "channel_focus_enabled": True,
        "amount_threshold": int(defaults["amount"]),
        "velocity_threshold": int(defaults["velocity"]),
        "behaviour_multiplier": float(defaults["behaviour_multiplier"]),
        "account_age_threshold": int(defaults["account_age"]),
        "min_customer_risk_level": defaults["min_customer_risk_level"],
        "high_risk_country_selection": list(defaults["high_risk_countries"]),
    }

    for key, value in fallback_state.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_data(show_spinner=False)
def load_sample_transactions(seed: int = 7, rows: int = 3500) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    country_names = list(COUNTRY_DISTRIBUTION.keys())
    country_weights = np.array(list(COUNTRY_DISTRIBUTION.values()), dtype=float)
    country_probs = country_weights / country_weights.sum()

    channel_probs = [0.26, 0.18, 0.16, 0.12, 0.18, 0.10]

    df = pd.DataFrame(
        {
            "transaction_id": np.arange(1, rows + 1),
            "customer_id": rng.integers(100000, 999999, size=rows),
            "transaction_amount_usd": np.round(rng.lognormal(3.1, 0.9, size=rows) * 120, 2),
            "txn_count_24h": rng.integers(1, 12, size=rows),
            "counterparty_country": rng.choice(country_names, size=rows, p=country_probs),
            "originating_country": rng.choice(country_names, size=rows, p=country_probs),
            "customer_risk_rating": rng.choice(
                RISK_LEVELS,
                size=rows,
                p=[0.45, 0.33, 0.17, 0.05],
            ),
            "is_pep": rng.choice([True, False], size=rows, p=[0.035, 0.965]),
            "channel": rng.choice(CHANNELS, size=rows, p=channel_probs),
            "behavior_multiplier": np.round(rng.uniform(0.6, 5.5, size=rows), 2),
            "account_age_months": rng.integers(1, 180, size=rows),
            "has_adverse_media": rng.choice([True, False], size=rows, p=[0.09, 0.91]),
        }
    )

    baseline_amount = np.clip(df["transaction_amount_usd"] / np.maximum(df["behavior_multiplier"], 0.1), 200, None)
    df["avg_amount_90d_usd"] = np.round(baseline_amount, 2)

    return df


def apply_rule(df: pd.DataFrame, controls: dict) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)

    if controls["amount"]["enabled"]:
        mask &= df["transaction_amount_usd"] >= controls["amount"]["threshold"]

    if controls["velocity"]["enabled"]:
        mask &= df["txn_count_24h"] >= controls["velocity"]["threshold"]

    if controls["geography"]["enabled"] and controls["geography"]["countries"]:
        mask &= df["counterparty_country"].isin(controls["geography"]["countries"])

    if controls["risk_rating"]["enabled"]:
        min_level = RISK_LEVEL_MAP.get(controls["risk_rating"]["min_level"], 1)
        mask &= df["customer_risk_rating"].map(RISK_LEVEL_MAP) >= min_level

    if controls["pep"]["enabled"]:
        mask &= df["is_pep"]

    if controls["behavior"]["enabled"]:
        mask &= df["behavior_multiplier"] >= controls["behavior"]["multiplier"]

    if controls["account_age"]["enabled"]:
        mask &= df["account_age_months"] <= controls["account_age"]["max_months"]

    if controls["adverse_media"]["enabled"]:
        mask &= df["has_adverse_media"]

    if controls["channel"]["enabled"] and controls["channel"]["channels"]:
        mask &= df["channel"].isin(controls["channel"]["channels"])

    return df.loc[mask].copy()


def generate_rule_summary(config: dict) -> list[str]:
    controls = config["controls"]
    lines: list[str] = []

    if controls["amount"]["enabled"]:
        lines.append(
            f"Flag single transactions at or above {format_currency(controls['amount']['threshold'])}."
        )
    if controls["velocity"]["enabled"]:
        lines.append(
            f"Require at least {controls['velocity']['threshold']} transactions within 24 hours."
        )
    if controls["geography"]["enabled"] and controls["geography"]["countries"]:
        countries = ", ".join(controls["geography"]["countries"][:6])
        if len(controls["geography"]["countries"]) > 6:
            countries += ", …"
        lines.append(f"Counterparty within monitored jurisdictions: {countries}.")
    if controls["risk_rating"]["enabled"]:
        lines.append(
            f"Customer risk rating of {controls['risk_rating']['min_level']} or higher."
        )
    if controls["pep"]["enabled"]:
        lines.append("Customer flagged as politically exposed person (PEP).")
    if controls["behavior"]["enabled"]:
        lines.append(
            f"Transactional spike ≥ {controls['behavior']['multiplier']:.1f}x the 90-day average."
        )
    if controls["account_age"]["enabled"]:
        lines.append(
            f"Account age ≤ {controls['account_age']['max_months']} months at time of transaction."
        )
    if controls["adverse_media"]["enabled"]:
        lines.append("Customer associated with adverse media hits.")
    if controls["channel"]["enabled"] and controls["channel"]["channels"]:
        channels = ", ".join(controls["channel"]["channels"])
        lines.append(f"Applies to {channels} activity only.")

    return lines


def build_sql_blueprint(config: dict) -> str:
    controls = config["controls"]
    clauses: list[str] = []

    if controls["amount"]["enabled"]:
        clauses.append(
            f"t.transaction_amount_usd >= {int(controls['amount']['threshold'])}"
        )
    if controls["velocity"]["enabled"]:
        clauses.append(
            f"t.txn_count_24h >= {int(controls['velocity']['threshold'])}"
        )
    if controls["geography"]["enabled"] and controls["geography"]["countries"]:
        countries = ", ".join(
            f"'{country}'" for country in controls["geography"]["countries"]
        )
        clauses.append(f"t.counterparty_country IN ({countries})")
    if controls["risk_rating"]["enabled"]:
        allowed_levels = RISK_LEVELS[RISK_LEVELS.index(controls["risk_rating"]["min_level"]):]
        levels = ", ".join(f"'{lvl}'" for lvl in allowed_levels)
        clauses.append(f"c.customer_risk_rating IN ({levels})")
    if controls["pep"]["enabled"]:
        clauses.append("c.is_pep = TRUE")
    if controls["behavior"]["enabled"]:
        clauses.append(
            f"(t.transaction_amount_usd / NULLIF(c.avg_amount_90d_usd, 0)) >= {controls['behavior']['multiplier']:.1f}"
        )
    if controls["account_age"]["enabled"]:
        clauses.append(
            f"c.account_age_months <= {int(controls['account_age']['max_months'])}"
        )
    if controls["adverse_media"]["enabled"]:
        clauses.append("c.has_adverse_media = TRUE")
    if controls["channel"]["enabled"] and controls["channel"]["channels"]:
        channels = ", ".join(f"'{channel}'" for channel in controls["channel"]["channels"])
        clauses.append(f"t.channel IN ({channels})")

    where_clause = "\n    AND ".join(["1=1"] + clauses) if clauses else "1=1"

    return dedent(
        f"""
        SELECT
            t.transaction_id,
            t.customer_id,
            t.transaction_amount_usd,
            t.channel,
            t.counterparty_country,
            t.processed_at_ts
        FROM transaction_fact t
        JOIN customer_dim c USING (customer_id)
        WHERE {where_clause};
        """
    ).strip()


def summarise_metrics(population: pd.DataFrame, alerts: pd.DataFrame) -> dict:
    total = len(population)
    alert_count = len(alerts)
    alert_rate = round((alert_count / total) * 100, 2) if total else 0.0
    median_amount = float(alerts["transaction_amount_usd"].median()) if alert_count else 0.0
    pep_share = (
        float(alerts["is_pep"].mean()) * 100 if alert_count else 0.0
    )
    high_risk_share = (
        float(
            (
                alerts["customer_risk_rating"].map(RISK_LEVEL_MAP)
                >= RISK_LEVEL_MAP["High"]
            ).mean()
        )
        * 100
        if alert_count
        else 0.0
    )

    return {
        "total": total,
        "alert_count": alert_count,
        "alert_rate": alert_rate,
        "median_amount": median_amount,
        "pep_share": round(pep_share, 1),
        "high_risk_share": round(high_risk_share, 1),
    }


def estimate_precision(controls: dict, risk_posture: str) -> float:
    base = {
        "Conservative": 0.18,
        "Balanced": 0.25,
        "Aggressive": 0.32,
    }[risk_posture]

    if controls["pep"]["enabled"]:
        base += 0.05
    if controls["adverse_media"]["enabled"]:
        base += 0.04
    if controls["geography"]["enabled"] and controls["geography"]["countries"]:
        if len(controls["geography"]["countries"]) <= 5:
            base += 0.03
        else:
            base += 0.01
    if controls["amount"]["enabled"]:
        threshold = controls["amount"]["threshold"]
        if threshold >= 40000:
            base += 0.05
        elif threshold <= 15000:
            base -= 0.03
    else:
        base -= 0.04

    if not controls["velocity"]["enabled"]:
        base -= 0.04

    if not controls["risk_rating"]["enabled"]:
        base -= 0.05

    if controls["behavior"]["enabled"]:
        base += 0.02

    return float(max(0.05, min(0.75, round(base, 2))))


def compute_rule_strength(controls: dict) -> int:
    weights = {
        "amount": 1.0,
        "velocity": 0.9,
        "geography": 0.9,
        "risk_rating": 0.8,
        "pep": 0.6,
        "behavior": 0.7,
        "account_age": 0.5,
        "adverse_media": 0.7,
        "channel": 0.4,
    }
    max_score = sum(weights.values())
    active_score = 0.0

    for control_name, control_value in controls.items():
        if control_name not in weights:
            continue
        enabled = (
            control_value["enabled"]
            if isinstance(control_value, dict)
            else bool(control_value)
        )
        if enabled:
            active_score += weights[control_name]

    return int(round((active_score / max_score) * 100))


def generate_rationale(context: dict, controls: dict, precision_estimate: float) -> str:
    high_risk_list = controls["geography"]["countries"]
    geo_text = (
        ", ".join(high_risk_list[:5]) + (", …" if len(high_risk_list) > 5 else "")
        if high_risk_list
        else "selected corridors"
    )
    posture_text = context["risk_posture"].lower()
    business = context["business_unit"].lower()
    channels = context["channels"] if context["channels"] else ["all monitored"]
    channel_text = ", ".join(channels)

    return dedent(
        f"""
        Calibrated for {business} operations operating under a {posture_text} detection posture.
        Focuses on {channel_text} flows interacting with {geo_text} counterparties.
        Expected precision of approximately {precision_estimate * 100:.0f}% based on indicator mix. Complement with manual review criteria for high-value customers to maintain proportionality.
        """
    ).strip()


def generate_implementation_notes(config: dict) -> list[str]:
    controls = config["controls"]
    notes = [
        "Validate source completeness for counterparty country and channel fields before production deployment.",
        "Align rule outputs with existing case management queues and ensure triage SLAs are defined.",
        "Back-test against historical SARs to baseline precision and tune thresholds accordingly.",
    ]

    if controls["behavior"]["enabled"]:
        notes.append(
            "Confirm availability of reliable rolling averages (90 day) prior to enabling behavioral spike criteria."
        )
    if controls["pep"]["enabled"]:
        notes.append(
            "Coordinate with KYC team to ensure PEP flag refresh cadence supports near-real-time screening."
        )
    if controls["adverse_media"]["enabled"]:
        notes.append(
            "Incorporate adverse media vendor confidence scores to suppress low-quality hits if needed."
        )

    return notes


def collect_configuration(context: dict) -> dict:
    controls = {
        "amount": {
            "enabled": st.session_state["amount_enabled"],
            "threshold": st.session_state["amount_threshold"],
        },
        "velocity": {
            "enabled": st.session_state["velocity_enabled"],
            "threshold": st.session_state["velocity_threshold"],
        },
        "geography": {
            "enabled": st.session_state["geo_enabled"],
            "countries": st.session_state["high_risk_country_selection"],
        },
        "risk_rating": {
            "enabled": st.session_state["risk_enabled"],
            "min_level": st.session_state["min_customer_risk_level"],
        },
        "pep": {
            "enabled": st.session_state["pep_enabled"],
        },
        "behavior": {
            "enabled": st.session_state["behavior_enabled"],
            "multiplier": st.session_state["behaviour_multiplier"],
        },
        "account_age": {
            "enabled": st.session_state["account_age_enabled"],
            "max_months": st.session_state["account_age_threshold"],
        },
        "adverse_media": {
            "enabled": st.session_state["adverse_media_enabled"],
        },
        "channel": {
            "enabled": st.session_state["channel_focus_enabled"],
            "channels": context["channels"],
        },
    }

    if not context["channels"]:
        controls["channel"]["enabled"] = False

    return {"context": context, "controls": controls}


st.title("🛡️ AML Rule Design Agent")
st.caption(
    "Assemble, test, and document anti-money laundering rules with synthetic telemetry and expert guidance."
)

business_options = list(BUSINESS_ADJUSTMENTS.keys())
business_options.insert(0, "Retail Banking") if "Retail Banking" not in business_options else None
if "Corporate Banking" not in business_options:
    business_options.append("Corporate Banking")

with st.sidebar:
    st.header("Program context")
    business_unit = st.selectbox(
        "Business segment",
        business_options,
        index=business_options.index("Retail Banking")
        if "Retail Banking" in business_options
        else 0,
    )
    risk_posture = st.radio(
        "Detection posture",
        ("Conservative", "Balanced", "Aggressive"),
        index=1,
        help="Conservative captures more alerts, Aggressive prioritises precision.",
    )
    jurisdictions = st.multiselect(
        "Jurisdictions monitored",
        COUNTRY_OPTIONS,
        default=["United States", "United Kingdom", "European Union" if "European Union" in COUNTRY_OPTIONS else "Germany"],
    )
    channel_focus = st.multiselect(
        "Channel coverage",
        CHANNELS,
        default=["Wire", "ACH / SEPA"],
    )
    context_notes = st.text_area(
        "Context notes",
        placeholder="Document regulatory obligations, customer footprint, or risk appetite insights…",
        height=120,
    )

    apply_recommended = st.button(
        "Apply recommended thresholds",
        use_container_width=True,
        help="Loads posture-specific defaults for the configuration widgets.",
    )

recommended = get_recommended_thresholds(risk_posture, business_unit)

if apply_recommended:
    update_state_with_defaults(recommended)

ensure_state_defaults(recommended)

config_context = {
    "business_unit": business_unit,
    "risk_posture": risk_posture,
    "jurisdictions": jurisdictions,
    "channels": channel_focus,
    "notes": context_notes,
}

st.markdown("---")
st.subheader("Rule indicators")
st.caption("Toggle and tune the data points that will shape the detection logic.")

col1, col2 = st.columns(2)

with col1:
    st.session_state["amount_enabled"] = st.checkbox(
        "High-value transaction",
        value=st.session_state["amount_enabled"],
        help="Minimum transaction amount to trip the rule.",
    )
    if st.session_state["amount_enabled"]:
        st.session_state["amount_threshold"] = st.number_input(
            "Minimum transaction amount (USD)",
            min_value=1000,
            max_value=250000,
            step=1000,
            value=int(st.session_state["amount_threshold"]),
        )

    st.session_state["velocity_enabled"] = st.checkbox(
        "Transaction burst (24h)",
        value=st.session_state["velocity_enabled"],
        help="Minimum count of transactions within a 24 hour window.",
    )
    if st.session_state["velocity_enabled"]:
        st.session_state["velocity_threshold"] = st.number_input(
            "Transactions in 24h",
            min_value=1,
            max_value=20,
            step=1,
            value=int(st.session_state["velocity_threshold"]),
        )

    st.session_state["geo_enabled"] = st.checkbox(
        "High-risk counterparty geography",
        value=st.session_state["geo_enabled"],
        help="Restrict to counterparties in selected jurisdictions.",
    )
    if st.session_state["geo_enabled"]:
        st.session_state["high_risk_country_selection"] = st.multiselect(
            "Counterparty jurisdictions",
            COUNTRY_OPTIONS,
            default=st.session_state["high_risk_country_selection"],
        )

    st.session_state["risk_enabled"] = st.checkbox(
        "Customer risk tier",
        value=st.session_state["risk_enabled"],
        help="Minimum internal risk-rating required for alerting.",
    )
    if st.session_state["risk_enabled"]:
        st.session_state["min_customer_risk_level"] = st.selectbox(
            "Minimum risk rating",
            RISK_LEVELS,
            index=RISK_LEVELS.index(st.session_state["min_customer_risk_level"]),
        )

with col2:
    st.session_state["pep_enabled"] = st.checkbox(
        "Require PEP flag",
        value=st.session_state["pep_enabled"],
        help="Limit to customers identified as politically exposed persons.",
    )

    st.session_state["behavior_enabled"] = st.checkbox(
        "Behavioural spike",
        value=st.session_state["behavior_enabled"],
        help="Compare current value to rolling 90-day average volume.",
    )
    if st.session_state["behavior_enabled"]:
        st.session_state["behaviour_multiplier"] = st.number_input(
            "Minimum spike multiple",
            min_value=1.0,
            max_value=10.0,
            step=0.1,
            value=float(st.session_state["behaviour_multiplier"]),
        )

    st.session_state["account_age_enabled"] = st.checkbox(
        "New-to-bank focus",
        value=st.session_state["account_age_enabled"],
        help="Target recently opened accounts (age in months).",
    )
    if st.session_state["account_age_enabled"]:
        st.session_state["account_age_threshold"] = st.number_input(
            "Account age max (months)",
            min_value=1,
            max_value=240,
            step=1,
            value=int(st.session_state["account_age_threshold"]),
        )

    st.session_state["adverse_media_enabled"] = st.checkbox(
        "Adverse media linkage",
        value=st.session_state["adverse_media_enabled"],
        help="Restrict to customers with negative media intelligence.",
    )

    st.session_state["channel_focus_enabled"] = st.checkbox(
        "Channel-specific filter",
        value=st.session_state["channel_focus_enabled"],
        help="Apply only to selected payment channels.",
    )

st.markdown("---")

generate_rule = st.button(
    "Generate rule blueprint",
    type="primary",
    use_container_width=True,
)

if generate_rule:
    if st.session_state["channel_focus_enabled"] and not channel_focus:
        st.warning("Select at least one channel or disable the channel-specific filter.")
    elif st.session_state["geo_enabled"] and not st.session_state["high_risk_country_selection"]:
        st.warning("Provide at least one counterparty jurisdiction when geography is enabled.")
    else:
        with st.spinner("Synthesizing rule, evaluating coverage, and drafting documentation…"):
            configuration = collect_configuration(config_context)
            synthetic_population = load_sample_transactions()
            alerts = apply_rule(synthetic_population, configuration["controls"])
            metrics = summarise_metrics(synthetic_population, alerts)
            summary_lines = generate_rule_summary(configuration)
            sql_blueprint = build_sql_blueprint(configuration)
            precision_estimate = estimate_precision(
                configuration["controls"], risk_posture
            )
            strength_score = compute_rule_strength(configuration["controls"])
            rationale = generate_rationale(
                configuration["context"], configuration["controls"], precision_estimate
            )
            implementation_notes = generate_implementation_notes(configuration)

        st.subheader("Rule narrative")
        if summary_lines:
            for line in summary_lines:
                st.write(f"- {line}")
        else:
            st.info("No indicators selected – adjust configuration to build a rule body.")

        st.subheader("Logic blueprint (SQL-style)")
        st.code(sql_blueprint, language="sql")

        kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
        kpi_col1.metric("Rule strength", f"{strength_score}%")
        kpi_col2.metric("Estimated precision", f"{precision_estimate * 100:.0f}%")
        kpi_col3.metric("Alert rate (synthetic)", f"{metrics['alert_rate']:.1f}%")

        st.subheader("Synthetic population impact")
        if metrics["alert_count"]:
            impact_cols = st.columns(3)
            impact_cols[0].metric("Alerts generated", metrics["alert_count"], delta=f"of {metrics['total']} sample txns")
            impact_cols[1].metric(
                "Median alert amount",
                format_currency(metrics["median_amount"]),
            )
            impact_cols[2].metric(
                "High-risk / PEP mix",
                f"{metrics['high_risk_share']:.0f}% high risk",
                delta=f"{metrics['pep_share']:.0f}% PEP",
            )

            display_cols = [
                "transaction_id",
                "customer_id",
                "transaction_amount_usd",
                "channel",
                "counterparty_country",
                "customer_risk_rating",
                "is_pep",
                "behavior_multiplier",
                "account_age_months",
                "has_adverse_media",
            ]

            st.dataframe(
                alerts[display_cols].head(25),
                use_container_width=True,
            )

            channel_counts = alerts["channel"].value_counts().rename_axis("channel").to_frame("alerts")
            st.bar_chart(channel_counts)
        else:
            st.info(
                "No synthetic transactions matched the current configuration. Reduce thresholds or relax filters to widen coverage."
            )

        st.subheader("Rationale & operating guidance")
        st.markdown(rationale)

        st.subheader("Implementation checklist")
        for note in implementation_notes:
            st.write(f"- {note}")

        if config_context["notes"]:
            st.markdown("**Program notes**")
            st.info(config_context["notes"])
