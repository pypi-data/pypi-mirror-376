# v0.0.3
- Added multi-baseline ablation game. This game computes ablation paths with respect to multiple baseline configurations and aggregates values for different paths via mean, min, max or variance.
- Added waterfall plots to the HyperSHAP interface.
- Added support for multi-data settings
- Enabled approximation of Shapley values and interactions for settings exceeding a certain number of hyperparameters.

# v0.0.2
- Added parallelization for faster analysis

## Maintenance
- Added unit tests for proper quality assurance and continuous integration
- Relaxed requirements to allow interoperability with python 3.10

# v0.0.1
- Initial implementation of HyperSHAP and its explanation games:
  - AblationGame
  - TunabilityGame
  - MistunabilityGame
  - SensitivityGame
  - OptimizerBiasGame
