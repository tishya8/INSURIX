import re
from collections import Counter

import pandas as pd


# ======================================================
# CONFIG
# ======================================================

INPUT_CSV = "evaluation/results/merged_result_qwen_V2.csv"
OUTPUT_CSV = "evaluation/results/merged_result_qwen_with_metrics_V2.csv"


# ======================================================
# TEXT NORMALIZATION
# ======================================================

def normalize(text):
    """
    Normalize text for comparison.

    Numbers are handled carefully since currency amounts, percentages,
    and decimals are semantically load-bearing in insurance answers
    (e.g. "50,000" and "50000" and "50.0" should compare equal, but
    "50" and "500" should not).
    """

    if pd.isna(text):
        return ""

    text = str(text).lower()

    # Normalize common currency notations to a single symbol so
    # "Rs.", "rs", "INR" and "₹" don't cause spurious mismatches.
    text = re.sub(r"\b(rs\.?|inr)\b", "₹", text)

    # Remove thousands separators *between digits* before stripping
    # punctuation, so "50,000" -> "50000" instead of "50 000".
    text = re.sub(r"(?<=\d),(?=\d)", "", text)

    # Remove punctuation, but keep decimal points between digits and
    # percent signs, since "10.5%" splitting into "10 5" would break
    # numeric matching.
    text = re.sub(r"(?<=\d)\.(?=\d)", "<DECIMAL>", text)  # protect decimals
    text = re.sub(r"[^\w\s₹%]", " ", text)
    text = text.replace("<DECIMAL>", ".")

    # remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


# ======================================================
# EXACT MATCH
# ======================================================

def exact_match(expected, generated):

    return int(
        normalize(expected) == normalize(generated)
    )


# ======================================================
# PRECISION / RECALL / F1 (multiset / Counter-based)
# ======================================================
# Uses Counter intersection rather than set intersection so repeated
# tokens (e.g. a number mentioned twice) are counted correctly, matching
# the standard SQuAD-style token-F1 implementation.

def precision_recall_f1(expected, generated):

    expected_tokens = Counter(normalize(expected).split())
    generated_tokens = Counter(normalize(generated).split())

    num_expected = sum(expected_tokens.values())
    num_generated = sum(generated_tokens.values())
    num_overlap = sum((expected_tokens & generated_tokens).values())

    precision = 0.0 if num_generated == 0 else num_overlap / num_generated
    recall = 0.0 if num_expected == 0 else num_overlap / num_expected

    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * recall / (precision + recall)

    return precision, recall, f1


# ======================================================
# MAIN
# ======================================================

df = pd.read_csv(INPUT_CSV)

# Exclude cases where the RAG pipeline itself failed (e.g. rows carrying
# an "Error" from evaluate_rag_updated.py). Scoring these as "wrong
# answers" conflates a pipeline crash with a bad generation and silently
# deflates your averages.
if "Error" in df.columns:
    failed_mask = df["Error"].notna()
else:
    failed_mask = pd.Series(False, index=df.index)

num_failed = int(failed_mask.sum())
scored_df = df.loc[~failed_mask].copy()

exact_matches = []
precisions = []
recalls = []
f1_scores = []

for _, row in scored_df.iterrows():

    expected = row["Expected Answer"]
    generated = row["Generated Answer"]

    em = exact_match(expected, generated)

    precision, recall, f1 = precision_recall_f1(
        expected,
        generated
    )

    exact_matches.append(em)
    precisions.append(round(precision, 3))
    recalls.append(round(recall, 3))
    f1_scores.append(round(f1, 3))

scored_df["Exact Match"] = exact_matches
scored_df["Precision"] = precisions
scored_df["Recall"] = recalls
scored_df["F1 Score"] = f1_scores

# Re-merge with failed rows (left with blank metric columns) so the
# output CSV still has one row per original test case.
for col in ["Exact Match", "Precision", "Recall", "F1 Score"]:
    df[col] = scored_df[col]


# ======================================================
# SAVE
# ======================================================

df.to_csv(
    OUTPUT_CSV,
    index=False
)


# ======================================================
# SUMMARY
# ======================================================

print("=" * 60)
print("Evaluation Metrics")
print("=" * 60)

print(f"Total Test Cases   : {len(df)}")
print(f"Scored Test Cases  : {len(scored_df)}")
if num_failed:
    print(f"Excluded (Errors)  : {num_failed}  <- pipeline failures, not scored")

print()

if len(scored_df):
    print(f"Exact Match : {scored_df['Exact Match'].mean():.3f}")
    print(f"Precision   : {scored_df['Precision'].mean():.3f}")
    print(f"Recall      : {scored_df['Recall'].mean():.3f}")
    print(f"F1 Score    : {scored_df['F1 Score'].mean():.3f}")
else:
    print("No scoreable test cases (all rows failed or empty dataset).")

print()

print(f"Saved to : {OUTPUT_CSV}")

print()
print("Note: Exact Match / token-F1 are lexical overlap metrics designed")
print("for short extractive answers. For generative LLM answers they are")
print("best read as secondary/diagnostic signals alongside semantic")
print("metrics (e.g. DeepEval Faithfulness / Answer Relevancy), not as")
print("the primary correctness score.")