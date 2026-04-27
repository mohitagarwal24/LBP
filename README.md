# Stochastic Option Pricing on NIFTY 50

**MAC-300: Laboratory-Based Project**
Department of Mathematics, IIT Roorkee | Academic Year 2025–26
Supervised by **Prof. Chaman Kumar**

**Authors:** Mohit Agarwal (23323023), Rishik Pulhani (23323033), Priyanshu Bawane (23323031)

---

## Overview

This project studies European option pricing on the NIFTY 50 index using four progressively richer stochastic models:

| Model | SDE | Parameters | IV Capability |
|---|---|---|---|
| Black–Scholes | GBM (constant σ) | 2 | Flat |
| Merton Jump-Diffusion | GBM + Poisson jumps | 5 | Smile |
| Heston (1993) | Stochastic variance (CIR) | 5 | Surface |
| Bates (1996) | Heston + Poisson jumps | 8 | Full surface |

All models are calibrated to real NIFTY 50 daily returns (2018–2024, 1721 observations) via MLE / quasi-MLE, and compared using AIC/BIC.

On the numerical side, we implement the **Convolution-FFT (CFFT)** pricing method from [Gao & Hyndman (2025)](https://arxiv.org/abs/2512.05326), which provides:
- A **stable characteristic function** (Thm 2.1) free of branch-cut discontinuities
- **Analytical error bounds** (Thm 3.1): truncation O(e^{-cN}) + discretisation O(N^{-2})

---

## Repository Structure

```
MAC-300 LBP/
├── MTE/                          # Mid-Term Evaluation (BS & Merton JD)
│   ├── Stochastic_Option_Pricing_v6_beamer.tex   # Beamer slides
│   ├── run_simulation.py                          # Calibration + figure generation
│   ├── stochastic_option_pricing_simulation.ipynb # Interactive notebook
│   ├── generate_presentation.py                   # PPTX generation helper
│   ├── render_equations.py                        # Equation image renderer
│   ├── math_explanation.txt                       # Derivation notes
│   └── speaker_notes.txt                          # MTE presentation script
│
├── ETE/                          # End-Term Evaluation (Heston & Bates + CFFT)
│   ├── ETE_Presentation.tex      # Beamer slides (21 frames)
│   ├── ete_simulation.py         # Full pipeline: data → calibration → pricing → figures
│   └── figures_ete/              # 12 generated figures
│       ├── 01_model_comparison.png
│       ├── 02_option_prices.png
│       ├── 03_iv_smile.png
│       ├── 04_cfft_accuracy.png
│       ├── 05_cfft_convergence.png
│       ├── 06_char_func.png
│       ├── 07_otm_puts.png
│       ├── 08_heston_paths.png
│       ├── 09_iv_surface_heston.png
│       ├── 10_iv_surface_bates.png
│       ├── 11_bates_paths.png
│       └── 12_atm_term_structure.png
│
├── figures/                      # MTE figures (data plots, equations, simulations)
├── local/                        # Speaker scripts and working notes
└── README.md
```

---

## Key Results

### Model Selection (calibrated on NIFTY 50 returns)

| Model | #Params | Log-Lik | AIC | BIC |
|---|---|---|---|---|
| Black–Scholes | 2 | 5285 | −10566 | −10555 |
| Merton JD | 5 | 5571 | −11131 | −11104 |
| Heston | 5 | 5501 | −10991 | −10964 |
| **Bates** | **8** | **5610** | **−11205** | **−11161** |

Bates wins on both AIC and BIC — NIFTY returns require both stochastic volatility and jumps.

### Calibrated Parameters (Heston + Bates extras)

| Parameter | Value | Interpretation |
|---|---|---|
| v₀ | 0.0051 | Initial vol ≈ 7.1% (calm market) |
| κ | 9.81 | Fast mean reversion (half-life ≈ 18 days) |
| θ | 0.0288 | Long-run vol ≈ 17.0% |
| σ | 0.648 | Vol-of-vol |
| ρ | −0.389 | Leverage effect confirmed |
| λ | 23.8 | ~24 jumps/year |
| μ_J | −0.0083 | Crash-biased (downward) jumps |
| σ_J | 0.0222 | Jump size dispersion ≈ 2.2% |

Feller condition satisfied: 2κθ = 0.565 > σ² = 0.420.

### Pricing and IV Results

- BS underprices OTM puts by **20–100%+** compared to Heston/Bates
- Heston produces IV **smile + term structure**; Bates adds steeper short-maturity skew
- ATM IV term structure: rises from √v₀ ≈ 7% (short end) to √θ ≈ 17% (long end)
- CFFT convergence verified at O(N⁻²), matching Theorem 3.1

---

## Running the Code

### Prerequisites

```
python >= 3.9
numpy
pandas
scipy
matplotlib
yfinance
```

### MTE (Black–Scholes & Merton)

```bash
cd MTE
python run_simulation.py
```

Generates figures in `../figures/` and prints calibration results.

### ETE (Heston, Bates, CFFT)

```bash
cd ETE
python ete_simulation.py
```

Downloads NIFTY data, calibrates all 4 models, runs CFFT/Carr–Madan pricing, generates all 12 figures in `figures_ete/`, and prints a summary table.

### Compiling Slides

```bash
cd ETE
pdflatex ETE_Presentation.tex
```

Requires a LaTeX distribution with `beamer`, `amsmath`, `booktabs`, `graphicx`.

---

## References

1. Black & Scholes (1973). *The Pricing of Options and Corporate Liabilities.* JPE 81(3).
2. Merton (1976). *Option pricing when underlying stock returns are discontinuous.* JFE 3(1–2).
3. Heston (1993). *A closed-form solution for options with stochastic volatility.* RFS 6(2).
4. Bates (1996). *Jumps and stochastic volatility.* RFS 9(1).
5. Carr & Madan (1999). *Option valuation using the fast Fourier transform.* J. Comp. Finance 2(4).
6. Kahl & Jäckel (2005). *Not-so-complex logarithms in the Heston model.* Wilmott 19(9).
7. **Gao & Hyndman (2025).** *Convolution-FFT for option pricing in the Heston model.* arXiv:2512.05326.
8. Dareiotis, Kumar & Sabanis (2016). *Tamed Euler for Lévy SDEs.* SIAM J. Numer. Anal. 54(3).
9. Kumar & Sabanis (2019). *Milstein with super-linear diffusion.* BIT 59(4).
10. Kumar & Kumar (2020). *Tamed Milstein for Markovian switching.* JCAM 377.
