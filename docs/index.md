# Django Migration Inspector

Django Migration Inspector is an open-source migration safety toolkit for Django teams.

It helps answer the questions that usually show up too late:

1. What will this migration chain actually do?
2. Are there merge conflicts or multiple heads in the graph?
3. Is rollback straightforward or dangerous?
4. Are our environments drifting away from the codebase?

The current implementation already provides:

1. Typed migration graph loading.
2. Graph intelligence reports for roots, leaves, merges, and conflict heads.
3. Local-first visual outputs in text, JSON, Mermaid, and Graphviz DOT.
4. A reusable Django management command that works in local development and CI.

## Why this toolkit exists

Django migrations are powerful, but teams still discover many migration problems too late:

1. During CI.
2. During deploys.
3. During rollback attempts.
4. After production drift is already confusing the release process.

This toolkit shifts that feedback left.

## Open-source-first promise

The project is designed to stay useful without any paid service:

1. All core functionality runs locally or in CI.
2. No hosted backend is required.
3. No account or telemetry is required.
4. Rules, schemas, and documentation live in the repository.

## Documentation hosting

This docs site is set up to work with both:

1. GitHub Pages through the `.github/workflows/docs.yml` workflow
2. Read the Docs through the `.readthedocs.yaml` configuration

## Next milestones

The next feature layers planned on top of the graph foundation are:

1. Rule-driven risk analysis.
2. Rollback simulation.
3. Environment snapshot export and drift comparison.
