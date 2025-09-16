# [0.9.0](https://github.com/kubeflow/sdk/releases/tag/0.9.0) (2025-09-15)

## New Features

- feat: Implement TrainerClient Backends & Local Process ([#33](https://github.com/kubeflow/sdk/pull/33)) by [@szaher](https://github.com/szaher)
- feat: KEP-2 Local Execution Mode Proposal ([#34](https://github.com/kubeflow/sdk/pull/34)) by [@szaher](https://github.com/szaher)
- feat(trainer): Add support for param unpacking in the training function call ([#62](https://github.com/kubeflow/sdk/pull/62)) by [@briangallagher](https://github.com/briangallagher)
- feat: Support multiple pip index URLs in CustomTrainer ([#79](https://github.com/kubeflow/sdk/pull/79)) by [@wassimbensalem](https://github.com/wassimbensalem)
- feat(trainer): Refactor get_job_logs() API with Iterator ([#83](https://github.com/kubeflow/sdk/pull/83)) by [@andreyvelich](https://github.com/andreyvelich)
- feat: Implement Kubernetes Backend ([#68](https://github.com/kubeflow/sdk/pull/68)) by [@szaher](https://github.com/szaher)
- feat(docs): add ROADMAP of Kubeflow SDK ([#44](https://github.com/kubeflow/sdk/pull/44)) by [@kramaranya](https://github.com/kramaranya)
- feat(trainer): Add `get_runtime_packages()` API ([#57](https://github.com/kubeflow/sdk/pull/57)) by [@andreyvelich](https://github.com/andreyvelich)
- feat(trainer): Support Framework Labels in Runtimes ([#56](https://github.com/kubeflow/sdk/pull/56)) by [@andreyvelich](https://github.com/andreyvelich)
- feat(trainer): Add environment variables argument to CustomTrainer ([#54](https://github.com/kubeflow/sdk/pull/54)) by [@astefanutti](https://github.com/astefanutti)
- feat(trainer): Add `wait_for_job_status()` API ([#52](https://github.com/kubeflow/sdk/pull/52)) by [@andreyvelich](https://github.com/andreyvelich)
- feat(ci): Add GitHub action to verify PR titles ([#42](https://github.com/kubeflow/sdk/pull/42)) by [@andreyvelich](https://github.com/andreyvelich)

## Bug Fixes

- fix: trainer client backend public ([#78](https://github.com/kubeflow/sdk/pull/78)) by [@jaiakash](https://github.com/jaiakash)
- fix(trainer): Keep the original runtime command in get_runtime_packages() API ([#64](https://github.com/kubeflow/sdk/pull/64)) by [@andreyvelich](https://github.com/andreyvelich)
- fix(trainer): fix __all__ import. ([#43](https://github.com/kubeflow/sdk/pull/43)) by [@Electronic-Waste](https://github.com/Electronic-Waste)
- fix: Expose BuiltinTrainer API to users ([#28](https://github.com/kubeflow/sdk/pull/28)) by [@Electronic-Waste](https://github.com/Electronic-Waste)

## Maintenance

- chore: Add proper ruff configuration ([#69](https://github.com/kubeflow/sdk/pull/69)) by [@szaher](https://github.com/szaher)
- chore: Update CONTRIBUTING.md to use uv ([#41](https://github.com/kubeflow/sdk/pull/41)) by [@szaher](https://github.com/szaher)
- chore: Add welcome new contributors CI ([#82](https://github.com/kubeflow/sdk/pull/82)) by [@kramaranya](https://github.com/kramaranya)
- chore(trainer): Use explicit exception chaining ([#80](https://github.com/kubeflow/sdk/pull/80)) by [@andreyvelich](https://github.com/andreyvelich)
- chore: Nominate @kramaranya and @szaher as Kubeflow SDK reviewers ([#76](https://github.com/kubeflow/sdk/pull/76)) by [@andreyvelich](https://github.com/andreyvelich)
- chore: Enable parallel builds for coveralls ([#81](https://github.com/kubeflow/sdk/pull/81)) by [@kramaranya](https://github.com/kramaranya)
- chore: Remove tool.hatch.build.targets from pyproject ([#73](https://github.com/kubeflow/sdk/pull/73)) by [@kramaranya](https://github.com/kramaranya)
- chore: Move dev extras to dependency-groups ([#71](https://github.com/kubeflow/sdk/pull/71)) by [@kramaranya](https://github.com/kramaranya)
- chore: Update README.md ([#67](https://github.com/kubeflow/sdk/pull/67)) by [@kramaranya](https://github.com/kramaranya)
- chore: move pyproject.toml to root ([#61](https://github.com/kubeflow/sdk/pull/61)) by [@kramaranya](https://github.com/kramaranya)
- chore(ci): Align Kubernetes versions from Trainer for e2e tests ([#58](https://github.com/kubeflow/sdk/pull/58)) by [@astefanutti](https://github.com/astefanutti)
- chore(ci): Add dev tests with master dependencies ([#55](https://github.com/kubeflow/sdk/pull/55)) by [@kramaranya](https://github.com/kramaranya)
- chore(docs): Add Coveralls Badge to the README ([#53](https://github.com/kubeflow/sdk/pull/53)) by [@andreyvelich](https://github.com/andreyvelich)
- chore(trainer): Remove accelerator label from the runtimes ([#51](https://github.com/kubeflow/sdk/pull/51)) by [@andreyvelich](https://github.com/andreyvelich)

## Other Changes

- add unit test for trainer sdk ([#17](https://github.com/kubeflow/sdk/pull/17)) by [@briangallagher](https://github.com/briangallagher)
- add e2e notebook tests ([#27](https://github.com/kubeflow/sdk/pull/27)) by [@briangallagher](https://github.com/briangallagher)
- Update pyproject.toml project links ([#40](https://github.com/kubeflow/sdk/pull/40)) by [@szaher](https://github.com/szaher)
- Add support for UV & Ruff ([#38](https://github.com/kubeflow/sdk/pull/38)) by [@szaher](https://github.com/szaher)
- Step down from sdk ownership role ([#37](https://github.com/kubeflow/sdk/pull/37)) by [@tenzen-y](https://github.com/tenzen-y)
- Add CONTRIBUTING.md ([#30](https://github.com/kubeflow/sdk/pull/30)) by [@abhijeet-dhumal](https://github.com/abhijeet-dhumal)
- Reflect owners updates from KF Trainer ([#32](https://github.com/kubeflow/sdk/pull/32)) by [@tenzen-y](https://github.com/tenzen-y)
- Consume Trainer models from external package kubeflow_trainer_api ([#15](https://github.com/kubeflow/sdk/pull/15)) by [@kramaranya](https://github.com/kramaranya)
- Add pre-commit and flake8 configs ([#6](https://github.com/kubeflow/sdk/pull/6)) by [@eoinfennessy](https://github.com/eoinfennessy)
- Add Stale GitHub action ([#7](https://github.com/kubeflow/sdk/pull/7)) by [@kramaranya](https://github.com/kramaranya)
- Add GitHub issue and PR templates ([#5](https://github.com/kubeflow/sdk/pull/5)) by [@eoinfennessy](https://github.com/eoinfennessy)

**Full Changelog**: https://github.com/kubeflow/sdk/compare/821e01f2b2a96204f851e27fd18ae02e8d876aa7...HEAD

# [0.9.0rc1](https://github.com/kubeflow/sdk/releases/tag/0.9.0rc1) (2025-09-15)

## New Features

- feat: Implement TrainerClient Backends & Local Process ([#33](https://github.com/kubeflow/sdk/pull/33)) by [@szaher](https://github.com/szaher)
- feat: KEP-2 Local Execution Mode Proposal ([#34](https://github.com/kubeflow/sdk/pull/34)) by [@szaher](https://github.com/szaher)
- feat(trainer): Add support for param unpacking in the training function call ([#62](https://github.com/kubeflow/sdk/pull/62)) by [@briangallagher](https://github.com/briangallagher)
- feat: Support multiple pip index URLs in CustomTrainer ([#79](https://github.com/kubeflow/sdk/pull/79)) by [@wassimbensalem](https://github.com/wassimbensalem)
- feat(trainer): Refactor get_job_logs() API with Iterator ([#83](https://github.com/kubeflow/sdk/pull/83)) by [@andreyvelich](https://github.com/andreyvelich)
- feat: Implement Kubernetes Backend ([#68](https://github.com/kubeflow/sdk/pull/68)) by [@szaher](https://github.com/szaher)
- feat(docs): add ROADMAP of Kubeflow SDK ([#44](https://github.com/kubeflow/sdk/pull/44)) by [@kramaranya](https://github.com/kramaranya)
- feat(trainer): Add `get_runtime_packages()` API ([#57](https://github.com/kubeflow/sdk/pull/57)) by [@andreyvelich](https://github.com/andreyvelich)
- feat(trainer): Support Framework Labels in Runtimes ([#56](https://github.com/kubeflow/sdk/pull/56)) by [@andreyvelich](https://github.com/andreyvelich)
- feat(trainer): Add environment variables argument to CustomTrainer ([#54](https://github.com/kubeflow/sdk/pull/54)) by [@astefanutti](https://github.com/astefanutti)
- feat(trainer): Add `wait_for_job_status()` API ([#52](https://github.com/kubeflow/sdk/pull/52)) by [@andreyvelich](https://github.com/andreyvelich)
- feat(ci): Add GitHub action to verify PR titles ([#42](https://github.com/kubeflow/sdk/pull/42)) by [@andreyvelich](https://github.com/andreyvelich)

## Bug Fixes

- fix: trainer client backend public ([#78](https://github.com/kubeflow/sdk/pull/78)) by [@jaiakash](https://github.com/jaiakash)
- fix(trainer): Keep the original runtime command in get_runtime_packages() API ([#64](https://github.com/kubeflow/sdk/pull/64)) by [@andreyvelich](https://github.com/andreyvelich)
- fix(trainer): fix __all__ import. ([#43](https://github.com/kubeflow/sdk/pull/43)) by [@Electronic-Waste](https://github.com/Electronic-Waste)
- fix: Expose BuiltinTrainer API to users ([#28](https://github.com/kubeflow/sdk/pull/28)) by [@Electronic-Waste](https://github.com/Electronic-Waste)

## Maintenance

- chore: Add proper ruff configuration ([#69](https://github.com/kubeflow/sdk/pull/69)) by [@szaher](https://github.com/szaher)
- chore: Update CONTRIBUTING.md to use uv ([#41](https://github.com/kubeflow/sdk/pull/41)) by [@szaher](https://github.com/szaher)
- chore: Add welcome new contributors CI ([#82](https://github.com/kubeflow/sdk/pull/82)) by [@kramaranya](https://github.com/kramaranya)
- chore(trainer): Use explicit exception chaining ([#80](https://github.com/kubeflow/sdk/pull/80)) by [@andreyvelich](https://github.com/andreyvelich)
- chore: Nominate @kramaranya and @szaher as Kubeflow SDK reviewers ([#76](https://github.com/kubeflow/sdk/pull/76)) by [@andreyvelich](https://github.com/andreyvelich)
- chore: Enable parallel builds for coveralls ([#81](https://github.com/kubeflow/sdk/pull/81)) by [@kramaranya](https://github.com/kramaranya)
- chore: Remove tool.hatch.build.targets from pyproject ([#73](https://github.com/kubeflow/sdk/pull/73)) by [@kramaranya](https://github.com/kramaranya)
- chore: Move dev extras to dependency-groups ([#71](https://github.com/kubeflow/sdk/pull/71)) by [@kramaranya](https://github.com/kramaranya)
- chore: Update README.md ([#67](https://github.com/kubeflow/sdk/pull/67)) by [@kramaranya](https://github.com/kramaranya)
- chore: move pyproject.toml to root ([#61](https://github.com/kubeflow/sdk/pull/61)) by [@kramaranya](https://github.com/kramaranya)
- chore(ci): Align Kubernetes versions from Trainer for e2e tests ([#58](https://github.com/kubeflow/sdk/pull/58)) by [@astefanutti](https://github.com/astefanutti)
- chore(ci): Add dev tests with master dependencies ([#55](https://github.com/kubeflow/sdk/pull/55)) by [@kramaranya](https://github.com/kramaranya)
- chore(docs): Add Coveralls Badge to the README ([#53](https://github.com/kubeflow/sdk/pull/53)) by [@andreyvelich](https://github.com/andreyvelich)
- chore(trainer): Remove accelerator label from the runtimes ([#51](https://github.com/kubeflow/sdk/pull/51)) by [@andreyvelich](https://github.com/andreyvelich)

## Other Changes

- add unit test for trainer sdk ([#17](https://github.com/kubeflow/sdk/pull/17)) by [@briangallagher](https://github.com/briangallagher)
- add e2e notebook tests ([#27](https://github.com/kubeflow/sdk/pull/27)) by [@briangallagher](https://github.com/briangallagher)
- Update pyproject.toml project links ([#40](https://github.com/kubeflow/sdk/pull/40)) by [@szaher](https://github.com/szaher)
- Add support for UV & Ruff ([#38](https://github.com/kubeflow/sdk/pull/38)) by [@szaher](https://github.com/szaher)
- Step down from sdk ownership role ([#37](https://github.com/kubeflow/sdk/pull/37)) by [@tenzen-y](https://github.com/tenzen-y)
- Add CONTRIBUTING.md ([#30](https://github.com/kubeflow/sdk/pull/30)) by [@abhijeet-dhumal](https://github.com/abhijeet-dhumal)
- Reflect owners updates from KF Trainer ([#32](https://github.com/kubeflow/sdk/pull/32)) by [@tenzen-y](https://github.com/tenzen-y)
- Consume Trainer models from external package kubeflow_trainer_api ([#15](https://github.com/kubeflow/sdk/pull/15)) by [@kramaranya](https://github.com/kramaranya)
- Add pre-commit and flake8 configs ([#6](https://github.com/kubeflow/sdk/pull/6)) by [@eoinfennessy](https://github.com/eoinfennessy)
- Add Stale GitHub action ([#7](https://github.com/kubeflow/sdk/pull/7)) by [@kramaranya](https://github.com/kramaranya)
- Add GitHub issue and PR templates ([#5](https://github.com/kubeflow/sdk/pull/5)) by [@eoinfennessy](https://github.com/eoinfennessy)

**Full Changelog**: https://github.com/kubeflow/sdk/compare/821e01f2b2a96204f851e27fd18ae02e8d876aa7...HEAD
