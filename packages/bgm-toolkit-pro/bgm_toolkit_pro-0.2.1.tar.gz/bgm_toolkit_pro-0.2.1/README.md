# BGM Toolkit – Pro v0.2
Config-driven Bourdieu-inspired gravity model for HE access.

## Quick start
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH="$PWD"
python run_bgm.py
# or: bgm-run --config configs/run.yaml

## Inputs
- students.csv (E,C,S)
- universities.csv (E,C,S, optional name)

## Outputs (in outputs/)
- H_matrix.csv, H_within_student_shares.csv, top_choices.csv, elasticities.json
- report_excel.xlsx, report_html.html
