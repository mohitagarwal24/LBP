"""
End-Term Evaluation: Stochastic Option Pricing on NIFTY 50
Extending BS & MJD (MTE) to Heston and Bates Models
Implements: Convolution-FFT (CFFT-I/II) from Gao & Hyndman (2025),
            Carr-Madan FFT, Heston semi-closed form, Bates FFT pricing
Calibration: MLE on returns + least-squares on implied vol surface
"""

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import norm, chi2
from scipy.optimize import minimize, brentq
from scipy.fft import fft, ifft
from scipy.integrate import quad
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings, os
warnings.filterwarnings('ignore')

plt.rcParams.update({
    'figure.figsize': (14, 6), 'font.size': 12, 'axes.titlesize': 14,
    'axes.labelsize': 12, 'legend.fontsize': 10, 'figure.dpi': 150,
    'savefig.dpi': 150, 'savefig.bbox': 'tight'
})

FIG = 'figures_ete/'
os.makedirs(FIG, exist_ok=True)

print('='*60)
print('ETE: Heston & Bates Option Pricing on NIFTY 50')
print('='*60)

# ============================================================
# 1. DATA
# ============================================================
print('\n1. Downloading NIFTY 50 data...')
data = yf.download('^NSEI', start='2018-01-01', end='2024-12-31')
prices = data['Close'].dropna()
if isinstance(prices, pd.DataFrame):
    prices = prices.iloc[:, 0]
log_returns = np.log(prices / prices.shift(1)).dropna()
r_data = log_returns.values
dt = 1/252
S0 = float(prices.iloc[-1])
r_f = 0.065

print(f'  S0 = {S0:.2f}, Obs = {len(r_data)}')
print(f'  Skew = {log_returns.skew():.3f}, Kurt = {log_returns.kurtosis():.3f}')

# ============================================================
# 2. BS & MJD MLE (recap from MTE)
# ============================================================
print('\n2. BS & MJD calibration (MTE recap)...')

def neg_ll_bs(params, ret, dt=1/252):
    mu, sigma = params
    if sigma <= 0: return 1e10
    m = (mu - 0.5*sigma**2)*dt
    v = sigma**2*dt
    return -np.sum(norm.logpdf(ret, loc=m, scale=np.sqrt(v)))

def neg_ll_mjd(params, ret, dt=1/252, K=15):
    mu, sigma, lam, mu_j, sigma_j = params
    if sigma <= 0 or lam < 0 or sigma_j <= 0: return 1e10
    ld = lam*dt; ks = np.arange(K)
    lp = -ld + ks*np.log(ld+1e-300) - np.array([np.sum(np.log(np.arange(1, k+1))) for k in ks])
    ms = (mu - 0.5*sigma**2)*dt + ks*mu_j
    vs = np.maximum(sigma**2*dt + ks*sigma_j**2, 1e-20)
    R = ret[:, None]
    lt = lp[None, :] + norm.logpdf(R, loc=ms[None, :], scale=np.sqrt(vs)[None, :])
    mx = lt.max(axis=1)
    return -np.sum(mx + np.log(np.sum(np.exp(lt - mx[:, None]), axis=1)))

mu0 = r_data.mean()/dt + 0.5*(r_data.std()/np.sqrt(dt))**2
sig0 = r_data.std()/np.sqrt(dt)
res_bs = minimize(neg_ll_bs, [mu0, sig0], args=(r_data,), method='Nelder-Mead',
                  options={'xatol': 1e-8, 'fatol': 1e-8})
mu_bs, sig_bs = res_bs.x
ll_bs = -res_bs.fun
print(f'  BS:  mu={mu_bs:.4f}, sigma={sig_bs:.4f}, LL={ll_bs:.2f}')

x0 = [mu_bs, sig_bs*0.8, 5.0, -0.02, 0.05]
bnd = [(None, None), (1e-4, None), (0, 50), (-0.5, 0.5), (1e-4, 1.0)]
res_mjd = minimize(neg_ll_mjd, x0, args=(r_data,), method='L-BFGS-B', bounds=bnd,
                   options={'maxiter': 300})
mu_m, sig_m, lam_m, muj_m, sigj_m = res_mjd.x
ll_mjd = -res_mjd.fun
LRT = 2*(ll_mjd - ll_bs)
pval_lrt = 1 - chi2.cdf(LRT, 3)
print(f'  MJD: sigma={sig_m:.4f}, lam={lam_m:.1f}, mu_J={muj_m:.4f}, sig_J={sigj_m:.4f}')
print(f'       LL={ll_mjd:.2f}, LRT={LRT:.1f}, p={pval_lrt:.2e}')

# ============================================================
# 3. HESTON MODEL
# ============================================================
print('\n3. Heston model implementation...')

def heston_cf_stable(p, v, tau, r, kappa, theta, sigma, rho, i_idx=1):
    """
    Stable characteristic function from Gao & Hyndman (2025), Thm 2.1.
    i_idx: 1 for P1 (S-measure), 2 for P2 (Q-measure).
    Returns psi_i(p) with q=0.
    """
    a = kappa * theta
    c_i = 0.5 if i_idx == 1 else -0.5
    b_i = (kappa - rho*sigma) if i_idx == 1 else kappa

    gamma = np.sqrt(sigma**2 * (p**2 - 2j*c_i*p) + (b_i - 1j*sigma*rho*p)**2)
    lam = b_i - 1j*sigma*rho*p

    zeta = 2.0 * gamma / (gamma + lam + (gamma - lam) * np.exp(-gamma * tau))

    exponent = (1j*p*r*tau
                + (gamma + lam)/sigma**2 * (1.0 - zeta) * v
                - (gamma - lam)/sigma**2 * a * tau
                + 2.0*a/sigma**2 * np.log(zeta))

    return np.exp(exponent)


