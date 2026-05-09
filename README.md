# ZAP Annotations GitHub Action

Parse OWASP ZAP XML reports, publish a pull request summary comment, and fail the job when configured severities are found.

## Features

- Reads `zapreport-*.xml` files from a configurable directory.
- Filters by severity threshold list.
- Sorts summary rows by severity (`Critical`, `High`, `Medium`, `Low`, `Informational`).
- Adds severity colors in the PR summary table.
- Fails workflow when matching alerts are present.

## Inputs

- `severities` (optional): comma-separated severities that should fail the job. Default: `Critical,High,Medium`
- `report-dir` (optional): directory containing `zapreport-*.xml`. Default: `test/output`

## Required Permissions

```yaml
permissions:
  contents: read
  pull-requests: write
  issues: write
```

## Usage

```yaml
name: DAST

on:
  pull_request:

permissions:
  contents: read
  pull-requests: write
  issues: write

jobs:
  zap-annotate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Your ZAP scan step should produce test/output/zapreport-*.xml
      - name: Run ZAP Annotation
        uses: your-org/zap-annotations@v1
        with:
          severities: "Critical,High,Medium"
          report-dir: "test/output"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Publishing

1. Create a public repository and push these files.
2. Create and push tags (`v1.0.0`, then move major tag `v1`).
3. Add a GitHub Release for each version.
4. Publish in GitHub Marketplace from the release flow.

## License

MIT
