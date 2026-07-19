import os
import pandas as pd
import matplotlib.pyplot as plt


# ======================================================
# CONFIG
# ======================================================

INPUT_CSV = "evaluation/results/merged_result_qwen.csv"
OUTPUT_DIR = "evaluation/results/report"

SEMANTIC_METRICS = ["Faithfulness", "Answer Relevancy", "Contextual Relevancy"]
TIMING_METRICS = ["Retrieval Time (ms)", "Generation Time (ms)", "Total Time (ms)"]
LENGTH_METRIC = "Response Length (words)"

ALL_NUMERIC_METRICS = SEMANTIC_METRICS + TIMING_METRICS + [LENGTH_METRIC]

DIFFICULTY_ORDER = ["Easy", "Medium", "Hard"]

# Score band thresholds used for the distribution breakdown of the three
# semantic (0-1) metrics. Adjust to match whatever bar you're evaluating
# against in your report.
SCORE_BANDS = [
    (0.0, 0.5, "Low (0.0-0.5)"),
    (0.5, 0.8, "Moderate (0.5-0.8)"),
    (0.8, 1.01, "High (0.8-1.0)"),  # 1.01 so a perfect 1.0 falls inside the band
]


# ======================================================
# LOAD DATA
# ======================================================

os.makedirs(OUTPUT_DIR, exist_ok=True)

df = pd.read_csv(INPUT_CSV)

# Exclude rows where the RAG pipeline itself failed, if present, so
# pipeline crashes aren't averaged in as low scores.
if "Error" in df.columns:
    failed_mask = df["Error"].notna()
else:
    failed_mask = pd.Series(False, index=df.index)

num_failed = int(failed_mask.sum())
df = df.loc[~failed_mask].copy()

# Order Difficulty categorically so groupby output is Easy -> Medium -> Hard
# instead of alphabetical.
if "Difficulty" in df.columns:
    present_levels = [d for d in DIFFICULTY_ORDER if d in df["Difficulty"].unique()]
    other_levels = [d for d in df["Difficulty"].unique() if d not in DIFFICULTY_ORDER]
    df["Difficulty"] = pd.Categorical(
        df["Difficulty"], categories=present_levels + other_levels, ordered=True
    )


# ======================================================
# OVERALL SUMMARY STATISTICS
# ======================================================

overall_stats = df[ALL_NUMERIC_METRICS].agg(
    ["mean", "std", "median", "min", "max"]
).T
overall_stats.insert(0, "count", len(df))
overall_stats = overall_stats.round(3)
overall_stats.index.name = "Metric"

overall_stats.to_csv(os.path.join(OUTPUT_DIR, "overall_summary.csv"))


# ======================================================
# SCORE DISTRIBUTION (semantic metrics only)
# ======================================================

distribution_rows = []
for metric in SEMANTIC_METRICS:
    for low, high, label in SCORE_BANDS:
        count = df[(df[metric] >= low) & (df[metric] < high)].shape[0]
        pct = round(100 * count / len(df), 1) if len(df) else 0.0
        distribution_rows.append({
            "Metric": metric,
            "Band": label,
            "Count": count,
            "Percent": pct,
        })

distribution_df = pd.DataFrame(distribution_rows)
distribution_df.to_csv(os.path.join(OUTPUT_DIR, "score_distribution.csv"), index=False)


# ======================================================
# BREAKDOWN BY CATEGORY
# ======================================================

category_breakdown = (
    df.groupby("Category", observed=True)[ALL_NUMERIC_METRICS]
    .mean()
    .round(3)
)
category_breakdown["Count"] = df.groupby("Category", observed=True).size()
category_breakdown = category_breakdown.sort_values("Count", ascending=False)
category_breakdown.to_csv(os.path.join(OUTPUT_DIR, "category_breakdown.csv"))


# ======================================================
# BREAKDOWN BY DIFFICULTY
# ======================================================

difficulty_breakdown = (
    df.groupby("Difficulty", observed=True)[ALL_NUMERIC_METRICS]
    .mean()
    .round(3)
)
difficulty_breakdown["Count"] = df.groupby("Difficulty", observed=True).size()
difficulty_breakdown.to_csv(os.path.join(OUTPUT_DIR, "difficulty_breakdown.csv"))


# ======================================================
# CORRELATION: RESPONSE LENGTH vs GENERATION TIME
# ======================================================

correlation = df[[LENGTH_METRIC, "Generation Time (ms)", "Total Time (ms)"]].corr().round(3)
correlation.to_csv(os.path.join(OUTPUT_DIR, "correlation.csv"))


# ======================================================
# CHARTS
# ======================================================

