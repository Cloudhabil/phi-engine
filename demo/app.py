"""
phi_engine.demo.app — Streamlit demo application.

4 tabs: D-Space Explorer, Calibration Tool, Constants Database, API Playground.
Pattern from sovereign-pio/docs/usecases/demos/demo_9_smb_cybersecurity.py.

Run: streamlit run phi_engine/demo/app.py
"""
from __future__ import annotations

import csv
import io
import uuid

import streamlit as st

from ..adapters.calibration import CalibrationAdapter
from ..adapters.photosynthesis import PhotosynthesisAdapter
from ..adapters.sensor_fusion import SensorFusionAdapter
from ..constants_db import ConstantsDB
from ..core import PHI, Theta
from ..photosynthesis_constants import MOF_MATERIALS, NATURAL_STEPS
from ..engine import PhiEngine
from .database import DemoDatabase
from .payment import (
    FREE_ANALYSES_PER_DAY,
    FREE_TRANSFORMS_PER_DAY,
    PaymentPlan,
    check_rate_limit,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Phi-Engine Demo",
    page_icon="PHI",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "email" not in st.session_state:
    st.session_state.email = ""
if "engine" not in st.session_state:
    engine = PhiEngine()
    engine.register_adapter("calibration", CalibrationAdapter())
    engine.register_adapter("sensor_fusion", SensorFusionAdapter())
    engine.register_adapter("photosynthesis", PhotosynthesisAdapter())
    st.session_state.engine = engine

engine: PhiEngine = st.session_state.engine
db = DemoDatabase()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("Phi-Engine")
st.sidebar.markdown(
    "**Zero-parameter algebraic prediction engine**\n\n"
    f"PHI = {PHI:.16f}\n\n"
    "Version 1.618.0"
)

email = st.sidebar.text_input("Email (for usage tracking)", value=st.session_state.email)
if email != st.session_state.email:
    st.session_state.email = email
    db.create_session(st.session_state.session_id, email=email)

st.sidebar.markdown("---")
st.sidebar.markdown("**Pricing**")
for plan in [PaymentPlan.FREE, PaymentPlan.PRO_MONTHLY, PaymentPlan.ENTERPRISE_MONTHLY]:
    st.sidebar.markdown(f"- {plan.label}: **{plan.price_usd}**/mo")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "D-Space Explorer",
    "Calibration Tool",
    "Constants Database",
    "API Playground",
    "Carbon Lab",
])

# ============================== TAB 1 ====================================
with tab1:
    st.header("D-Space Explorer")
    st.markdown("Transform values to D-space and verify energy conservation.")

    input_mode = st.radio("Input mode", ["Manual", "CSV Upload"], horizontal=True)

    values: list[float] = []
    if input_mode == "Manual":
        raw = st.text_input(
            "Enter comma-separated values (> 0)",
            value="0.5, 1.0, 2.0, 3.14",
        )
        try:
            values = [float(v.strip()) for v in raw.split(",") if v.strip()]
        except ValueError:
            st.error("Invalid input — enter numbers separated by commas")
    else:
        uploaded = st.file_uploader("Upload CSV (one column of values)", type=["csv"])
        if uploaded is not None:
            reader = csv.reader(io.StringIO(uploaded.getvalue().decode("utf-8")))
            for row in reader:
                for cell in row:
                    try:
                        values.append(float(cell.strip()))
                    except ValueError:
                        pass

    if values and st.button("Transform", key="transform_btn"):
        rl = check_rate_limit(st.session_state.email, "transform")
        if not rl["allowed"]:
            st.warning(
                f"Free tier limit reached ({FREE_TRANSFORMS_PER_DAY}/day). "
                "Upgrade to Pro for unlimited transforms."
            )
        else:
            d_vals = engine.transform([v for v in values if v > 0])
            energies = engine.energy([v for v in values if v > 0])
            checks = [engine.check(v) for v in values if v > 0]

            col1, col2, col3 = st.columns(3)
            col1.metric("Values", len(values))
            col2.metric("D-space mean", f"{sum(d_vals)/len(d_vals):.4f}" if d_vals else "—")
            col3.metric("Energy (all)", f"{energies[0]:.6f}" if energies else "—")

            st.subheader("Results")
            table_data = []
            for i, v in enumerate([v for v in values if v > 0]):
                table_data.append({
                    "Value": v,
                    "D(x)": round(d_vals[i], 8),
                    "Theta(x)": round(Theta(v), 8),
                    "Energy(x)": round(energies[i], 8),
                    "Closure": checks[i]["d_space_closure"]["valid"],
                    "E=2pi": checks[i]["energy_conservation"]["valid"],
                })
            st.dataframe(table_data, use_container_width=True)

            db.log_transform(st.session_state.session_id, "d_space", len(values))
            if st.session_state.email:
                db.increment_usage(st.session_state.email, transforms=1)

