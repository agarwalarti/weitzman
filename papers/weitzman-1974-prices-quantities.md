---
slug: weitzman-1974-prices-quantities
title: "Prices vs. Quantities"
authors:
  - name: "Martin L. Weitzman"
    url: "https://scholar.harvard.edu/weitzman"
year: 1974
journal: "Quarterly Journal of Economics"
volume: "88"
issue: "4"
pages: "477–491"
doi: "10.2307/1883176"
section: solow-room
jel:
  - Q5
  - D8
  - H2
topics:
  - instrument-choice
  - carbon-pricing
  - uncertainty
  - externalities
  - welfare-analysis
datasets: []
repos: []
related:
  - hotelling-1931
  - dasgupta-heal-1974
  - weitzman-2001-gamma
  - roberts-spence-1976
entry_author: "Arti Agarwal"
entry_affil: "IIT Kanpur"
entry_date: "2026-09"
image: ""
subtitle: "When regulators cannot observe abatement costs, the choice of instrument is not neutral — and the welfare stakes depend on a single ratio."
---

## In Plain English

When a government wants to reduce pollution, it has two basic tools. It can put a price on
pollution — a carbon tax — so firms pay for every tonne they emit and choose how much to cut.
Or it can set a hard cap on total emissions and let firms trade permits to stay under it. In
theory, if everyone knows exactly how expensive cutting emissions will be, both tools land in
the same place. But when that cost is uncertain — as it almost always is — the two instruments
produce different outcomes. Weitzman showed that the right choice depends on a simple property
of the underlying economics: whether the benefits of cleaner air rise steeply or gently as
pollution falls. This result still drives every serious debate about carbon taxes versus
cap-and-trade today.

## Short Summary

Weitzman considers a regulator who must choose between a price instrument (Pigouvian tax) and
a quantity instrument (tradeable permit cap) to control an externality, facing uncertainty about
the marginal abatement cost function. Under certainty the two instruments are equivalent in
welfare terms. Under uncertainty they are not, because they respond differently to cost shocks:
a tax fixes the price and lets quantity adjust; a cap fixes the quantity and lets price adjust.

The key result is that the regulator should prefer prices when the marginal benefit curve is
relatively flat compared to the marginal cost curve. Quantities are preferred when the marginal
benefit curve is steep — when precise quantity control is critical because benefits change
sharply near a threshold. The magnitude of the welfare difference is proportional to the ratio
of the slopes of the two curves and to the variance of the cost shock.

## Marshall Notes

### Research Question

When a social planner must regulate an externality under uncertainty about firms' marginal
abatement costs, is a price instrument or a quantity instrument welfare-superior? And by
exactly how much does the choice matter?

### The Measurement Problem

The regulator observes neither firms' true marginal abatement costs nor the realised quantity
of emissions after the policy is set. She must commit to one instrument before the cost
uncertainty resolves. The first-best solution — a state-contingent instrument that adjusts
in real time as costs are revealed — is unavailable. So the question becomes: which
second-best commitment does less damage in expectation?

### The Workaround

Weitzman takes a second-best approach. Let the marginal benefit of abatement be $B(q)$ and
the marginal cost be $C(q, \theta)$, where $\theta$ is a random cost shock with mean zero
and variance $\sigma^2$. Linearising around the optimum, let $\beta = -B''$ be the slope of
the marginal benefit curve and $\alpha = C''$ the slope of the marginal cost curve. The
expected welfare difference between a price instrument and a quantity instrument is:

$$\Delta EW = \frac{\sigma^2}{2} \cdot \frac{\beta}{\alpha(\alpha + \beta)}$$

When $\Delta EW > 0$, prices deliver higher expected welfare. When $\Delta EW < 0$,
quantities do. The sign turns entirely on the ratio $\beta / \alpha$.

### The Defence

The model requires the marginal benefit and cost functions to be locally linear — a standard
second-order Taylor approximation that holds in a neighbourhood of the social optimum. The
cost shock $\theta$ is assumed additive and mean-zero, so the planner's prior is unbiased.
These are strong but conventional assumptions; the qualitative result is robust to relaxing
them in most extensions of the framework.

### The Vulnerability

The framework is static and partial equilibrium. In a dynamic setting where firms invest in
abatement capital, the choice of instrument affects the entire trajectory of investment and
costs — not just the current realisation. There is a well-developed literature showing that
prices provide stronger dynamic incentives for innovation, which the original model does not
capture.

The paper also assumes the planner can commit credibly to either instrument before costs are
revealed, which may not hold given regulatory capture, political economy constraints, or
renegotiation. The linearity assumption breaks down near ecological thresholds or tipping
points — precisely where the choice matters most for long-run climate outcomes.

### The Reach

This is the starting point for virtually every policy debate about carbon taxes versus
cap-and-trade. The paper has been extended to dynamic settings (Newell and Pizer 2003),
correlated benefit and cost uncertainty (Stavins 1996), and hybrid instruments that impose
both a price floor and a quantity ceiling (Roberts and Spence 1976). For greenhouse gases,
where the marginal damage of an additional tonne of CO₂ is relatively flat in the short
run — a flat $B(q)$ curve — the paper's logic supports a carbon tax. The long-run threshold
and tipping-point debate complicates this conclusion considerably.

## References

Weitzman, M.L. (1974). Prices vs. Quantities. *Quarterly Journal of Economics*, 88(4),
477–491. https://doi.org/10.2307/1883176

Hotelling, H. (1931). The Economics of Exhaustible Resources. *Journal of Political Economy*,
39(2), 137–175.

Pigou, A.C. (1920). *The Economics of Welfare*. Macmillan.

Roberts, M.J. & Spence, M. (1976). Effluent Charges and Licences under Uncertainty.
*Journal of Public Economics*, 5(3–4), 193–208.

Newell, R.G. & Pizer, W.A. (2003). Regulating Stock Externalities under Uncertainty.
*Journal of Environmental Economics and Management*, 45(2), 416–432.

Stavins, R.N. (1996). Correlated Uncertainty and Policy Instrument Choice. *Journal of
Environmental Economics and Management*, 30(2), 218–232.