plt.style.use("seaborn-v0_8-whitegrid")

# Chart 1: Mean semantic scores by Category
fig, ax = plt.subplots(figsize=(9, 5))
category_breakdown[SEMANTIC_METRICS].plot(kind="bar", ax=ax)
ax.set_ylabel("Mean Score (0-1)")
ax.set_title("Mean Semantic Scores by Question Category")
ax.set_ylim(0, 1)
plt.xticks(rotation=40, ha="right")
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "scores_by_category.png"), dpi=150)
plt.close(fig)

# Chart 2: Mean semantic scores by Difficulty
fig, ax = plt.subplots(figsize=(7, 5))
difficulty_breakdown[SEMANTIC_METRICS].plot(kind="bar", ax=ax)
ax.set_ylabel("Mean Score (0-1)")
ax.set_title("Mean Semantic Scores by Difficulty")
ax.set_ylim(0, 1)
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "scores_by_difficulty.png"), dpi=150)
plt.close(fig)

# Chart 3: Timing breakdown by Difficulty (stacked retrieval + generation)
fig, ax = plt.subplots(figsize=(7, 5))
difficulty_breakdown[["Retrieval Time (ms)", "Generation Time (ms)"]].plot(
    kind="bar", stacked=True, ax=ax
)
ax.set_ylabel("Time (ms)")
ax.set_title("Mean Retrieval / Generation Time by Difficulty")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "timing_by_difficulty.png"), dpi=150)
plt.close(fig)

# Chart 4: Response length vs generation time (scatter)
fig, ax = plt.subplots(figsize=(7, 5))
ax.scatter(df[LENGTH_METRIC], df["Generation Time (ms)"], alpha=0.7)
ax.set_xlabel("Response Length (words)")
ax.set_ylabel("Generation Time (ms)")
ax.set_title("Response Length vs Generation Time")
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "length_vs_time.png"), dpi=150)
plt.close(fig)

# Chart 5: Semantic score distribution (stacked bar of Low/Moderate/High bands)
pivot = distribution_df.pivot(index="Metric", columns="Band", values="Count")
band_order = [b[2] for b in SCORE_BANDS]
pivot = pivot[[b for b in band_order if b in pivot.columns]]
fig, ax = plt.subplots(figsize=(7, 5))
pivot.plot(kind="bar", stacked=True, ax=ax, color=["#d9534f", "#f0ad4e", "#5cb85c"])
ax.set_ylabel("Number of Test Cases")
ax.set_title("Score Distribution by Band (Semantic Metrics)")
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, "score_bands.png"), dpi=150)
plt.close(fig)


# ======================================================
# MARKDOWN SUMMARY (paste-ready for a report)
# ======================================================

md_lines = []
md_lines.append("# RAG Evaluation Summary\n")
md_lines.append(f"**Total test cases:** {len(df)}")
if num_failed:
    md_lines.append(f"  \n**Excluded (pipeline errors):** {num_failed}")
md_lines.append("\n## Overall Metrics\n")
md_lines.append(overall_stats.to_markdown())
md_lines.append("\n## Score Distribution\n")
md_lines.append(distribution_df.to_markdown(index=False))
md_lines.append("\n## Breakdown by Category\n")
md_lines.append(category_breakdown.to_markdown())
md_lines.append("\n## Breakdown by Difficulty\n")
md_lines.append(difficulty_breakdown.to_markdown())
md_lines.append("\n## Correlation (Length / Timing)\n")
md_lines.append(correlation.to_markdown())

with open(os.path.join(OUTPUT_DIR, "summary_report.md"), "w") as f:
    f.write("\n".join(md_lines))


# ======================================================
# CONSOLE SUMMARY
# ======================================================

print("=" * 70)
print("RAG Evaluation Summary")
print("=" * 70)
print(f"Total Test Cases      : {len(df)}")
if num_failed:
    print(f"Excluded (Errors)     : {num_failed}")
print()
print("-- Overall Metrics --")
print(overall_stats)
print()
print("-- Score Distribution --")
print(distribution_df.to_string(index=False))
print()
print("-- By Category --")
print(category_breakdown)
print()
print("-- By Difficulty --")
print(difficulty_breakdown)
print()
print("-- Correlation --")
print(correlation)
print()
print(f"All report-ready files saved to: {OUTPUT_DIR}/")
print("  overall_summary.csv, score_distribution.csv, category_breakdown.csv,")
print("  difficulty_breakdown.csv, correlation.csv, summary_report.md,")
print("  scores_by_category.png, scores_by_difficulty.png,")
print("  timing_by_difficulty.png, length_vs_time.png, score_bands.png")