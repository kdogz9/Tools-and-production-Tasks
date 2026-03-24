"""
Greedy Piggies — Social Media Performance Visualization Suite
=============================================================
Generates three high-resolution charts and a summary analysis report
from the reels_performance_metrics.csv dataset.

Charts produced:
  1. reach_vs_engagement.png   – Dual-axis bar + line
  2. retention_analysis.png    – Scatter plot (Duration vs Avg Watch Time)
  3. engagement_breakdown.png  – Stacked bar chart
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
import numpy as np
import os, textwrap

# ──────────────────────────────────────────────
# 0.  Configuration
# ──────────────────────────────────────────────
DATA_PATH = os.path.join(os.path.dirname(__file__), "reels_performance_metrics.csv")
OUT_DIR   = os.path.dirname(__file__)
DPI       = 300

# Professional colour palette
COLORS = {
    "reach":      "#2E86AB",   # steel blue
    "engagement": "#F24236",   # coral red
    "likes":      "#6C5CE7",   # vivid purple
    "saves":      "#00B894",   # mint green
    "shares":     "#FDCB6E",   # warm amber
    "comments":   "#E17055",   # terracotta
    "scatter":    "#0984E3",   # ocean blue
    "trendline":  "#D63031",   # strong red
}

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update({
    "font.family":      "sans-serif",
    "font.sans-serif":  ["Segoe UI", "Arial", "Helvetica", "DejaVu Sans"],
    "axes.titlesize":   14,
    "axes.titleweight":  "bold",
    "axes.labelsize":   11,
    "legend.fontsize":  9,
    "figure.facecolor": "white",
})

# ──────────────────────────────────────────────
# 1.  Data Loading & Processing
# ──────────────────────────────────────────────
df = pd.read_csv(DATA_PATH)

# Strip whitespace from column names
df.columns = df.columns.str.strip()

# Combine Date + Time → datetime
df["Datetime"] = pd.to_datetime(df["Date"] + " " + df["Time"], format="%b %d, %Y %I:%M %p")
df.sort_values("Datetime", inplace=True)
df.reset_index(drop=True, inplace=True)

# Convert Duration (M:SS) to total seconds
def duration_to_seconds(val):
    """Convert M:SS or H:MM:SS string to total seconds."""
    parts = str(val).split(":")
    parts = [int(p) for p in parts]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    elif len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return 0

df["Duration_sec"] = df["Duration"].apply(duration_to_seconds)

# Convert Total Watch Time (H:MM:SS) to total seconds
df["Total_Watch_sec"] = df["Total Watch Time"].apply(duration_to_seconds)

# Short label for x-axes (wraps caption to ≤30 chars)
df["ShortLabel"] = df["Post Caption"].apply(
    lambda c: textwrap.shorten(c, width=35, placeholder="…")
)

# Date labels for time-series axes
df["DateLabel"] = df["Datetime"].dt.strftime("%b %d")

print("✅  Data loaded and processed successfully.")
print(df[["DateLabel", "Reach", "Engagement Rate (%)", "Duration_sec", "Avg Watch Time (s)"]].to_string(index=False))

# ──────────────────────────────────────────────
# 2.  Chart 1 — Reach vs. Engagement Rate
# ──────────────────────────────────────────────
fig, ax1 = plt.subplots(figsize=(10, 5.5))

x = np.arange(len(df))
bar_width = 0.55

# Bars — Reach
bars = ax1.bar(x, df["Reach"], width=bar_width, color=COLORS["reach"],
               alpha=0.85, label="Reach", zorder=2, edgecolor="white", linewidth=0.6)
ax1.set_xlabel("Post (chronological)")
ax1.set_ylabel("Reach", color=COLORS["reach"], fontweight="bold")
ax1.tick_params(axis="y", labelcolor=COLORS["reach"])
ax1.set_xticks(x)
ax1.set_xticklabels(df["DateLabel"], rotation=0, fontsize=9)

# Add value labels on bars
for bar in bars:
    height = bar.get_height()
    ax1.annotate(f'{int(height)}',
                 xy=(bar.get_x() + bar.get_width() / 2, height),
                 xytext=(0, 4), textcoords="offset points",
                 ha='center', va='bottom', fontsize=8, fontweight='bold',
                 color=COLORS["reach"])

# Line — Engagement Rate on secondary y-axis
ax2 = ax1.twinx()
line = ax2.plot(x, df["Engagement Rate (%)"], color=COLORS["engagement"],
                marker="o", markersize=8, linewidth=2.5, label="Engagement Rate (%)",
                zorder=3)
ax2.set_ylabel("Engagement Rate (%)", color=COLORS["engagement"], fontweight="bold")
ax2.tick_params(axis="y", labelcolor=COLORS["engagement"])

# Add value labels on line points
for i, val in enumerate(df["Engagement Rate (%)"]):
    ax2.annotate(f'{val:.1f}%',
                 xy=(x[i], val),
                 xytext=(0, 10), textcoords="offset points",
                 ha='center', va='bottom', fontsize=8, fontweight='bold',
                 color=COLORS["engagement"])

# Combined legend
lines_labels = ax1.get_legend_handles_labels()
lines_labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines_labels[0] + lines_labels2[0],
           lines_labels[1] + lines_labels2[1],
           loc="upper left", framealpha=0.9)

ax1.set_title("Reach vs. Engagement Rate Over Time\n",
              fontsize=15, fontweight="bold", pad=10)
fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "reach_vs_engagement.png"), dpi=DPI,
            bbox_inches="tight", facecolor="white")
plt.close(fig)
print("📊  Saved reach_vs_engagement.png")

# ──────────────────────────────────────────────
# 3.  Chart 2 — Retention Analysis (Duration vs Avg Watch Time)
# ──────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 6))

# Bubble size proportional to Reach
sizes = (df["Reach"] / df["Reach"].max()) * 500 + 80

scatter = ax.scatter(df["Duration_sec"], df["Avg Watch Time (s)"],
                     s=sizes, c=COLORS["scatter"], alpha=0.7, edgecolors="white",
                     linewidth=1.5, zorder=3)

# Trendline
z = np.polyfit(df["Duration_sec"], df["Avg Watch Time (s)"], 1)
p = np.poly1d(z)
x_line = np.linspace(df["Duration_sec"].min() - 1, df["Duration_sec"].max() + 1, 100)
ax.plot(x_line, p(x_line), "--", color=COLORS["trendline"], linewidth=1.8,
        alpha=0.7, label="Trend line")

# Annotate each point with its short label
for i, row in df.iterrows():
    ax.annotate(row["DateLabel"],
                xy=(row["Duration_sec"], row["Avg Watch Time (s)"]),
                xytext=(8, -5), textcoords="offset points",
                fontsize=8, color="#333333",
                arrowprops=dict(arrowstyle="-", color="#aaaaaa", lw=0.7))

ax.set_xlabel("Video Duration (seconds)", fontweight="bold")
ax.set_ylabel("Avg Watch Time (seconds)", fontweight="bold")
ax.set_title("Retention Analysis: Duration vs. Avg Watch Time\n"
             "(bubble size ∝ Reach)",
             fontsize=14, fontweight="bold", pad=10)
ax.legend(loc="lower right", framealpha=0.9)
ax.set_xlim(left=0)
ax.set_ylim(bottom=0)
fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "retention_analysis.png"), dpi=DPI,
            bbox_inches="tight", facecolor="white")
plt.close(fig)
print("📊  Saved retention_analysis.png")

# ──────────────────────────────────────────────
# 4.  Chart 3 — Engagement Breakdown (Stacked Bar)
# ──────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 6))

categories = ["Likes", "Saves", "Shares", "Comments"]
colors_stack = [COLORS["likes"], COLORS["saves"], COLORS["shares"], COLORS["comments"]]

x = np.arange(len(df))
bar_width = 0.6
bottoms = np.zeros(len(df))

for cat, col in zip(categories, colors_stack):
    vals = df[cat].values
    ax.bar(x, vals, width=bar_width, bottom=bottoms, label=cat,
           color=col, edgecolor="white", linewidth=0.5, zorder=2)
    # Add value labels for segments >= 5
    for i, (v, b) in enumerate(zip(vals, bottoms)):
        if v >= 5:
            ax.text(x[i], b + v / 2, str(int(v)),
                    ha="center", va="center", fontsize=7.5,
                    fontweight="bold", color="white")
    bottoms += vals

# Total label on top of each bar
for i, total in enumerate(bottoms):
    ax.text(x[i], total + 1.2, f"Σ {int(total)}",
            ha="center", va="bottom", fontsize=8.5, fontweight="bold",
            color="#333333")

ax.set_xticks(x)
# Use wrapped captions
labels = [textwrap.fill(l, 22) for l in df["ShortLabel"]]
ax.set_xticklabels(labels, fontsize=7.5, ha="center")
ax.set_ylabel("Number of Interactions", fontweight="bold")
ax.set_title("Engagement Breakdown by Post\n",
             fontsize=15, fontweight="bold", pad=10)
ax.legend(loc="upper right", framealpha=0.9, ncol=2)
ax.set_ylim(top=bottoms.max() * 1.15)
fig.tight_layout()
fig.savefig(os.path.join(OUT_DIR, "engagement_breakdown.png"), dpi=DPI,
            bbox_inches="tight", facecolor="white")
plt.close(fig)
print("📊  Saved engagement_breakdown.png")

# ──────────────────────────────────────────────
# 5.  Compute KPIs for report
# ──────────────────────────────────────────────
kpis = {
    "total_posts":       len(df),
    "avg_reach":         df["Reach"].mean(),
    "max_reach":         df["Reach"].max(),
    "avg_impressions":   df["Impressions"].mean(),
    "avg_engagement":    df["Engagement Rate (%)"].mean(),
    "max_engagement":    df["Engagement Rate (%)"].max(),
    "total_likes":       df["Likes"].sum(),
    "total_saves":       df["Saves"].sum(),
    "total_shares":      df["Shares"].sum(),
    "total_comments":    df["Comments"].sum(),
    "avg_watch_time":    df["Avg Watch Time (s)"].mean(),
    "best_post_reach":   df.loc[df["Reach"].idxmax(), "Post Caption"],
    "best_post_eng":     df.loc[df["Engagement Rate (%)"].idxmax(), "Post Caption"],
}

# Best performing duration bucket
sweet = df.loc[df["Avg Watch Time (s)"].idxmax()]
kpis["sweet_spot_duration"] = sweet["Duration_sec"]
kpis["sweet_spot_avg_watch"] = sweet["Avg Watch Time (s)"]

print("\n✅  All charts saved. KPIs computed.")
print(f"   Average Reach:       {kpis['avg_reach']:.0f}")
print(f"   Average Engagement:  {kpis['avg_engagement']:.2f}%")
print(f"   Average Watch Time:  {kpis['avg_watch_time']:.1f}s")

# ──────────────────────────────────────────────
# 6.  Generate Summary_Analysis.md
# ──────────────────────────────────────────────
report = f"""# 🎮 Greedy Piggies — Social Media Performance Report

