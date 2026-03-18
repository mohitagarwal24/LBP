"""
PPTX: Stochastic Option Pricing on NIFTY 50
Focus: BS vs MJD OPTION PRICES (not stock returns)
"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

FIG = "figures/"
OUT = "Stochastic_Option_Pricing_Presentation_v3.pptx"

DB = RGBColor(0x1B,0x3A,0x6B); OR = RGBColor(0xC8,0x52,0x1A)
WH = RGBColor(0xFF,0xFF,0xFF); BK = RGBColor(0x00,0x00,0x00)
GD = RGBColor(0xD4,0xA0,0x2F); GY = RGBColor(0x44,0x44,0x44)

prs = Presentation()
prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)

def bg(s, c=DB):
    f=s.background.fill; f.solid(); f.fore_color.rgb=c
def bar(s,l,t,w,h,c=OR):
    sh=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(l),Inches(t),Inches(w),Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb=c; sh.line.fill.background()
def tx(s,l,t,w,h,txt,fs=18,c=WH,b=False,a=PP_ALIGN.LEFT):
    bx=s.shapes.add_textbox(Inches(l),Inches(t),Inches(w),Inches(h))
    p=bx.text_frame.paragraphs[0]; bx.text_frame.word_wrap=True
    p.text=txt; p.font.size=Pt(fs); p.font.color.rgb=c; p.font.bold=b; p.font.name='Calibri'; p.alignment=a
def bl(s,l,t,w,h,items,fs=16,c=BK):
    bx=s.shapes.add_textbox(Inches(l),Inches(t),Inches(w),Inches(h))
    tf=bx.text_frame; tf.word_wrap=True
    for i,line in enumerate(items):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.text=line; p.font.size=Pt(fs); p.font.color.rgb=c; p.font.name='Calibri'
def img(s,f,l,t,w=None,h=None,width=None,height=None):
    p=os.path.join(FIG,f)
    if not os.path.exists(p): return
    ww=w or width; hh=h or height
    kw={}
    if ww: kw['width']=Inches(ww)
    if hh: kw['height']=Inches(hh)
    s.shapes.add_picture(p,Inches(l),Inches(t),**kw)

# ── Slide 1: Title ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
bar(s,0,0,13.333,.15); bar(s,0,7.35,13.333,.15)
tx(s,1.5,1,10,1.5,'COMPARATIVE STUDY OF STOCHASTIC MODELS\nFOR OPTION PRICING',36,WH,True,PP_ALIGN.CENTER)
tx(s,1.5,2.8,10,.6,'Black–Scholes vs Merton Jump–Diffusion on NIFTY 50 Options',22,GD,False,PP_ALIGN.CENTER)
bar(s,4,3.6,5,.04)
tx(s,1.5,5,10,.4,'Mid-Term Evaluation | Academic Year 2025–26',16,RGBColor(0x99,0xBB,0xDD),False,PP_ALIGN.CENTER)
tx(s,1.5,5.6,10,.4,'Under supervision of Prof. Chaman Kumar',18,WH,True,PP_ALIGN.CENTER)
tx(s,1.5,6.2,10,.4,'Department of Mathematics, IIT Roorkee',14,RGBColor(0x99,0xBB,0xDD),False,PP_ALIGN.CENTER)

# ── Slide 2: Outline ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s,WH); bar(s,0,0,13.333,.08,DB)
tx(s,.8,.3,7,.6,'Outline',32,DB,True); bar(s,.8,1,.3,.04)
bl(s,.8,1.4,5.5,5,[
    '1. Motivation: why option pricing needs better models',
    '2. Data & Model Calibration (MLE on NIFTY returns)',
    '3. Black–Scholes option pricing:',
    '   • GBM SDE → MLE → closed-form call/put → MC',
    '4. Merton Jump–Diffusion option pricing:',
    '   • SDE with jumps → MLE → MC pricing',
],17)
bl(s,7,1.4,5.5,5,[
    '5. Option price comparison:',
    '   • Calls & puts across strikes',
    '   • OTM puts: where BS fails catastrophically',
    '   • Implied volatility smile',
    '   • Option pricing at crisis events',
    '6. Statistical model selection (LRT, AIC/BIC)',
    '7. Future work: Heston & Bates models',
],17)

# ── Slide 3: Motivation ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s,WH); bar(s,0,0,13.333,.08,DB)
tx(s,.8,.3,10,.6,'1. Why Option Pricing Needs Better Models',30,DB,True); bar(s,.8,1,.3,.04)
bl(s,.8,1.3,11.5,5.5,[
    '• NIFTY 50 index options are among the most actively traded contracts globally',
    '• Practitioners use Black-Scholes to price & hedge — but it systematically misprices:',
    '   – Deep out-of-the-money (OTM) PUTS are underpriced → inadequate crash protection',
    '   – The "volatility smile" in market data contradicts BS flat-IV assumption',
    '',
    '• Root cause: BS assumes Gaussian log-returns (thin tails + constant volatility)',
    '  → assigns near-zero probability to large moves like COVID −13% day, election −8% gap',
    '',
    '• This project: compare BS vs Merton Jump-Diffusion option prices on NIFTY 50',
    '  → calibrate both models to historical data, then price European calls & puts',
    '  → quantify how much BS underprices crash protection',
    '',
    '• References: Black & Scholes (1973), Merton (1976)',
],15)

# ── Slide 4: Calibration Data ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s,WH); bar(s,0,0,13.333,.08,DB)
tx(s,.8,.3,10,.6,'2. Calibration Data: NIFTY 50 (2018–2024)',30,DB,True); bar(s,.8,1,.3,.04)
img(s,'01_calibration_data.png',.3,1.2,width=12.3)
bl(s,.8,6.3,11,1.2,[
    'NIFTY daily returns used to estimate model parameters via MLE. Left-tail zoom shows fat tails → BS underprices OTM puts.',
    'Source: Yahoo Finance (^NSEI). Risk-free rate: RBI repo ≈ 6.5%',
],13,GY)

# ── Slide 5: BS SDE & Itô ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s,WH); bar(s,0,0,13.333,.08,DB)
tx(s,.8,.3,10,.6,'3. Black–Scholes: GBM SDE & Log-Price',30,DB,True); bar(s,.8,1,.3,.04)
img(s,'eq_bs_sde.png',.7,1.2,width=6)
img(s,'eq_ito_lemma.png',.7,2.3,width=6)
img(s,'eq_bs_solution.png',.7,3.4,width=6.5)
img(s,'eq_bs_logret.png',.7,4.6,width=6.5)
bl(s,7,1.4,5.5,5,[
    'GBM SDE → Itô\'s lemma gives the log-price SDE.',
    'Integrating gives the log-normal terminal distribution S(T).',
    'Daily log-returns are i.i.d. Gaussian — this is the model we fit via MLE.',
    'The estimated σ̂ is then plugged into the BS option pricing formula.',
],14)

# ── Slide 6: BS MLE ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s,WH); bar(s,0,0,13.333,.08,DB)
tx(s,.8,.3,10,.6,'3. Black–Scholes: Maximum Likelihood Estimation',30,DB,True); bar(s,.8,1,.3,.04)
img(s,'eq_bs_loglik.png',.7,1.4,width=6.7)
img(s,'eq_bs_mle_solution.png',.7,2.8,width=6.7)
bl(s,7.2,1.5,5.5,3,[
    'MLE on n daily NIFTY returns. Closed-form for σ̂² and μ̂ exists for GBM.',
    'We use numerical optimisation (Nelder-Mead) for consistency with MJD estimation.',
    'The key output for option pricing is σ̂ ≈ 17.8% (annualised).',
],14)
img(s,'eq_bs_riskneutral.png',.7,4.2,width=6)
bl(s,7.2,4.2,5.5,2,[
    'For pricing: switch to risk-neutral measure Q (Girsanov). Drift becomes r_f, but σ stays the same.',
],14)

# ── Slide 7: BS Option Pricing Formula ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s,WH); bar(s,0,0,13.333,.08,DB)
tx(s,.8,.3,10,.6,'3. Black–Scholes: Closed-Form Option Prices',30,DB,True); bar(s,.8,1,.3,.04)
img(s,'eq_bs_call.png',.7,1.4,width=6)
img(s,'eq_bs_d1d2.png',.7,2.5,width=6.5)
img(s,'eq_bs_mc.png',.7,3.7,width=6.5)
bl(s,7.2,1.4,5.5,4,[
    'The celebrated BS formula gives exact European call (and put via put-call parity).',
    'd₁ and d₂ encode moneyness, time to expiry, and volatility.',
    'Monte Carlo estimator validates the closed-form: simulate N paths under Q, average discounted payoffs.',
    'SE shrinks as 1/√N (CLT). [Glasserman, 2003]',
],14)
bl(s,.7,5,11,1.5,[
    'Key limitation: σ is CONSTANT across all strikes and maturities → flat implied volatility surface.',
    '→ In reality, NIFTY options trade with a pronounced volatility smile/skew. BS cannot reproduce this.',
],14,RGBColor(0xAA,0x00,0x00))

# ── Slide 8: MJD SDE ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s,WH); bar(s,0,0,13.333,.08,DB)
tx(s,.8,.3,10,.6,'4. Merton Jump-Diffusion: SDE & Log-Return',30,DB,True); bar(s,.8,1,.3,.04)
img(s,'eq_mjd_sde.png',.7,1.3,width=6.7)
img(s,'eq_mjd_jumps.png',.7,2.4,width=6.7)
img(s,'eq_mjd_ito.png',.7,3.5,width=6.7)
img(s,'eq_mjd_conditional.png',.7,4.7,width=6.9)
bl(s,7.1,1.5,5.4,4.7,[
    'Superimposes compound Poisson jumps on GBM — captures sudden dislocations.',
    'Itô for jump-diffusions: extra J dN(t) term in log-price.',
    'Conditional on k jumps: Gaussian with shifted mean & inflated variance.',
    'This directly explains why MJD produces different option prices from BS.',
    '[Me76] Merton (1976), [CT04] Cont & Tankov (2004).',
],14)

# ── Slide 9: MJD Likelihood & Moments ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s,WH); bar(s,0,0,13.333,.08,DB)
tx(s,.8,.3,10,.6,'4. MJD: Likelihood & Excess Kurtosis',30,DB,True); bar(s,.8,1,.3,.04)
img(s,'eq_mjd_density.png',.7,1.4,width=6.9)
img(s,'eq_mjd_loglik.png',.7,2.8,width=6.9)
img(s,'eq_mjd_variance.png',.7,4,width=6)
img(s,'eq_mjd_kurtosis.png',.7,4.9,width=6.2)
bl(s,7.1,1.5,5.4,4.7,[
    'Log-likelihood = sum of log Gaussian-mixture densities.',
    'Maximised numerically (L-BFGS-B) over θ = (μ,σ,λ,μ_J,σ_J).',
    'Variance decomposition: jump component λ(μ_J²+σ_J²) adds kurtosis.',
    'Excess kurtosis > 0 → fatter tails → higher OTM option prices.',
    'This is the precise mechanism by which MJD prices puts higher than BS.',
],14)

# ── Slide 10: ATM Option Prices ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s,WH); bar(s,0,0,13.333,.08,DB)
tx(s,.8,.3,10,.6,'5. ATM Option Prices: BS vs MJD',30,DB,True); bar(s,.8,1,.3,.04)
img(s,'02_atm_option_prices.png',.3,1.2,width=12.5)
bl(s,.8,6,11.5,1.2,[
    'Left: ATM call & put prices. Centre: terminal S(T) distributions — MJD has heavier tails.',
    'Right: put payoff distribution — MJD assigns more weight to large payoffs (crash scenarios).',
],13,GY)

# ── Slide 11: Options across strikes ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s,WH); bar(s,0,0,13.333,.08,DB)
tx(s,.8,.3,10,.6,'5. Option Prices Across Strikes',30,DB,True); bar(s,.8,1,.3,.04)
img(s,'03_option_prices_across_strikes.png',.3,1.2,width=12.5)
bl(s,.8,6.2,11.5,1,[
    'MJD puts are consistently more expensive than BS puts, especially for OTM puts (K/S₀ < 1).',
    'Bottom-right: percentage difference shows BS can underprice OTM puts by 20-100%+.',
],13,GY)

# ── Slide 12: IV Smile ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s,WH); bar(s,0,0,13.333,.08,DB)
tx(s,.8,.3,10,.6,'5. Implied Volatility Smile',30,DB,True); bar(s,.8,1,.3,.04)
img(s,'04_iv_smile.png',.3,1.2,width=12.5)
bl(s,.8,6,11.5,1.2,[
    'BS-implied volatility backed out from MJD option prices. MJD produces the smile that market data shows.',
    'BS can only produce a flat line — the "smile inconsistency" [Rubinstein, 1994].',
],13,GY)

# ── Slide 13: OTM Puts ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s,WH); bar(s,0,0,13.333,.08,DB)
tx(s,.8,.3,10,.6,'5. OTM Put Pricing — Where BS Fails Most',30,DB,True); bar(s,.8,1,.3,.04)
img(s,'06_otm_put_pricing.png',.3,1.2,width=12.5)
bl(s,.8,6,11.5,1.2,[
    'Deep OTM puts: MJD price can be 2–5× the BS price. This is crash protection that BS undervalues.',
    'For a NIFTY options trader, using BS means systematically selling insurance too cheaply.',
],13,GY)

# ── Slide 14: Option term structure ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s,WH); bar(s,0,0,13.333,.08,DB)
tx(s,.8,.3,10,.6,'5. Option Prices Across Maturities',30,DB,True); bar(s,.8,1,.3,.04)
img(s,'05_option_term_structure.png',.3,1.2,width=12.5)
bl(s,.8,6,11.5,1.2,[
    'MJD puts are consistently more expensive than BS across all maturities — the jump risk premium persists.',
    'Difference is largest for shorter maturities where individual jumps have more impact.',
],13,GY)

# ── Slide 15: Sensitivity heatmap ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s,WH); bar(s,0,0,13.333,.08,DB)
tx(s,.8,.3,10,.6,'5. Option Price Sensitivity to Jump Parameters',30,DB,True); bar(s,.8,1,.3,.04)
img(s,'07_option_sensitivity_heatmap.png',.3,1.2,width=12.5)
bl(s,.8,6.2,11.5,1,[
    'Non-linear interaction between λ and σ_J on option prices. Higher jump intensity and vol → higher option prices.',
],13,GY)

# ── Slide 16: MC Convergence ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s,WH); bar(s,0,0,13.333,.08,DB)
tx(s,.8,.3,10,.6,'5. Monte Carlo Convergence (Option Prices)',30,DB,True); bar(s,.8,1,.3,.04)
img(s,'08_mc_convergence_options.png',.3,1.2,width=12.5)
bl(s,.8,6,11.5,1.2,[
    'BS MC converges to closed-form; MJD converges to its own value. SE ∝ 1/√N confirmed.',
    'Validates both implementations and the theoretical pricing framework [Glasserman, 2003].',
],13,GY)

# ── Slide 17: Event option pricing ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s,WH); bar(s,0,0,13.333,.08,DB)
tx(s,.8,.3,10,.6,'5. Option Pricing at Indian Market Crises',30,DB,True); bar(s,.8,1,.3,.04)
img(s,'11_event_option_pricing.png',.3,1.2,width=12.5)
bl(s,.8,6.2,11.5,1,[
    'At each crisis: BS put price vs MJD put price vs realised payoff. BS consistently underprices — positive error = underpricing.',
],13,GY)

# ── Slide 18: Variance reduction ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s,WH); bar(s,0,0,13.333,.08,DB)
tx(s,.8,.3,10,.6,'5. Variance Reduction for Option Pricing MC',30,DB,True); bar(s,.8,1,.3,.04)
img(s,'09_variance_reduction_options.png',1.5,1.2,width=10)
bl(s,.8,5.5,11.5,1.5,[
    'Antithetic variates and control variates reduce MC standard error for option prices.',
    'Control variate (using BS closed-form as control for MJD MC) gives ~50% SE reduction.',
    '[Glasserman, 2003].',
],14)

# ── Slide 19: Model Selection ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s,WH); bar(s,0,0,13.333,.08,DB)
tx(s,.8,.3,10,.6,'6. Statistical Model Selection',30,DB,True); bar(s,.8,1,.3,.04)
img(s,'10_model_selection.png',.3,1.2,width=12.5)
img(s,'eq_lrt.png',.7,5.5,width=6)
img(s,'eq_aic_bic.png',7,5.5,width=5.5)
bl(s,.8,6.5,11.5,.8,[
    'LRT p-value ≈ 0 → jumps are overwhelmingly significant. AIC & BIC both prefer MJD despite penalty for 3 extra parameters.',
],13,GY)

# ── Slide 20: GBM vs MJD paths ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s,WH); bar(s,0,0,13.333,.08,DB)
tx(s,.8,.3,10,.6,'Underlying Paths: How Jumps Affect S(T)',30,DB,True); bar(s,.8,1,.3,.04)
img(s,'12_gbm_vs_mjd_paths.png',.3,1.2,width=12.5)
bl(s,.8,6,11.5,1.2,[
    'GBM paths are smooth; MJD paths have jumps (red dots). Jump events change the terminal distribution S(T),',
    'which is what determines option payoffs max(S(T)−K, 0) or max(K−S(T), 0).',
],13,GY)

# ── Slide 21: QQ ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s,WH); bar(s,0,0,13.333,.08,DB)
tx(s,.8,.3,10,.6,'Return Diagnostics (Motivation for MJD)',30,DB,True); bar(s,.8,1,.3,.04)
img(s,'13_qq_plots.png',.3,1.2,width=12.5)
bl(s,.8,6,11.5,1.2,[
    'QQ vs Normal: heavy-tailed departures → BS option mispricing. QQ vs MJD: better tail fit.',
],13,GY)

# ── Slide 22: Summary ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s,WH); bar(s,0,0,13.333,.08,DB)
tx(s,.8,.3,10,.6,'Summary: BS vs MJD Option Pricing Comparison',30,DB,True); bar(s,.8,1,.3,.04)
img(s,'14_summary_dashboard.png',.3,1.2,width=12.5)

# ── Slide 23: Comparison Table ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s,WH); bar(s,0,0,13.333,.08,DB)
tx(s,.8,.3,10,.6,'Model Comparison for Option Pricing',30,DB,True); bar(s,.8,1,.3,.04)
td=[['Feature','Black-Scholes','Merton JD'],
    ['Underlying SDE','GBM (continuous)','GBM + Poisson jumps'],
    ['Parameters','2 (μ, σ)','5 (μ, σ, λ, μ_J, σ_J)'],
    ['Return distribution','Gaussian','Gaussian mixture'],
    ['Option pricing','Closed-form (BS formula)','Monte Carlo required'],
    ['Implied volatility','Flat (constant σ)','Smile / skew'],
    ['OTM put pricing','Systematically low','More realistic'],
    ['Captures crashes','No','Yes (jump component)'],
    ['Calibration','Analytic MLE','Numerical MLE (L-BFGS-B)']]
tbl=s.shapes.add_table(len(td),3,Inches(.5),Inches(1.3),Inches(12.3),Inches(4.5)).table
for ci in range(3): tbl.columns[ci].width=Inches(12.3/3)
for ri,row in enumerate(td):
    for ci,cell_text in enumerate(row):
        cell=tbl.cell(ri,ci); cell.text=cell_text
        for p in cell.text_frame.paragraphs:
            p.font.size=Pt(13); p.font.name='Calibri'; p.alignment=PP_ALIGN.CENTER
            p.font.bold=(ri==0); p.font.color.rgb=WH if ri==0 else BK
        if ri==0: cell.fill.solid(); cell.fill.fore_color.rgb=DB
        elif ri%2==0: cell.fill.solid(); cell.fill.fore_color.rgb=RGBColor(0xE8,0xEC,0xF1)

# ── Slide 24: Future Work ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s,WH); bar(s,0,0,13.333,.08,DB)
tx(s,.8,.3,10,.6,'7. Future Work & Connection to Supervisor Research',30,DB,True); bar(s,.8,1,.3,.04)
bl(s,.8,1.3,11.5,5.5,[
    'End-term: extend option pricing comparison to stochastic volatility models:',
    '',
    '  • Heston (1993): variance v(t) follows CIR process → produces full IV surface',
    '  • Bates (1996): Heston + jumps → 8 parameters, most flexible model',
    '  • Calibrate to live NIFTY option chain prices (not just returns)',
    '',
    'Numerical challenge: CIR process has non-Lipschitz √v(t) coefficient',
    '  → Standard Euler-Maruyama can give negative variance',
    '',
    'Prof. Chaman Kumar\'s research directly addresses this:',
    '  • Tamed Euler for Lévy SDEs [DKS16, SIAM J. Numer. Anal., 54(3)]',
    '  • Tamed Milstein for super-linear coefficients [KS17, EJP 22]',
    '  • Milstein for Markovian switching [KK20, J. Comp. Appl. Math. 377]',
    '  • McKean-Vlasov equations [KNRS20] — future scope: mean-field option markets',
],15)

# ── Slide 25: References ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s,WH); bar(s,0,0,13.333,.08,DB)
tx(s,.8,.3,10,.6,'References',30,DB,True); bar(s,.8,1,.3,.04)
bl(s,.8,1.2,11.5,6,[
    'Option Pricing Models:',
    '  [BS73] Black & Scholes (1973). J. Political Economy, 81(3), 637–654.',
    '  [Me76] Merton (1976). J. Financial Economics, 3(1-2), 125–144.',
    '  [He93] Heston (1993). Review of Financial Studies, 6(2), 327–343.',
    '  [Ba96] Bates (1996). Review of Financial Studies, 9(1), 69–107.',
    '',
    'Statistical & Computational Methods:',
    '  [Aït-Sa02] Aït-Sahalia (2002). Econometrica, 70(1), 223–262.',
    '  [CT04] Cont & Tankov (2004). Financial Modelling with Jump Processes.',
    '  [Gl03] Glasserman (2003). MC Methods in Financial Engineering.',
    '  [Ru94] Rubinstein (1994). J. Finance, 49(3), 771–818.',
    '',
    'Supervisor\'s Research:',
    '  [DKS16] Dareiotis, Kumar & Sabanis (2016). SIAM J. Numer. Anal., 54(3).',
    '  [KS17] Kumar & Sabanis (2017). Electr. J. Probability, 22.',
    '  [KK20] Kumar & Kumar (2020). J. Comp. Appl. Math., 377.',
    '  [KNRS20] Kumar, Neelima, Reisinger & Stockinger (2020). arXiv:2006.00463.',
],12)

# ── Slide 26: Thank You ──
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
bar(s,0,0,13.333,.15); bar(s,0,7.35,13.333,.15)
tx(s,1.5,2,10,1,'Thank You',48,WH,True,PP_ALIGN.CENTER)
bar(s,5,3.2,3,.04)
tx(s,1.5,3.5,10,.6,'Option Pricing: Black-Scholes vs Merton Jump-Diffusion\non the Indian Stock Market (NIFTY 50)',20,RGBColor(0xAA,0xCC,0xEE),False,PP_ALIGN.CENTER)
tx(s,1.5,4.5,10,.4,'Prof. Chaman Kumar | IIT Roorkee',18,WH,True,PP_ALIGN.CENTER)
tx(s,1.5,5.8,10,.4,'Questions?',24,GD,True,PP_ALIGN.CENTER)

prs.save(OUT)
print(f'Saved: {OUT} ({len(prs.slides)} slides)')
