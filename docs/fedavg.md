# Weighted FedAvg Aggregation & Update Validation

This document describes the mathematical formulation of Weighted FedAvg model aggregation and update validation implemented in NeuroBroker.

---

## 1. Critical Distinction: Scheduler Score vs FedAvg Weight

> [!IMPORTANT]
> NeuroBroker strictly separates two distinct weighting mechanisms:
> * **Scheduler Capability Score**: Decides **WHO** should be assigned to train and **WHAT PROPORTION** of the dataset they receive.
> * **FedAvg Sample Weight**: Decides **HOW** trained local model weights are aggregated mathematically.

---

## 2. Mathematical Formulation

Let $K$ be the number of participating volunteer nodes in round $r$. Each node $i$ trains on $n_i$ local samples, with the total number of processed samples given by:

$$N = \sum_{i=1}^{K} n_i$$

The aggregation weight for volunteer node $i$ is strictly proportional to its sample volume:

$$w_i = \frac{n_i}{N}$$

The updated global model parameters $\mathbf{W}^{(r+1)}$ are computed via element-wise weighted averaging:

$$\mathbf{W}^{(r+1)} = \sum_{i=1}^{K} w_i \mathbf{W}_i^{(r)}$$

---

## 3. Pre-Aggregation State Dict Validation Pipeline

Before any weights are merged into the global model, `UpdateValidator` executes 6 strict integrity checks:
1. **SHA-256 Checksum Verification**: Guarantees update file was not truncated or corrupted in transit.
2. **PyTorch Tensor Deserialization**: Ensures the payload is a valid PyTorch `state_dict`.
3. **Key Name Consistency**: Verifies exact key set matches base model.
4. **Tensor Shape Matching**: Verifies every weight and bias dimension matches model architecture.
5. **Finite Value Guard**: Rejects updates containing `NaN` or `Inf` floating point values.
6. **Sample Volume Verification**: Rejects updates reporting $n_i \le 0$.
