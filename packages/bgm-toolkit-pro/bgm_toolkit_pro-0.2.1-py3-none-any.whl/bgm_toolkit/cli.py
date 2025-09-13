import os
import argparse
import numpy as np
import pandas as pd
import statsmodels.api as sm

from .io import load_config, ensure_output_dir, validate_inputs, validate_config
from .preprocess import capital_volume
from .distance import pairwise_distance
from .report import write_excel_report, write_html_report

def _load_cfg(path_or_default):
    cfg_path = path_or_default or "configs/labour_demo.yaml"
    return load_config(cfg_path)

def _apply_overrides(cfg, args):
    dsec = cfg.setdefault("distance", {})
    if args.distance: dsec["metric"] = args.distance
    if args.weights: dsec["weights"] = [float(x) for x in str(args.weights).split(",") if x.strip()!='']
    if args.outdir: cfg.setdefault("output", {})["dir"] = args.outdir
    cfg.setdefault("output", {}).setdefault("dir", "./outputs")
    return cfg

def _load_capacity(cfg, names):
    cap_cfg = cfg.get("capacity", {}) or {}
    cap_csv = cap_cfg.get("uni_capacities_csv") or cap_cfg.get("job_capacities_csv")
    if not cap_csv or not os.path.exists(cap_csv):
        return None
    cap = pd.read_csv(cap_csv)
    if not {"name","capacity"}.issubset(set(cap.columns)):
        raise ValueError("capacity CSV must have columns: name, capacity")
    cap = cap.set_index("name").reindex(pd.Index(names, dtype=str))
    cap = cap.reset_index().rename(columns={"index":"name"})
    return cap

def main():
    parser = argparse.ArgumentParser(prog="bgm-run", description="Bourdieusian Gravity Model runner")
    parser.add_argument("--config", help="Path to YAML config (default: configs/labour_demo.yaml)")
    parser.add_argument("--distance", choices=["euclidean","weighted","mahalanobis","cosine","aitchison"], help="Override distance metric")
    parser.add_argument("--weights", help="Comma-separated weights for metric=weighted, e.g. 0.8,1,1.2")
    parser.add_argument("--outdir", help="Output directory")
    parser.add_argument("--students", help="Override students/workers CSV")
    parser.add_argument("--universities", help="Override universities/jobs CSV")
    args = parser.parse_args()

    cfg = _apply_overrides(_load_cfg(args.config), args)
    cfg = validate_config(cfg)
    outdir = ensure_output_dir(cfg.get("output",{}).get("dir","./outputs"))

    data = cfg.get("data", {})
    S_path = args.students or data.get("students_csv") or data.get("workers_csv")
    U_path = args.universities or data.get("universities_csv") or data.get("jobs_csv")

    S_df = pd.read_csv(S_path)
    U_df = pd.read_csv(U_path)
    capitals = tuple(data.get("capitals", ["E","C","S"]))
    S_df, U_df = validate_inputs(S_df, U_df, capitals=capitals)
    names = U_df["name"].astype(str).tolist() if "name" in U_df.columns else [f"U{j+1}" for j in range(len(U_df))]

    metric_cfg = cfg.get("distance", {})
    metric = metric_cfg.get("metric","euclidean")
    weights = metric_cfg.get("weights")
    eps = float(metric_cfg.get("eps", 1e-9))

    S_arr = S_df[list(capitals)].astype(float).to_numpy()
    U_arr = U_df[list(capitals)].astype(float).to_numpy()
    D = pairwise_distance(metric, S_arr, U_arr, weights=weights, eps=eps)

    Ci = capital_volume(S_df, capitals)
    Cj = capital_volume(U_df, capitals)
    H = np.outer(Ci, Cj) / np.maximum(D, eps)
    shares = H / H.sum(axis=1, keepdims=True)

    top_idx = shares.argmax(axis=1)
    top_share = shares[np.arange(len(top_idx)), top_idx]
    top_table = pd.DataFrame({
        "student_id": np.arange(1, len(top_idx)+1),
        "top_university_index_0based": top_idx,
        "top_university": [names[k] for k in top_idx],
        "top_share": top_share
    })

    I, J = H.shape
    logH  = np.log(H.reshape(I*J))
    logCi = np.log(np.repeat(Ci, J))
    logCj = np.log(np.tile(Cj, I))
    logD  = np.log(D.reshape(I*J))
    X = sm.add_constant(np.column_stack([logCi, logCj, logD]))
    ols = sm.OLS(logH, X).fit(cov_type="HC1")
    elasticities = {"b_Ci": float(ols.params[1]), "b_Cj": float(ols.params[2]), "b_D": float(ols.params[3])}

    # Expected demand per destination j
    exp_dem = pd.Series(shares.sum(axis=0), index=names, name="expected_demand")
    exp_dem_df = exp_dem.reset_index().rename(columns={"index":"name"})
    exp_dem_df.to_csv(os.path.join(outdir, "expected_demand.csv"), index=False)

    # Capacity utilization (if capacity CSV present)
    capacity_df = _load_capacity(cfg, names)
    if capacity_df is not None:
        merged = capacity_df.copy()
        merged["name"] = merged["name"].astype(str)
        merged = merged.set_index("name").join(exp_dem, how="left").reset_index()
        merged["expected_demand"] = merged["expected_demand"].fillna(0.0)
        merged["overfill"] = merged["expected_demand"] - merged["capacity"]
        merged["utilization_rate"] = np.where(merged["capacity"] > 0, merged["expected_demand"]/merged["capacity"], np.nan)
        merged.to_csv(os.path.join(outdir, "capacity_utilization.csv"), index=False)
    else:
        merged = None

    # Write core outputs
    pd.DataFrame(H, columns=names).to_csv(os.path.join(outdir, "H_matrix.csv"), index=False)
    pd.DataFrame(shares, columns=names).to_csv(os.path.join(outdir, "shares.csv"), index=False)
    top_table.to_csv(os.path.join(outdir, "top_choices.csv"), index=False)
    import json
    with open(os.path.join(outdir, "elasticities.json"), "w", encoding="utf-8") as f:
        json.dump(elasticities, f, ensure_ascii=False, indent=2)

    # Reports
    try:
        write_html_report(
            os.path.join(outdir, "report_html.html"),
            H, shares, top_table, elasticities,
            delta=None,
            metric_info={"metric": metric, "weights": weights},
            names=names,
            capacity_df=merged
        )
        write_excel_report(os.path.join(outdir, "report_excel.xlsx"), H, shares, top_table, elasticities, S_df, U_df, names)
    except Exception as e:
        print(f"[warn] Report writing failed: {e}")

    print(f"[info] Outputs written to: {outdir}")
    print(ols.summary())

if __name__ == "__main__":
    main()
