# Releasing to PyPI

Publication is triggered by a **published GitHub Release**, not an ordinary push
or a tag alone. The release workflow calls CI, then uploads the checked
distributions using PyPI Trusted Publishing. No PyPI API token is required.

## One-time setup

The GitHub repository is `xyz1001/cmakelang-compat`, and its deployment environment
is named `pypi`. That environment allows deployments only from tags matching
`v*`.

Before the first release, sign in to PyPI and register a pending publisher at
<https://pypi.org/manage/account/publishing/>:

| Field | Value |
| --- | --- |
| PyPI project name | `cmakelang-compat` |
| GitHub owner | `xyz1001` |
| Repository | `cmakelang-compat` |
| Workflow filename | `publish.yml` |
| Environment | `pypi` |

Use the filename alone, not `.github/workflows/publish.yml`. A pending publisher
does not reserve the project name; the first successful upload creates the
project. If the project already exists under your account, configure its Trusted
Publisher from the project's publishing settings instead.

Restrict who can create releases and modify release workflows. Consider required
reviewers on the GitHub `pypi` environment if uploads should need an additional
approval; without that extra gate, publishing follows a successful release run
automatically. Never grant publishing permissions to pull-request jobs.

## Release a version

1. Set the version in `pyproject.toml`, commit it, and push to `main`.
2. Confirm CI passes.
3. Create and push a tag that is exactly `v` followed by that version.
4. Publish a GitHub Release for the tag.

For the initial alpha, the commands are:

```sh
git tag v0.1.0a1
git push origin v0.1.0a1
gh release create v0.1.0a1 --title "0.1.0a1" --generate-notes --prerelease
```

These are release commands, not development setup commands. Do not run them until
the PyPI publisher is configured and you intend to publish that version.

The workflow checks the tag against `pyproject.toml`, builds the wheel and sdist,
checks their metadata, and tests the installed wheel. Only the separate publish
job receives `id-token: write`; it downloads the checked artifacts and uploads
them without rebuilding or checking out source.

## If publication fails

- Check the `publish` workflow logs and any pending environment approval.
- Confirm all five publisher fields match exactly, especially `publish.yml` and
  `pypi`.
- PyPI versions are immutable. Do not replace an already uploaded version or
  silently skip conflicting files; prepare a new version when necessary.
- Fix workflow or configuration errors before retrying. Never paste PyPI tokens
  into issues or workflow files.