def heston_cf_riskneutral(u, S, tau, r, v0, kappa, theta, sigma, rho):
    """Risk-neutral CF of log(S_T) for Carr-Madan FFT."""
    xi = kappa - sigma*rho*1j*u
    d = np.sqrt(xi**2 + sigma**2*(u*1j + u**2))
    g = (xi - d) / (xi + d)
    C = 1j*u*np.log(S) + 1j*u*r*tau
    C += (kappa*theta/sigma**2) * ((xi - d)*tau - 2*np.log((1 - g*np.exp(-d*tau))/(1 - g)))
    D = ((xi - d)/sigma**2) * (1 - np.exp(-d*tau)) / (1 - g*np.exp(-d*tau))
    return np.exp(C + D*v0)


def heston_semi_closed(S, K, tau, r, v0, kappa, theta, sigma, rho):
    """Semi-closed form using stable CF."""
    def integrand_Pi(p, i_idx):
        psi = heston_cf_stable(p, v0, tau, r, kappa, theta, sigma, rho, i_idx)
        return np.real(psi / (1j * p))

    P1 = 0.5 + (1.0/np.pi) * quad(integrand_Pi, 1e-8, 100, args=(1,), limit=200)[0]
    P2 = 0.5 + (1.0/np.pi) * quad(integrand_Pi, 1e-8, 100, args=(2,), limit=200)[0]
    call = S * P1 - K * np.exp(-r*tau) * P2
    put = call - S + K * np.exp(-r*tau)
    return call, put, P1, P2


# ============================================================
# 4. CFFT METHODS
# ============================================================
print('\n4. CFFT methods implementation...')

def cfft_i_price(S, K, tau, r, v0, kappa, theta, sigma, rho, N=2048, L=10.0):
    """CFFT-I: convolution of indicator with transition kernel (Eq. 3.12)."""
    dx = L / N
    x = np.log(S/K)
    x_grid = (np.arange(N) - N/2) * dx + x
    p_grid = (np.arange(N) - N/2) * (2*np.pi/L)

    delta_func = np.where(x_grid >= 0, 1.0, 0.0)
    w = np.ones(N) * dx
    w[0] = dx / 2; w[-1] = dx / 2

    results = {}
    for i_idx in [1, 2]:
        f = delta_func.copy()
        A_s = (f[-1] - f[0]) / (x_grid[-1] - x_grid[0])
        B_s = (x_grid[-1]*f[0] - x_grid[0]*f[-1]) / (x_grid[-1] - x_grid[0])
        f_tilde = f - (A_s * x_grid + B_s)

        signs = (-1.0)**np.arange(N)
        F_f = fft(w * signs * f_tilde)

        psi_vals = np.zeros(N, dtype=complex)
        for k in range(N):
            pk = p_grid[k]
            if abs(pk) > 1e-12:
                psi_vals[k] = heston_cf_stable(pk, v0, tau, r, kappa, theta, sigma, rho, i_idx)
            else:
                psi_vals[k] = 1.0

        product = w * F_f * psi_vals
        Pi_raw = np.real(signs * ifft(product)) / dx

        dp_val = 1e-5
        psi_0 = heston_cf_stable(1e-12, v0, tau, r, kappa, theta, sigma, rho, i_idx)
        psi_dp = heston_cf_stable(dp_val, v0, tau, r, kappa, theta, sigma, rho, i_idx)
        dpsi = np.imag((psi_dp - psi_0) / dp_val)
        E_shift = -A_s * dpsi + B_s
        Pi = Pi_raw + E_shift
        results[i_idx] = Pi

    idx_x = np.argmin(np.abs(x_grid - x))
    P1 = np.clip(results[1][idx_x], 0, 1)
    P2 = np.clip(results[2][idx_x], 0, 1)
    call = S * P1 - K * np.exp(-r*tau) * P2
    put = call - S + K * np.exp(-r*tau)
    return call, put, P1, P2


def cfft_ii_price(S, K, tau, r, v0, kappa, theta, sigma, rho,
                  N=2048, L=10.0, alpha=-2.0):
    """CFFT-II: damped call convolution (Eq. 3.14)."""
    dx = L / N
    x_center = np.log(S/K)
    x_grid = (np.arange(N) - N/2) * dx + x_center
    p_grid = (np.arange(N) - N/2) * (2*np.pi/L)

    g = np.maximum(K * np.exp(x_grid) - K, 0.0)

    f0p = (-3*g[0] + 4*g[1] - g[2]) / (2*dx)
    fNp = (3*g[-1] - 4*g[-2] + g[-3]) / (2*dx)
    denom = np.exp((alpha+1)*x_grid[-1]) - np.exp((alpha+1)*x_grid[0])
    if abs(denom) > 1e-30:
        A_s = (np.exp(alpha*x_grid[-1])*fNp - np.exp(alpha*x_grid[0])*f0p) / denom
    else:
        A_s = 0.0
    B_s = (x_grid[-1]*g[0] - x_grid[0]*g[-1]) / (x_grid[-1] - x_grid[0])
    h = A_s * np.exp(x_grid) + B_s
    f_tilde = np.exp(alpha * x_grid) * (g - h)

    w = np.ones(N) * dx
    w[0] = dx / 2; w[-1] = dx / 2
    signs = (-1.0)**np.arange(N)
    F_f = fft(w * signs * f_tilde)

    psi2_vals = np.zeros(N, dtype=complex)
    for k in range(N):
        pk = p_grid[k]
        psi2_vals[k] = heston_cf_stable(pk + alpha*1j, v0, tau, r, kappa, theta, sigma, rho, 2)

    product = w * F_f * psi2_vals
    C_damped = np.real(signs * ifft(product)) / dx
    C_grid = np.exp(-r*tau - alpha*x_grid) * C_damped

    psi2_mi = heston_cf_stable(-1j, v0, tau, r, kappa, theta, sigma, rho, 2)
    E_h = np.real(A_s * psi2_mi + B_s)
    C_grid = C_grid + np.exp(-r*tau) * E_h

    idx_x = np.argmin(np.abs(x_grid - x_center))
    call = max(C_grid[idx_x], 0.0)
    put = call - S + K * np.exp(-r*tau)
    return call, put


