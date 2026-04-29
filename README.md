# ProjectTemplateDemo5

A iOS project structure template that creates a standard folder layout from user input and optionally files a **Bug** on a Jira board.

## What it does

`ios_template.py` creates a project directory with an iOS-friendly layout and, if Jira credentials are provided, opens a Bug issue on the configured Jira project.

### Generated folder structure

```
<ProjectName>/
├── App/
├── Resources/
│   ├── Assets.xcassets/
│   └── Localizations/
├── Core/
│   ├── Models/
│   ├── Networking/
│   ├── Utilities/
│   └── Extensions/
├── Modules/
│   └── <Feature>/        # one per --features entry
│       ├── View/
│       ├── ViewModel/
│       └── Model/
├── Services/
└── SupportingFiles/
    ├── Configs/
    └── Constants/
```

Optional additions:

- Feature module scaffolding (`--features Auth,Profile`)
- Test folders (`--include-tests`): `Tests/UnitTests`, `Tests/UITests`

## Usage

### Basic

```bash
python3 ios_template.py MyApp
```

### With feature modules and tests

```bash
python3 ios_template.py MyApp --features Auth,Profile,Settings --include-tests
```

### Create under a custom path

```bash
python3 ios_template.py MyApp --base-path /path/to/workspace
```

### Interactive mode (project name prompted)

```bash
python3 ios_template.py
```

## Jira integration

After scaffolding, the tool can create a Bug on your Jira board. Supply credentials via **environment variables** or **CLI flags**.

### Environment variables

| Variable           | Description                                      |
|--------------------|--------------------------------------------------|
| `JIRA_URL`         | Jira instance base URL (e.g. `https://org.atlassian.net`) |
| `JIRA_EMAIL`       | Atlassian account email                          |
| `JIRA_API_TOKEN`   | API token from <https://id.atlassian.com>        |
| `JIRA_PROJECT_KEY` | Jira project key (e.g. `MYAPP`)                 |

```bash
export JIRA_URL="https://yourorg.atlassian.net"
export JIRA_EMAIL="you@example.com"
export JIRA_API_TOKEN="your_api_token"
export JIRA_PROJECT_KEY="MYAPP"

python3 ios_template.py MyApp --features Auth --include-tests
```

### CLI flags

```bash
python3 ios_template.py MyApp \
  --jira-url "https://yourorg.atlassian.net" \
  --jira-email "you@example.com" \
  --jira-api-token "your_api_token" \
  --jira-project "MYAPP"
```

### Skip Jira creation

```bash
python3 ios_template.py MyApp --skip-jira
```

## All options

```
positional arguments:
  project_name          Project folder name. If omitted, you will be prompted.

optional arguments:
  --base-path PATH      Where to create the project folder (default: .)
  --features FEATURES   Comma-separated feature module names (e.g. Auth,Profile)
  --include-tests       Create UnitTests and UITests folders
  --force               Allow using an existing non-empty project directory

Jira:
  --jira-url URL        Jira instance base URL
  --jira-email EMAIL    Atlassian account email
  --jira-api-token TOKEN  Jira API token
  --jira-project KEY    Jira project key
  --skip-jira           Skip Jira bug creation
```