# ============================== TAB 2 ====================================
with tab2:
    st.header("Calibration Tool")
    st.markdown("Upload instrument readings for D-space calibration.")

    reference = st.number_input("Reference value", value=1.0, min_value=0.001, format="%.6f")
    instrument = st.text_input("Instrument ID", value="sensor-001")

    readings_raw = st.text_area(
        "Readings (comma-separated or one per line)",
        value="0.98, 1.01, 0.995, 1.003, 0.997",
    )
    readings: list[float] = []
    for part in readings_raw.replace("\n", ",").split(","):
        try:
            readings.append(float(part.strip()))
        except ValueError:
            pass

    if readings and st.button("Calibrate", key="calibrate_btn"):
        rl = check_rate_limit(st.session_state.email, "analysis")
        if not rl["allowed"]:
            st.warning(
                f"Free tier limit reached ({FREE_ANALYSES_PER_DAY}/day). "
                "Upgrade to Pro."
            )
        else:
            result = engine.run("calibration", {
                "readings": readings,
                "reference": reference,
                "instrument": instrument,
            })

            score = result.get("consistency_score", 0)
            st.metric("Consistency Score", f"{score:.6f}")

            drift = result.get("drift", {})
            if drift:
                col1, col2 = st.columns(2)
                col1.metric("Drift Direction", drift.get("direction", "—"))
                col2.metric("Drift Magnitude", f"{drift.get('magnitude', 0):.6f}")

            corrected = result.get("corrected_values", [])
            if corrected:
                st.subheader("Corrected Values")
                table = []
                for i, (raw_v, corr_v) in enumerate(zip(readings, corrected)):
                    table.append({
                        "Reading": i + 1,
                        "Raw": round(raw_v, 6),
                        "Corrected": round(corr_v, 6),
                        "Delta": round(corr_v - raw_v, 8),
                    })
                st.dataframe(table, use_container_width=True)

            recs = result.get("recommendations", [])
            if recs:
                st.subheader("Recommendations")
                for r in recs:
                    st.info(r)

            db.log_analysis(
                st.session_state.session_id,
                "calibration",
                {"readings": readings, "reference": reference},
                score,
                recs,
            )
            if st.session_state.email:
                db.increment_usage(st.session_state.email, analyses=1)

# ============================== TAB 3 ====================================
with tab3:
    st.header("Constants Database")
    st.markdown("Browse 50+ physics constants predicted from PHI.")

    cdb = ConstantsDB()

    col1, col2 = st.columns(2)
    sector = col1.selectbox("Sector", ["all"] + cdb.sectors)
    query = col2.text_input("Search", "")

    s = None if sector == "all" else sector
    q = query if query else None
    entries = cdb.search(sector=s, query=q)

    st.markdown(f"**{len(entries)} constants found**")

    if entries:
        table = []
        for e in entries:
            table.append({
                "Name": e["name"],
                "Predicted": e["value"],
                "Experimental": e["experimental"],
                "Unit": e["unit"],
                "Deviation (ppm)": e["deviation_ppm"],
                "Formula": e["formula"],
            })
        st.dataframe(table, use_container_width=True)

    st.subheader("Scorecard")
    sc = cdb.scorecard()
    cols = st.columns(4)
    cols[0].metric("Total Constants", sc["total_constants"])
    cols[1].metric("Non-exact", sc["non_exact"])
    cols[2].metric("Best ppm", sc["min_ppm"])
    cols[3].metric("Mean ppm", sc["mean_ppm"])