# ============================================================
# 5. CARR-MADAN FFT
# ============================================================
def carr_madan_heston(S, K_array, tau, r, v0, kappa, theta, sigma, rho,
                      N=4096, alpha_cm=1.5, eta=0.25):
    """Carr & Madan (1999) FFT for Heston."""
    lam_cm = 2*np.pi / (N * eta)
    b = N * lam_cm / 2
    v_j = np.arange(N) * eta
    k_u = -b + np.arange(N) * lam_cm

    simpson = 3 + (-1)**np.arange(1, N+1)
    simpson[0] = 1; simpson = simpson / 3.0

    cf_vals = heston_cf_riskneutral(v_j - (alpha_cm+1)*1j, S, tau, r, v0, kappa, theta, sigma, rho)
    mod_cf = np.exp(-r*tau) * cf_vals / (alpha_cm**2 + alpha_cm - v_j**2 + 1j*(2*alpha_cm+1)*v_j)

    x = np.exp(1j * v_j * b) * mod_cf * eta * simpson
    fft_result = fft(x)
    call_grid = np.exp(-alpha_cm * k_u) / np.pi * np.real(fft_result)
    return np.maximum(np.interp(np.log(np.asarray(K_array)), k_u, call_grid), 0.0)


# ============================================================
# 6. BATES MODEL
# ============================================================
print('\n5. Bates model implementation...')

def bates_cf(u, S, tau, r, v0, kappa, theta, sigma, rho, lam_j, mu_j, sigma_j):
    """Bates (1996) CF = Heston CF * Jump CF."""
    xi = kappa - sigma*rho*1j*u
    d = np.sqrt(xi**2 + sigma**2*(u*1j + u**2))
    g = (xi - d) / (xi + d)
    kappa_j = np.exp(mu_j + 0.5*sigma_j**2) - 1

    C = 1j*u*np.log(S) + 1j*u*(r - lam_j*kappa_j)*tau
    C += (kappa*theta/sigma**2) * ((xi - d)*tau - 2*np.log((1 - g*np.exp(-d*tau))/(1 - g)))
    D = ((xi - d)/sigma**2) * (1 - np.exp(-d*tau)) / (1 - g*np.exp(-d*tau))
    jump_cf = lam_j * tau * (np.exp(1j*u*mu_j - 0.5*sigma_j**2*u**2) - 1)
    return np.exp(C + D*v0 + jump_cf)


def carr_madan_bates(S, K_array, tau, r, v0, kappa, theta, sigma, rho,
                     lam_j, mu_j, sigma_j, N=4096, alpha_cm=1.5, eta=0.25):
    """Carr-Madan FFT for Bates."""
    lam_cm = 2*np.pi / (N * eta)
    b = N * lam_cm / 2
    v_j = np.arange(N) * eta
    k_u = -b + np.arange(N) * lam_cm

    simpson = 3 + (-1)**np.arange(1, N+1)
    simpson[0] = 1; simpson = simpson / 3.0

    cf_vals = np.array([bates_cf(vv - (alpha_cm+1)*1j, S, tau, r, v0, kappa, theta,
                                  sigma, rho, lam_j, mu_j, sigma_j) for vv in v_j])
    mod_cf = np.exp(-r*tau) * cf_vals / (alpha_cm**2 + alpha_cm - v_j**2 + 1j*(2*alpha_cm+1)*v_j)

    x = np.exp(1j * v_j * b) * mod_cf * eta * simpson
    fft_result = fft(x)
    call_grid = np.exp(-alpha_cm * k_u) / np.pi * np.real(fft_result)
    return np.maximum(np.interp(np.log(np.asarray(K_array)), k_u, call_grid), 0.0)


