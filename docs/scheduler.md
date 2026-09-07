# Intelligent Resource-Aware Multi-Objective Scheduler

The scheduler is the decision engine of NeuroBroker, responsible for dynamically ranking volunteer workers, balancing compute heterogeneity, estimating network bottlenecks, and producing transparent, explainable assignment rationales.

---

## 1. Multi-Objective Scoring Formulation

The composite score $S_i$ for volunteer node $i$ is calculated as:

$$\begin{aligned}
S_i &= w_{\text{cpu}} \cdot \text{CPU}_i + w_{\text{ram}} \cdot \text{RAM}_i + w_{\text{gpu}} \cdot \text{GPU}_i + w_{\text{vram}} \cdot \text{VRAM}_i \\
    &\quad + w_{\text{net}} \cdot \text{Net}_i + w_{\text{rel}} \cdot \text{Rel}_i + w_{\text{hist}} \cdot \text{Hist}_i + 0.10 \cdot \text{Fairness}_i \\
    &\quad - w_{\text{load}} \cdot \text{Load}_i - w_{\text{transfer}} \cdot \text{Penalty}_{\text{transfer}, i}
\end{aligned}$$

Where:
* **$\text{CPU}_i$**: Normalized available CPU fraction and core volume.
* **$\text{RAM}_i$**: Free RAM fraction and total capacity.
* **$\text{GPU}_i$ & $\text{VRAM}_i$**: CUDA / MPS hardware acceleration capability and free video memory.
* **$\text{Net}_i$**: Combined bandwidth score and latency penalty.
* **$\text{Rel}_i$**: Dynamic reliability rating ($0.1 \le \text{Rel}_i \le 1.0$) updated based on task completions and timeouts.
* **$\text{Fairness}_i$**: Contribution balance score ensuring capable nodes do not starve weaker nodes.
* **$\text{Load}_i$**: Current background workload on the volunteer OS.
* **$\text{Penalty}_{\text{transfer}, i}$**: Transfer time estimate penalty:
  $$\text{Transfer Time} = \frac{\text{Dataset Size} + \text{Model Size}}{\text{Bandwidth}} + \text{Latency}$$

---

## 2. Dynamic Data Allocation

To prevent straggler workers from stalling synchronous aggregation rounds, data chunks are allocated proportionally to worker compute capability:

$$a_i = \text{clamp}\left(\frac{C_i}{\sum_{j} C_j}, 0.10, 0.60\right)$$

This ensures stronger workers (e.g. RTX 4090) process proportionally more samples than CPU nodes while maintaining stratified class balance.

---

## 3. Explainability Output Example

For every decision, a natural language justification is stored in `scheduler_decisions`:

```text
[NODE-01 SELECTED - Score: 0.892]
Key factors:
  • High GPU acceleration capability (NVIDIA GeForce RTX 4090)
  • Low CPU utilization with 24 cores
  • Ample free RAM available
  • High network throughput (850 Mbps, transfer est: 0.6s)
  • High trust & reliability rating (98%)
  • Total Estimated Completion: 12.4s (Train: 11.8s, Transfer: 0.6s)
```