# ============================== TAB 4 ====================================
with tab4:
    st.header("API Playground")
    st.markdown("Test phi-engine endpoints interactively.")

    endpoint = st.selectbox("Endpoint", [
        "transform", "validate", "decompose", "ladder", "scale_map",
    ])

    if endpoint == "transform":
        raw = st.text_input("Values (comma-separated)", "0.5, 1.0, 2.0")
        if st.button("Run", key="api_transform"):
            vals = [float(v.strip()) for v in raw.split(",")]
            result = engine.transform(vals)
            st.json({"original": vals, "d_space": result})

    elif endpoint == "validate":
        coeffs_raw = st.text_input("Coefficients", "-1, 1, 2, 0.5")
        expected = st.number_input("Expected sum", value=2.5)
        if st.button("Run", key="api_validate"):
            coeffs = [float(c.strip()) for c in coeffs_raw.split(",")]
            result = engine.validate(coeffs, expected)
            st.json(result)

    elif endpoint == "decompose":
        dim = st.number_input("Dimension", value=45, min_value=1, step=1)
        if st.button("Run", key="api_decompose"):
            result = engine.decompose(int(dim))
            st.json(result)

    elif endpoint == "ladder":
        n_max = st.slider("Max n", 1, 248, 78)
        if st.button("Run", key="api_ladder"):
            ladder = engine.ladder.full_ladder(n_max)
            # Show only labelled entries for clarity
            labelled = [e for e in ladder if "label" in e]
            st.json(labelled if labelled else ladder[:20])

    elif endpoint == "scale_map":
        n = st.number_input("n", value=78, min_value=0, step=1)
        if st.button("Run", key="api_scale"):
            result = engine.scale_map(int(n))
            st.json(result)

