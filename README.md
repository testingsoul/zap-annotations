# ZAP Annotations GitHub Action

Parse OWASP ZAP XML reports, publish a pull request summary comment, and fail the job when configured severities are found.

## Features

- Reads `zapreport-*.xml` files from a configurable directory.
- Filters by severity threshold list.
- Sorts summary rows by severity (`Critical`, `High`, `Medium`, `Low`, `Informational`).
- Publishes a PR summary table with severity labels and occurrence counts.
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

Use this action in pull request workflows after your ZAP scan step has generated XML reports.

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
        uses: testingsoul/zap-annotations@v1
        with:
          severities: "Critical,High,Medium"
          report-dir: "test/output"
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Notes

- `report-dir` must contain files named like `zapreport-*.xml`.
- If any alert matches `severities`, the step exits with code `1` to fail the job.
- On `pull_request` events, the action posts a comment to the PR with a summary table.


## License

MIT
