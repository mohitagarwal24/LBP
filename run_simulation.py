"""
Run all simulations and generate figures for the presentation.
This is a standalone Python script equivalent to the Jupyter notebook.
"""

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import norm, probplot, gaussian_kde, chi2
from scipy.optimize import minimize, brentq
from scipy.special import factorial
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import math
import warnings
import os
warnings.filterwarnings('ignore')

plt.rcParams.update({
    'figure.figsize': (14, 6),
    'font.size': 12,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'legend.fontsize': 10,
    'figure.dpi': 150,
    'savefig.dpi': 150,
    'savefig.bbox': 'tight'
})

FIGURES_DIR = 'figures/'
os.makedirs(FIGURES_DIR, exist_ok=True)

# ============================================================
# 1. DATA ACQUISITION
# ============================================================
print('1. Downloading NIFTY 50 data...')
ticker = '^NSEI'
data = yf.download(ticker, start='2018-01-01', end='2024-12-31')
prices = data['Close'].dropna()
if isinstance(prices, pd.DataFrame):
    prices = prices.iloc[:, 0]
log_returns = np.log(prices / prices.shift(1)).dropna()
r = log_returns.values
dt = 1/252

print(f'  Period: {prices.index[0].date()} to {prices.index[-1].date()}')
print(f'  Observations: {len(log_returns)}')
print(f'  Mean: {r.mean():.6f}, Std: {r.std():.6f}, Skew: {log_returns.skew():.4f}, Kurt: {log_returns.kurtosis():.4f}')

# ============================================================
# Figure 1: Data Overview
# ============================================================
print('  Generating Figure 1: Data Overview...')
fig, axes = plt.subplots(2, 2, figsize=(16, 10))

ax = axes[0, 0]
ax.plot(prices.index, prices.values, color='#1B3A6B', linewidth=0.8)
events = {
    '2018-09-21': 'IL&FS Crisis',
    '2020-03-23': 'COVID Crash',
    '2022-02-24': 'Russia-Ukraine',
    '2024-06-04': 'Election Surprise'
}
for date_str, label in events.items():
    date = pd.Timestamp(date_str)
    ax.axvline(date, color='red', alpha=0.5, linestyle='--', linewidth=0.8)
    ylim = ax.get_ylim()
    ax.text(date, ylim[1]*0.95, label, rotation=45, fontsize=7, ha='right', color='red')
ax.set_title('NIFTY 50 Price History (2018-2024) with Key Events')
ax.set_ylabel('Price (INR)')
ax.grid(True, alpha=0.3)

ax = axes[0, 1]
ax.plot(log_returns.index, log_returns.values, color='#C8521A', linewidth=0.3, alpha=0.8)
ax.axhline(0, color='black', linewidth=0.5)
ax.set_title('Daily Log Returns')
ax.set_ylabel('Log Return')
ax.grid(True, alpha=0.3)

ax = axes[1, 0]
ax.hist(r, bins=100, density=True, color='#1B3A6B', alpha=0.6, label='Empirical')
x_range = np.linspace(r.min(), r.max(), 500)
ax.plot(x_range, norm.pdf(x_range, r.mean(), r.std()), 'r-', linewidth=2, label=f'Normal fit')
ax.set_title('Return Distribution vs Normal')
ax.set_xlabel('Log Return')
ax.set_ylabel('Density')
ax.legend()
ax.grid(True, alpha=0.3)

ax = axes[1, 1]
bins_left = np.linspace(-0.15, -0.01, 80)
ax.hist(r[r < -0.01], bins=bins_left, density=True, color='#1B3A6B', alpha=0.6, label='Empirical NIFTY')
x_left = np.linspace(-0.15, -0.01, 300)
ax.plot(x_left, norm.pdf(x_left, r.mean(), r.std()), 'r-', linewidth=2.5, label='Normal (BS) fit')
ax.axvline(np.percentile(r, 1), color='darkred', ls='--', lw=2, label=f'1% VaR = {np.percentile(r,1)*100:.2f}%')
ax.axvline(np.percentile(r, 0.5), color='orange', ls='--', lw=2, label=f'0.5% VaR = {np.percentile(r,0.5)*100:.2f}%')
ax.set_title('LEFT TAIL ZOOM: BS Underestimates Crash Risk', fontweight='bold')
ax.set_xlabel('Log Return')
ax.set_ylabel('Density')
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)
ax.annotate('Fat tails!\nBS assigns near-zero\nprobability here',
            xy=(-0.08, 0.5), fontsize=9, color='red', fontweight='bold',
            ha='center')

plt.tight_layout()
plt.savefig(f'{FIGURES_DIR}01_data_overview.png')
plt.close()

# ============================================================
# 2. BLACK-SCHOLES MLE
# ============================================================
print('2. Black-Scholes MLE...')

def neg_log_likelihood_bs(params, returns, dt=1/252):
    mu, sigma = params
    if sigma <= 0:
        return 1e10
    mean = (mu - 0.5 * sigma**2) * dt
    var = sigma**2 * dt
    ll = np.sum(norm.logpdf(returns, loc=mean, scale=np.sqrt(var)))
    return -ll

mu0 = r.mean() / dt + 0.5 * (r.std() / np.sqrt(dt))**2
sigma0 = r.std() / np.sqrt(dt)

result_bs = minimize(neg_log_likelihood_bs, x0=[mu0, sigma0],
                     args=(r, dt), method='Nelder-Mead',
                     options={'xatol': 1e-8, 'fatol': 1e-8})

mu_mle, sigma_mle = result_bs.x
ll_bs = -result_bs.fun
print(f'  mu={mu_mle:.4f}, sigma={sigma_mle:.4f}, LL={ll_bs:.2f}')

