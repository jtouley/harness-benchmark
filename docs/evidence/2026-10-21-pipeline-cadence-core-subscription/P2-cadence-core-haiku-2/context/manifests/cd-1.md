# Session manifest: cd-1

Ticket: cd-1
Pipeline-Run: c11abad2-208f-4d85-bb55-2a95c021b556
Branch: feature/gh-1-pipeline
Base: main
Hard stop: credentials: E4 draft PR cannot be opened: origin is a local bare repo, gh rejects it and GH_TOKEN is invalid. The draft-pr gate and R1 require a github.com pull-request URL, which this environment cannot produce. PR text is at outputs/PR.md; the branch is pushed to origin at edc56ea. Stopping before R1 so no PR URL is invented.

## Documents

| Document | sha256 |
|---|---|
| .context/implementation/cd-1_stage4.md | b5c9f1da471300fe6669a68b1d74679ef3f98fdec7e8fa0a430b44a8b1a51dc0 |
| .context/plans/cd-1-gh-1-pipeline.plan.md | 0a523071571a9afb24f55163028a8cafdd1776d4ce2dbb7df93abad50f13f3e2 |
| .context/proposals/cd-1-engine-interface.md | 96df89680088f26c6d28eba14a79a64a32d16d55d4f6427f9920163440df09cb |
| .context/proposals/cd-1-event-identity.md | 53a7a1d3eabfddf578d067895a0758ef228f5575e403d050cbb280bbf915356c |
| .context/proposals/cd-1-geography-basis.md | 3af4f3e1a7aa56b1c2941d0d3d9f752ab334fb9d40ea75cc1bebd3b806e191ff |
| .context/proposals/cd-1-lake-layout.md | 1d17120207e2d56b8d82d165961a0132af7c82015bc1f62c134b8429cfbb73c0 |
| .context/proposals/cd-1-late-events.md | b970e9b965d5b9055f9f523c7976f0be07938d2a0882cf1ab46d9a9adb55d142 |
| .context/proposals/cd-1-money-decimal.md | 1a40b33728cc36f243bcf158a24bf8befb81d54a3cf6b33a7d35fde05fd7bc7e |
| .context/proposals/cd-1-population-vintage.md | 4a848c5bd369cd60814d4fefd58157308de16c42b66d4881610c09e8586d50de |
| .context/proposals/cd-1-stream-commit.md | 1ea91966d39fe16ae8771114175303f23c39b023c5f7c4316683f02dfd91f3f9 |
| .context/proposals/cd-1-yaml-validation.md | ad9ed0ba0ef5d9ad548e77d459362c140842dfdc40612b3d67fee5b997e7bf77 |
| .context/proposals/cd-1.md | 854df8ca189270382db9a0bb3df3bad60e8e1ec3dcee6a9a691eb2758e2074fb |
| .context/prs/draft-pr-c11abad2-208f-4d85-bb55-2a95c021b556.md | 527ec9e82198278ef3b0a72f36599dd75e800dac71b47ffeb3b8a7500c44f474 |
| .context/reviews/plan_cd-1-gh-1-pipeline.md | b8afec0bf6bb28db4dab427ca8b148e5bdcc3ad6b6e0a565a1fe725c22465518 |

## Commits

- edc56ea refactor: meet the R3 limits for the cadence run
- b6ba463 phase 10: oracle map, decisions file, checks, and acceptance run
- aef8769 phase 9: dbt stream models: edit fact and 5-minute window mart
- 659274d phase 8: dbt batch models: staging, star schema, Question A mart
- f966319 phase 7: pipeline YAML files and make targets
- 4a1945f phase 6: event identity, edit rule and late events
- 775dbdb phase 5: stream source and micro-batch stream sink
- 911a543 phase 4: polars and datafusion transforms
- cd24c00 phase 3: file sources and clean source tables
- 3dc531e phase 2: engine core and parquet lake sink
- 7c9272e phase 1: pipeline YAML loading and schema validation
- 92eee78 phase 0: dependencies and package skeleton
- 4e102b4 cadence config for the trial

Write the summary to .context/summaries/cd-1.md.
