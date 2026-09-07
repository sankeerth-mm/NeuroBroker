import json
import matplotlib.pyplot as plt
from pathlib import Path

def plot_benchmark_charts():
    base_dir = Path(__file__).resolve().parent
    results_file = base_dir / "benchmark_results.json"
    if not results_file.exists():
        print("benchmark_results.json not found. Run benchmark_schedulers.py first.")
        return
        
    with open(results_file, "r") as f:
        data = json.load(f)
        
    schedulers = list(data.keys())
    total_times = [data[s]["total_job_time_sec"] for s in schedulers]
    avg_round_times = [data[s]["avg_round_time_sec"] for s in schedulers]
    final_accuracies = [data[s]["final_accuracy"] for s in schedulers]
    fairness_indices = [data[s]["jains_fairness_index"] for s in schedulers]
    
    # 1. Total Execution Time Comparison Bar Chart
    plt.figure(figsize=(10, 6))
    colors = ["#ef4444", "#f59e0b", "#10b981", "#6366f1"]
    bars = plt.bar(schedulers, total_times, color=colors, width=0.55, edgecolor="black", linewidth=1.2)
    plt.title("Federated Training Duration Comparison (Lower is Better)", fontsize=14, fontweight="bold", pad=15)
    plt.ylabel("Total Training Time (Seconds)", fontsize=12)
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2.0, yval + 1.5, f"{yval:.1f}s", ha="center", va="bottom", fontweight="bold")
    plt.tight_layout()
    chart1_path = base_dir / "chart_training_time.png"
    plt.savefig(chart1_path, dpi=300)
    plt.close()
    
    # 2. Accuracy Convergence over Rounds
    plt.figure(figsize=(10, 6))
    markers = ["o", "s", "^", "D"]
    for idx, s in enumerate(schedulers):
        rounds = list(range(1, len(data[s]["round_accuracies"]) + 1))
        plt.plot(rounds, data[s]["round_accuracies"], marker=markers[idx], linewidth=2.5, label=s, color=colors[idx])
    plt.title("Model Convergence Accuracy Across Federated Rounds", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Federated Round Number", fontsize=12)
    plt.ylabel("Global Accuracy (%)", fontsize=12)
    plt.ylim(0, 100)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(fontsize=11, loc="lower right")
    plt.tight_layout()
    chart2_path = base_dir / "chart_accuracy_convergence.png"
    plt.savefig(chart2_path, dpi=300)
    plt.close()
    
    print(f"Benchmark charts saved to:\n  - {chart1_path}\n  - {chart2_path}")

if __name__ == "__main__":
    plot_benchmark_charts()