# ============================================================
# BS Pricing
# ============================================================
def black_scholes(S, K, T, r_f, sigma, option_type='call'):
    d1 = (np.log(S / K) + (r_f + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if option_type == 'call':
        price = S * norm.cdf(d1) - K * np.exp(-r_f * T) * norm.cdf(d2)
    else:
        price = K * np.exp(-r_f * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    return price, d1, d2

S0 = float(prices.iloc[-1])
K = round(S0 / 100) * 100
T = 30 / 252
r_f = 0.065

call_bs, d1, d2 = black_scholes(S0, K, T, r_f, sigma_mle, 'call')
put_bs, _, _ = black_scholes(S0, K, T, r_f, sigma_mle, 'put')
print(f'  BS Call={call_bs:.2f}, Put={put_bs:.2f}')

# ============================================================
# BS Monte Carlo
# ============================================================
def bs_monte_carlo(S0, K, T, r_f, sigma, n_paths=100_000, n_steps=252, seed=42):
    np.random.seed(seed)
    dt_mc = T / n_steps
    Z = np.random.standard_normal((n_paths, n_steps))
    inc = (r_f - 0.5 * sigma**2) * dt_mc + sigma * np.sqrt(dt_mc) * Z
    log_S = np.log(S0) + np.cumsum(inc, axis=1)
    S_T = np.exp(log_S[:, -1])
    payoff_call = np.maximum(S_T - K, 0)
    payoff_put = np.maximum(K - S_T, 0)
    discount = np.exp(-r_f * T)
    mc_call = discount * payoff_call.mean()
    mc_put = discount * payoff_put.mean()
    se_call = discount * payoff_call.std() / np.sqrt(n_paths)
    se_put = discount * payoff_put.std() / np.sqrt(n_paths)
    return mc_call, mc_put, se_call, se_put, log_S

mc_call_bs, mc_put_bs, se_c, se_p, log_paths_bs = bs_monte_carlo(S0, K, T, r_f, sigma_mle)
print(f'  MC Call={mc_call_bs:.2f}, MC Put={mc_put_bs:.2f}')

# ============================================================
# Figure 2: BS Paths and Terminal Distribution
# ============================================================
print('  Generating Figure 2: BS Paths...')
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

ax = axes[0]
n_show = 15
t_grid = np.linspace(0, T, log_paths_bs.shape[1])
for i in range(n_show):
    ax.plot(t_grid * 252, np.exp(log_paths_bs[i, :]), linewidth=0.6, alpha=0.7)
ax.axhline(K, color='red', linestyle='--', label=f'Strike K={K:.0f}')
ax.set_title('Sample GBM Price Paths (Black-Scholes)')
ax.set_xlabel('Trading Days')
ax.set_ylabel('Price (INR)')
ax.legend()
ax.grid(True, alpha=0.3)

ax = axes[1]
S_T_bs = np.exp(log_paths_bs[:, -1])
ax.hist(S_T_bs, bins=150, density=True, color='#1B3A6B', alpha=0.6)
ax.axvline(K, color='red', linestyle='--', linewidth=2, label=f'Strike K={K:.0f}')
ax.axvline(S0, color='green', linestyle='--', linewidth=2, label=f'S0={S0:.0f}')
ax.set_title('BS Terminal Price Distribution S(T)')
ax.set_xlabel('Price (INR)')
ax.set_ylabel('Density')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{FIGURES_DIR}02_bs_paths_and_terminal.png')
plt.close()

# ============================================================
# 3. MERTON JUMP-DIFFUSION MLE
# ============================================================
print('3. Merton Jump-Diffusion MLE...')

def mjd_log_likelihood(params, returns, dt=1/252, n_terms=15):
    mu, sigma, lam, mu_j, sigma_j = params
    if sigma <= 0 or lam < 0 or sigma_j <= 0:
        return 1e10
    lam_dt = lam * dt
    mu_tilde = mu - 0.5 * sigma**2
    ks = np.arange(n_terms)
    log_poisson = -lam_dt + ks * np.log(lam_dt + 1e-300) - np.array([np.sum(np.log(np.arange(1, k+1))) for k in ks])
    means = mu_tilde * dt + ks * mu_j
    variances = sigma**2 * dt + ks * sigma_j**2
    variances = np.maximum(variances, 1e-20)
    stds = np.sqrt(variances)
    R = returns[:, None]
    log_terms = log_poisson[None, :] + norm.logpdf(R, loc=means[None, :], scale=stds[None, :])
    max_log = np.max(log_terms, axis=1)
    ll = np.sum(max_log + np.log(np.sum(np.exp(log_terms - max_log[:, None]), axis=1)))
    return -ll

x0 = [mu_mle, sigma_mle * 0.8, 5.0, -0.02, 0.05]
bounds = [(None, None), (1e-4, None), (0, 50), (-0.5, 0.5), (1e-4, 1.0)]

res_mjd = minimize(mjd_log_likelihood, x0=x0, args=(r, 1/252, 15),
                   method='L-BFGS-B', bounds=bounds,
                   options={'maxiter': 500})

mu_m, sig_m, lam_m, muj_m, sigj_m = res_mjd.x
ll_mjd = -res_mjd.fun
print(f'  mu={mu_m:.4f}, sigma={sig_m:.4f}, lambda={lam_m:.4f}, mu_j={muj_m:.6f}, sigma_j={sigj_m:.6f}')
print(f'  LL={ll_mjd:.2f}')

LRT = 2 * (ll_mjd - ll_bs)
p_value = 1 - chi2.cdf(LRT, df=3)
print(f'  LRT={LRT:.4f}, p-value={p_value:.2e}')

aic_bs = 2*2 - 2*ll_bs
aic_mjd = 2*5 - 2*ll_mjd
bic_bs = 2*np.log(len(r)) - 2*ll_bs
bic_mjd = 5*np.log(len(r)) - 2*ll_mjd

# ============================================================
# MJD Monte Carlo
# ============================================================
def mjd_monte_carlo(S0, K, T, r_f, sigma, lam, mu_j, sigma_j,
                    n_paths=100_000, n_steps=252, seed=42, return_paths=False):
    np.random.seed(seed)
    dt_mc = T / n_steps
    kappa = np.exp(mu_j + 0.5 * sigma_j**2) - 1
    mu_rn = r_f - 0.5 * sigma**2 - lam * kappa

    log_S = np.full(n_paths, np.log(S0))
    if return_paths:
        all_log_S = np.zeros((n_paths, n_steps))

    for step in range(n_steps):
        Z = np.random.standard_normal(n_paths)
        N_jumps = np.random.poisson(lam * dt_mc, n_paths)
        J = np.where(N_jumps > 0,
                     np.array([np.random.normal(mu_j, sigma_j, int(n)).sum() if n > 0 else 0.0
                              for n in N_jumps]),
                     0.0)
        log_S += mu_rn * dt_mc + sigma * np.sqrt(dt_mc) * Z + J
        if return_paths:
            all_log_S[:, step] = log_S

    S_T = np.exp(log_S)
    payoff_call = np.maximum(S_T - K, 0)
    payoff_put = np.maximum(K - S_T, 0)
    discount = np.exp(-r_f * T)

    result = (discount * payoff_call.mean(), discount * payoff_put.mean(),
              discount * payoff_call.std() / np.sqrt(n_paths),
              discount * payoff_put.std() / np.sqrt(n_paths))
    if return_paths:
        return result + (all_log_S,)
    return result

mjd_call, mjd_put, se_jc, se_jp, log_paths_mjd = mjd_monte_carlo(
    S0, K, T, r_f, sig_m, lam_m, muj_m, sigj_m, return_paths=True)
print(f'  MJD MC Call={mjd_call:.2f}, Put={mjd_put:.2f}')

# ============================================================
# Figure 3: GBM vs MJD Paths — 1 year horizon, jumps emphasized
# ============================================================
print('  Generating Figure 3: GBM vs MJD Paths...')
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

T_demo = 1.0
n_steps_demo = 252
dt_demo = T_demo / n_steps_demo
t_demo = np.arange(n_steps_demo)

# Top-left: GBM paths (smooth)
ax = axes[0, 0]
np.random.seed(42)
for i in range(6):
    Z = np.random.standard_normal(n_steps_demo)
    log_s = np.log(S0) + np.cumsum((r_f - 0.5*sigma_mle**2)*dt_demo + sigma_mle*np.sqrt(dt_demo)*Z)
    ax.plot(t_demo, np.exp(log_s), linewidth=1.2, alpha=0.8)
ax.axhline(S0, color='gray', linestyle=':', alpha=0.5)
ax.set_title('GBM Paths (Black-Scholes) — Smooth, No Jumps', fontsize=12, fontweight='bold')
ax.set_xlabel('Trading Days')
ax.set_ylabel('Price (INR)')
ax.grid(True, alpha=0.3)

# Top-right: MJD paths with jump markers
ax = axes[0, 1]
np.random.seed(100)
kappa_demo = np.exp(muj_m + 0.5*sigj_m**2) - 1
mu_rn_demo = r_f - 0.5*sig_m**2 - lam_m*kappa_demo
path_colors = plt.cm.tab10(np.linspace(0, 1, 6))
for i in range(6):
    Z = np.random.standard_normal(n_steps_demo)
    N_j = np.random.poisson(lam_m * dt_demo, n_steps_demo)
    J = np.array([np.random.normal(muj_m, sigj_m, int(n)).sum() if n > 0 else 0.0 for n in N_j])
    log_s = np.log(S0) + np.cumsum(mu_rn_demo*dt_demo + sig_m*np.sqrt(dt_demo)*Z + J)
    path = np.exp(log_s)
    ax.plot(t_demo, path, linewidth=1.2, alpha=0.8, color=path_colors[i])
    jump_days = np.where(N_j > 0)[0]
    for jd in jump_days:
        ax.axvline(t_demo[jd], color='red', alpha=0.08, linewidth=1)
    if len(jump_days) > 0:
        ax.scatter(t_demo[jump_days], path[jump_days], s=40, c='red',
                   zorder=5, alpha=0.7, edgecolors='darkred', linewidths=0.5)
ax.scatter([], [], s=40, c='red', edgecolors='darkred', label='Jump events')
ax.axhline(S0, color='gray', linestyle=':', alpha=0.5)
ax.set_title('MJD Paths — Jumps Marked (red dots)', fontsize=12, fontweight='bold')
ax.set_xlabel('Trading Days')
ax.set_ylabel('Price (INR)')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

# Bottom-left: Single path decomposition — diffusion only vs diffusion+jumps
ax = axes[1, 0]
np.random.seed(77)
Z_single = np.random.standard_normal(n_steps_demo)
N_j_single = np.random.poisson(lam_m * dt_demo, n_steps_demo)
J_single = np.array([np.random.normal(muj_m, sigj_m, int(n)).sum() if n > 0 else 0.0 for n in N_j_single])

log_s_diff = np.log(S0) + np.cumsum(mu_rn_demo*dt_demo + sig_m*np.sqrt(dt_demo)*Z_single)
log_s_full = np.log(S0) + np.cumsum(mu_rn_demo*dt_demo + sig_m*np.sqrt(dt_demo)*Z_single + J_single)

ax.plot(t_demo, np.exp(log_s_diff), color='#1B3A6B', linewidth=2, label='Diffusion only (no jumps)', alpha=0.8)
ax.plot(t_demo, np.exp(log_s_full), color='#C8521A', linewidth=2, label='Diffusion + Jumps (MJD)', alpha=0.9)
jump_days_s = np.where(N_j_single > 0)[0]
for jd in jump_days_s:
    price_before = np.exp(log_s_full[max(0,jd-1)] if jd > 0 else np.log(S0))
    price_after = np.exp(log_s_full[jd])
    ax.annotate('', xy=(t_demo[jd], price_after), xytext=(t_demo[jd], price_before),
                arrowprops=dict(arrowstyle='->', color='red', lw=1.5))
ax.scatter(t_demo[jump_days_s], np.exp(log_s_full[jump_days_s]), s=50, c='red',
           zorder=5, edgecolors='darkred', linewidths=1, label='Jump impact')
ax.set_title('Single Path Decomposition: Diffusion vs Full MJD', fontsize=12, fontweight='bold')
ax.set_xlabel('Trading Days')
ax.set_ylabel('Price (INR)')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# Bottom-right: Jump sizes histogram
ax = axes[1, 1]
np.random.seed(42)
n_jump_samples = 10000
jump_sizes = np.random.normal(muj_m, sigj_m, n_jump_samples)
ax.hist(jump_sizes * 100, bins=80, density=True, color='#C8521A', alpha=0.7, edgecolor='black', linewidth=0.3)
ax.axvline(muj_m * 100, color='darkred', linewidth=2, linestyle='--',
           label=f'Mean jump = {muj_m*100:.2f}%')
ax.axvline(0, color='black', linewidth=0.5)
ax.fill_betweenx([0, ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else 50], -15, muj_m*100 - 2*sigj_m*100,
                 alpha=0.15, color='red', label='Large negative jumps')
ax.set_title(f'Distribution of Jump Sizes J ~ N({muj_m*100:.2f}%, {sigj_m*100:.2f}%)', fontsize=12, fontweight='bold')
ax.set_xlabel('Jump Size (%)')
ax.set_ylabel('Density')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

plt.suptitle(f'GBM vs MJD: Estimated λ = {lam_m:.1f} jumps/year, μ_J = {muj_m*100:.2f}%, σ_J = {sigj_m*100:.2f}%',
             fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig(f'{FIGURES_DIR}03_gbm_vs_mjd_paths.png')
plt.close()

# ============================================================
# Figure 4: Tail Behavior Comparison
# ============================================================
print('  Generating Figure 4: Tail Behavior...')
n_sim = 200_000
np.random.seed(42)

bs_rets = np.random.normal((mu_mle - 0.5*sigma_mle**2)*dt, sigma_mle*np.sqrt(dt), n_sim)

Z_sim = np.random.standard_normal(n_sim)
N_j_sim = np.random.poisson(lam_m * dt, n_sim)
J_j_sim = np.array([np.random.normal(muj_m, sigj_m, int(n)).sum() if n > 0 else 0.0 for n in N_j_sim])
mjd_rets = (mu_m - 0.5*sig_m**2)*dt + sig_m*np.sqrt(dt)*Z_sim + J_j_sim

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

ax = axes[0]
bins = np.linspace(-0.08, 0.08, 200)
ax.hist(r, bins=bins, density=True, alpha=0.5, color='gray', label='Empirical NIFTY')
ax.hist(bs_rets, bins=bins, density=True, alpha=0.4, color='#1B3A6B', label='BS (Gaussian)')
ax.hist(mjd_rets, bins=bins, density=True, alpha=0.4, color='#C8521A', label='MJD (Mixture)')
ax.set_title('Return Distributions', fontweight='bold')
ax.set_xlabel('Daily Log Return')
ax.set_ylabel('Density')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

ax = axes[1]
bins_tail = np.linspace(-0.10, -0.02, 100)
ax.hist(r, bins=bins_tail, density=True, alpha=0.5, color='gray', label='Empirical NIFTY')
ax.hist(bs_rets, bins=bins_tail, density=True, alpha=0.4, color='#1B3A6B', label='BS')
ax.hist(mjd_rets, bins=bins_tail, density=True, alpha=0.4, color='#C8521A', label='MJD')
ax.axvline(np.percentile(r, 1), color='red', ls='--', lw=2, label='1% Empirical VaR')
ax.set_title('LEFT TAIL Zoom (Crash Risk)', fontweight='bold')
ax.set_xlabel('Daily Log Return')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

ax = axes[2]
x_kde = np.linspace(-0.08, 0.08, 500)
kde_emp = gaussian_kde(r)
kde_bs = gaussian_kde(bs_rets)
kde_mjd = gaussian_kde(mjd_rets)
ax.plot(x_kde, kde_emp(x_kde), 'k-', linewidth=2.5, label='Empirical NIFTY')
ax.plot(x_kde, kde_bs(x_kde), '--', color='#1B3A6B', linewidth=2, label='BS')
ax.plot(x_kde, kde_mjd(x_kde), '--', color='#C8521A', linewidth=2, label='MJD')
ax.set_title('KDE Density Comparison', fontweight='bold')
ax.set_xlabel('Daily Log Return')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{FIGURES_DIR}04_tail_behavior_comparison.png')
plt.close()

# ============================================================
# Figure 5: QQ Plots
# ============================================================
print('  Generating Figure 5: QQ Plots...')
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

ax = axes[0]
probplot(r, dist='norm', plot=ax)
ax.set_title('QQ Plot: Empirical vs Normal (BS)', fontweight='bold')
ax.get_lines()[0].set_color('#1B3A6B')
ax.get_lines()[0].set_markersize(3)
ax.grid(True, alpha=0.3)

ax = axes[1]
emp_sorted = np.sort(r)
mjd_sorted = np.sort(mjd_rets[:len(r)])
ax.scatter(mjd_sorted, emp_sorted, s=3, color='#C8521A', alpha=0.5)
lims = [min(emp_sorted.min(), mjd_sorted.min()), max(emp_sorted.max(), mjd_sorted.max())]
ax.plot(lims, lims, 'k--', linewidth=1, label='45 deg line')
ax.set_xlabel('MJD Quantiles')
ax.set_ylabel('Empirical Quantiles')
ax.set_title('QQ Plot: Empirical vs MJD', fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{FIGURES_DIR}05_qq_plots.png')
plt.close()

# ============================================================
# Figure 6: Model Comparison Criteria
# ============================================================
print('  Generating Figure 6: Model Comparison Criteria...')
fig, axes = plt.subplots(1, 3, figsize=(16, 5))

models = ['Black-Scholes', 'Merton JD']
colors = ['#1B3A6B', '#C8521A']

ax = axes[0]
bars = ax.bar(models, [ll_bs, ll_mjd], color=colors, alpha=0.8, edgecolor='black')
for bar, val in zip(bars, [ll_bs, ll_mjd]):
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 10,
            f'{val:.1f}', ha='center', va='bottom', fontweight='bold')
ax.set_title('Log-Likelihood', fontweight='bold')
ax.set_ylabel('Log-Likelihood')
ax.grid(True, alpha=0.3, axis='y')

ax = axes[1]
bars = ax.bar(models, [aic_bs, aic_mjd], color=colors, alpha=0.8, edgecolor='black')
for bar, val in zip(bars, [aic_bs, aic_mjd]):
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1,
            f'{val:.1f}', ha='center', va='bottom', fontweight='bold')
ax.set_title('AIC (lower is better)', fontweight='bold')
ax.set_ylabel('AIC')
ax.grid(True, alpha=0.3, axis='y')

ax = axes[2]
bars = ax.bar(models, [bic_bs, bic_mjd], color=colors, alpha=0.8, edgecolor='black')
for bar, val in zip(bars, [bic_bs, bic_mjd]):
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1,
            f'{val:.1f}', ha='center', va='bottom', fontweight='bold')
ax.set_title('BIC (lower is better)', fontweight='bold')
ax.set_ylabel('BIC')
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(f'{FIGURES_DIR}06_model_comparison_criteria.png')
plt.close()

# ============================================================
# Figure 7: Implied Volatility Smile
# ============================================================
print('  Generating Figure 7: IV Smile...')
strikes = np.linspace(S0 * 0.85, S0 * 1.15, 25)
iv_from_mjd = []

def bs_iv(market_price, S, K, T, r_f, option_type='call'):
    def objective(sigma):
        p, _, _ = black_scholes(S, K, T, r_f, sigma, option_type)
        return p - market_price
    try:
        return brentq(objective, 0.01, 3.0)
    except:
        return np.nan

for Ki in strikes:
    mjd_price, _, _, _ = mjd_monte_carlo(S0, Ki, T, r_f, sig_m, lam_m, muj_m, sigj_m,
                                          n_paths=50_000, n_steps=60, seed=42)
    iv = bs_iv(mjd_price, S0, Ki, T, r_f, 'call')
    iv_from_mjd.append(iv)

iv_from_mjd = np.array(iv_from_mjd)
moneyness = strikes / S0

fig, ax = plt.subplots(figsize=(12, 6))
valid = ~np.isnan(iv_from_mjd)
ax.plot(moneyness[valid], iv_from_mjd[valid] * 100, 'o-', color='#C8521A',
        linewidth=2, markersize=5, label='BS IV from MJD prices')
ax.axhline(sigma_mle * 100, color='#1B3A6B', linestyle='--', linewidth=2,
           label=f'BS constant sigma = {sigma_mle*100:.1f}%')
ax.axvline(1.0, color='gray', linestyle=':', alpha=0.5, label='ATM (K/S0 = 1)')
ax.set_xlabel('Moneyness (K/S0)', fontsize=12)
ax.set_ylabel('Implied Volatility (%)', fontsize=12)
ax.set_title('Implied Volatility Smile: MJD generates skew that BS cannot produce',
             fontweight='bold', fontsize=13)
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{FIGURES_DIR}07_implied_volatility_smile.png')
plt.close()

# ============================================================
# Figure 8: Parameter Sensitivity Heatmap
# ============================================================
print('  Generating Figure 8: Sensitivity Heatmap...')
lambda_range = np.linspace(0.5, 30, 12)
sigj_range = np.linspace(0.01, 0.15, 12)
price_grid = np.zeros((len(sigj_range), len(lambda_range)))

for i, sj in enumerate(sigj_range):
    for j, lm in enumerate(lambda_range):
        p, _, _, _ = mjd_monte_carlo(S0, K, T, r_f, sig_m, lm, muj_m, sj,
                                      n_paths=15_000, n_steps=30, seed=42)
        price_grid[i, j] = p

fig, ax = plt.subplots(figsize=(12, 8))
sns.heatmap(price_grid,
            xticklabels=[f'{l:.0f}' for l in lambda_range],
            yticklabels=[f'{s:.3f}' for s in sigj_range],
            annot=True, fmt='.0f', cmap='YlOrRd', ax=ax)
ax.set_xlabel('Lambda (Jump Intensity, jumps/year)', fontsize=12)
ax.set_ylabel('sigma_J (Jump Volatility)', fontsize=12)
ax.set_title('MJD ATM Call Price (INR) - Sensitivity to Jump Parameters',
             fontweight='bold', fontsize=13)

plt.tight_layout()
plt.savefig(f'{FIGURES_DIR}08_parameter_sensitivity_heatmap.png')
plt.close()

# ============================================================
# Figure 9: MC Convergence
# ============================================================
print('  Generating Figure 9: MC Convergence...')
path_counts = [100, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 200000]

mc_prices_bs = []
mc_ses_bs = []
mc_prices_mjd = []
mc_ses_mjd = []

for N in path_counts:
    c_bs, _, se_bs, _, _ = bs_monte_carlo(S0, K, T, r_f, sigma_mle, n_paths=N, seed=42)
    mc_prices_bs.append(c_bs)
    mc_ses_bs.append(se_bs)
    c_mjd, _, se_mjd, _ = mjd_monte_carlo(S0, K, T, r_f, sig_m, lam_m, muj_m, sigj_m,
                                            n_paths=N, n_steps=60, seed=42)
    mc_prices_mjd.append(c_mjd)
    mc_ses_mjd.append(se_mjd)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

ax = axes[0]
ax.semilogx(path_counts, mc_prices_bs, 'o-', color='#1B3A6B', label='BS MC Price')
ax.fill_between(path_counts,
                [p - 1.96*s for p, s in zip(mc_prices_bs, mc_ses_bs)],
                [p + 1.96*s for p, s in zip(mc_prices_bs, mc_ses_bs)],
                alpha=0.2, color='#1B3A6B')
ax.axhline(call_bs, color='red', linestyle='--', label=f'BS Closed-Form = {call_bs:.2f}')
ax.set_title('BS MC Convergence', fontweight='bold')
ax.set_xlabel('Number of Paths (log scale)')
ax.set_ylabel('Call Price (INR)')
ax.legend()
ax.grid(True, alpha=0.3)

ax = axes[1]
ax.loglog(path_counts, [1.96*s for s in mc_ses_bs], 'o-', color='#1B3A6B', label='BS MC SE')
ax.loglog(path_counts, [1.96*s for s in mc_ses_mjd], 's-', color='#C8521A', label='MJD MC SE')
N_ref = np.array(path_counts, dtype=float)
ax.loglog(N_ref, mc_ses_bs[0]*1.96 * np.sqrt(path_counts[0]) / np.sqrt(N_ref),
          'k--', alpha=0.5, label='1/sqrt(N) reference')
ax.set_title('MC Standard Error (95% CI width)', fontweight='bold')
ax.set_xlabel('Number of Paths')
ax.set_ylabel('95% CI Half-Width (INR)')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{FIGURES_DIR}09_mc_convergence.png')
plt.close()

# ============================================================
# Figure 10: Event Analysis
# ============================================================
print('  Generating Figure 10: Event Analysis...')
event_dates = {
    'IL&FS Crisis\n(Sep 2018)': '2018-09-21',
    'COVID Crash\n(Mar 2020)': '2020-03-23',
    'Russia-Ukraine\n(Feb 2022)': '2022-02-24',
    'Election Surprise\n(Jun 2024)': '2024-06-04'
}

fig, axes = plt.subplots(2, 2, figsize=(16, 10))

for idx, (label, date_str) in enumerate(event_dates.items()):
    ax = axes[idx // 2, idx % 2]
    event_date = pd.Timestamp(date_str)
    window_start = event_date - pd.Timedelta(days=60)
    window_end = event_date + pd.Timedelta(days=60)
    mask = (prices.index >= window_start) & (prices.index <= window_end)
    window_prices = prices[mask]

    ax.plot(window_prices.index, window_prices.values, color='#1B3A6B', linewidth=1.5)
    ax.axvline(event_date, color='red', linestyle='--', linewidth=2, alpha=0.8)

    nearest_idx = window_prices.index.get_indexer([event_date], method='nearest')[0]
    if 0 < nearest_idx < len(window_prices):
        event_price = window_prices.iloc[nearest_idx]
        ax.scatter([window_prices.index[nearest_idx]], [event_price],
                   color='red', s=100, zorder=5)
        ret_1d = np.log(window_prices.iloc[nearest_idx] / window_prices.iloc[nearest_idx-1])
        ax.text(0.05, 0.95, f'1-day return: {ret_1d*100:.1f}%',
                transform=ax.transAxes, fontsize=10, fontweight='bold',
                color='red', va='top')

    ax.set_title(label.replace('\n', ' '), fontweight='bold', fontsize=12)
    ax.set_ylabel('NIFTY 50')
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30)

plt.suptitle('NIFTY 50 Around Key Market Events (+/- 60 days)', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(f'{FIGURES_DIR}10_event_analysis.png')
plt.close()

# ============================================================
# Figure 11: Tail Risk Probability
# ============================================================
print('  Generating Figure 11: Tail Risk Probability...')
thresholds = np.linspace(-0.15, -0.01, 50)

prob_bs = norm.cdf(thresholds, loc=(mu_mle - 0.5*sigma_mle**2)*dt, scale=sigma_mle*np.sqrt(dt))

def mjd_cdf(x, mu, sigma, lam, mu_j, sigma_j, dt, n_terms=20):
    cdf_val = 0.0
    lam_dt = lam * dt
    for k in range(n_terms):
        m_k = (mu - 0.5*sigma**2)*dt + k*mu_j
        v_k = sigma**2*dt + k*sigma_j**2
        p_k = np.exp(-lam_dt) * lam_dt**k / math.factorial(k)
        cdf_val += p_k * norm.cdf(x, loc=m_k, scale=np.sqrt(v_k))
    return cdf_val

prob_mjd = np.array([mjd_cdf(t, mu_m, sig_m, lam_m, muj_m, sigj_m, dt) for t in thresholds])
emp_prob = np.array([np.mean(r <= t) for t in thresholds])

fig, ax = plt.subplots(figsize=(12, 6))
ax.semilogy(-thresholds*100, emp_prob, 'ko-', markersize=3, label='Empirical NIFTY', linewidth=2)
ax.semilogy(-thresholds*100, prob_bs, '--', color='#1B3A6B', linewidth=2, label='BS (Gaussian)')
ax.semilogy(-thresholds*100, prob_mjd, '--', color='#C8521A', linewidth=2, label='MJD')
ax.axvline(13, color='red', alpha=0.3, linewidth=8, label='COVID crash (13%)')
ax.axvline(8, color='orange', alpha=0.3, linewidth=8, label='Election surprise (8%)')
ax.set_xlabel('Loss Magnitude (% daily drop)', fontsize=12)
ax.set_ylabel('Probability (log scale)', fontsize=12)
ax.set_title('Tail Risk: Probability of Daily Loss Exceeding X%\nBS vastly underestimates crash probability',
             fontweight='bold', fontsize=13)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
ax.invert_xaxis()

plt.tight_layout()
plt.savefig(f'{FIGURES_DIR}11_tail_risk_probability.png')
plt.close()

# ============================================================
# Figure 12: VaR Backtesting
# ============================================================
print('  Generating Figure 12: VaR Backtesting...')
window = 252
var_bs_series = []
var_mjd_series = []
dates_var = []
actual_returns_var = []

for i in range(window, len(r)):
    window_r = r[i-window:i]
    mu_w = window_r.mean() / dt + 0.5 * (window_r.std()/np.sqrt(dt))**2
    sig_w = window_r.std() / np.sqrt(dt)
    var_bs_1pct = norm.ppf(0.01, loc=(mu_w - 0.5*sig_w**2)*dt, scale=sig_w*np.sqrt(dt))
    var_bs_series.append(var_bs_1pct)
    var_mjd_1pct = np.percentile(window_r, 1)
    var_mjd_series.append(var_mjd_1pct)
    dates_var.append(log_returns.index[i])
    actual_returns_var.append(r[i])

var_bs_series = np.array(var_bs_series)
var_mjd_series = np.array(var_mjd_series)
actual_returns_var = np.array(actual_returns_var)

breaches_bs = actual_returns_var < var_bs_series
breaches_mjd = actual_returns_var < var_mjd_series

fig, axes = plt.subplots(2, 1, figsize=(16, 10))

ax = axes[0]
ax.plot(dates_var, actual_returns_var * 100, color='gray', alpha=0.4, linewidth=0.5, label='Actual returns')
ax.plot(dates_var, var_bs_series * 100, color='#1B3A6B', linewidth=1.5, label='BS 1% VaR')
ax.plot(dates_var, var_mjd_series * 100, color='#C8521A', linewidth=1.5, label='Empirical 1% VaR')
breach_idx_bs = np.where(breaches_bs)[0]
ax.scatter(np.array(dates_var)[breach_idx_bs], actual_returns_var[breach_idx_bs]*100,
           c='red', s=15, zorder=5, label=f'BS breaches ({breaches_bs.sum()})')
ax.set_title('Value-at-Risk Backtesting (1% Daily VaR, 252-day rolling)', fontweight='bold')
ax.set_ylabel('Return (%)')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

ax = axes[1]
cum_breaches_bs = np.cumsum(breaches_bs)
cum_breaches_mjd = np.cumsum(breaches_mjd)
expected = np.arange(1, len(breaches_bs)+1) * 0.01
ax.plot(dates_var, cum_breaches_bs, color='#1B3A6B', linewidth=2, label=f'BS breaches (total: {breaches_bs.sum()})')
ax.plot(dates_var, cum_breaches_mjd, color='#C8521A', linewidth=2, label=f'Emp breaches (total: {breaches_mjd.sum()})')
ax.plot(dates_var, expected, 'k--', linewidth=1, label='Expected (1%)')
ax.set_title('Cumulative VaR Breaches', fontweight='bold')
ax.set_ylabel('Cumulative Breaches')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{FIGURES_DIR}12_var_backtesting.png')
plt.close()

# ============================================================
# Figure 13: Variance Reduction
# ============================================================
print('  Generating Figure 13: Variance Reduction...')
np.random.seed(42)
Z_naive = np.random.standard_normal(100_000)
S_T_naive = S0 * np.exp((r_f - 0.5*sigma_mle**2)*T + sigma_mle*np.sqrt(T)*Z_naive)
payoff_naive = np.maximum(S_T_naive - K, 0)
naive_price = np.exp(-r_f*T) * payoff_naive.mean()
naive_se = np.exp(-r_f*T) * payoff_naive.std() / np.sqrt(100_000)

# Antithetic
np.random.seed(42)
n_half = 50_000
Z_anti = np.random.standard_normal(n_half)
S_T_pos = S0 * np.exp((r_f - 0.5*sigma_mle**2)*T + sigma_mle*np.sqrt(T)*Z_anti)
S_T_neg = S0 * np.exp((r_f - 0.5*sigma_mle**2)*T + sigma_mle*np.sqrt(T)*(-Z_anti))
payoff_avg = (np.maximum(S_T_pos - K, 0) + np.maximum(S_T_neg - K, 0)) / 2
anti_price = np.exp(-r_f*T) * payoff_avg.mean()
anti_se = np.exp(-r_f*T) * payoff_avg.std() / np.sqrt(n_half)

# Control Variate
np.random.seed(42)
Z_cv = np.random.standard_normal(100_000)
S_T_cv = S0 * np.exp((r_f - 0.5*sigma_mle**2)*T + sigma_mle*np.sqrt(T)*Z_cv)
payoff_cv = np.maximum(S_T_cv - K, 0)
control = S_T_cv
expected_control = S0 * np.exp(r_f * T)
beta = np.cov(payoff_cv, control)[0, 1] / np.var(control)
adjusted_payoff = payoff_cv - beta * (control - expected_control)
cv_price = np.exp(-r_f*T) * adjusted_payoff.mean()
cv_se = np.exp(-r_f*T) * adjusted_payoff.std() / np.sqrt(100_000)

print(f'  Naive SE={naive_se:.4f}, Anti SE={anti_se:.4f} ({(1-anti_se/naive_se)*100:.0f}% reduction)')
print(f'  CV SE={cv_se:.4f} ({(1-cv_se/naive_se)*100:.0f}% reduction)')

fig, ax = plt.subplots(figsize=(10, 6))
methods = ['Naive MC', 'Antithetic', 'Control Variate']
ses = [naive_se, anti_se, cv_se]
colors_vr = ['#1B3A6B', '#2E8B57', '#C8521A']

ax.bar(methods, ses, color=colors_vr, alpha=0.8, edgecolor='black')
for i, (m, s) in enumerate(zip(methods, ses)):
    ax.text(i, s + 0.0005, f'SE={s:.4f}', ha='center', fontweight='bold', fontsize=11)
ax.set_title('Monte Carlo Standard Error - Variance Reduction Comparison', fontweight='bold')
ax.set_ylabel('Standard Error (INR)')
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig(f'{FIGURES_DIR}13_variance_reduction.png')
plt.close()

# ============================================================
# Figure 14: BS vs MJD Option Prices Across Strikes
# ============================================================
print('  Generating Figure 14: BS vs MJD Option Prices...')
strike_range = np.linspace(S0 * 0.85, S0 * 1.15, 20)
bs_prices_arr = []
mjd_prices_arr = []

for Ki in strike_range:
    p_bs, _, _ = black_scholes(S0, Ki, T, r_f, sigma_mle, 'call')
    bs_prices_arr.append(p_bs)
    p_mjd, _, _, _ = mjd_monte_carlo(S0, Ki, T, r_f, sig_m, lam_m, muj_m, sigj_m,
                                      n_paths=30_000, n_steps=60, seed=42)
    mjd_prices_arr.append(p_mjd)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
moneyness_plot = strike_range / S0

ax = axes[0]
ax.plot(moneyness_plot, bs_prices_arr, 'o-', color='#1B3A6B', linewidth=2, label='Black-Scholes')
ax.plot(moneyness_plot, mjd_prices_arr, 's-', color='#C8521A', linewidth=2, label='Merton JD')
ax.axvline(1.0, color='gray', linestyle=':', alpha=0.5)
ax.set_xlabel('Moneyness (K/S0)', fontsize=12)
ax.set_ylabel('Call Price (INR)', fontsize=12)
ax.set_title('European Call Prices: BS vs MJD', fontweight='bold')
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)

ax = axes[1]
ax.plot(moneyness_plot, np.array(mjd_prices_arr) - np.array(bs_prices_arr), 's-',
        color='#C8521A', linewidth=2, label='MJD - BS')
ax.axhline(0, color='black', linewidth=0.5)
ax.axvline(1.0, color='gray', linestyle=':', alpha=0.5)
ax.fill_between(moneyness_plot, 0, np.array(mjd_prices_arr) - np.array(bs_prices_arr),
                where=np.array(mjd_prices_arr) > np.array(bs_prices_arr), alpha=0.2, color='#C8521A')
ax.fill_between(moneyness_plot, 0, np.array(mjd_prices_arr) - np.array(bs_prices_arr),
                where=np.array(mjd_prices_arr) < np.array(bs_prices_arr), alpha=0.2, color='#1B3A6B')
ax.set_xlabel('Moneyness (K/S0)', fontsize=12)
ax.set_ylabel('Price Difference: MJD - BS (INR)', fontsize=12)
ax.set_title('Pricing Deviation from Black-Scholes', fontweight='bold')
ax.legend(fontsize=11)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(f'{FIGURES_DIR}14_bs_vs_mjd_prices.png')
plt.close()

# ============================================================
# Figure 15: Summary Dashboard (BS vs MJD only)
# ============================================================
print('  Generating Figure 15: Summary Dashboard...')
emp_kurt = float(log_returns.kurtosis())
bs_kurt = 0.0
denom = (sig_m**2 + lam_m*(muj_m**2 + sigj_m**2))**2
if denom > 0:
    mjd_kurt_analytical = 3 * lam_m * (muj_m**2 + sigj_m**2)**2 / denom
else:
    mjd_kurt_analytical = 0.0

fig, axes = plt.subplots(2, 3, figsize=(18, 10))

ax = axes[0, 0]
ax.barh(['BS (2 params)', 'MJD (5 params)'], [2, 5], color=['#1B3A6B', '#C8521A'], alpha=0.8)
ax.set_xlabel('Number of Parameters')
ax.set_title('Model Complexity', fontweight='bold')
ax.grid(True, alpha=0.3, axis='x')

ax = axes[0, 1]
bars = ax.bar(['BS', 'MJD'], [ll_bs, ll_mjd], color=['#1B3A6B', '#C8521A'], alpha=0.8, edgecolor='black')
for bar, val in zip(bars, [ll_bs, ll_mjd]):
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
            f'{val:.0f}', ha='center', va='bottom', fontweight='bold', fontsize=10)
ax.set_title('Log-Likelihood (higher = better)', fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')

ax = axes[0, 2]
x_pos = np.arange(2)
width = 0.35
ax.bar(x_pos - width/2, [call_bs, mjd_call], width, color=['#1B3A6B', '#C8521A'],
       alpha=0.8, label='Call')
ax.bar(x_pos + width/2, [put_bs, mjd_put], width, color=['#1B3A6B', '#C8521A'],
       alpha=0.4, label='Put', hatch='//')
ax.set_xticks(x_pos)
ax.set_xticklabels(['BS', 'MJD'])
ax.set_title('ATM Option Prices (INR)', fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

ax = axes[1, 0]
x_kde2 = np.linspace(-0.06, 0.06, 500)
ax.plot(x_kde2, kde_emp(x_kde2), 'k-', linewidth=2.5, label='Empirical')
ax.plot(x_kde2, kde_bs(x_kde2), '--', color='#1B3A6B', linewidth=2, label='BS')
ax.plot(x_kde2, kde_mjd(x_kde2), '--', color='#C8521A', linewidth=2, label='MJD')
ax.set_title('Return Densities (KDE)', fontweight='bold')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

ax = axes[1, 1]
bars = ax.bar(['Empirical', 'BS', 'MJD'], [emp_kurt, bs_kurt, mjd_kurt_analytical],
              color=['gray', '#1B3A6B', '#C8521A'], alpha=0.8, edgecolor='black')
for bar, val in zip(bars, [emp_kurt, bs_kurt, mjd_kurt_analytical]):
    ax.text(bar.get_x() + bar.get_width()/2., max(bar.get_height(), 0) + 0.1,
            f'{val:.2f}', ha='center', fontweight='bold', fontsize=10)
ax.set_title('Excess Kurtosis', fontweight='bold')
ax.grid(True, alpha=0.3, axis='y')

ax = axes[1, 2]
ax.bar(['LRT Statistic'], [LRT], color='#C8521A', alpha=0.8, edgecolor='black')
ax.axhline(chi2.ppf(0.99, 3), color='red', linestyle='--', label=f'chi2(3) 1% crit = {chi2.ppf(0.99,3):.1f}')
ax.axhline(chi2.ppf(0.95, 3), color='orange', linestyle='--', label=f'chi2(3) 5% crit = {chi2.ppf(0.95,3):.1f}')
ax.text(0, LRT + 2, f'LRT = {LRT:.1f}', ha='center', fontweight='bold', fontsize=12)
ax.set_title('Likelihood Ratio Test\nBS vs MJD', fontweight='bold')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3, axis='y')

plt.suptitle('Black-Scholes vs Merton Jump-Diffusion — Comprehensive Comparison',
             fontsize=15, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(f'{FIGURES_DIR}15_summary_comparison.png')
plt.close()

# ============================================================
# DONE
# ============================================================
print('\n=== ALL FIGURES GENERATED SUCCESSFULLY ===')
for f in sorted(os.listdir(FIGURES_DIR)):
    if f.endswith('.png'):
        print(f'  {f}')
print(f'\nTotal: {len([f for f in os.listdir(FIGURES_DIR) if f.endswith(".png")])} figures')
