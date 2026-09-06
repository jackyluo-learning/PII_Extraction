# Numerical audit

The first full 10,000-refit pass halted on Weibull replicate 6203 after an L-BFGS line-search ABNORMAL status; it did not discard the replicate or produce final results. Increased the line-search step cap from the SciPy default 20 to 100, preserving the likelihood, initial values, tolerance, draw and all observations. The exact replicate is independently checked against lifelines before repeating the full pass.
