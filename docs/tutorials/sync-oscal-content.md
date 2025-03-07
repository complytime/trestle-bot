# The trestlebot command line sync-oscal-content Tutorial

This tutorial provides how to use `trestlebot sync-oscal-content` sync OSCAL models to [Cac content](https://github.com/ComplianceAsCode/content).

Currently, this command has one sub-commands `cac-control`

## cac-control

This command is to sync OSCAL component definitions(transformed from cac content using `sync-cac-content component-definition` cmd)
to Cac content profile file and control files.

The CLI performs the following sync:

- Sync OSCAL component definition parameters/rules changes to Cac content profile file
- Sync OSCAL component definition parameters/rules changes to Cac content control file

### 1. Prerequisites

- Initialize the [trestlebot workspace](../tutorials/github.md#3-initialize-trestlebot-workspace).

- Pull the [CacContent repository](https://github.com/ComplianceAsCode/content).

- Has an OSCAL component definition file(transformed from cac content using `sync-cac-content component-definition` cmd)

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