# ============================== TAB 5 ====================================
with tab5:
    st.header("Carbon Lab")
    st.markdown(
        "Artificial photosynthesis, MOF CO2 filters, "
        "and quantum coherence — all analysed in D-space."
    )

    section = st.radio(
        "Analysis mode",
        ["Photosynthesis Cascade", "MOF Filter Design", "Full System"],
        horizontal=True,
        key="carbon_section",
    )

    # ---- Section A: Photosynthesis Cascade ----
    if section == "Photosynthesis Cascade":
        st.subheader("Photosynthesis Cascade")
        st.markdown("Adjust step efficiencies (natural plant defaults shown).")

        step_etas: list[dict] = []
        cols = st.columns(2)
        for i, step in enumerate(NATURAL_STEPS):
            col = cols[i % 2]
            eta = col.slider(
                step["name"],
                min_value=0.01, max_value=1.0,
                value=step["efficiency"],
                step=0.01,
                key=f"cascade_{i}",
            )
            step_etas.append({"name": step["name"], "efficiency": eta,
                              "catalyst": step.get("catalyst", "")})

        c1, c2, c3 = st.columns(3)
        temp_c = c1.number_input("Temperature (C)", value=25.0, key="cas_temp")
        co2_ppm = c2.number_input("CO2 (ppm)", value=415.0, key="cas_co2")
        target = c3.slider(
            "Target efficiency", 0.01, 0.50, 0.20, 0.01, key="cas_target",
        )

        if st.button("Analyze Cascade", key="cascade_btn"):
            result = engine.run("photosynthesis", {
                "mode": "cascade",
                "steps": step_etas,
                "temperature_c": temp_c,
                "co2_ppm": co2_ppm,
                "target_efficiency": target,
            })
            eff = result.get("overall_efficiency", {})
            if isinstance(eff, dict):
                st.metric("Overall efficiency",
                          f"{eff.get('value', 0):.4%}")
            else:
                st.metric("Overall efficiency", f"{eff:.4%}")
            st.metric("Consistency", f"{result.get('consistency_score', 0):.6f}")

            steps_out = result.get("step_analysis", [])
            if steps_out:
                st.subheader("Step Analysis")
                st.dataframe([
                    {"Step": s["name"],
                     "Efficiency": round(s["efficiency"], 3),
                     "D-value": round(s["d_value"], 4),
                     "Contribution %": round(s.get("contribution_pct", 0), 1)}
                    for s in steps_out
                ], use_container_width=True)

            bn = result.get("bottleneck", {})
            if bn:
                st.warning(
                    f"Bottleneck: **{bn.get('step_name', '?')}** "
                    f"(D={bn.get('d_value', 0):.3f}, "
                    f"{bn.get('contribution_pct', 0):.1f}% of total D)"
                )

            for rec in result.get("recommendations", []):
                st.info(rec)

    # ---- Section B: MOF Filter Design ----
    elif section == "MOF Filter Design":
        st.subheader("MOF Filter Design")
        all_names = list(MOF_MATERIALS.keys())
        selected = st.multiselect(
            "Select MOF candidates", all_names, default=all_names,
            key="mof_select",
        )
        c1, c2 = st.columns(2)
        abundant_only = c1.checkbox("Abundant elements only", value=True,
                                    key="mof_abundant")
        self_healing = c2.checkbox("Self-healing required", value=False,
                                   key="mof_healing")
        max_cost = st.slider("Max relative cost", 0.5, 5.0, 3.0, 0.1,
                             key="mof_cost")

        if st.button("Score MOFs", key="mof_btn"):
            result = engine.run("photosynthesis", {
                "mode": "mof_filter",
                "candidates": selected,
                "constraints": {
                    "abundant_only": abundant_only,
                    "self_healing": self_healing,
                    "max_cost_relative": max_cost,
                },
            })
            ranking = result.get("mof_ranking", [])
            if ranking:
                st.dataframe([
                    {"MOF": m["name"],
                     "Score": round(m["score"], 1),
                     "Capacity (mmol/g)": m["co2_capacity_mmol_g"],
                     "Selectivity": m["co2_n2_selectivity"],
                     "Pore-PHI gap (nm)": round(m["pore_phi_match"], 4),
                     "Abundant": m.get("abundant", False),
                     "Self-healing": m.get("self_healing", False)}
                    for m in ranking
                ], use_container_width=True)
            else:
                st.warning("No MOFs match the constraints.")
            for rec in result.get("recommendations", []):
                st.info(rec)

    # ---- Section C: Full System ----
    elif section == "Full System":
        st.subheader("Full System Model")
        st.markdown("Cascade + MOF + quantum coherence combined.")

        mof_choice = st.selectbox(
            "MOF for CO2 capture", list(MOF_MATERIALS.keys()),
            index=list(MOF_MATERIALS.keys()).index("Fe-BTC"),
            key="full_mof",
        )
        c1, c2 = st.columns(2)
        coupling = c1.slider(
            "Coherence coupling", 0.1, 2.0, 0.8, 0.05, key="full_coupling",
        )
        irradiance = c2.number_input(
            "Solar irradiance (W/m2)", value=1000.0, key="full_irr",
        )
        c3, c4 = st.columns(2)
        temp_c = c3.number_input("Temperature (C)", value=25.0, key="full_temp")
        co2_ppm = c4.number_input("CO2 (ppm)", value=415.0, key="full_co2")

        if st.button("Model System", key="full_btn"):
            result = engine.run("photosynthesis", {
                "mode": "full_system",
                "steps": NATURAL_STEPS,
                "mof": mof_choice,
                "coherence_coupling": coupling,
                "temperature_c": temp_c,
                "co2_ppm": co2_ppm,
                "solar_irradiance_w_m2": irradiance,
                "unit_area_m2": 1.0,
            })
            c1, c2, c3 = st.columns(3)
            c1.metric("System efficiency",
                      f"{result.get('overall_efficiency', 0):.4%}")
            c2.metric("CO2 captured",
                      f"{result.get('co2_per_m2_day_kg', 0):.4f} kg/m2/day")
            coh = result.get("coherence", {})
            c3.metric("Coherence factor",
                      f"{coh.get('factor', 0):.4f}")

            subs = result.get("subsystems", [])
            if subs:
                st.subheader("Subsystem Breakdown")
                st.dataframe([
                    {"Subsystem": s["name"],
                     "Efficiency": round(s["efficiency"], 4),
                     "D-value": round(s["d_value"], 4)}
                    for s in subs
                ], use_container_width=True)

            bn = result.get("bottleneck", {})
            if bn:
                st.warning(
                    f"System bottleneck: **{bn.get('subsystem', '?')}** "
                    f"(D={bn.get('d_value', 0):.3f})"
                )
            for rec in result.get("recommendations", []):
                st.info(rec)
