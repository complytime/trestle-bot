# The trestlebot command line sync-oscal-content Tutorial

This tutorial provides how to use `trestlebot sync-oscal-content` sync OSCAL models to [CaC content](https://github.com/ComplianceAsCode/content).

Currently, this command has two sub-command: `component-definition` and `profile`

## component-definition

This command is to sync OSCAL Component Definition information to CaC content side.

The CLI performs the following sync:

- Sync OSCAL component definition parameters/rules changes to CaC content profile file
- Sync OSCAL component definition parameters/rules changes to CaC content control file
- Add a hint comment to the control file when a missing rule is found in the CaC content repo.
- Sync OSCAL component definition control status changes to CaC content control file. Since status mapping between
cac and OSCAL is many-to-many relationship, if status can not be determined when sync, then add a comment to let user
decide. Discussion detail in [doc](https://github.com/complytime/trestle-bot/discussions/511)
- Add new option to cac var file when found variable exists but missing the option we sync.
- Sync OSCAL component definition statements field to CaC control notes field

### 1. Prerequisites

- Initialize the [trestlebot workspace](../tutorials/github.md#3-initialize-trestlebot-workspace).

- Pull the [CaC Content repository](https://github.com/ComplianceAsCode/content).

- Has an OSCAL Component Definition file, (transformed from CaC content using `sync-cac-content component-definition` cmd)

### 2. Run the CLI sync-oscal-content component-definition
```shell
poetry run trestlebot sync-oscal-content component-definition \ 
--branch main \
--cac-content-root $cac-content-dir \
--committer-name test \
--committer-email test@redhat.com \
--dry-run \
--repo-path $trestlebot-workspace-dir \
--product $product-name \
--oscal-profile $oscal-profile-name
```

For more details about these options and additional flags, you can use the --help flag:
`poetry run trestlebot sync-oscal-content component-definition --help`
This will display a full list of available options and their descriptions.


## profile

This command is to sync OSCAL profile information to CaC content side.

The CLI performs the following sync:

- Sync OSCAL profile control levels change to CaC control files

### 1. Prerequisites

- Initialize the [trestlebot workspace](../tutorials/github.md#3-initialize-trestlebot-workspace).

- Pull the [CaC Content repository](https://github.com/ComplianceAsCode/content).

- Have OSCAL profile file, (transformed from CaC content using `sync-cac-content profile` cmd)

### 2. Run the CLI sync-oscal-content profile
```shell
poetry run trestlebot sync-oscal-content profile \
--dry-run \
--repo-path ~/trestlebot-workspace \
--committer-email test@redhat.com \
--committer-name test\
--branch main \
--cac-content-root ~/content \
--cac-policy-id cis_rhel8 \
--product rhel8
```

For more details about these options and additional flags, you can use the --help flag:
`poetry run trestlebot sync-oscal-content profile --help`
This will display a full list of available options and their descriptions.
