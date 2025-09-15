Changelog
=========

0.3.0 (2025-09-15)
------------------

- Fixed handling of feature names for numpy input in `AnchorBooster`.
- Added support for pandas DataFrame input in `AnchorBooster`.

0.2.1 (2025-07-01)
------------------

- `AnchorBooster.refit` no longer raises an error if the model stopped boosting early during initial training.

0.2.0 (2025-06-12)
------------------

- Sped up boosting.

0.1.0 (2025-05-29)
------------------

- Initial release of the `anchorboosting` package.
- Implemented `AnchorBooster` class for anchor regression and anchor probit classification.