# 🛡️ AML Rule Design Agent

Interactive Streamlit workspace for designing, calibrating, and documenting anti-money laundering (AML) detection rules. The agent combines posture-aware defaults, configurable indicators, synthetic population testing, and ready-to-implement logic blueprints.

## Key capabilities

- Compose multi-indicator rules covering value thresholds, geography, customer risk tiers, PEP status, behavioural spikes, adverse media, and more.
- Apply posture-specific recommendations per business segment and adjust controls with instant feedback.
- Run the rule against a synthetic transaction population to estimate alert rates, precision, and channel mix.
- Export a SQL-style blueprint plus implementation checklist and written rationale for governance artefacts.

## Getting started

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Launch the Streamlit app:

   ```bash
   streamlit run streamlit_app.py
   ```

3. Provide programme context in the sidebar, tune indicators, and generate a blueprint to review simulated impact and documentation.