**Report Date:** March 10, 2026  
**Reporting Period:** Feb 17 – Mar 8, 2026  
**Prepared for:** Greedy Piggies Studio Team

---

## 📈 Key Performance Indicators (KPIs)

| Metric | Value |
|---|---|
| **Total Posts Analyzed** | {kpis['total_posts']} |
| **Average Reach** | {kpis['avg_reach']:.0f} |
| **Peak Reach** | {kpis['max_reach']} |
| **Average Impressions** | {kpis['avg_impressions']:.0f} |
| **Average Engagement Rate** | {kpis['avg_engagement']:.2f}% |
| **Peak Engagement Rate** | {kpis['max_engagement']:.2f}% |
| **Total Likes** | {kpis['total_likes']} |
| **Total Saves** | {kpis['total_saves']} |
| **Total Shares** | {kpis['total_shares']} |
| **Total Comments** | {kpis['total_comments']} |
| **Average Watch Time** | {kpis['avg_watch_time']:.1f}s |

---

## 🔍 Content Theme Analysis

Based on a review of post captions, three distinct content strategies were employed during this period. Here's how each performed:

### 1. 🏆 Relatable Meme / Humor Content
**Post:** *"Average game dev experience…"* (Feb 24)  
- **Reach:** 179 | **Engagement Rate:** 22.91%  
- **Shares:** 13 | **Saves:** 27  
- **Insight:** This meme-style reel struck a strong balance between reach and engagement. The relatable humor drove high save and share counts, indicating genuine audience connection. Humor is your viral catalyst.

