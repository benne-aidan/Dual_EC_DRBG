# Dual Elliptic Curve Deterministic Random Bit Generator
`run_spec_gen()` will run the DRBG according to the NIST specification.

`backdoor()` will instantiate the DRBG with malicious choice of $P$ and $Q$ such that $P=dQ$, and use this to determine the internal state based on only two outputs. Running on my own PC (Intel i7 4790 CPU, 32GB RAM) takes roughly 3-4 minutes.
