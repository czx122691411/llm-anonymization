#!/usr/bin/env python3
"""
Plot utility scores for DeepSeek adversarial training
Following the README methodology
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

# Set style
sns.set_style("whitegrid")

# Color palette
color_palette = ["#EA985F", "#00A669", "#FFD500", "#E74C41", "#1D81A2", "#333333"]

# Data path
base_path = "/home/rooter/llm-anonymization/anonymized_results/synthetic/deepseek_full"
csv_file = f"{base_path}/eval_df_out.csv"
output_dir = f"{base_path}/plots_readme_method"

# Create output directory
os.makedirs(output_dir, exist_ok=True)

# Load data
df = pd.read_csv(csv_file)

# Normalize data following plot_anonymized.py
df["is_correct_list"] = df["is_correct"].apply(lambda x: [1, 1, 1] if x == 1 else [0, 0, 0])
df["first_correct"] = df["is_correct_list"].apply(lambda x: x[0] == 1)

# Map pii types to standard names
pii_map = {
    "gender": "SEX",
    "age": "AGE",
    "location": "LOC",
    "occupation": "OCCP",
    "married": "REL",
    "income": "INC",
    "education": "EDU",
    "pobp": "POBP",
}
df["pii_type_std"] = df["pii_type"].map(pii_map)

# Create full_anon_setting for consistency
df["full_anon_setting"] = df["anon_setting"].astype(str) + "-" + df["anon_level"].astype(str)

# Calculate utility per setting
mean_data = (
    df.groupby(["anon_level"])
    .agg({
        "utility_bleu": "mean",
        "utility_rouge": "mean",
        "utility_comb": "mean",
        "utility_model": "mean",
        "first_correct": ["sum", "count"],
    })
    .reset_index()
)

mean_data.columns = ["anon_level", "bleu", "rouge", "comb", "model", "correct_sum", "count"]
mean_data["round"] = mean_data["anon_level"]
mean_data["accuracy"] = mean_data["correct_sum"] / mean_data["count"]

print("=== DeepSeek Utility Scores by Round ===")
print(mean_data[["round", "bleu", "rouge", "accuracy"]].to_string(index=False))

# Plot 1: Utility vs Accuracy (BLEU)
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# BLEU vs Accuracy
ax = axes[0, 0]
scatter = ax.scatter(
    mean_data["accuracy"],
    mean_data["bleu"],
    c=mean_data["round"],
    s=200,
    alpha=0.7,
    cmap="viridis",
    edgecolors="black",
    linewidths=2
)
for i, row in mean_data.iterrows():
    ax.annotate(
        f"R{int(row['round'])}",
        (row["accuracy"], row["bleu"]),
        xytext=(5, 5),
        textcoords="offset points",
        fontsize=10,
        fontweight="bold"
    )
ax.plot(mean_data["accuracy"], mean_data["bleu"], "k--", alpha=0.3)
ax.set_xlabel("Attacker Accuracy", fontsize=12)
ax.set_ylabel("BLEU Score", fontsize=12)
ax.set_title("Privacy-Utility Trade-off (BLEU)", fontsize=14, fontweight="bold")
ax.grid(True, alpha=0.3)
ax.set_xlim(0, 1)
ax.set_ylim(0.6, 1.0)

# ROUGE vs Accuracy
ax = axes[0, 1]
scatter = ax.scatter(
    mean_data["accuracy"],
    mean_data["rouge"],
    c=mean_data["round"],
    s=200,
    alpha=0.7,
    cmap="viridis",
    edgecolors="black",
    linewidths=2
)
for i, row in mean_data.iterrows():
    ax.annotate(
        f"R{int(row['round'])}",
        (row["accuracy"], row["rouge"]),
        xytext=(5, 5),
        textcoords="offset points",
        fontsize=10,
        fontweight="bold"
    )
ax.plot(mean_data["accuracy"], mean_data["rouge"], "k--", alpha=0.3)
ax.set_xlabel("Attacker Accuracy", fontsize=12)
ax.set_ylabel("ROUGE-1 Score", fontsize=12)
ax.set_title("Privacy-Utility Trade-off (ROUGE-1)", fontsize=14, fontweight="bold")
ax.grid(True, alpha=0.3)
ax.set_xlim(0, 1)
ax.set_ylim(0.8, 1.0)

# BLEU by Round
ax = axes[1, 0]
bars = ax.bar(mean_data["round"], mean_data["bleu"], color=color_palette[:3], alpha=0.7)
ax.set_xlabel("Adversarial Round", fontsize=12)
ax.set_ylabel("BLEU Score", fontsize=12)
ax.set_title("BLEU Score by Round", fontsize=14, fontweight="bold")
ax.grid(True, alpha=0.3, axis="y")
ax.set_ylim(0.6, 1.0)
for i, v in enumerate(mean_data["bleu"]):
    ax.text(i + 1, v + 0.01, f"{v:.4f}", ha="center", fontsize=10)

# ROUGE by Round
ax = axes[1, 1]
bars = ax.bar(mean_data["round"], mean_data["rouge"], color=color_palette[3:6], alpha=0.7)
ax.set_xlabel("Adversarial Round", fontsize=12)
ax.set_ylabel("ROUGE-1 Score", fontsize=12)
ax.set_title("ROUGE-1 Score by Round", fontsize=14, fontweight="bold")
ax.grid(True, alpha=0.3, axis="y")
ax.set_ylim(0.8, 1.0)
for i, v in enumerate(mean_data["rouge"]):
    ax.text(i + 1, v + 0.005, f"{v:.4f}", ha="center", fontsize=10)

plt.suptitle("DeepSeek Adversarial Training: Utility Scores Analysis",
             fontsize=16, fontweight="bold", y=0.995)
plt.tight_layout()

# Save the plot
plot_path = os.path.join(output_dir, "utility_scores_overview.png")
plt.savefig(plot_path, dpi=300, bbox_inches="tight")
print(f"\nSaved utility scores overview to {plot_path}")

# Also save as PDF
pdf_path = plot_path.replace(".png", ".pdf")
plt.savefig(pdf_path, bbox_inches="tight")
print(f"Saved PDF to {pdf_path}")

plt.close()

# Plot 2: Utility by PII Type
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

pii_utility = df.groupby(["pii_type_std", "anon_level"]).agg({
    "utility_bleu": "mean",
    "utility_rouge": "mean"
}).reset_index()

# BLEU by PII Type and Round
ax = axes[0]
for pii in pii_utility["pii_type_std"].unique():
    data = pii_utility[pii_utility["pii_type_std"] == pii]
    ax.plot(data["anon_level"], data["utility_bleu"], marker="o", label=pii, linewidth=2)

ax.set_xlabel("Adversarial Round", fontsize=12)
ax.set_ylabel("BLEU Score", fontsize=12)
ax.set_title("BLEU Score by PII Type and Round", fontsize=14, fontweight="bold")
ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=9)
ax.grid(True, alpha=0.3)
ax.set_ylim(0, 1)

# ROUGE by PII Type and Round
ax = axes[1]
for pii in pii_utility["pii_type_std"].unique():
    data = pii_utility[pii_utility["pii_type_std"] == pii]
    ax.plot(data["anon_level"], data["utility_rouge"], marker="s", label=pii, linewidth=2)

ax.set_xlabel("Adversarial Round", fontsize=12)
ax.set_ylabel("ROUGE-1 Score", fontsize=12)
ax.set_title("ROUGE-1 Score by PII Type and Round", fontsize=14, fontweight="bold")
ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=9)
ax.grid(True, alpha=0.3)
ax.set_ylim(0, 1)

plt.tight_layout()
plot_path = os.path.join(output_dir, "utility_by_pii_type.png")
plt.savefig(plot_path, dpi=300, bbox_inches="tight")
print(f"Saved utility by PII type to {plot_path}")

pdf_path = plot_path.replace(".png", ".pdf")
plt.savefig(pdf_path, bbox_inches="tight")
print(f"Saved PDF to {pdf_path}")
plt.close()

# Plot 3: Combined Privacy-Utility Analysis
fig, ax = plt.subplots(figsize=(10, 8))

# Plot rounds as a trajectory
for i, row in mean_data.iterrows():
    circle = plt.Circle(
        (row["accuracy"], row["bleu"]),
        0.03,
        color=plt.cm.viridis(i / len(mean_data)),
        alpha=0.6
    )
    ax.add_patch(circle)
    ax.annotate(
        f"R{int(row['round'])}",
        (row["accuracy"], row["bleu"]),
        xytext=(0, 10),
        textcoords="offset points",
        ha="center",
        fontsize=11,
        fontweight="bold"
    )

# Draw arrows between rounds
for i in range(len(mean_data) - 1):
    x1, y1 = mean_data.iloc[i]["accuracy"], mean_data.iloc[i]["bleu"]
    x2, y2 = mean_data.iloc[i + 1]["accuracy"], mean_data.iloc[i + 1]["bleu"]
    ax.annotate(
        "",
        xy=(x2, y2),
        xytext=(x1, y1),
        arrowprops=dict(arrowstyle="->", lw=2, color="gray", alpha=0.7)
    )

# Add regions
ax.text(0.85, 0.85, "Ideal:\nHigh Privacy\nHigh Utility",
        fontsize=12, style="italic", color="green",
        bbox=dict(boxstyle="round,pad=0.5", fc="lightgreen", alpha=0.5))

ax.set_xlim(0, 1)
ax.set_ylim(0.65, 0.95)
ax.set_xlabel("Attacker Accuracy (Privacy Risk - Lower is Better)", fontsize=13)
ax.set_ylabel("BLEU Score (Text Utility - Higher is Better)", fontsize=13)
ax.set_title("DeepSeek Adversarial Training: Privacy-Utility Trajectory",
             fontsize=15, fontweight="bold", pad=20)
ax.grid(True, alpha=0.3, linestyle=":")

# Add reference lines
ax.axhline(y=0.75, color="orange", linestyle="--", alpha=0.5, label="75% Utility")
ax.axvline(x=0.5, color="red", linestyle="--", alpha=0.5, label="50% Accuracy")
ax.legend(fontsize=10)

plt.tight_layout()
plot_path = os.path.join(output_dir, "privacy_utility_trajectory.png")
plt.savefig(plot_path, dpi=300, bbox_inches="tight")
print(f"Saved privacy-utility trajectory to {plot_path}")

pdf_path = plot_path.replace(".png", ".pdf")
plt.savefig(pdf_path, bbox_inches="tight")
print(f"Saved PDF to {pdf_path}")
plt.close()

print("\n=== All plots generated successfully ===")
print(f"Output directory: {output_dir}")