### 2. 🏆🏆 Behind-the-Scenes / Studio Tour
**Post:** *"POV: You're walking into the studio…"* (Feb 17)  
- **Reach:** 401 (📈 highest) | **Engagement Rate:** 13.97%  
- **Saves:** 39 (📈 highest) | **Shares:** 17  
- **Insight:** This was your highest-reach post by a wide margin. The "Studio Tour" concept generates strong curiosity and shareability. While the engagement *rate* was lower, the sheer volume of interactions (112 total) was the highest of any post. This content builds brand identity.

### 3. 🎯 Gameplay / Tutorial Content
**Post:** *"How to play greedy piggies explained by pigs"* (Mar 8)  
- **Reach:** 93 | **Engagement Rate:** 40.86% (📈 highest!)  
- **Shares:** 18 (📈 highest) | **Saves:** 19  
- **Insight:** Despite the lowest reach, this gameplay explainer achieved a remarkable 40.86% engagement rate—nearly double the average. People who *did* see it were deeply engaged. This format converts viewers into community members.

### 4. 🎨 Educational / Dev Process
**Posts:** *"The Secret To Making Levels…"* (Feb 27) and *"The chosen level theme…"* (Mar 5)  
- **Avg Reach:** ~143 | **Avg Engagement:** ~19.8%  
- **Insight:** Educational and poll-style content performs steadily. The level design explainer had the highest average watch time (44.1s), suggesting that dev-process content keeps dedicated viewers watching longer.

