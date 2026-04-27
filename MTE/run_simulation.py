"""
Stochastic Option Pricing — NIFTY 50 European Options
Comparative Study: Black-Scholes vs Merton Jump-Diffusion
Focus: OPTION PRICES (calls & puts across strikes, maturities, events)
Calibration uses stock returns; all outputs are about option pricing.
"""

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import norm, probplot, gaussian_kde, chi2
from scipy.optimize import minimize, brentq
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import warnings, os
warnings.filterwarnings('ignore')

plt.rcParams.update({
    'figure.figsize': (14, 6), 'font.size': 12, 'axes.titlesize': 14,
    'axes.labelsize': 12, 'legend.fontsize': 10, 'figure.dpi': 150,
    'savefig.dpi': 150, 'savefig.bbox': 'tight'
})

FIG = 'figures/'
os.makedirs(FIG, exist_ok=True)

# ============================================================
# 1. DATA & CALIBRATION  (stock returns → model parameters)
# ============================================================
print('1. Downloading NIFTY 50 data for model calibration...')
data = yf.download('^NSEI', start='2018-01-01', end='2024-12-31')
prices = data['Close'].dropna()
if isinstance(prices, pd.DataFrame): prices = prices.iloc[:, 0]
log_returns = np.log(prices / prices.shift(1)).dropna()
r = log_returns.values
dt = 1/252
S0 = float(prices.iloc[-1])
r_f = 0.065

print(f'  S0 (last close) = {S0:.2f}')
print(f'  Observations: {len(r)}, Skew={log_returns.skew():.2f}, Kurt={log_returns.kurtosis():.2f}')

# --- BS MLE ---
def neg_ll_bs(params, ret, dt=1/252):
    mu, sigma = params
    if sigma <= 0: return 1e10
    m = (mu - 0.5*sigma**2)*dt
    v = sigma**2*dt
    return -np.sum(norm.logpdf(ret, loc=m, scale=np.sqrt(v)))

mu0 = r.mean()/dt + 0.5*(r.std()/np.sqrt(dt))**2
sig0 = r.std()/np.sqrt(dt)
res_bs = minimize(neg_ll_bs, [mu0, sig0], args=(r,), method='Nelder-Mead',
                  options={'xatol':1e-8,'fatol':1e-8})
mu_bs, sig_bs = res_bs.x
ll_bs = -res_bs.fun
print(f'  BS MLE: mu={mu_bs:.4f}, sigma={sig_bs:.4f} ({sig_bs*100:.1f}%), LL={ll_bs:.2f}')

# --- MJD MLE (vectorised) ---
def neg_ll_mjd(params, ret, dt=1/252, K=15):
    mu,sigma,lam,mu_j,sigma_j = params
    if sigma<=0 or lam<0 or sigma_j<=0: return 1e10
    ld = lam*dt; ks = np.arange(K)
    lp = -ld + ks*np.log(ld+1e-300) - np.array([np.sum(np.log(np.arange(1,k+1))) for k in ks])
    ms = (mu-0.5*sigma**2)*dt + ks*mu_j
    vs = np.maximum(sigma**2*dt + ks*sigma_j**2, 1e-20)
    R = ret[:,None]
    lt = lp[None,:] + norm.logpdf(R, loc=ms[None,:], scale=np.sqrt(vs)[None,:])
    mx = lt.max(axis=1)
    return -np.sum(mx + np.log(np.sum(np.exp(lt - mx[:,None]), axis=1)))

x0 = [mu_bs, sig_bs*0.8, 5.0, -0.02, 0.05]
bnd = [(None,None),(1e-4,None),(0,50),(-0.5,0.5),(1e-4,1.0)]
res_mjd = minimize(neg_ll_mjd, x0, args=(r,), method='L-BFGS-B', bounds=bnd, options={'maxiter':500})
mu_m, sig_m, lam_m, muj_m, sigj_m = res_mjd.x
ll_mjd = -res_mjd.fun
LRT = 2*(ll_mjd - ll_bs)
pval = 1 - chi2.cdf(LRT, 3)
print(f'  MJD MLE: sigma={sig_m:.4f}, lam={lam_m:.1f}, mu_J={muj_m*100:.2f}%, sig_J={sigj_m*100:.2f}%')
print(f'  MJD LL={ll_mjd:.2f}, LRT={LRT:.1f}, p={pval:.2e}')

aic_bs  = 4 - 2*ll_bs;  bic_bs  = 2*np.log(len(r)) - 2*ll_bs
aic_mjd = 10 - 2*ll_mjd; bic_mjd = 5*np.log(len(r)) - 2*ll_mjd

