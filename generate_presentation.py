"""
Generate PPTX presentation focused on Black–Scholes and Merton
Jump–Diffusion models for NIFTY 50, with strong emphasis on MLE
derivations and visual evidence of fat tails.
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

FIGURES_DIR = "figures/"
OUTPUT_FILE = "Stochastic_Option_Pricing_Presentation_v2.pptx"

DARK_BLUE = RGBColor(0x1B, 0x3A, 0x6B)
ORANGE = RGBColor(0xC8, 0x52, 0x1A)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BLACK = RGBColor(0x00, 0x00, 0x00)
ACCENT_GOLD = RGBColor(0xD4, 0xA0, 0x2F)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)


def add_background(slide, color=DARK_BLUE):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_textbox(
    slide,
    left,
    top,
    width,
    height,
    text,
    font_size=18,
    color=WHITE,
    bold=False,
    alignment=PP_ALIGN.LEFT,
    font_name="Calibri",
):
    tx = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tx.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font_name
    p.alignment = alignment
    return tx


def add_bullets(
    slide, left, top, width, height, bullets, font_size=16, color=BLACK, font_name="Calibri"
):
    tx = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tx.text_frame
    tf.word_wrap = True
    for i, line in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = line
        p.font.size = Pt(font_size)
        p.font.color.rgb = color
        p.font.name = font_name
        p.level = 0
    return tx


def add_image(slide, filename, left, top, width=None, height=None):
    path = os.path.join(FIGURES_DIR, filename)
    if not os.path.exists(path):
        return False
    kwargs = {}
    if width:
        kwargs["width"] = Inches(width)
    if height:
        kwargs["height"] = Inches(height)
    slide.shapes.add_picture(path, Inches(left), Inches(top), **kwargs)
    return True


def add_bar(slide, left, top, width, height, color=ORANGE):
    shp = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height)
    )
    shp.fill.solid()
    shp.fill.fore_color.rgb = color
    shp.line.fill.background()
    return shp


# Backwards‑compatibility helpers for the slide code below
def add_accent_bar(slide, left, top, width, height, color=ORANGE):
    return add_bar(slide, left, top, width, height, color)


def add_image_safe(slide, filename, left, top, width=None, height=None):
    return add_image(slide, filename, left, top, width, height)


def add_bullet_slide(slide, left, top, width, height, bullets, font_size=16, color=BLACK, font_name="Calibri"):
    return add_bullets(slide, left, top, width, height, bullets, font_size, color, font_name)


# ─────────────────────────────
# Slide 1 – Title
# ─────────────────────────────
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, DARK_BLUE)
add_bar(slide, 0, 0, 13.333, 0.15, ORANGE)
add_bar(slide, 0, 7.35, 13.333, 0.15, ORANGE)

add_textbox(
    slide,
    1.5,
    1.0,
    10,
    1.5,
    "COMPARATIVE STUDY OF STOCHASTIC MODELS\nFOR OPTION PRICING",
    font_size=36,
    color=WHITE,
    bold=True,
    alignment=PP_ALIGN.CENTER,
)
add_textbox(
    slide,
    1.5,
    2.8,
    10,
    0.6,
    "Focus: Black–Scholes vs Merton Jump–Diffusion on NIFTY 50",
    font_size=22,
    color=ACCENT_GOLD,
    alignment=PP_ALIGN.CENTER,
)
add_bar(slide, 4, 3.6, 5, 0.04, ORANGE)
add_textbox(
    slide,
    1.5,
    5.0,
    10,
    0.4,
    "Project Report | Academic Year 2025–26",
    font_size=16,
    color=RGBColor(0x99, 0xBB, 0xDD),
    alignment=PP_ALIGN.CENTER,
)
add_textbox(
    slide,
    1.5,
    5.6,
    10,
    0.4,
    "Under supervision of Prof. Chaman Kumar",
    font_size=18,
    color=WHITE,
    bold=True,
    alignment=PP_ALIGN.CENTER,
)
add_textbox(
    slide,
    1.5,
    6.2,
    10,
    0.4,
    "Department of Mathematics, IIT Roorkee",
    font_size=14,
    color=RGBColor(0x99, 0xBB, 0xDD),
    alignment=PP_ALIGN.CENTER,
)


# ─────────────────────────────
# Slide 2 – Outline
# ─────────────────────────────
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 7, 0.6, "Outline", font_size=32, color=DARK_BLUE, bold=True)
add_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

add_bullets(
    slide,
    0.8,
    1.4,
    5.7,
    5.0,
    [
        "1. Motivation & empirical stylised facts (Indian market)",
        "2. Data: NIFTY 50 (2018–2024)",
        "3. Black–Scholes model:",
        "   • GBM SDE and log‑price solution",
        "   • Maximum Likelihood Estimation (MLE)",
        "   • Closed‑form pricing & Monte Carlo",
    ],
    font_size=17,
)
add_bullets(
    slide,
    7.0,
    1.4,
    5.7,
    5.0,
    [
        "4. Merton Jump–Diffusion:",
        "   • SDE with jumps and log‑return derivation",
        "   • Gaussian‑mixture likelihood & MLE",
        "5. Evidence from NIFTY 50:",
        "   • Fat tails, VaR failures, volatility smile",
        "6. Model selection (LRT, AIC/BIC) & future work (Heston/Bates)",
    ],
    font_size=17,
)


# ═══════════════════════════════════════════════════════════════
# SLIDE 3: Motivation
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 8, 0.6, '1. Motivation & Background', font_size=32, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

bullets_motivation = [
    '• Indian derivatives market (NIFTY 50 options) is among the most liquid globally',
    '• Black-Scholes assumes constant volatility & continuous paths — violated in practice',
    '• Extreme events in India: COVID crash (−13% single day), IL&FS crisis,',
    '   election surprises — GBM cannot generate such dislocations',
    '• Project goal: rigorous comparison of increasingly sophisticated stochastic models',
    '   calibrated to NIFTY 50 data, benchmarked on empirical features',
    '',
    'Model Hierarchy (each relaxes a key BS assumption):',
    '   BS (constant σ) → MJD (+ jumps) → Heston (+ stochastic vol) → Bates (+ both)',
    '',
    'References: Black & Scholes (1973), Merton (1976), Heston (1993), Bates (1996)',
]
add_bullet_slide(slide, 0.8, 1.3, 11.5, 5.5, bullets_motivation, font_size=16, color=BLACK)


# ═══════════════════════════════════════════════════════════════
# SLIDE 4: Data Overview (with figure)
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 8, 0.6, '2. Data: NIFTY 50 (Jan 2018 – Dec 2024)', font_size=32, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

add_image_safe(slide, '01_data_overview.png', 0.5, 1.2, width=12.3)

bullets_data = [
    'Source: Yahoo Finance (^NSEI) via yfinance | Risk-free rate: RBI repo rate ≈ 6.5%',
    'Empirical return distribution shows negative skewness and excess kurtosis — fat tails that BS ignores',
]
add_bullet_slide(slide, 0.8, 6.3, 11, 1.2, bullets_data, font_size=13, color=RGBColor(0x44, 0x44, 0x44))


# ═══════════════════════════════════════════════════════════════
# SLIDE 5: Black-Scholes Theory
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 8, 0.6, '3. Black-Scholes Model — Theory', font_size=32, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

add_image_safe(slide, 'eq_bs_sde.png', 0.8, 1.2, width=6.0)
add_image_safe(slide, 'eq_ito_lemma.png', 0.8, 2.3, width=6.0)
add_image_safe(slide, 'eq_bs_solution.png', 0.8, 3.4, width=6.5)
add_image_safe(slide, 'eq_bs_logret.png', 0.8, 4.6, width=6.5)
add_bullet_slide(
    slide,
    7.0,
    1.4,
    5.5,
    4.8,
    [
        'GBM SDE → log‑price SDE via Itô’s lemma.',
        'Solution gives log‑normal terminal distribution; daily log‑returns Gaussian with mean (μ−σ²/2)Δt.',
        'These expressions feed directly into the MLE and Monte Carlo estimator.',
        '[BS73] Black & Scholes (1973), [Aït‑Sa02] Aït‑Sahalia (2002).',
    ],
    font_size=14,
    color=BLACK,
)


# ═══════════════════════════════════════════════════════════════
# SLIDE 6: Black-Scholes MLE
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 10, 0.6, '3. Black-Scholes — Maximum Likelihood Estimation', font_size=30, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

add_image_safe(slide, 'eq_bs_loglik.png', 0.7, 1.4, width=6.7)
add_image_safe(slide, 'eq_bs_mle_solution.png', 0.7, 2.8, width=6.7)
add_image_safe(slide, 'eq_bs_riskneutral.png', 0.7, 4.0, width=6.0)
add_bullet_slide(
    slide,
    7.2,
    1.5,
    5.5,
    4.7,
    [
        'Under discretely observed GBM, log‑returns are i.i.d. Gaussian ⇒ closed‑form MLE for (μ,σ).',
        'We still use numerical optimisation (Nelder–Mead) to match the framework used later for MJD.',
        'Risk‑neutral drift replaces μ by r_f, but the volatility estimate σ̂_MLE is carried into pricing.',
        'This slide is where you can explicitly mention numerical values of μ̂ and σ̂ from the code output.',
    ],
    font_size=14,
    color=BLACK,
)


# ═══════════════════════════════════════════════════════════════
# SLIDE 7: Merton JD — SDE & Log-Return Derivation
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 10, 0.6, '4. Merton Jump-Diffusion — SDE & Log-Return', font_size=30, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

add_image_safe(slide, 'eq_mjd_sde.png', 0.7, 1.3, width=6.7)
add_image_safe(slide, 'eq_mjd_jumps.png', 0.7, 2.4, width=6.7)
add_image_safe(slide, 'eq_mjd_ito.png', 0.7, 3.5, width=6.7)
add_image_safe(slide, 'eq_mjd_conditional.png', 0.7, 4.7, width=6.9)
add_bullet_slide(
    slide,
    7.1,
    1.5,
    5.4,
    4.7,
    [
        'Jump term S(t−)(e^J − 1)dN(t) superimposes compound Poisson jumps on GBM.',
        'Applying Itô for jump–diffusions gives d(ln S) with an extra J dN(t) term.',
        'Conditioning on N=k jumps → Gaussian with shifted mean/variance;',
        'marginalising over k gives a Poisson‑weighted Gaussian mixture.',
        '[Me76] Merton (1976), [CT04] Cont & Tankov (2004).',
    ],
    font_size=14,
    color=BLACK,
)


# ═══════════════════════════════════════════════════════════════
# SLIDE 8: Merton JD — Likelihood & Variance
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 10, 0.6, '4. Merton Jump-Diffusion — Likelihood & Moments', font_size=30, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

add_image_safe(slide, 'eq_mjd_density.png', 0.7, 1.4, width=6.9)
add_image_safe(slide, 'eq_mjd_loglik.png', 0.7, 2.8, width=6.9)
add_image_safe(slide, 'eq_mjd_variance.png', 0.7, 4.0, width=6.0)
add_image_safe(slide, 'eq_mjd_kurtosis.png', 0.7, 4.9, width=6.2)
add_bullet_slide(
    slide,
    7.1,
    1.5,
    5.4,
    4.7,
    [
        'Log‑likelihood is a sum of log Gaussian‑mixture densities evaluated at NIFTY log‑returns.',
        'We maximise ℓ(θ) numerically (L‑BFGS‑B) over θ = (μ, σ, λ, μ_J, σ_J).',
        'Variance decomposition highlights the role of λ(μ_J²+σ_J²) term in generating fat tails.',
        'Closed‑form excess kurtosis shows MJD can match empirical kurtosis where BS cannot.',
    ],
    font_size=14,
    color=BLACK,
)


# ═══════════════════════════════════════════════════════════════
# SLIDE 9: GBM vs MJD Paths (1‑year horizon)
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 10, 0.6, '4. GBM vs MJD — Sample Price Paths', font_size=32, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

add_image_safe(slide, '03_gbm_vs_mjd_paths.png', 0.3, 1.2, width=12.5)

path_text = [
    'Top row: GBM paths are smooth; MJD paths show red vertical lines and dots at jump times.',
    'Bottom‑left: single‑path decomposition — diffusion only vs diffusion+jumps; arrows show discrete jumps.',
    'Bottom‑right: histogram of jump sizes J ~ N(μ_J, σ_J²); most jumps are small but frequent (λ≈23/year).',
]
add_bullet_slide(slide, 0.8, 6.0, 11.5, 1.2, path_text, font_size=14, color=RGBColor(0x44, 0x44, 0x44))


# ═══════════════════════════════════════════════════════════════
# SLIDE 9: Tail Behavior
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 10, 0.6, '5. Tail Behavior — BS vs MJD vs Empirical', font_size=32, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

add_image_safe(slide, '04_tail_behavior_comparison.png', 0.3, 1.2, width=12.5)

tail_text = [
    'MJD\'s Gaussian mixture captures fat tails; BS (pure Gaussian) dramatically underestimates extreme returns.',
    'Excess kurtosis: BS = 0 (by definition), MJD = 3λ(μ_J² + σ_J²)² / σ⁴ > 0, Empirical NIFTY >> 0',
]
add_bullet_slide(slide, 0.8, 6.0, 11.5, 1.2, tail_text, font_size=14, color=RGBColor(0x44, 0x44, 0x44))


# ═══════════════════════════════════════════════════════════════
# SLIDE 10: QQ Plots
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 10, 0.6, '5. QQ Plots — Quantile Diagnostic', font_size=32, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

add_image_safe(slide, '05_qq_plots.png', 0.3, 1.2, width=12.5)

qq_text = [
    'QQ vs Normal: heavy-tailed departure from 45° line at extremes → BS misfit.',
    'QQ vs MJD: better alignment in tails → MJD captures empirical quantile structure of NIFTY 50.',
]
add_bullet_slide(slide, 0.8, 6.0, 11.5, 1.2, qq_text, font_size=14, color=RGBColor(0x44, 0x44, 0x44))


# ═══════════════════════════════════════════════════════════════
# SLIDE 11: Statistical Model Selection
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 10, 0.6, '6. Statistical Model Selection', font_size=32, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

add_image_safe(slide, '06_model_comparison_criteria.png', 0.3, 1.2, width=12.5)

stat_text = [
    'Likelihood Ratio Test:  LRT = 2[ℓ(MJD) − ℓ(BS)] ~ χ²(3) under H₀: λ=0',
    'AIC = 2k − 2ℓ,  BIC = k·ln(n) − 2ℓ  — penalize complexity; MJD overcomes penalty',
    '[Aït-Ja07] Aït-Sahalia & Jacod (2007). Annals of Statistics, 35(1), 355-392.',
]
add_bullet_slide(slide, 0.8, 5.8, 11.5, 1.5, stat_text, font_size=14, color=RGBColor(0x44, 0x44, 0x44))


# ═══════════════════════════════════════════════════════════════
# SLIDE 12: Implied Volatility Smile
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 10, 0.6, '5. Implied Volatility Smile', font_size=32, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

add_image_safe(slide, '07_implied_volatility_smile.png', 0.3, 1.2, width=12.5)

smile_text = [
    'BS produces flat IV by construction; MJD generates the "smile" / skew observed in NIFTY option markets.',
    'This is the classical smile inconsistency — documented by Rubinstein (1994) [Ru94].',
]
add_bullet_slide(slide, 0.8, 6.0, 11.5, 1.2, smile_text, font_size=14, color=RGBColor(0x44, 0x44, 0x44))


# ═══════════════════════════════════════════════════════════════
# SLIDE 13: Parameter Sensitivity
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 10, 0.6, '5. MJD Parameter Sensitivity', font_size=32, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

add_image_safe(slide, '08_parameter_sensitivity_heatmap.png', 1.0, 1.2, width=11)

sens_text = [
    'Non-linear interaction between λ (jump intensity) and σ_J (jump volatility) — unavailable in BS world.',
    'Higher λ and σ_J → substantially higher option prices, reflecting crash risk premium.',
]
add_bullet_slide(slide, 0.8, 6.3, 11.5, 1, sens_text, font_size=14, color=RGBColor(0x44, 0x44, 0x44))


# ═══════════════════════════════════════════════════════════════
# SLIDE 14: Monte Carlo Convergence
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 10, 0.6, '5. Monte Carlo Convergence', font_size=32, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

add_image_safe(slide, '09_mc_convergence.png', 0.3, 1.2, width=12.5)

mc_text = [
    'MC price → closed-form as N→∞, confirming 1/√N convergence rate (CLT).',
    'Standard error comparison validates implementation correctness [Glasserman (2003)].',
]
add_bullet_slide(slide, 0.8, 6.0, 11.5, 1.2, mc_text, font_size=14, color=RGBColor(0x44, 0x44, 0x44))


# ═══════════════════════════════════════════════════════════════
# SLIDE 15: Event Analysis
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 10, 0.6, '5. Indian Market Event Analysis', font_size=32, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

add_image_safe(slide, '10_event_analysis.png', 0.3, 1.2, width=12.5)

event_text = [
    'Key events: IL&FS crisis (Sep 2018), COVID crash (Mar 2020), Russia-Ukraine (Feb 2022), Election (Jun 2024)',
    'BS assigns near-zero probability to such moves; MJD jump parameters capture this crash risk.',
]
add_bullet_slide(slide, 0.8, 6.1, 11.5, 1.2, event_text, font_size=14, color=RGBColor(0x44, 0x44, 0x44))


# ═══════════════════════════════════════════════════════════════
# SLIDE 16: Tail Risk Probability
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 10, 0.6, '5. Tail Risk: Crash Probability', font_size=32, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

add_image_safe(slide, '11_tail_risk_probability.png', 0.3, 1.2, width=12.5)

tail_risk = [
    'BS vastly underestimates the probability of large daily losses — a critical failure for risk management.',
    'MJD provides realistic tail probabilities closer to empirical NIFTY returns, essential under SEBI regulations.',
]
add_bullet_slide(slide, 0.8, 6.0, 11.5, 1.2, tail_risk, font_size=14, color=RGBColor(0x44, 0x44, 0x44))


# ═══════════════════════════════════════════════════════════════
# SLIDE 17: VaR Backtesting
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 10, 0.6, '5. Value-at-Risk Backtesting', font_size=32, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

add_image_safe(slide, '12_var_backtesting.png', 0.3, 1.2, width=12.5)

var_text = [
    '1% VaR breaches under BS Gaussian model exceed expected rate — BS fails Kupiec test.',
    'Empirical VaR (from historical quantiles, analogous to MJD) stays closer to 1% expected rate.',
]
add_bullet_slide(slide, 0.8, 6.0, 11.5, 1.2, var_text, font_size=14, color=RGBColor(0x44, 0x44, 0x44))


# ═══════════════════════════════════════════════════════════════
# SLIDE 18: Variance Reduction
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 10, 0.6, '5. Variance Reduction Techniques', font_size=32, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

add_image_safe(slide, '13_variance_reduction.png', 1.5, 1.2, width=10)

vr_text = [
    'Antithetic variates: pair (Z, −Z) → roughly halves variance for smooth payoffs.',
    'Control variate: use BS closed-form as control for MJD MC → 30-70% SE reduction near ATM.',
    '[Gl03] Glasserman, P. (2003). Monte Carlo Methods in Financial Engineering. Springer.',
]
add_bullet_slide(slide, 0.8, 5.8, 11.5, 1.5, vr_text, font_size=14, color=RGBColor(0x44, 0x44, 0x44))


# ═══════════════════════════════════════════════════════════════
# SLIDE 19: Heston Model — End Term Proposal
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 10, 0.6, '7. End-Term: Heston Stochastic Volatility', font_size=32, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

heston_text = [
    'Heston (1993) — variance v(t) follows CIR process:',
    '   dS(t) = r_f S(t) dt + √v(t) S(t) dW_S^Q(t)',
    '   dv(t) = κ[θ − v(t)] dt + ξ √v(t) dW_v^Q(t)',
    '   Corr(dW_S, dW_v) = ρ dt    (leverage effect: ρ < 0)',
    '',
    'Parameters: κ (mean-reversion), θ (long-run var), ξ (vol-of-vol), ρ (correlation), v₀',
    'Feller condition: 2κθ > ξ² ensures v(t) > 0',
    '',
    'Produces full implied volatility smile & term structure',
    'Semi-analytic pricing via Fourier inversion [Carr-Madan (1999)]',
    '',
    '[He93] Heston, S.L. (1993). Review of Financial Studies, 6(2), 327-343.',
]
add_bullet_slide(slide, 0.8, 1.2, 5.5, 6, heston_text, font_size=14, color=BLACK)
add_image_safe(slide, '14_heston_paths.png', 6.5, 1.2, width=6.5)


# ═══════════════════════════════════════════════════════════════
# SLIDE 20: Heston IV Surface
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 10, 0.6, '7. Heston Implied Volatility Surface', font_size=32, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

add_image_safe(slide, '15_heston_iv_surface.png', 0.3, 1.2, width=12.5)

iv_surface_text = [
    'Stochastic volatility produces realistic IV smile & term structure — flat BS surface is a special case.',
    'Negative ρ (leverage effect) creates the asymmetric skew observed in NIFTY index options.',
]
add_bullet_slide(slide, 0.8, 6.0, 11.5, 1.2, iv_surface_text, font_size=14, color=RGBColor(0x44, 0x44, 0x44))


# ═══════════════════════════════════════════════════════════════
# SLIDE 21: Connection to Supervisor's Research
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 10, 0.6, '8. Connection to Supervisor\'s Research', font_size=32, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

supervisor_text = [
    'The CIR variance process √v(t) has non-globally-Lipschitz coefficients.',
    'Standard Euler-Maruyama can produce negative variance — numerical instability.',
    '',
    'Prof. Chaman Kumar\'s research directly addresses this:',
    '',
    '  • Tamed Euler scheme for Lévy-driven SDEs',
    '     [DKS16] Dareiotis, Kumar & Sabanis (2016). SIAM J. Numer. Anal., 54(3). IF: 2.712',
    '',
    '  • Explicit tamed Milstein for super-linear diffusion coefficients',
    '     [KS17a] Kumar & Sabanis (2017). Electronic J. Probability, 22, 1-19. IF: 1.123',
    '',
    '  • Milstein scheme for Lévy SDEs with super-linear coefficients',
    '     [K20] Kumar (2020). DCDS-B. DOI: 10.3934/dcdsb.2020167',
    '',
    '  • Tamed Milstein for SDEs with Markovian switching',
    '     [KK20] Kumar & Kumar (2020). J. Comp. Appl. Math., 377. IF: 2.037',
    '',
    '  • McKean-Vlasov equations — future scope for mean-field option markets',
    '     [KNRS20] Kumar, Neelima, Reisinger & Stockinger (2020). arXiv:2006.00463',
]
add_bullet_slide(slide, 0.8, 1.2, 11.5, 6, supervisor_text, font_size=14, color=BLACK)


# ═══════════════════════════════════════════════════════════════
# SLIDE 22: Tamed Euler — Numerical Results
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 10, 0.6, '8. Tamed Euler — Numerical Comparison', font_size=32, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

add_image_safe(slide, '16_tamed_euler_convergence.png', 0.3, 1.2, width=12.5)

tamed_text = [
    'Standard Euler produces negative variance excursions; Tamed Euler (DKS16) maintains positivity.',
    'Convergence rate: slope ≈ 0.5 (Euler) confirmed — matches theoretical rates from cited papers.',
]
add_bullet_slide(slide, 0.8, 6.0, 11.5, 1.2, tamed_text, font_size=14, color=RGBColor(0x44, 0x44, 0x44))


# ═══════════════════════════════════════════════════════════════
# SLIDE 23: Full Model Comparison
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 10, 0.6, '5. Option Prices — All Models Compared', font_size=32, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

add_image_safe(slide, '17_option_prices_all_models.png', 0.3, 1.2, width=12.5)

all_models_text = [
    'MJD prices diverge from BS for OTM options (fat tails); Heston captures smile-driven deviation.',
    'Bates (Heston + Jumps) will combine both effects — the most flexible model in this study.',
]
add_bullet_slide(slide, 0.8, 6.0, 11.5, 1.2, all_models_text, font_size=14, color=RGBColor(0x44, 0x44, 0x44))


# ═══════════════════════════════════════════════════════════════
# SLIDE 24: Summary Dashboard
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 10, 0.6, 'Summary — Comprehensive Comparison', font_size=32, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

add_image_safe(slide, '18_summary_comparison.png', 0.3, 1.2, width=12.5)


# ═══════════════════════════════════════════════════════════════
# SLIDE 25: Model Comparison Table
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 10, 0.6, 'Model Comparison Summary', font_size=32, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

table_data = [
    ['Feature', 'Black-Scholes', 'Merton JD', 'Heston', 'Bates'],
    ['SDE type', 'GBM', 'GBM + Poisson', 'GBM + CIR vol', 'GBM + CIR + Jumps'],
    ['Parameters', '2', '5', '5', '8'],
    ['Return dist.', 'Gaussian', 'Mixture', 'Non-Gaussian', 'Non-Gaussian'],
    ['Closed-form', 'Yes', 'Series approx.', 'Fourier', 'Fourier'],
    ['Vol smile', 'No (flat IV)', 'Partial', 'Full smile', 'Full smile'],
    ['Jumps', 'No', 'Yes', 'No', 'Yes'],
    ['Extreme events', 'Poor', 'Good', 'Moderate', 'Best'],
    ['Calibration', 'Analytic MLE', 'Numerical MLE', 'Option chain', 'Option chain'],
]

rows, cols = len(table_data), len(table_data[0])
table = slide.shapes.add_table(rows, cols, Inches(0.5), Inches(1.3), Inches(12.3), Inches(5)).table

for col_idx in range(cols):
    table.columns[col_idx].width = Inches(12.3 / cols)

for row_idx in range(rows):
    for col_idx in range(cols):
        cell = table.cell(row_idx, col_idx)
        cell.text = table_data[row_idx][col_idx]
        for paragraph in cell.text_frame.paragraphs:
            paragraph.font.size = Pt(13)
            paragraph.font.name = 'Calibri'
            paragraph.alignment = PP_ALIGN.CENTER
            if row_idx == 0:
                paragraph.font.bold = True
                paragraph.font.color.rgb = WHITE
            else:
                paragraph.font.color.rgb = BLACK
        
        if row_idx == 0:
            cell.fill.solid()
            cell.fill.fore_color.rgb = DARK_BLUE
        elif row_idx % 2 == 0:
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(0xE8, 0xEC, 0xF1)


# ═══════════════════════════════════════════════════════════════
# SLIDE 26: End-Term Plan
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 10, 0.6, 'End-Term Evaluation Plan', font_size=32, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

endterm_text = [
    'Planned Deliverables:',
    '',
    '1. Full Heston calibration to NIFTY option chain (3 maturities × 7 strikes)',
    '',
    '2. Bates model (Heston + Jumps) — 8-parameter calibration',
    '',
    '3. Comprehensive 4-model comparison:',
    '     • Option pricing RMSE on market prices',
    '     • Implied volatility smile fit across strikes & maturities',
    '     • 1% VaR backtesting on 2023-24 NIFTY data',
    '',
    '4. Sensitivity analysis: Greeks (Δ, Γ, V) under each model',
    '',
    '5. Statistical model selection: LRT (nested), AIC/BIC (non-nested)',
    '',
    '6. Numerical methods: Tamed Euler vs Standard Euler convergence',
    '     for CIR process — connecting to Prof. Kumar\'s research',
    '',
    '7. Future scope: McKean-Vlasov / mean-field game formulation',
    '     for multi-agent option markets [KNRS20]',
]
add_bullet_slide(slide, 0.8, 1.3, 11.5, 6, endterm_text, font_size=15, color=BLACK)


# ═══════════════════════════════════════════════════════════════
# SLIDE 27: References
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, WHITE)
add_accent_bar(slide, 0, 0, 13.333, 0.08, DARK_BLUE)
add_textbox(slide, 0.8, 0.3, 10, 0.6, 'References', font_size=32, color=DARK_BLUE, bold=True)
add_accent_bar(slide, 0.8, 1.0, 3, 0.04, ORANGE)

refs = [
    'Foundational Models:',
    '  [BS73] Black & Scholes (1973). J. Political Economy, 81(3), 637-654.',
    '  [Me76] Merton (1976). J. Financial Economics, 3(1-2), 125-144.',
    '  [He93] Heston (1993). Review of Financial Studies, 6(2), 327-343.',
    '  [Ba96] Bates (1996). Review of Financial Studies, 9(1), 69-107.',
    '',
    'Statistical Methods:',
    '  [Aït-Sa02] Aït-Sahalia (2002). Econometrica, 70(1), 223-262.',
    '  [Aït-Ja07] Aït-Sahalia & Jacod (2007). Annals of Statistics, 35(1), 355-392.',
    '  [CT04] Cont & Tankov (2004). Financial Modelling with Jump Processes. CRC.',
    '  [Gl03] Glasserman (2003). MC Methods in Financial Engineering. Springer.',
    '',
    'Supervisor\'s Research (Numerical SDE Methods):',
    '  [DKS16] Dareiotis, Kumar & Sabanis (2016). SIAM J. Numer. Anal., 54(3).',
    '  [KS17] Kumar & Sabanis (2017). Electr. J. Probability, 22, 1-19.',
    '  [KK20] Kumar & Kumar (2020). J. Comp. Appl. Math., 377, 112917.',
    '  [K20] Kumar (2020). DCDS-B. DOI: 10.3934/dcdsb.2020167.',
    '  [KNRS20] Kumar, Neelima, Reisinger & Stockinger (2020). arXiv:2006.00463.',
]
add_bullet_slide(slide, 0.8, 1.2, 11.5, 6, refs, font_size=12, color=BLACK)


# ═══════════════════════════════════════════════════════════════
# SLIDE 28: Thank You
# ═══════════════════════════════════════════════════════════════
slide = prs.slides.add_slide(prs.slide_layouts[6])
add_background(slide, DARK_BLUE)
add_accent_bar(slide, 0, 0, 13.333, 0.15, ORANGE)
add_accent_bar(slide, 0, 7.35, 13.333, 0.15, ORANGE)

add_textbox(slide, 1.5, 2.0, 10, 1,
            'Thank You',
            font_size=48, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
add_accent_bar(slide, 5, 3.2, 3, 0.04, ORANGE)
add_textbox(slide, 1.5, 3.5, 10, 0.6,
            'Comparative Study of Stochastic Models for Option Pricing\nin the Indian Stock Market',
            font_size=20, color=RGBColor(0xAA, 0xCC, 0xEE), alignment=PP_ALIGN.CENTER)
add_textbox(slide, 1.5, 4.5, 10, 0.4,
            'Under the supervision of Prof. Chaman Kumar',
            font_size=18, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
add_textbox(slide, 1.5, 5.2, 10, 0.4,
            'Department of Mathematics, IIT Roorkee',
            font_size=14, color=RGBColor(0x99, 0xBB, 0xDD), alignment=PP_ALIGN.CENTER)
add_textbox(slide, 1.5, 5.8, 10, 0.4,
            'Questions?',
            font_size=24, color=ACCENT_GOLD, bold=True, alignment=PP_ALIGN.CENTER)


prs.save(OUTPUT_FILE)
print(f'Presentation saved to: {OUTPUT_FILE}')
print(f'Total slides: {len(prs.slides)}')