# ============================================================
# 7. BS HELPERS
# ============================================================
def bs_price(S, K, T, rf, sigma, otype='call'):
    d1 = (np.log(S/K) + (rf + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
    d2 = d1 - sigma*np.sqrt(T)
    if otype == 'call': return S*norm.cdf(d1) - K*np.exp(-rf*T)*norm.cdf(d2)
    return K*np.exp(-rf*T)*norm.cdf(-d2) - S*norm.cdf(-d1)

def bs_iv(mkt_price, S, K, T, rf, otype='call'):
    try: return brentq(lambda s: bs_price(S, K, T, rf, s, otype) - mkt_price, 0.01, 5.0)
    except: return np.nan


# ============================================================
# 8. HESTON/BATES CALIBRATION (Fast quasi-MLE)
# ============================================================
print('\n6. Calibrating Heston on NIFTY 50...')

realized_var = np.var(r_data) * 252

def heston_qmle(params, returns, dt=1/252, rf=0.065):
    """Fast quasi-MLE using Euler discretisation."""
    v0, kappa, theta, sigma_v, rho = params
    if v0 <= 0 or kappa <= 0 or theta <= 0 or sigma_v <= 0 or abs(rho) >= 0.999:
        return 1e10
    n = len(returns)
    v = v0
    ll = 0.0
    for t in range(n):
        vt = max(v, 1e-8)
        mean_r = (rf - 0.5*vt)*dt
        var_r = max(vt*dt, 1e-15)
        ll += norm.logpdf(returns[t], loc=mean_r, scale=np.sqrt(var_r))
        innov = (returns[t] - mean_r) / np.sqrt(var_r)
        dv = kappa*(theta - vt)*dt + sigma_v*np.sqrt(max(vt, 0)*dt)*rho*innov
        v = max(vt + dv, 1e-8)
    return -ll

x0_h = [realized_var, 3.0, realized_var, 0.3, -0.5]
bnd_h = [(0.005, 0.15), (0.5, 10), (0.005, 0.15), (0.05, 1.5), (-0.99, -0.01)]
res_h = minimize(heston_qmle, x0_h, args=(r_data,), method='L-BFGS-B',
                 bounds=bnd_h, options={'maxiter': 300})
v0_h, kappa_h, theta_h, sigma_h, rho_h = res_h.x
ll_heston = -res_h.fun
print(f'  v0={v0_h:.4f}, kappa={kappa_h:.2f}, theta={theta_h:.4f}, sigma={sigma_h:.3f}, rho={rho_h:.3f}')
print(f'  LL={ll_heston:.2f}')
print(f'  Feller: 2*kappa*theta={2*kappa_h*theta_h:.4f} vs sigma^2={sigma_h**2:.4f} '
      f'({"OK" if 2*kappa_h*theta_h >= sigma_h**2 else "VIOLATED"})')

aic_h = 10 - 2*ll_heston; bic_h = 5*np.log(len(r_data)) - 2*ll_heston

print('\n7. Calibrating Bates on NIFTY 50...')

def bates_qmle(params, returns, dt=1/252, rf=0.065):
    v0, kappa, theta, sigma_v, rho, lam_j, mu_j, sigma_j = params
    if v0 <= 0 or kappa <= 0 or theta <= 0 or sigma_v <= 0 or sigma_j <= 0 or lam_j < 0:
        return 1e10
    if abs(rho) >= 0.999: return 1e10
    kappa_j = np.exp(mu_j + 0.5*sigma_j**2) - 1
    n = len(returns)
    v = v0; ll = 0.0
    K_t = 10; ks = np.arange(K_t)
    log_fact = np.array([np.sum(np.log(np.arange(1, k+1))) for k in ks])
    for t in range(n):
        vt = max(v, 1e-8)
        ld = lam_j * dt
        log_poisson = -ld + ks*np.log(ld + 1e-300) - log_fact
        means = (rf - 0.5*vt - lam_j*kappa_j)*dt + ks*mu_j
        variances = np.maximum(vt*dt + ks*sigma_j**2, 1e-20)
        log_d = log_poisson + norm.logpdf(returns[t], loc=means, scale=np.sqrt(variances))
        mx = log_d.max()
        ll += mx + np.log(np.sum(np.exp(log_d - mx)))
        innov = (returns[t] - means[0]) / np.sqrt(max(variances[0], 1e-15))
        dv = kappa*(theta - vt)*dt + sigma_v*np.sqrt(max(vt, 0)*dt)*rho*innov
        v = max(vt + dv, 1e-8)
    return -ll

x0_b = [v0_h, kappa_h, theta_h, sigma_h, rho_h, lam_m, muj_m, sigj_m]
bnd_b = [(0.005, 0.15), (0.5, 10), (0.005, 0.15), (0.05, 1.5),
         (-0.99, -0.01), (0, 30), (-0.1, 0.1), (0.01, 0.3)]
res_b = minimize(bates_qmle, x0_b, args=(r_data,), method='L-BFGS-B',
                 bounds=bnd_b, options={'maxiter': 300})
v0_b, kappa_b, theta_b, sigma_b, rho_b, lam_b, muj_b, sigj_b = res_b.x
ll_bates = -res_b.fun
print(f'  v0={v0_b:.4f}, kappa={kappa_b:.2f}, theta={theta_b:.4f}, sigma={sigma_b:.3f}, rho={rho_b:.3f}')
print(f'  lam_j={lam_b:.2f}, mu_j={muj_b:.4f}, sig_j={sigj_b:.4f}')
print(f'  LL={ll_bates:.2f}')

aic_b = 16 - 2*ll_bates; bic_b = 8*np.log(len(r_data)) - 2*ll_bates

# ============================================================
# 9. GENERATE FIGURES
# ============================================================
print('\n8. Generating figures...')
K_atm = round(S0/100)*100
T_1m = 30/252; T_3m = 90/252; T_6m = 180/252

# --- Fig 01: Model comparison ---
print('  Fig 01: Model comparison table...')
fig, ax = plt.subplots(figsize=(14, 4))
ax.axis('off')
table_data = [
    ['Model', '#Params', 'Log-Lik', 'AIC', 'BIC', 'Key Feature'],
    ['Black-Scholes', '2', f'{ll_bs:.1f}', f'{4-2*ll_bs:.1f}', f'{2*np.log(len(r_data))-2*ll_bs:.1f}', 'Constant vol'],
    ['Merton JD', '5', f'{ll_mjd:.1f}', f'{10-2*ll_mjd:.1f}', f'{5*np.log(len(r_data))-2*ll_mjd:.1f}', 'Jumps'],
    ['Heston', '5', f'{ll_heston:.1f}', f'{aic_h:.1f}', f'{bic_h:.1f}', 'Stoch vol'],
    ['Bates', '8', f'{ll_bates:.1f}', f'{aic_b:.1f}', f'{bic_b:.1f}', 'Stoch vol + jumps'],
]
table = ax.table(cellText=table_data, loc='center', cellLoc='center')
table.auto_set_font_size(False); table.set_fontsize(11); table.scale(1.2, 1.8)
for j in range(6):
    table[0, j].set_facecolor('#1B3A6B')
    table[0, j].set_text_props(color='white', fontweight='bold')
ax.set_title('Model Comparison: BS vs MJD vs Heston vs Bates on NIFTY 50',
             fontsize=14, fontweight='bold', pad=20)
plt.tight_layout(); plt.savefig(f'{FIG}01_model_comparison.png'); plt.close()

# --- Fig 02: Option prices across strikes ---
print('  Fig 02: Option prices across strikes...')
strikes = np.linspace(S0*0.85, S0*1.15, 30)
bs_calls = np.array([bs_price(S0, Ki, T_3m, r_f, sig_bs, 'call') for Ki in strikes])
bs_puts = np.array([bs_price(S0, Ki, T_3m, r_f, sig_bs, 'put') for Ki in strikes])

heston_calls = carr_madan_heston(S0, strikes, T_3m, r_f, v0_h, kappa_h, theta_h, sigma_h, rho_h)
heston_puts = heston_calls - S0 + strikes * np.exp(-r_f*T_3m)

bates_calls = carr_madan_bates(S0, strikes, T_3m, r_f, v0_b, kappa_b, theta_b, sigma_b, rho_b,
                                lam_b, muj_b, sigj_b)
bates_puts = bates_calls - S0 + strikes * np.exp(-r_f*T_3m)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
for ax, calls, puts, title in [(axes[0], [bs_calls, heston_calls, bates_calls], None, 'Call'),
                                 (axes[1], None, [bs_puts, heston_puts, bates_puts], 'Put')]:
    data_list = calls if calls else puts
    for d, lbl, sty in zip(data_list, ['BS', 'Heston', 'Bates'], ['b-', 'r--', 'g-.']):
        ax.plot(strikes/S0, d, sty, lw=2, label=lbl)
    ax.set_xlabel('Moneyness K/S'); ax.set_ylabel(f'{title} Price (INR)')
    ax.set_title(f'{title} Prices (T=3m)'); ax.legend(); ax.grid(True, alpha=0.3)
plt.suptitle('Option Pricing: BS vs Heston vs Bates on NIFTY 50',
             fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout(); plt.savefig(f'{FIG}02_option_prices.png'); plt.close()

# --- Fig 03: IV Smile ---
print('  Fig 03: IV smile comparison...')
fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))
for idx_t, (T_val, T_label) in enumerate([(T_1m, '1 month'), (T_3m, '3 months'), (T_6m, '6 months')]):
    h_calls = carr_madan_heston(S0, strikes, T_val, r_f, v0_h, kappa_h, theta_h, sigma_h, rho_h)
    b_calls = carr_madan_bates(S0, strikes, T_val, r_f, v0_b, kappa_b, theta_b, sigma_b, rho_b,
                                lam_b, muj_b, sigj_b)
    iv_h = [bs_iv(max(c, 1e-6), S0, Ki, T_val, r_f) for c, Ki in zip(h_calls, strikes)]
    iv_b = [bs_iv(max(c, 1e-6), S0, Ki, T_val, r_f) for c, Ki in zip(b_calls, strikes)]

    ax = axes[idx_t]
    ax.plot(strikes/S0, [sig_bs]*len(strikes), 'b-', lw=2, label='BS (flat)')
    ax.plot(strikes/S0, iv_h, 'r--o', lw=2, ms=3, label='Heston')
    ax.plot(strikes/S0, iv_b, 'g-.s', lw=2, ms=3, label='Bates')
    ax.axvline(1.0, color='gray', ls=':', alpha=0.5)
    ax.set_xlabel('Moneyness K/S'); ax.set_ylabel('Implied Volatility')
    ax.set_title(f'T = {T_label}'); ax.legend(fontsize=9); ax.grid(True, alpha=0.3)
plt.suptitle('Implied Volatility Smile: Heston & Bates vs BS',
             fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout(); plt.savefig(f'{FIG}03_iv_smile.png'); plt.close()

# --- Fig 04: CFFT accuracy ---
print('  Fig 04: CFFT vs Carr-Madan accuracy...')
test_K = np.linspace(S0*0.88, S0*1.12, 15)
semi_calls = []; cfft1_calls = []; cfft2_calls = []
cm_calls = carr_madan_heston(S0, test_K, T_3m, r_f, v0_h, kappa_h, theta_h, sigma_h, rho_h)

for Ki in test_K:
    sc, _, _, _ = heston_semi_closed(S0, Ki, T_3m, r_f, v0_h, kappa_h, theta_h, sigma_h, rho_h)
    semi_calls.append(sc)
    c1, _, _, _ = cfft_i_price(S0, Ki, T_3m, r_f, v0_h, kappa_h, theta_h, sigma_h, rho_h, N=2048)
    cfft1_calls.append(c1)
    c2, _ = cfft_ii_price(S0, Ki, T_3m, r_f, v0_h, kappa_h, theta_h, sigma_h, rho_h, N=2048)
    cfft2_calls.append(c2)

semi_calls = np.array(semi_calls)
cfft1_calls = np.array(cfft1_calls)
cfft2_calls = np.array(cfft2_calls)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
ax = axes[0]
ax.plot(test_K/S0, semi_calls, 'k-', lw=2, label='Semi-closed (benchmark)')
ax.plot(test_K/S0, cm_calls, 'b--', lw=2, label='Carr-Madan FFT')
ax.plot(test_K/S0, cfft1_calls, 'r-.', lw=2, label='CFFT-I')
ax.plot(test_K/S0, cfft2_calls, 'g:', lw=2.5, label='CFFT-II')
ax.set_xlabel('Moneyness K/S'); ax.set_ylabel('Call Price')
ax.set_title('Price Comparison'); ax.legend(); ax.grid(True, alpha=0.3)

ax = axes[1]
err_cm = np.abs(cm_calls - semi_calls) + 1e-15
err_c1 = np.abs(cfft1_calls - semi_calls) + 1e-15
err_c2 = np.abs(cfft2_calls - semi_calls) + 1e-15
ax.semilogy(test_K/S0, err_cm, 'b-o', lw=2, ms=4, label='Carr-Madan')
ax.semilogy(test_K/S0, err_c1, 'r-s', lw=2, ms=4, label='CFFT-I')
ax.semilogy(test_K/S0, err_c2, 'g-^', lw=2, ms=4, label='CFFT-II')
ax.set_xlabel('Moneyness K/S'); ax.set_ylabel('|Error| (log)')
ax.set_title('Pricing Error vs Benchmark'); ax.legend(); ax.grid(True, alpha=0.3)
plt.suptitle('CFFT Method Accuracy (Gao & Hyndman 2025)',
             fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout(); plt.savefig(f'{FIG}04_cfft_accuracy.png'); plt.close()

# --- Fig 05: CFFT convergence ---
print('  Fig 05: CFFT convergence...')
N_vals = [64, 128, 256, 512, 1024, 2048, 4096]
ref, _, _, _ = heston_semi_closed(S0, K_atm, T_3m, r_f, v0_h, kappa_h, theta_h, sigma_h, rho_h)
err1 = []; err2 = []
for Nv in N_vals:
    c1, _, _, _ = cfft_i_price(S0, K_atm, T_3m, r_f, v0_h, kappa_h, theta_h, sigma_h, rho_h, N=Nv)
    c2, _ = cfft_ii_price(S0, K_atm, T_3m, r_f, v0_h, kappa_h, theta_h, sigma_h, rho_h, N=Nv)
    err1.append(max(abs(c1 - ref), 1e-16)); err2.append(max(abs(c2 - ref), 1e-16))

fig, ax = plt.subplots(figsize=(10, 6))
ax.loglog(N_vals, err1, 'r-o', lw=2, ms=8, label='CFFT-I')
ax.loglog(N_vals, err2, 'g-s', lw=2, ms=8, label='CFFT-II')
Na = np.array(N_vals, dtype=float)
ax.loglog(Na, err2[0]*(Na[0]/Na)**2, 'k--', alpha=0.5, label=r'$O(N^{-2})$ ref')
ax.set_xlabel('Grid Size N'); ax.set_ylabel('Absolute Error')
ax.set_title(f'CFFT Convergence (ATM, K={K_atm}, T=3m)'); ax.legend(); ax.grid(True, alpha=0.3)
plt.tight_layout(); plt.savefig(f'{FIG}05_cfft_convergence.png'); plt.close()

# --- Fig 06: Characteristic function stability ---
print('  Fig 06: Char function stability...')
p_range = np.linspace(-50, 50, 500)
psi1 = [heston_cf_stable(p, v0_h, T_3m, r_f, kappa_h, theta_h, sigma_h, rho_h, 1) for p in p_range]
psi2 = [heston_cf_stable(p, v0_h, T_3m, r_f, kappa_h, theta_h, sigma_h, rho_h, 2) for p in p_range]

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
axes[0,0].plot(p_range, [np.real(p) for p in psi1], 'b-', lw=1)
axes[0,0].set_title(r'Re[$\psi_1(p)$]'); axes[0,0].grid(True, alpha=0.3)
axes[0,1].plot(p_range, [np.imag(p) for p in psi1], 'r-', lw=1)
axes[0,1].set_title(r'Im[$\psi_1(p)$]'); axes[0,1].grid(True, alpha=0.3)
axes[1,0].plot(p_range, [np.real(p) for p in psi2], 'b-', lw=1)
axes[1,0].set_title(r'Re[$\psi_2(p)$]'); axes[1,0].grid(True, alpha=0.3)
axes[1,1].plot(p_range, [np.imag(p) for p in psi2], 'r-', lw=1)
axes[1,1].set_title(r'Im[$\psi_2(p)$]'); axes[1,1].grid(True, alpha=0.3)
for ax in axes.flat: ax.set_xlabel('p')
plt.suptitle('Stable Characteristic Function (Gao & Hyndman, Thm 2.1)',
             fontsize=14, fontweight='bold')
plt.tight_layout(); plt.savefig(f'{FIG}06_char_func.png'); plt.close()

# --- Fig 07: OTM put comparison ---
print('  Fig 07: OTM put pricing...')
otm_K = np.linspace(S0*0.80, S0*0.98, 20)
otm_bs = np.array([bs_price(S0, Ki, T_3m, r_f, sig_bs, 'put') for Ki in otm_K])
otm_h = carr_madan_heston(S0, otm_K, T_3m, r_f, v0_h, kappa_h, theta_h, sigma_h, rho_h)
otm_hp = otm_h - S0 + otm_K * np.exp(-r_f*T_3m)
otm_b = carr_madan_bates(S0, otm_K, T_3m, r_f, v0_b, kappa_b, theta_b, sigma_b, rho_b,
                          lam_b, muj_b, sigj_b)
otm_bp = otm_b - S0 + otm_K * np.exp(-r_f*T_3m)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
axes[0].plot(otm_K/S0, otm_bs, 'b-', lw=2, label='BS')
axes[0].plot(otm_K/S0, otm_hp, 'r--', lw=2, label='Heston')
axes[0].plot(otm_K/S0, otm_bp, 'g-.', lw=2, label='Bates')
axes[0].set_xlabel('Moneyness K/S'); axes[0].set_ylabel('Put Price')
axes[0].set_title('OTM Put Prices'); axes[0].legend(); axes[0].grid(True, alpha=0.3)

pct_h = (otm_hp - otm_bs) / np.maximum(otm_bs, 0.01) * 100
pct_b = (otm_bp - otm_bs) / np.maximum(otm_bs, 0.01) * 100
axes[1].plot(otm_K/S0, pct_h, 'r-o', lw=2, ms=4, label='(Heston-BS)/BS')
axes[1].plot(otm_K/S0, pct_b, 'g-s', lw=2, ms=4, label='(Bates-BS)/BS')
axes[1].axhline(0, color='black', lw=0.5)
axes[1].set_xlabel('Moneyness K/S'); axes[1].set_ylabel('% diff vs BS')
axes[1].set_title('OTM Put: BS Underpricing'); axes[1].legend(); axes[1].grid(True, alpha=0.3)
plt.suptitle('OTM Put Pricing: Crash Protection',
             fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout(); plt.savefig(f'{FIG}07_otm_puts.png'); plt.close()

# --- Fig 08: Heston sample paths ---
print('  Fig 08: Heston paths...')
np.random.seed(42)
n_steps_path = 252; dt_path = 1/252
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
for _ in range(5):
    S_path = [S0]; v_path = [v0_h]
    for __ in range(n_steps_path):
        vt = max(v_path[-1], 1e-8)
        Z1 = np.random.standard_normal()
        Z2 = rho_h*Z1 + np.sqrt(1-rho_h**2)*np.random.standard_normal()
        v_new = max(vt + kappa_h*(theta_h-vt)*dt_path + sigma_h*np.sqrt(vt*dt_path)*Z2, 1e-8)
        S_new = S_path[-1] * np.exp((r_f - 0.5*vt)*dt_path + np.sqrt(vt*dt_path)*Z1)
        S_path.append(S_new); v_path.append(v_new)
    axes[0].plot(S_path, alpha=0.7, lw=0.8)
    axes[1].plot(np.sqrt(np.array(v_path))*100, alpha=0.7, lw=0.8)
axes[0].axhline(K_atm, color='red', ls='--', lw=1.5, label=f'K={K_atm}')
axes[0].set_title('Heston Price Paths'); axes[0].set_xlabel('Days'); axes[0].set_ylabel('Price')
axes[0].legend(); axes[0].grid(True, alpha=0.3)
axes[1].set_title('Stochastic Volatility'); axes[1].set_xlabel('Days'); axes[1].set_ylabel('Vol (%)')
axes[1].grid(True, alpha=0.3)
plt.suptitle('Heston Model Dynamics', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout(); plt.savefig(f'{FIG}08_heston_paths.png'); plt.close()

# --- Fig 09: IV Surface (Heston) ---
print('  Fig 09: IV surface (Heston)...')
mats = np.array([5, 10, 21, 42, 63, 126, 252]) / 252
K_surf = np.linspace(S0*0.85, S0*1.15, 20)
iv_surf = np.zeros((len(mats), len(K_surf)))
for i, T_val in enumerate(mats):
    hc = carr_madan_heston(S0, K_surf, T_val, r_f, v0_h, kappa_h, theta_h, sigma_h, rho_h)
    for j, (c, Ki) in enumerate(zip(hc, K_surf)):
        iv_surf[i, j] = bs_iv(max(c, 1e-6), S0, Ki, T_val, r_f)

M_g, T_g = np.meshgrid(K_surf/S0, mats*252)
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')
ax.plot_surface(M_g, T_g, iv_surf*100, cmap='viridis', alpha=0.8)
ax.set_xlabel('Moneyness K/S'); ax.set_ylabel('Maturity (days)'); ax.set_zlabel('IV (%)')
ax.set_title('Heston IV Surface — NIFTY 50')
plt.tight_layout(); plt.savefig(f'{FIG}09_iv_surface_heston.png'); plt.close()

# --- Fig 10: IV Surface (Bates) ---
print('  Fig 10: IV surface (Bates)...')
iv_surf_b = np.zeros((len(mats), len(K_surf)))
for i, T_val in enumerate(mats):
    bc = carr_madan_bates(S0, K_surf, T_val, r_f, v0_b, kappa_b, theta_b, sigma_b, rho_b,
                           lam_b, muj_b, sigj_b)
    for j, (c, Ki) in enumerate(zip(bc, K_surf)):
        iv_surf_b[i, j] = bs_iv(max(c, 1e-6), S0, Ki, T_val, r_f)

fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')
ax.plot_surface(M_g, T_g, iv_surf_b*100, cmap='plasma', alpha=0.8)
ax.set_xlabel('Moneyness K/S'); ax.set_ylabel('Maturity (days)'); ax.set_zlabel('IV (%)')
ax.set_title('Bates IV Surface — NIFTY 50')
plt.tight_layout(); plt.savefig(f'{FIG}10_iv_surface_bates.png'); plt.close()

# --- Fig 11: Bates paths with jumps ---
print('  Fig 11: Bates paths...')
np.random.seed(42)
kappa_j_b = np.exp(muj_b + 0.5*sigj_b**2) - 1
fig, axes = plt.subplots(1, 2, figsize=(16, 6))
for _ in range(5):
    S_p = [S0]; v_p = [v0_b]; jtimes = []
    for step in range(n_steps_path):
        vt = max(v_p[-1], 1e-8)
        Z1 = np.random.standard_normal()
        Z2 = rho_b*Z1 + np.sqrt(1-rho_b**2)*np.random.standard_normal()
        Nj = np.random.poisson(lam_b*dt_path)
        J = np.random.normal(muj_b, sigj_b, int(Nj)).sum() if Nj > 0 else 0
        if Nj > 0: jtimes.append(step)
        v_new = max(vt + kappa_b*(theta_b-vt)*dt_path + sigma_b*np.sqrt(vt*dt_path)*Z2, 1e-8)
        S_new = S_p[-1] * np.exp((r_f - 0.5*vt - lam_b*kappa_j_b)*dt_path + np.sqrt(vt*dt_path)*Z1 + J)
        S_p.append(S_new); v_p.append(v_new)
    axes[0].plot(S_p, alpha=0.7, lw=0.8)
    for jt in jtimes: axes[0].plot(jt, S_p[jt], 'rv', ms=3, alpha=0.5)
    axes[1].plot(np.sqrt(np.array(v_p))*100, alpha=0.7, lw=0.8)
axes[0].axhline(K_atm, color='red', ls='--', lw=1.5)
axes[0].set_title('Bates: Price Paths (jumps = red triangles)')
axes[0].set_xlabel('Days'); axes[0].set_ylabel('Price'); axes[0].grid(True, alpha=0.3)
axes[1].set_title('Stochastic Volatility'); axes[1].set_xlabel('Days')
axes[1].set_ylabel('Vol (%)'); axes[1].grid(True, alpha=0.3)
plt.suptitle('Bates Model: Stoch Vol + Jumps', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout(); plt.savefig(f'{FIG}11_bates_paths.png'); plt.close()

# --- Fig 12: ATM term structure ---
print('  Fig 12: ATM IV term structure...')
mats_ts = np.array([5, 10, 21, 42, 63, 126, 189, 252]) / 252
atm_h = []; atm_b = []
for Tv in mats_ts:
    hc = carr_madan_heston(S0, [K_atm], Tv, r_f, v0_h, kappa_h, theta_h, sigma_h, rho_h)[0]
    bc = carr_madan_bates(S0, [K_atm], Tv, r_f, v0_b, kappa_b, theta_b, sigma_b, rho_b,
                           lam_b, muj_b, sigj_b)[0]
    atm_h.append(bs_iv(max(hc, 1e-6), S0, K_atm, Tv, r_f))
    atm_b.append(bs_iv(max(bc, 1e-6), S0, K_atm, Tv, r_f))

fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(mats_ts*252, [sig_bs]*len(mats_ts), 'b-', lw=2, label='BS (flat)')
ax.plot(mats_ts*252, atm_h, 'r-o', lw=2, ms=6, label='Heston')
ax.plot(mats_ts*252, atm_b, 'g-s', lw=2, ms=6, label='Bates')
ax.set_xlabel('Maturity (days)'); ax.set_ylabel('ATM IV')
ax.set_title('ATM IV Term Structure'); ax.legend(); ax.grid(True, alpha=0.3)
plt.tight_layout(); plt.savefig(f'{FIG}12_atm_term_structure.png'); plt.close()

# ============================================================
# SUMMARY
# ============================================================
print('\n' + '='*60)
print('SUMMARY')
print('='*60)
print(f'S0={S0:.2f}, rf={r_f*100:.1f}%')
print(f'\n{"Model":<12} {"LL":>10} {"AIC":>10} {"BIC":>10}')
print('-'*44)
print(f'{"BS":<12} {ll_bs:>10.1f} {4-2*ll_bs:>10.1f} {2*np.log(len(r_data))-2*ll_bs:>10.1f}')
print(f'{"MJD":<12} {ll_mjd:>10.1f} {10-2*ll_mjd:>10.1f} {5*np.log(len(r_data))-2*ll_mjd:>10.1f}')
print(f'{"Heston":<12} {ll_heston:>10.1f} {aic_h:>10.1f} {bic_h:>10.1f}')
print(f'{"Bates":<12} {ll_bates:>10.1f} {aic_b:>10.1f} {bic_b:>10.1f}')
print(f'\nHeston: v0={v0_h:.4f} kap={kappa_h:.2f} th={theta_h:.4f} sig={sigma_h:.3f} rho={rho_h:.3f}')
print(f'Bates:  v0={v0_b:.4f} kap={kappa_b:.2f} th={theta_b:.4f} sig={sigma_b:.3f} rho={rho_b:.3f}')
print(f'        lam={lam_b:.2f} muJ={muj_b:.4f} sigJ={sigj_b:.4f}')
print(f'\nAll figures saved to {FIG}')
print('='*60)