---

## 📊 Visual Insights

### Reach vs. Engagement (see `reach_vs_engagement.png`)
An inverse trend is visible: the highest-reach post (401) had the lowest engagement rate (13.97%), while the lowest-reach post (93) had the highest engagement rate (40.86%). This is a common pattern—broader reach often means less targeted audiences. **Focus on engagement quality over raw reach.**

### Retention Sweet Spot (see `retention_analysis.png`)
- The **14-second video** ("Secret To Making Levels") achieved the highest avg watch time of **44.1s** — a 3.15× replay ratio.
- Shorter 8–9 second reels cluster around 37–41s avg watch time, still strong.
- **Recommendation:** Videos in the **8–16 second range** are the sweet spot for this audience. They are short enough to trigger replays but long enough to convey value.

### Engagement Breakdown (see `engagement_breakdown.png`)
- **Likes** dominate total interactions across all posts (avg 37.8 per post).
- **Saves** are consistently high (avg 24.2)—an excellent signal of content value. Saves indicate "I want to come back to this."
- **Shares** vary significantly (3–18), driven by meme or gameplay content.
- **Comments** are critically low (only 1 comment total). This is the biggest growth opportunity.

---

## 🚀 Actionable Recommendations — Next 30 Days

### 1. Double Down on Gameplay Reveals
Your gameplay explainer earned a 40.86% engagement rate. Release **2–3 more gameplay teasers** in the next month. Show mechanics, character abilities, or level walkthroughs with the same fun, character-driven narration style.

### 2. Create a "Studio Diary" Series
The behind-the-scenes post had 401 reach. Turn this into a **weekly series** (e.g., "Studio Sundays") to build a consistent brand narrative and keep reach high. Include team members, whiteboard sessions, and candid moments.

### 3. Fix the Comments Gap ⚠️
With only **1 comment across 5 posts**, audience dialogue is nearly nonexistent. Try:
- Ending each reel with a **direct question** (e.g., "Which pig is YOUR play-style? 🐷")
- Using **poll stickers** in Stories that link to your reel
- Replying to every single comment to encourage more interaction

### 4. Keep Videos Under 16 Seconds
Your data shows that **8–16 second reels** maximize both replays and watch time. Avoid going over 16 seconds unless the content genuinely warrants it (e.g., a detailed tutorial).

### 5. Post Twice a Week at 6 PM
All posts were published around 6 PM, which appears to work well for this audience. Increase frequency from ~1 post/week to **2 posts/week** to capitalize on algorithmic momentum.

### 6. Leverage Your Save Rate
An average save rate this high (avg ~25% of likes) means people find lasting value in your content. Add a **CTA in the caption**: "Save this for later 🔖" to amplify this natural behavior.

---

## 🎯 30-Day Content Calendar Suggestion

| Week | Post 1 | Post 2 |
|---|---|---|
| **Week 1** | 🎮 Gameplay mechanic teaser | 🏠 Studio Diary #1 |
| **Week 2** | 😂 Meme / relatable dev humor | 🎨 Level design reveal + poll |
| **Week 3** | 🎮 Character ability showcase | 🏠 Studio Diary #2 |
| **Week 4** | 🐷 "Which pig are you?" quiz-style reel | 🚀 Recap + hype for what's next |

---

> *"You're not just building a game—you're building a community. Every reel is a brick. Keep stacking."* 🧱🐷

---

*Report generated by the Greedy Piggies Analytics Suite.*
"""

report_path = os.path.join(OUT_DIR, "Summary_Analysis.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.write(report)

print(f"\n📝  Saved Summary_Analysis.md")
print("🎉  Analysis complete! All outputs are in: " + OUT_DIR)