# ============================================================
# OPTION PRICING FUNCTIONS
# ============================================================
def bs_price(S, K, T, rf, sigma, otype='call'):
    d1 = (np.log(S/K)+(rf+0.5*sigma**2)*T)/(sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    if otype=='call': return S*norm.cdf(d1) - K*np.exp(-rf*T)*norm.cdf(d2)
    return K*np.exp(-rf*T)*norm.cdf(-d2) - S*norm.cdf(-d1)

def bs_iv(mkt_price, S, K, T, rf, otype='call'):
    try: return brentq(lambda s: bs_price(S,K,T,rf,s,otype)-mkt_price, 0.01, 5.0)
    except: return np.nan

def mjd_mc_price(S0, K, T, rf, sigma, lam, mu_j, sigma_j,
                 n_paths=80_000, n_steps=None, seed=42):
    if n_steps is None: n_steps = max(int(T*252), 30)
    np.random.seed(seed)
    dtm = T/n_steps
    kappa = np.exp(mu_j+0.5*sigma_j**2)-1
    mu_rn = rf - 0.5*sigma**2 - lam*kappa
    logS = np.full(n_paths, np.log(S0))
    for _ in range(n_steps):
        Z = np.random.standard_normal(n_paths)
        Nj = np.random.poisson(lam*dtm, n_paths)
        J = np.where(Nj>0,
                     np.array([np.random.normal(mu_j,sigma_j,int(n)).sum() if n>0 else 0. for n in Nj]),
                     0.)
        logS += mu_rn*dtm + sigma*np.sqrt(dtm)*Z + J
    ST = np.exp(logS)
    disc = np.exp(-rf*T)
    c = disc*np.maximum(ST-K,0).mean()
    p = disc*np.maximum(K-ST,0).mean()
    se_c = disc*np.maximum(ST-K,0).std()/np.sqrt(n_paths)
    se_p = disc*np.maximum(K-ST,0).std()/np.sqrt(n_paths)
    return {'call':c,'put':p,'se_c':se_c,'se_p':se_p,'ST':ST}

def mjd_merton_series_price(S0, K, T, rf, sigma, lam, mu_j, sigma_j, k_max=40, use_lambda_prime=True):
    """
    Merton (1976) series price via Law of Total Expectation.
    Uses a Poisson-weighted average of BS prices conditional on k jumps.

    Notes:
      - kappa = E[e^J - 1]
      - risk-neutral compensator sets drift to (rf - lam*kappa)
      - some presentations use lambda' = lam*(1+kappa) under Q; we allow this toggle
    """
    kappa = np.exp(mu_j + 0.5*sigma_j**2) - 1
    lam_q = lam*(1+kappa) if use_lambda_prime else lam
    # Poisson weights under Q
    ks = np.arange(0, k_max+1)
    w = np.exp(-lam_q*T) * (lam_q*T)**ks / np.array([math.factorial(int(k)) for k in ks], dtype=float)
    # Modified parameters conditional on k jumps
    sig_k = np.sqrt(sigma**2 + (ks * sigma_j**2)/max(T, 1e-12))
    r_k = rf - lam*kappa + (ks*mu_j)/max(T, 1e-12) + (ks*sigma_j**2)/(2*max(T, 1e-12))
    # Series call/put
    call = float(np.sum(w * np.array([bs_price(S0, K, T, rk, sk, 'call') for rk, sk in zip(r_k, sig_k)])))
    put  = float(np.sum(w * np.array([bs_price(S0, K, T, rk, sk, 'put')  for rk, sk in zip(r_k, sig_k)])))
    tail_mass = float(1 - np.sum(w))
    return {"call": call, "put": put, "tail_mass": tail_mass, "lam_q": float(lam_q), "kappa": float(kappa), "weights": w, "ks": ks}

# Common option parameters
K_atm = round(S0/100)*100
T30 = 30/252          # 1-month maturity
T90 = 90/252          # 3-month maturity
T180 = 180/252        # 6-month maturity

print(f'\n  ATM strike K = {K_atm}, S0 = {S0:.2f}')

# ============================================================
# Fig 01: Calibration Data Overview
# ============================================================
print('\n2. Generating figures...')
print('  Fig 01: Calibration data overview...')
fig, axes = plt.subplots(2, 2, figsize=(16, 10))

ax = axes[0,0]
ax.plot(prices.index, prices.values, color='#1B3A6B', lw=0.8)
for ds, lb in {'2018-09-21':'IL&FS','2020-03-23':'COVID','2022-02-24':'Ru-Ukr','2024-06-04':'Election'}.items():
    ax.axvline(pd.Timestamp(ds), color='red', alpha=.5, ls='--', lw=.8)
    ax.text(pd.Timestamp(ds), ax.get_ylim()[1]*.95, lb, rotation=45, fontsize=7, ha='right', color='red')
ax.set_title('NIFTY 50 — Underlying Price (used for model calibration)')
ax.set_ylabel('Price (₹)'); ax.grid(True, alpha=.3)

ax = axes[0,1]
ax.plot(log_returns.index, log_returns.values, color='#C8521A', lw=.3, alpha=.8)
ax.axhline(0, color='black', lw=.5)
ax.set_title('Daily Log Returns (input to MLE)')
ax.set_ylabel('Log Return'); ax.grid(True, alpha=.3)

ax = axes[1,0]
ax.hist(r, bins=100, density=True, color='#1B3A6B', alpha=.6, label='Empirical')
x_rng = np.linspace(r.min(), r.max(), 500)
ax.plot(x_rng, norm.pdf(x_rng, r.mean(), r.std()), 'r-', lw=2, label='Normal (BS assumes this)')
ax.set_title('Return Distribution — fat tails cause option mispricing')
ax.set_xlabel('Log Return'); ax.set_ylabel('Density'); ax.legend(); ax.grid(True, alpha=.3)

ax = axes[1,1]
bl = np.linspace(-.15, -.01, 80)
ax.hist(r[r<-0.01], bins=bl, density=True, color='#1B3A6B', alpha=.6, label='Empirical')
ax.plot(np.linspace(-.15,-.01,300), norm.pdf(np.linspace(-.15,-.01,300), r.mean(), r.std()),
        'r-', lw=2.5, label='Normal (BS)')
ax.axvline(np.percentile(r,1), color='darkred', ls='--', lw=2, label=f'1% VaR={np.percentile(r,1)*100:.2f}%')
ax.set_title('LEFT TAIL ZOOM — BS underestimates crash probability')
ax.set_xlabel('Log Return'); ax.legend(fontsize=8); ax.grid(True, alpha=.3)
ax.annotate('Fat tails → BS\nunderprices OTM puts', xy=(-.08,.3), fontsize=9, color='red', fontweight='bold', ha='center')

plt.tight_layout(); plt.savefig(f'{FIG}01_calibration_data.png'); plt.close()

# ============================================================
# Fig 02: ATM Option Prices — BS vs MJD
# ============================================================
print('  Fig 02: ATM option prices (BS vs MJD)...')
bs_call = bs_price(S0, K_atm, T30, r_f, sig_bs, 'call')
bs_put  = bs_price(S0, K_atm, T30, r_f, sig_bs, 'put')
mjd_res = mjd_mc_price(S0, K_atm, T30, r_f, sig_m, lam_m, muj_m, sigj_m)

fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

ax = axes[0]
labels = ['BS Call', 'MJD Call', 'BS Put', 'MJD Put']
vals = [bs_call, mjd_res['call'], bs_put, mjd_res['put']]
cols = ['#1B3A6B','#C8521A','#1B3A6B','#C8521A']
hatches = ['','','//','//']
bars = ax.bar(labels, vals, color=cols, alpha=.8, edgecolor='black')
for b,h in zip(bars,hatches): b.set_hatch(h)
for b,v in zip(bars,vals):
    ax.text(b.get_x()+b.get_width()/2, v+5, f'₹{v:.2f}', ha='center', fontweight='bold', fontsize=10)
ax.set_title(f'ATM Option Prices (K={K_atm}, T=30d)', fontweight='bold')
ax.set_ylabel('Option Price (₹)'); ax.grid(True, alpha=.3, axis='y')

ax = axes[1]
ST_bs = S0*np.exp((r_f-.5*sig_bs**2)*T30 + sig_bs*np.sqrt(T30)*np.random.standard_normal(80000))
ax.hist(ST_bs, bins=150, density=True, alpha=.5, color='#1B3A6B', label='BS terminal S(T)')
ax.hist(mjd_res['ST'], bins=150, density=True, alpha=.5, color='#C8521A', label='MJD terminal S(T)')
ax.axvline(K_atm, color='red', ls='--', lw=2, label=f'Strike K={K_atm}')
ax.set_title('Terminal Price Distribution — affects option payoffs')
ax.set_xlabel('S(T) at expiry'); ax.legend(fontsize=9); ax.grid(True, alpha=.3)

ax = axes[2]
payoff_bs = np.maximum(K_atm - ST_bs, 0)
payoff_mjd = np.maximum(K_atm - mjd_res['ST'], 0)
bins_po = np.linspace(0, np.percentile(payoff_mjd, 99.5), 80)
ax.hist(payoff_bs[payoff_bs>0], bins=bins_po, density=True, alpha=.5, color='#1B3A6B', label='BS put payoff')
ax.hist(payoff_mjd[payoff_mjd>0], bins=bins_po, density=True, alpha=.5, color='#C8521A', label='MJD put payoff')
ax.set_title('Put Payoff Distribution — MJD has heavier right tail')
ax.set_xlabel('Put payoff max(K−S(T), 0)'); ax.legend(fontsize=9); ax.grid(True, alpha=.3)

plt.suptitle('Option Pricing Comparison: Black-Scholes vs Merton Jump-Diffusion', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout(); plt.savefig(f'{FIG}02_atm_option_prices.png'); plt.close()

# ============================================================
# Fig 03: Call & Put prices across strikes
# ============================================================
print('  Fig 03: Option prices across strikes...')
strikes = np.linspace(S0*0.85, S0*1.15, 25)
bs_calls, bs_puts, mjd_calls, mjd_puts = [], [], [], []
for Ki in strikes:
    bs_calls.append(bs_price(S0, Ki, T30, r_f, sig_bs, 'call'))
    bs_puts.append(bs_price(S0, Ki, T30, r_f, sig_bs, 'put'))
    res = mjd_mc_price(S0, Ki, T30, r_f, sig_m, lam_m, muj_m, sigj_m, n_paths=40000, seed=42)
    mjd_calls.append(res['call']); mjd_puts.append(res['put'])

moneyness = strikes/S0
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

ax = axes[0,0]
ax.plot(moneyness, bs_calls, 'o-', color='#1B3A6B', lw=2, ms=4, label='BS Call')
ax.plot(moneyness, mjd_calls, 's-', color='#C8521A', lw=2, ms=4, label='MJD Call')
ax.axvline(1, color='gray', ls=':', alpha=.5)
ax.set_title('European CALL Prices (T=30 days)', fontweight='bold')
ax.set_xlabel('Moneyness K/S₀'); ax.set_ylabel('Call Price (₹)'); ax.legend(); ax.grid(True, alpha=.3)

ax = axes[0,1]
ax.plot(moneyness, bs_puts, 'o-', color='#1B3A6B', lw=2, ms=4, label='BS Put')
ax.plot(moneyness, mjd_puts, 's-', color='#C8521A', lw=2, ms=4, label='MJD Put')
ax.axvline(1, color='gray', ls=':', alpha=.5)
ax.set_title('European PUT Prices (T=30 days)', fontweight='bold')
ax.set_xlabel('Moneyness K/S₀'); ax.set_ylabel('Put Price (₹)'); ax.legend(); ax.grid(True, alpha=.3)

ax = axes[1,0]
diff_c = np.array(mjd_calls)-np.array(bs_calls)
diff_p = np.array(mjd_puts)-np.array(bs_puts)
ax.plot(moneyness, diff_c, 's-', color='#C8521A', lw=2, label='Call: MJD − BS')
ax.plot(moneyness, diff_p, '^-', color='#2E8B57', lw=2, label='Put: MJD − BS')
ax.axhline(0, color='black', lw=.5); ax.axvline(1, color='gray', ls=':', alpha=.5)
ax.fill_between(moneyness, 0, diff_p, where=np.array(diff_p)>0, alpha=.15, color='#2E8B57')
ax.set_title('Pricing Difference (MJD − BS)', fontweight='bold')
ax.set_xlabel('Moneyness K/S₀'); ax.set_ylabel('Price Difference (₹)'); ax.legend(); ax.grid(True, alpha=.3)

ax = axes[1,1]
pct_diff_p = (np.array(mjd_puts)-np.array(bs_puts))/np.array(bs_puts)*100
valid = np.array(bs_puts)>1
ax.plot(moneyness[valid], pct_diff_p[valid], '^-', color='#2E8B57', lw=2)
ax.axhline(0, color='black', lw=.5); ax.axvline(1, color='gray', ls=':', alpha=.5)
ax.set_title('PUT Price: % Difference (MJD vs BS)', fontweight='bold')
ax.set_xlabel('Moneyness K/S₀'); ax.set_ylabel('(MJD−BS)/BS × 100%'); ax.grid(True, alpha=.3)
ax.annotate('OTM puts: BS severely\nunderprices crash protection', xy=(.87,ax.get_ylim()[1]*.6),
            fontsize=10, color='red', fontweight='bold')

plt.suptitle('Option Prices Across Strikes: BS vs MJD (T=30 days)', fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout(); plt.savefig(f'{FIG}03_option_prices_across_strikes.png'); plt.close()

# ============================================================
# Fig 04: Implied Volatility Smile from MJD option prices
# ============================================================
print('  Fig 04: Implied Volatility Smile...')
iv_from_mjd = []
for Ki, mc in zip(strikes, mjd_calls):
    iv_from_mjd.append(bs_iv(mc, S0, Ki, T30, r_f, 'call'))
iv_arr = np.array(iv_from_mjd)

fig, ax = plt.subplots(figsize=(12, 6))
valid = ~np.isnan(iv_arr)
ax.plot(moneyness[valid], iv_arr[valid]*100, 'o-', color='#C8521A', lw=2, ms=5, label='IV from MJD prices')
ax.axhline(sig_bs*100, color='#1B3A6B', ls='--', lw=2, label=f'BS constant σ = {sig_bs*100:.1f}%')
ax.axvline(1, color='gray', ls=':', alpha=.5, label='ATM')
ax.set_xlabel('Moneyness K/S₀'); ax.set_ylabel('Implied Volatility (%)')
ax.set_title('Implied Volatility Smile: MJD option prices reveal skew that BS cannot produce', fontweight='bold')
ax.legend(fontsize=11); ax.grid(True, alpha=.3)
plt.tight_layout(); plt.savefig(f'{FIG}04_iv_smile.png'); plt.close()

# ============================================================
# Fig 05: Option prices across maturities (term structure)
# ============================================================
print('  Fig 05: Option term structure...')
mats = [7, 14, 30, 60, 90, 180]
mat_labels = ['7d','14d','30d','60d','90d','180d']
bs_c_mat, bs_p_mat, mjd_c_mat, mjd_p_mat = [], [], [], []
K_test = K_atm
for Td in mats:
    Ty = Td/252
    bs_c_mat.append(bs_price(S0, K_test, Ty, r_f, sig_bs, 'call'))
    bs_p_mat.append(bs_price(S0, K_test, Ty, r_f, sig_bs, 'put'))
    res = mjd_mc_price(S0, K_test, Ty, r_f, sig_m, lam_m, muj_m, sigj_m, n_paths=50000, seed=42)
    mjd_c_mat.append(res['call']); mjd_p_mat.append(res['put'])

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

ax = axes[0]
x = np.arange(len(mats)); w=.35
ax.bar(x-w/2, bs_c_mat, w, color='#1B3A6B', alpha=.8, label='BS Call')
ax.bar(x+w/2, mjd_c_mat, w, color='#C8521A', alpha=.8, label='MJD Call')
ax.set_xticks(x); ax.set_xticklabels(mat_labels)
ax.set_title(f'ATM Call Prices Across Maturities (K={K_test})', fontweight='bold')
ax.set_xlabel('Maturity'); ax.set_ylabel('Call Price (₹)'); ax.legend(); ax.grid(True, alpha=.3, axis='y')

ax = axes[1]
ax.bar(x-w/2, bs_p_mat, w, color='#1B3A6B', alpha=.8, label='BS Put')
ax.bar(x+w/2, mjd_p_mat, w, color='#C8521A', alpha=.8, label='MJD Put')
ax.set_xticks(x); ax.set_xticklabels(mat_labels)
ax.set_title(f'ATM Put Prices Across Maturities (K={K_test})', fontweight='bold')
ax.set_xlabel('Maturity'); ax.set_ylabel('Put Price (₹)'); ax.legend(); ax.grid(True, alpha=.3, axis='y')

plt.suptitle('Option Price Term Structure: MJD puts are consistently more expensive (crash risk premium)',
             fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout(); plt.savefig(f'{FIG}05_option_term_structure.png'); plt.close()

# ============================================================
# Fig 06: OTM Put pricing — where BS fails most
# ============================================================
print('  Fig 06: OTM put pricing comparison...')
otm_strikes = np.linspace(S0*0.80, S0*0.98, 20)
bs_otm, mjd_otm = [], []
for Ki in otm_strikes:
    bs_otm.append(bs_price(S0, Ki, T30, r_f, sig_bs, 'put'))
    res = mjd_mc_price(S0, Ki, T30, r_f, sig_m, lam_m, muj_m, sigj_m, n_paths=50000, seed=42)
    mjd_otm.append(res['put'])

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

ax = axes[0]
ax.plot(otm_strikes/S0, bs_otm, 'o-', color='#1B3A6B', lw=2, label='BS Put')
ax.plot(otm_strikes/S0, mjd_otm, 's-', color='#C8521A', lw=2, label='MJD Put')
ax.set_title('OTM Put Prices (T=30d) — crash protection', fontweight='bold')
ax.set_xlabel('Moneyness K/S₀'); ax.set_ylabel('Put Price (₹)'); ax.legend(); ax.grid(True, alpha=.3)

ax = axes[1]
ratio = np.array(mjd_otm)/np.array(bs_otm)
ax.plot(otm_strikes/S0, ratio, 'D-', color='darkred', lw=2)
ax.axhline(1, color='black', ls='--', lw=.5)
ax.fill_between(otm_strikes/S0, 1, ratio, where=ratio>1, alpha=.2, color='red')
ax.set_title('MJD/BS Put Price Ratio — how much BS underprices', fontweight='bold')
ax.set_xlabel('Moneyness K/S₀'); ax.set_ylabel('MJD Price / BS Price'); ax.grid(True, alpha=.3)
ax.annotate('Deep OTM: MJD prices\ncan be 2-5× higher than BS', xy=(.83, ratio.max()*.8),
            fontsize=10, color='red', fontweight='bold')

plt.suptitle('OTM Put Option Pricing: BS systematically underprices crash protection',
             fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout(); plt.savefig(f'{FIG}06_otm_put_pricing.png'); plt.close()

# ============================================================
# Fig 07: Jump parameter sensitivity on option prices
# ============================================================
print('  Fig 07: Parameter sensitivity heatmap (option prices)...')
lam_rng = np.linspace(1, 30, 12)
sigj_rng = np.linspace(0.01, 0.15, 12)
call_grid = np.zeros((len(sigj_rng), len(lam_rng)))
put_grid = np.zeros_like(call_grid)
for i, sj in enumerate(sigj_rng):
    for j, lm in enumerate(lam_rng):
        res = mjd_mc_price(S0, K_atm, T30, r_f, sig_m, lm, muj_m, sj, n_paths=15000, seed=42)
        call_grid[i,j] = res['call']; put_grid[i,j] = res['put']

fig, axes = plt.subplots(1, 2, figsize=(16, 7))
for ax, grid, title in [(axes[0], call_grid, 'ATM Call Price (₹)'), (axes[1], put_grid, 'ATM Put Price (₹)')]:
    sns.heatmap(grid, xticklabels=[f'{l:.0f}' for l in lam_rng],
                yticklabels=[f'{s:.3f}' for s in sigj_rng], annot=True, fmt='.0f', cmap='YlOrRd', ax=ax)
    ax.set_xlabel('λ (jumps/year)'); ax.set_ylabel('σ_J'); ax.set_title(title, fontweight='bold')
plt.suptitle('MJD Option Price Sensitivity to Jump Parameters', fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout(); plt.savefig(f'{FIG}07_option_sensitivity_heatmap.png'); plt.close()

# ============================================================
# Fig 08: Monte Carlo convergence (option prices)
# ============================================================
print('  Fig 08: MC convergence (option prices)...')
Ns = [100,500,1000,2000,5000,10000,20000,50000,100000,200000]
mc_bs, mc_mjd, se_bs_list, se_mjd_list = [], [], [], []
for N in Ns:
    np.random.seed(42)
    Z = np.random.standard_normal(N)
    ST = S0*np.exp((r_f-.5*sig_bs**2)*T30+sig_bs*np.sqrt(T30)*Z)
    po = np.maximum(ST-K_atm,0)*np.exp(-r_f*T30)
    mc_bs.append(po.mean()); se_bs_list.append(po.std()/np.sqrt(N))
    res = mjd_mc_price(S0, K_atm, T30, r_f, sig_m, lam_m, muj_m, sigj_m, n_paths=N, seed=42)
    mc_mjd.append(res['call']); se_mjd_list.append(res['se_c'])

cf_call = bs_price(S0, K_atm, T30, r_f, sig_bs, 'call')

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
ax = axes[0]
ax.semilogx(Ns, mc_bs, 'o-', color='#1B3A6B', label='BS MC Call')
ax.fill_between(Ns, [p-1.96*s for p,s in zip(mc_bs,se_bs_list)],
                    [p+1.96*s for p,s in zip(mc_bs,se_bs_list)], alpha=.2, color='#1B3A6B')
ax.axhline(cf_call, color='red', ls='--', label=f'BS Closed-Form = ₹{cf_call:.2f}')
ax.semilogx(Ns, mc_mjd, 's-', color='#C8521A', label='MJD MC Call')
ax.set_title('MC Option Price Convergence', fontweight='bold')
ax.set_xlabel('# Paths'); ax.set_ylabel('Call Price (₹)'); ax.legend(); ax.grid(True, alpha=.3)

ax = axes[1]
ax.loglog(Ns, [1.96*s for s in se_bs_list], 'o-', color='#1B3A6B', label='BS SE')
ax.loglog(Ns, [1.96*s for s in se_mjd_list], 's-', color='#C8521A', label='MJD SE')
Nf = np.array(Ns, dtype=float)
ax.loglog(Nf, se_bs_list[0]*1.96*np.sqrt(Ns[0])/np.sqrt(Nf), 'k--', alpha=.5, label='1/√N reference')
ax.set_title('MC Standard Error (95% CI width)', fontweight='bold')
ax.set_xlabel('# Paths'); ax.set_ylabel('95% CI half-width (₹)'); ax.legend(); ax.grid(True, alpha=.3)

plt.suptitle('Monte Carlo Convergence for Option Pricing', fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout(); plt.savefig(f'{FIG}08_mc_convergence_options.png'); plt.close()

# ============================================================
# Fig 09: Variance Reduction for option pricing MC
# ============================================================
print('  Fig 09: Variance reduction (option pricing)...')
np.random.seed(42)
Z_n = np.random.standard_normal(100000)
ST_n = S0*np.exp((r_f-.5*sig_bs**2)*T30+sig_bs*np.sqrt(T30)*Z_n)
po_n = np.maximum(ST_n-K_atm,0)*np.exp(-r_f*T30)
naive_se = po_n.std()/np.sqrt(100000)

np.random.seed(42)
Za = np.random.standard_normal(50000)
ST_p = S0*np.exp((r_f-.5*sig_bs**2)*T30+sig_bs*np.sqrt(T30)*Za)
ST_m = S0*np.exp((r_f-.5*sig_bs**2)*T30+sig_bs*np.sqrt(T30)*(-Za))
po_a = (np.maximum(ST_p-K_atm,0)+np.maximum(ST_m-K_atm,0))/2*np.exp(-r_f*T30)
anti_se = po_a.std()/np.sqrt(50000)

np.random.seed(42)
Zc = np.random.standard_normal(100000)
ST_c = S0*np.exp((r_f-.5*sig_bs**2)*T30+sig_bs*np.sqrt(T30)*Zc)
po_c = np.maximum(ST_c-K_atm,0)*np.exp(-r_f*T30)
beta = np.cov(po_c,ST_c)[0,1]/np.var(ST_c)
po_cv = po_c - beta*(ST_c - S0*np.exp(r_f*T30))
cv_se = po_cv.std()/np.sqrt(100000)

fig, ax = plt.subplots(figsize=(10, 6))
ms = ['Naive MC', 'Antithetic', 'Control Variate']
ses = [naive_se, anti_se, cv_se]
ax.bar(ms, ses, color=['#1B3A6B','#2E8B57','#C8521A'], alpha=.8, edgecolor='black')
for i,(m,s) in enumerate(zip(ms,ses)):
    ax.text(i, s+.05, f'SE=₹{s:.3f}', ha='center', fontweight='bold', fontsize=11)
ax.set_title('Option Pricing MC Standard Error — Variance Reduction', fontweight='bold')
ax.set_ylabel('SE (₹)'); ax.grid(True, alpha=.3, axis='y')
plt.tight_layout(); plt.savefig(f'{FIG}09_variance_reduction_options.png'); plt.close()

# ============================================================
# Fig 10: Model comparison criteria
# ============================================================
print('  Fig 10: Model selection criteria...')
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
cols2 = ['#1B3A6B','#C8521A']
for ax, vals, title in [(axes[0],[ll_bs,ll_mjd],'Log-Likelihood ℓ(θ̂)'),
                         (axes[1],[aic_bs,aic_mjd],'AIC (lower = better)'),
                         (axes[2],[bic_bs,bic_mjd],'BIC (lower = better)')]:
    bars = ax.bar(['BS','MJD'], vals, color=cols2, alpha=.8, edgecolor='black')
    for b,v in zip(bars,vals):
        ax.text(b.get_x()+b.get_width()/2, b.get_height(), f'{v:.1f}', ha='center', va='bottom', fontweight='bold')
    ax.set_title(title, fontweight='bold'); ax.grid(True, alpha=.3, axis='y')
plt.tight_layout(); plt.savefig(f'{FIG}10_model_selection.png'); plt.close()

# ============================================================
# Fig 11: Option pricing at Indian market crisis events
# ============================================================
print('  Fig 11: Option pricing at crisis events...')
events = {
    'IL&FS\nSep 2018': ('2018-09-14', '2018-09-21'),
    'COVID\nMar 2020': ('2020-03-16', '2020-03-23'),
    'Ru-Ukr\nFeb 2022': ('2022-02-18', '2022-02-24'),
    'Election\nJun 2024': ('2024-05-28', '2024-06-04'),
}

fig, axes = plt.subplots(1, 2, figsize=(16, 7))
ev_names, bs_errs, mjd_errs = [], [], []
bs_puts_ev, mjd_puts_ev = [], []

for label, (pre_date, event_date) in events.items():
    pre = pd.Timestamp(pre_date)
    ev = pd.Timestamp(event_date)
    idx_pre = prices.index.get_indexer([pre], method='nearest')[0]
    idx_ev = prices.index.get_indexer([ev], method='nearest')[0]
    if idx_pre < 0 or idx_ev < 0: continue
    S_pre = float(prices.iloc[idx_pre])
    S_ev = float(prices.iloc[idx_ev])
    K_ev = round(S_pre/100)*100
    T_ev = 5/252

    bs_p = bs_price(S_pre, K_ev, T_ev, r_f, sig_bs, 'put')
    mjd_p = mjd_mc_price(S_pre, K_ev, T_ev, r_f, sig_m, lam_m, muj_m, sigj_m, n_paths=50000, seed=42)['put']
    realized = max(K_ev - S_ev, 0)

    ev_names.append(label)
    bs_puts_ev.append(bs_p); mjd_puts_ev.append(mjd_p)
    bs_errs.append(realized - bs_p); mjd_errs.append(realized - mjd_p)

ax = axes[0]
x = np.arange(len(ev_names)); w = .25
ax.bar(x-w, bs_puts_ev, w, color='#1B3A6B', alpha=.8, label='BS Put Price')
ax.bar(x, mjd_puts_ev, w, color='#C8521A', alpha=.8, label='MJD Put Price')
realized_list = [bs_puts_ev[i]+bs_errs[i] for i in range(len(ev_names))]
ax.bar(x+w, realized_list, w, color='green', alpha=.6, label='Realized Payoff')
ax.set_xticks(x); ax.set_xticklabels(ev_names, fontsize=10)
ax.set_title('ATM Put: Model Price vs Realized Payoff at Events', fontweight='bold')
ax.set_ylabel('₹'); ax.legend(fontsize=9); ax.grid(True, alpha=.3, axis='y')

ax = axes[1]
ax.bar(x-w/2, bs_errs, w, color='#1B3A6B', alpha=.8, label='BS Pricing Error')
ax.bar(x+w/2, mjd_errs, w, color='#C8521A', alpha=.8, label='MJD Pricing Error')
ax.axhline(0, color='black', lw=.5)
ax.set_xticks(x); ax.set_xticklabels(ev_names, fontsize=10)
ax.set_title('Option Pricing Error = Realized − Model Price', fontweight='bold')
ax.set_ylabel('Pricing Error (₹)'); ax.legend(fontsize=9); ax.grid(True, alpha=.3, axis='y')
ax.annotate('Positive = model underpriced\nthe put (underestimated crash)', xy=(0, max(bs_errs)*.7),
            fontsize=9, color='red', fontweight='bold')

plt.suptitle('Option Pricing at Indian Market Crises: BS consistently underprices protective puts',
             fontsize=13, fontweight='bold', y=1.02)
plt.tight_layout(); plt.savefig(f'{FIG}11_event_option_pricing.png'); plt.close()

# ============================================================
# Fig 12: GBM vs MJD paths (1-year, jumps emphasized)
# ============================================================
print('  Fig 12: GBM vs MJD sample paths...')
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
T_demo=1.0; n_demo=252; dt_d=T_demo/n_demo; t_d=np.arange(n_demo)
np.random.seed(42)
ax=axes[0]
for i in range(6):
    Z=np.random.standard_normal(n_demo)
    ls=np.log(S0)+np.cumsum((r_f-.5*sig_bs**2)*dt_d+sig_bs*np.sqrt(dt_d)*Z)
    ax.plot(t_d, np.exp(ls), lw=1.2, alpha=.8)
ax.axhline(S0, color='gray', ls=':', alpha=.5)
ax.set_title('GBM Paths (BS) — smooth, no jumps', fontweight='bold')
ax.set_xlabel('Trading Days'); ax.set_ylabel('Price (₹)'); ax.grid(True, alpha=.3)

np.random.seed(100)
kd=np.exp(muj_m+.5*sigj_m**2)-1; md=r_f-.5*sig_m**2-lam_m*kd
ax=axes[1]
for i in range(6):
    Z=np.random.standard_normal(n_demo); Nj=np.random.poisson(lam_m*dt_d,n_demo)
    J=np.array([np.random.normal(muj_m,sigj_m,int(n)).sum() if n>0 else 0. for n in Nj])
    ls=np.log(S0)+np.cumsum(md*dt_d+sig_m*np.sqrt(dt_d)*Z+J)
    p=np.exp(ls); ax.plot(t_d,p,lw=1.2,alpha=.8)
    jd=np.where(Nj>0)[0]
    if len(jd)>0: ax.scatter(t_d[jd],p[jd],s=30,c='red',zorder=5,alpha=.7,edgecolors='darkred',lw=.5)
ax.scatter([],[],s=30,c='red',edgecolors='darkred',label='Jump events')
ax.axhline(S0, color='gray', ls=':', alpha=.5)
ax.set_title('MJD Paths — jumps affect option payoffs at expiry', fontweight='bold')
ax.set_xlabel('Trading Days'); ax.set_ylabel('Price (₹)'); ax.legend(); ax.grid(True, alpha=.3)

plt.suptitle('Underlying Price Paths: jumps create fat tails in S(T) → affect option prices',
             fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout(); plt.savefig(f'{FIG}12_gbm_vs_mjd_paths.png'); plt.close()

# ============================================================
# Fig 13: QQ plots of returns (motivation for option mispricing)
# ============================================================
print('  Fig 13: QQ plots (motivation)...')
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
ax=axes[0]; probplot(r, dist='norm', plot=ax)
ax.set_title('QQ: Empirical vs Normal — tail departure → option mispricing', fontweight='bold')
ax.get_lines()[0].set_color('#1B3A6B'); ax.get_lines()[0].set_markersize(3); ax.grid(True, alpha=.3)

ax=axes[1]
n_sim=200000; np.random.seed(42)
Zs=np.random.standard_normal(n_sim); Njs=np.random.poisson(lam_m*dt,n_sim)
Jjs=np.array([np.random.normal(muj_m,sigj_m,int(n)).sum() if n>0 else 0. for n in Njs])
mjd_rets=(mu_m-.5*sig_m**2)*dt+sig_m*np.sqrt(dt)*Zs+Jjs
emp=np.sort(r); mjd_s=np.sort(mjd_rets[:len(r)])
ax.scatter(mjd_s,emp,s=3,color='#C8521A',alpha=.5)
lm=[min(emp.min(),mjd_s.min()),max(emp.max(),mjd_s.max())]
ax.plot(lm,lm,'k--',lw=1,label='45° line')
ax.set_xlabel('MJD Quantiles'); ax.set_ylabel('Empirical Quantiles')
ax.set_title('QQ: Empirical vs MJD — better tail fit', fontweight='bold'); ax.legend(); ax.grid(True,alpha=.3)
plt.tight_layout(); plt.savefig(f'{FIG}13_qq_plots.png'); plt.close()

# ============================================================
# Fig 14: Summary dashboard
# ============================================================
print('  Fig 14: Summary dashboard...')
emp_kurt = float(log_returns.kurtosis())
denom = (sig_m**2+lam_m*(muj_m**2+sigj_m**2))**2
mjd_kurt = 3*lam_m*(muj_m**2+sigj_m**2)**2/denom if denom>0 else 0

fig, axes = plt.subplots(2, 3, figsize=(18, 10))

ax=axes[0,0]
ax.barh(['BS (2)','MJD (5)'],[2,5],color=['#1B3A6B','#C8521A'],alpha=.8)
ax.set_xlabel('# Parameters'); ax.set_title('Model Complexity',fontweight='bold'); ax.grid(True,alpha=.3,axis='x')

ax=axes[0,1]
bars=ax.bar(['BS','MJD'],[ll_bs,ll_mjd],color=['#1B3A6B','#C8521A'],alpha=.8,edgecolor='black')
for b,v in zip(bars,[ll_bs,ll_mjd]): ax.text(b.get_x()+b.get_width()/2,b.get_height(),f'{v:.0f}',ha='center',va='bottom',fontweight='bold')
ax.set_title('Log-Likelihood',fontweight='bold'); ax.grid(True,alpha=.3,axis='y')

ax=axes[0,2]
x2=np.arange(2); w2=.35
ax.bar(x2-w2/2,[bs_call,bs_put],w2,color='#1B3A6B',alpha=.8,label='BS')
ax.bar(x2+w2/2,[mjd_res['call'],mjd_res['put']],w2,color='#C8521A',alpha=.8,label='MJD')
ax.set_xticks(x2); ax.set_xticklabels(['Call','Put'])
ax.set_title('ATM Option Prices (₹)',fontweight='bold'); ax.legend(); ax.grid(True,alpha=.3,axis='y')

ax=axes[1,0]
bars=ax.bar(['Emp','BS','MJD'],[emp_kurt,0,mjd_kurt],color=['gray','#1B3A6B','#C8521A'],alpha=.8,edgecolor='black')
for b,v in zip(bars,[emp_kurt,0,mjd_kurt]):
    ax.text(b.get_x()+b.get_width()/2,max(b.get_height(),0)+.1,f'{v:.2f}',ha='center',fontweight='bold')
ax.set_title('Excess Kurtosis (drives OTM put pricing)',fontweight='bold'); ax.grid(True,alpha=.3,axis='y')

ax=axes[1,1]
ax.bar(['LRT'],[LRT],color='#C8521A',alpha=.8,edgecolor='black')
ax.axhline(chi2.ppf(.99,3),color='red',ls='--',label=f'χ²(3) 1% = {chi2.ppf(.99,3):.1f}')
ax.text(0,LRT+2,f'LRT={LRT:.1f}',ha='center',fontweight='bold',fontsize=12)
ax.set_title('Likelihood Ratio Test',fontweight='bold'); ax.legend(fontsize=9); ax.grid(True,alpha=.3,axis='y')

ax=axes[1,2]
otm_k = S0*0.9
bs_otm_p = bs_price(S0,otm_k,T30,r_f,sig_bs,'put')
mjd_otm_p = mjd_mc_price(S0,otm_k,T30,r_f,sig_m,lam_m,muj_m,sigj_m,seed=42)['put']
bars=ax.bar(['BS OTM Put','MJD OTM Put'],[bs_otm_p,mjd_otm_p],color=['#1B3A6B','#C8521A'],alpha=.8,edgecolor='black')
for b,v in zip(bars,[bs_otm_p,mjd_otm_p]):
    ax.text(b.get_x()+b.get_width()/2,v+1,f'₹{v:.1f}',ha='center',fontweight='bold')
ax.set_title(f'10% OTM Put Price (K={otm_k:.0f})',fontweight='bold'); ax.grid(True,alpha=.3,axis='y')

plt.suptitle('BS vs MJD: Comprehensive Option Pricing Comparison on NIFTY 50',fontsize=15,fontweight='bold',y=1.02)
plt.tight_layout(); plt.savefig(f'{FIG}14_summary_dashboard.png'); plt.close()

print('  Fig 15: Merton series truncation visualization...')
series = mjd_merton_series_price(S0, K_atm, T30, r_f, sig_m, lam_m, muj_m, sigj_m, k_max=60, use_lambda_prime=True)
ks = series["ks"]; w = series["weights"]
cum = np.cumsum(w)

# Price convergence vs k_max
k_grid = np.arange(0, 41)
calls_k = []
tail_k = []
for kmax in k_grid:
    sr = mjd_merton_series_price(S0, K_atm, T30, r_f, sig_m, lam_m, muj_m, sigj_m, k_max=int(kmax), use_lambda_prime=True)
    calls_k.append(sr["call"])
    tail_k.append(sr["tail_mass"])

fig, axes = plt.subplots(2, 2, figsize=(16, 10))

ax = axes[0,0]
ax.bar(ks[:26], w[:26], color='#1B3A6B', alpha=0.85, edgecolor='black', linewidth=0.3)
ax.set_title('Risk-neutral Poisson weights:  P(N(T)=k)', fontweight='bold')
ax.set_xlabel('k jumps before expiry'); ax.set_ylabel('Probability mass')
ax.grid(True, alpha=0.25, axis='y')
ax.text(
    0.98,
    0.95,
    f"lambda'={series['lam_q']:.2f}/yr\nT={T30*252:.0f}d",
    transform=ax.transAxes,
    ha='right',
    va='top',
    fontsize=11,
    color='#333333',
    bbox=dict(boxstyle='round,pad=0.35', facecolor='white', alpha=0.85, edgecolor='#999999'),
)

ax = axes[0,1]
ax.plot(ks, cum, color='#C8521A', lw=2.5)
ax.axhline(0.999, color='gray', ls='--', lw=1)
ax.axhline(0.9999, color='gray', ls=':', lw=1)
ax.set_ylim(0.95, 1.00005)
ax.set_title('Cumulative mass  Σ P(N≤k)  (tail mass vanishes fast)', fontweight='bold')
ax.set_xlabel('k'); ax.set_ylabel('Cumulative probability')
ax.grid(True, alpha=0.25)

ax = axes[1,0]
ax.plot(k_grid, calls_k, 'o-', color='#1B3A6B', lw=2, ms=4)
ax.set_title('Merton series call price convergence vs truncation k_max', fontweight='bold')
ax.set_xlabel('k_max (truncate series at k_max)'); ax.set_ylabel('Call Price (₹)')
ax.grid(True, alpha=0.25)
ax.annotate('Beyond ~20 terms: change is negligible', xy=(20, calls_k[20]), xytext=(10, calls_k[20]*1.02),
            arrowprops=dict(arrowstyle='->', color='red', lw=1.5),
            fontsize=10, color='red', fontweight='bold')

ax = axes[1,1]
ax.semilogy(k_grid, np.maximum(tail_k, 1e-20), 's-', color='darkred', lw=2, ms=4)
ax.set_title('Tail probability mass  1 − Σ_{k=0}^{k_max} P(N=k)', fontweight='bold')
ax.set_xlabel('k_max'); ax.set_ylabel('Tail mass (log scale)')
ax.grid(True, alpha=0.25)
ax.annotate('k! grows fast ⇒ weights after k≈20 are tiny', xy=(20, max(tail_k[20],1e-20)),
            xytext=(7, 1e-6), arrowprops=dict(arrowstyle='->', color='darkred', lw=1.5),
            fontsize=10, color='darkred', fontweight='bold')

plt.suptitle('Why truncating the Merton infinite series is safe (Law of Total Expectation + Poisson tails)',
             fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout(); plt.savefig(f'{FIG}15_merton_series_truncation.png'); plt.close()

print(f'\n=== ALL FIGURES GENERATED ===')
for f in sorted(os.listdir(FIG)):
    if f.endswith('.png') and not f.startswith('eq_'): print(f'  {f}')
print(f'  + equation PNGs (eq_*.png)')
