# trestle-bot

[![Pre commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![License](https://img.shields.io/badge/license-apache-blue.svg)](http://www.apache.org/licenses/LICENSE-2.0.html)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=rh-psce_trestle-bot&metric=coverage)](https://sonarcloud.io/summary/new_code?id=rh-psce_trestle-bot)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=rh-psce_trestle-bot&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=rh-psce_trestle-bot)


** **Note: Trestle-bot has moved from [RedHatProductSecurity](https://github.com/RedHatProductSecurity/) to the [Complytime](https://github.com/complytime/) GitHub organization.** **

trestle-bot is a CLI tool that assists users in leveraging [Compliance-Trestle](https://github.com/oscal-compass/compliance-trestle) in CI/CD workflows for [OSCAL](https://github.com/usnistgov/OSCAL) formatted compliance content management.

> WARNING: This project is currently under initial development. APIs may be changed incompatibly from one commit to another.

## Getting Started

### Available Commands

The `autosync` command will sync trestle-generated Markdown files to OSCAL JSON files in a trestle workspace. All content under the provided markdown directory will be transformed when the action is run. This action supports all top-level models [supported by compliance-trestle for authoring](https://oscal-compass.github.io/compliance-trestle/tutorials/ssp_profile_catalog_authoring/ssp_profile_catalog_authoring/).

The `rules-transform` command can be used when managing [OSCAL Component Definitions](https://pages.nist.gov/OSCAL-Reference/models/v1.1.1/component-definition/json-outline/) in a trestle workspace. The action will transform rules defined in the rules YAML view to an OSCAL Component Definition JSON file.

The `create compdef` command can be used to create a new [OSCAL Component Definition](https://pages.nist.gov/OSCAL-Reference/models/v1.1.1/component-definition/json-outline/) in a trestle workspace. The action will create a new Component Definition JSON file and corresponding directories that contain rules YAML files and trestle-generated Markdown files. This action prepares the workspace for use with the `rules-transform` and `autosync` actions.

The `sync-upstreams` command can be used to sync and validate upstream OSCAL content stored in a git repository to a local trestle workspace. The inputs `include_models` and `exclude_models` determine which content is synced to the trestle workspace.

The `create ssp` command can be used to create a new [OSCAL System Security Plans](https://pages.nist.gov/OSCAL-Reference/models/v1.1.1/system-security-plan/json-outline/) (SSP) in a trestle workspace. The action will create a new SSP JSON file and corresponding directories that contain trestle-generated Markdown files. This action prepares the workspace for use with the `autosync` action by creating or updating the `ssp-index.json` file. The `ssp-index.json` file is used to track the relationships between the SSP and the other OSCAL content in the workspace for the `autosync` action.

The `sync-cac-content` command supports transforming the [CaC content](https://github.com/ComplianceAsCode/content) to OSCAL models in a trestle workspace. For detailed documentation on how to use, see the [sync-cac-content.md](./docs/tutorials/sync-cac-content.md).  

The `sync-oscal-content` command supports sync OSCAL models to the [CaC content](https://github.com/ComplianceAsCode/content) in a trestle workspace. For detailed documentation on how to use, see the [sync-oscal-content.md](./docs/tutorials/sync-oscal-content.md).  


Below is a table of the available commands and their current availability as a GitHub Action:

| Command                                   | Available as a GitHub Action |
|-------------------------------------------|------------------------------|
| `autosync`                                | &#10003;                     |
| `rules-transform`                         | &#10003;                     |                   
| `create compdef`                          | &#10003;                     |
| `sync-upstreams`                          | &#10003;                     |
| `create ssp`                              |                              |
| `sync-cac-content component-definition`   |                              |
| `sync-cac-content profile`                |                              |
| `sync-cac-content catalog`                |                              |
| `sync-oscal-content component-definition` |                              |
| `sync-oscal-content profile`              |                              |

For detailed documentation on how to use each action, see the README.md in each folder under [actions](./actions/).


### Supported Git Providers

> Note: Only applicable if using `trestle-bot` to create pull requests. Automatically detecting the git
provider information is supported for GitHub Actions (GitHub) and GitLab CI (GitLab).

- GitHub
- GitLab

### Run as a Container

> Note: When running the commands in a container, all are prefixed with `trestlebot` (e.g. `trestlebot autosync`). The default entrypoint for the container is the autosync command.

Build and run the container locally:

```bash
podman build -f Dockerfile -t trestle-bot .
podman run -v $(pwd):/data -w /data trestle-bot
```

Container images are available in `quay.io`:

```bash
podman run -v $(pwd):/data -w /data quay.io/continuouscompliance/trestle-bot:<tag>
```

## Contributing

For information about contributing to trestle-bot, see the [CONTRIBUTING.md](./CONTRIBUTING.md) file.

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE.md](LICENSE) file for details.

## Troubleshooting

See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for troubleshooting tips.
