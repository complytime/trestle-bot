# The trestlebot command line sync-oscal-content Tutorial

This tutorial provides how to use `trestlebot sync-oscal-content` sync OSCAL models to [CaC content](https://github.com/ComplianceAsCode/content).

Currently, this command has one sub-command: `cac-control`

## cac-control

This command is to sync OSCAL Component Definition files to CaC content profile file and control files.

The CLI performs the following sync:

- Sync OSCAL component definition parameters/rules changes to CaC content profile file
- Sync OSCAL component definition parameters/rules changes to CaC content control file
- Add a hint comment to the control file when a missing rule is found in the CaC content repo.
- Add new option to cac var file when found variable exists but missing the option we sync.

### 1. Prerequisites

- Initialize the [trestlebot workspace](../tutorials/github.md#3-initialize-trestlebot-workspace).

- Pull the [CaC Content repository](https://github.com/ComplianceAsCode/content).

- Has an OSCAL Component Definition file, (transformed from CaC content using `sync-cac-content component-definition` cmd)

### 2. Run the CLI sync-oscal-content cac-control
```shell
poetry run trestlebot sync-oscal-content cac-control \ 
--branch main \
--cac-content-root $cac-content-dir \
--committer-name test \
--committer-email test@redhat.com \
--dry-run \
--repo-path $trestlebot-workspace-dir \
--product $product-name
```

For more details about these options and additional flags, you can use the --help flag:
`poetry run trestlebot sync-oscal-content cac-control --help'
This will display a full list of available options and their descriptions.
