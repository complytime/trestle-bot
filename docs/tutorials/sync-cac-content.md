# The trestlebot command line sync-cac-content Tutorial

This tutorial provides how to use `trestlebot sync-cac-content` transform [Cac content](https://github.com/ComplianceAsCode/content) to OSCAL models.
This command has two sub-commands `component-definition` and `profile`

## component-definition

This command is to create OSCAL component definitions by transforming Cac content control files.

The CLI performs the following transformations:

- Populate CaC product information to Oscal component title and description
- Ensure OSCAL component control mappings are populated with rule and rule parameter data from CaC control files
- Create a validation component from SSG rules to check mappings
- Ensure OSCAL Component Definition implemented requirements are populated from control notes in the control file
- Ensure implementation status of an implemented requirement in OSCAL component definitions are populated with the status from CaC control files

### 1. Prerequisites

- Initialize the [trestlebot workspace](../tutorials/github.md#3-initialize-trestlebot-workspace).

- Pull the [CacContent repository](https://github.com/ComplianceAsCode/content).

### 2. Run the CLI sync-cac-content component-definition
```shell
poetry run trestlebot sync-cac-content component-definition \
  --repo-path $trestlebot_workspace_directory \
  --branch main \
  --cac-content-root ~/content \
  --cac-profile $high-rev-4 \
  --oscal-profile $OSCAL-profile-name \
  --committer-email test@redhat.com \
  --committer-name tester \
  --product $productname \
  --dry-run \
  --component-definition-type $type
```

For more details about these options and additional flags, you can use the --help flag:
`poetry run trestlebot sync-cac-content component-definition --help'
This will display a full list of available options and their descriptions.

After run the CLI with the right options, you would successfully generate an OSCAL component definition under $trestlebot_workplace_directory/component-definitions/$product_name.

## profile

This command is to generate OSCAL profile according to content policy 

### 1. Prerequisites

- Initialize the [trestlebot workspace](../tutorials/github.md#3-initialize-trestlebot-workspace) if you do not have one.

- Pull the [CacContent repository](https://github.com/ComplianceAsCode/content).

### 2. Run the CLI sync-cac-content profile
```shell
poetry run trestlebot sync-cac-content profile \ 
--repo-path ~/trestlebot-workspace \
--dry-run \
--cac-content-root ~/content \
--product ocp4 \ 
--oscal-catalog nist_rev5_800_53 \
--cac-policy-id nist_ocp4 \ 
--committer-email test@redhat.com \
--committer-name test \
--branch main
```

For more details about these options and additional flags, you can use the --help flag:
`poetry run trestlebot sync-cac-content profile --help'
This will display a full list of available options and their descriptions.

After run the CLI with the right options, you would successfully generate an OSCAL profile under $trestlebot_workplace_directory/profiles.
