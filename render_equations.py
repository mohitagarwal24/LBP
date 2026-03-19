"""
Render LaTeX equations as PNG images for embedding in PPTX.
Uses matplotlib's mathtext renderer (no LaTeX installation needed).
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

FIGURES_DIR = 'figures/'
os.makedirs(FIGURES_DIR, exist_ok=True)

def render_latex(latex_str, filename, fontsize=22, dpi=200, color='#1B3A6B'):
    fig, ax = plt.subplots(figsize=(0.1, 0.1))
    ax.axis('off')
    fig.patch.set_alpha(0)
    text = ax.text(0, 0.5, latex_str, fontsize=fontsize, color=color,
                   ha='left', va='center', transform=ax.transAxes,
                   math_fontfamily='cm')
    fig.savefig(os.path.join(FIGURES_DIR, filename), dpi=dpi,
                bbox_inches='tight', pad_inches=0.15, transparent=True)
    plt.close()
    print(f'  {filename}')

print('Rendering LaTeX equations...')

# BS: GBM SDE
render_latex(
    r'$dS(t) = \mu\, S(t)\, dt + \sigma\, S(t)\, dW(t)$',
    'eq_bs_sde.png', fontsize=24)

# BS: Hedged portfolio setup (PDE derivation)
render_latex(
    r'$\Pi = V(S,t) - \Delta S,\qquad d\Pi = dV - \Delta\, dS$',
    'eq_bs_portfolio.png', fontsize=24)

# BS: Ito for option value
render_latex(
    r'$dV = \left(V_t + \mu S V_S + \frac{1}{2}\sigma^2 S^2 V_{SS}\right)dt + \sigma S V_S\, dW$',
    'eq_bs_ito_option.png', fontsize=20)

# BS: Choose Delta to eliminate randomness
render_latex(
    r'$\Delta = V_S \;\Rightarrow\; \sigma S\,(V_S-\Delta)\, dW = 0,\;\;\mu\ \mathrm{cancels}$',
    'eq_bs_delta_hedge.png', fontsize=22)

# BS: No-arbitrage -> PDE
render_latex(
    r'$d\Pi = r_f \Pi\, dt \;\Rightarrow\; V_t + \frac{1}{2}\sigma^2 S^2 V_{SS} + r_f S V_S - r_f V = 0$',
    'eq_bs_pde.png', fontsize=20)

# Discrete-sampling likelihood (general diffusion)
render_latex(
    r'$\ell_n(\theta)=\sum_{i=1}^{n}\ln\!\left\{p(\Delta, x_i \mid x_{i-1};\theta)\right\}$',
    'eq_disc_loglik.png', fontsize=24)

# Aït-Sahalia: closed-form Hermite expansion idea
render_latex(
    r'$p(\Delta,x\mid x_0;\theta)\ \approx\ p^{(J)}(\Delta,x\mid x_0;\theta)\ \ \text{(closed-form Hermite expansion, }J=2,3\text{)}$',
    'eq_as_hermite.png', fontsize=18)

# Euler pseudo-likelihood (Gaussian local approximation)
render_latex(
    r'$X_{t+\Delta}\approx X_t + \mu(X_t;\theta)\Delta + \sigma(X_t;\theta)\sqrt{\Delta}\,Z,\ \ Z\sim N(0,1)$',
    'eq_euler_pseudolik.png', fontsize=18)

# BS: Ito's Lemma result
render_latex(
    r'$S(T) = S_0 \cdot \exp\!\left[\left(\mu - \frac{\sigma^2}{2}\right)T + \sigma\sqrt{T}\, Z\right],\quad Z \sim \mathcal{N}(0,1)$',
    'eq_bs_solution.png', fontsize=22)

# BS: Log-return distribution
render_latex(
    r'$r_t = \ln\!\frac{S_t}{S_{t-1}} \sim \mathcal{N}\!\left(\left(\mu - \frac{\sigma^2}{2}\right)\Delta t,\;\sigma^2 \Delta t\right)$',
    'eq_bs_logret.png', fontsize=22)

# BS: MLE Log-likelihood
render_latex(
    r'$\ell(\mu, \sigma) = -\frac{n}{2}\ln(2\pi) - \frac{n}{2}\ln(\sigma^2\Delta t) - \sum_{i=1}^{n} \frac{(r_i - \tilde{\mu}\Delta t)^2}{2\sigma^2\Delta t}$',
    'eq_bs_loglik.png', fontsize=20)

# BS: MLE solutions
render_latex(
    r'$\hat{\sigma}^2_{MLE} = \frac{1}{n\Delta t}\sum_{i=1}^{n}(r_i - \bar{r})^2, \qquad \hat{\mu}_{MLE} = \frac{\bar{r}}{\Delta t} + \frac{\hat{\sigma}^2}{2}$',
    'eq_bs_mle_solution.png', fontsize=20)

# BS: Pricing formula
render_latex(
    r'$C = S_0\, \Phi(d_1) - K\, e^{-r_f T}\, \Phi(d_2)$',
    'eq_bs_call.png', fontsize=24)

render_latex(
    r'$d_1 = \frac{\ln(S_0/K) + (r_f + \sigma^2/2)\,T}{\sigma\sqrt{T}}, \qquad d_2 = d_1 - \sigma\sqrt{T}$',
    'eq_bs_d1d2.png', fontsize=22)

# BS: Risk-neutral SDE
render_latex(
    r'$dS(t) = r_f\, S(t)\, dt + \sigma\, S(t)\, dW^{\mathbb{Q}}(t)$',
    'eq_bs_riskneutral.png', fontsize=24)

# BS: MC estimator
render_latex(
    r'$\hat{C}_{MC} = e^{-r_f T} \cdot \frac{1}{N}\sum_{i=1}^{N} \max\!\left(S_T^{(i)} - K,\; 0\right)$',
    'eq_bs_mc.png', fontsize=22)

# MJD: SDE
render_latex(
    r'$dS(t) = \mu\, S(t)\, dt + \sigma\, S(t)\, dW(t) + S(t^{-})(e^{J} - 1)\, dN(t)$',
    'eq_mjd_sde.png', fontsize=22)

# MJD: Jump distributions
render_latex(
    r'$N(t) \sim \mathrm{Poisson}(\lambda),\qquad J \sim \mathcal{N}(\mu_J, \sigma_J^2)$',
    'eq_mjd_jumps.png', fontsize=22)

# MJD: Conditional log-return
render_latex(
    r'$r\,|\,N{=}k \;\sim\; \mathcal{N}\!\left(\left(\mu - \frac{\sigma^2}{2}\right)\Delta t + k\mu_J,\;\;\sigma^2\Delta t + k\sigma_J^2\right)$',
    'eq_mjd_conditional.png', fontsize=20)

# MJD: Marginal density
render_latex(
    r'$f(r) = \sum_{k=0}^{\infty} \frac{e^{-\lambda\Delta t}(\lambda\Delta t)^k}{k!} \cdot \varphi\!\left(r;\; \tilde{\mu}\Delta t + k\mu_J,\;\sigma^2\Delta t + k\sigma_J^2\right)$',
    'eq_mjd_density.png', fontsize=18)

# MJD: Log-likelihood
render_latex(
    r'$\ell(\theta) = \sum_{t=1}^{n} \ln\!\left[\sum_{k=0}^{K} \frac{e^{-\lambda\Delta t}(\lambda\Delta t)^k}{k!} \cdot \varphi(r_t;\; m_k,\; v_k)\right]$',
    'eq_mjd_loglik.png', fontsize=18)

# MJD: Variance decomposition
render_latex(
    r'$\mathrm{Var}(r) = \sigma^2\Delta t + \lambda\Delta t\,(\mu_J^2 + \sigma_J^2)$',
    'eq_mjd_variance.png', fontsize=22)

# MJD: Risk-neutral compensator
render_latex(
    r'$\kappa = \mathbb{E}[e^J - 1] = e^{\mu_J + \sigma_J^2/2} - 1$',
    'eq_mjd_kappa.png', fontsize=22)

# MJD: Risk-neutral drift (compensator) for option pricing
render_latex(
    r'$dS(t) = (r_f - \lambda\kappa)\,S(t^{-})dt + \sigma S(t^{-})\,dW^{\mathbb{Q}}(t) + S(t^{-})(e^{J}-1)\,dN(t)$',
    'eq_mjd_riskneutral_sde.png', fontsize=18)

# MJD: Conditional BS parameters given k jumps
render_latex(
    r'$\sigma_k^2 = \sigma^2 + \frac{k\sigma_J^2}{T},\qquad r_k = r_f-\lambda\kappa + \frac{k\mu_J}{T} + \frac{k\sigma_J^2}{2T}$',
    'eq_mjd_rk_sigk.png', fontsize=18)

# MJD: Merton series price (mixture of BS prices)
render_latex(
    r'$V_{MJD} = \sum_{k=0}^{\infty}\frac{e^{-\lambda T}(\lambda T)^k}{k!}\;\mathrm{BS}\!\left(S_0,K,T,r_k,\sigma_k\right)$',
    'eq_mjd_series.png', fontsize=18)

# MJD: Excess kurtosis
render_latex(
    r'$\mathrm{Kurt}_{MJD} = \frac{3\lambda\,(\mu_J^2 + \sigma_J^2)^2}{\left(\sigma^2 + \lambda(\mu_J^2 + \sigma_J^2)\right)^2}$',
    'eq_mjd_kurtosis.png', fontsize=20)

# LRT
render_latex(
    r'$\Lambda = 2\left[\ell(\hat{\theta}_{MJD}) - \ell(\hat{\theta}_{BS})\right] \sim \chi^2(3)\;\;\mathrm{under}\;\; H_0: \lambda = 0$',
    'eq_lrt.png', fontsize=20)

# AIC/BIC
render_latex(
    r'$\mathrm{AIC} = 2k - 2\ell(\hat{\theta}), \qquad \mathrm{BIC} = k\ln(n) - 2\ell(\hat{\theta})$',
    'eq_aic_bic.png', fontsize=22)

# Ito's Lemma application
render_latex(
    r'$d(\ln S) = \left(\mu - \frac{\sigma^2}{2}\right)dt + \sigma\, dW(t)$',
    'eq_ito_lemma.png', fontsize=24)

# MJD: Ito for jump-diffusion
render_latex(
    r'$d(\ln S) = \left(\mu - \frac{\sigma^2}{2}\right)dt + \sigma\, dW(t) + J\, dN(t)$',
    'eq_mjd_ito.png', fontsize=22)

print(f'\nAll equations rendered to {FIGURES_DIR}')
