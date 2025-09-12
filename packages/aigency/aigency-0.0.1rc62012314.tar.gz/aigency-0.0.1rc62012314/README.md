# aigency-lib

A library for creating and managing AI agents.

## Quick Start

To test a simple agent:

```bash
cd examples/simple_agents/hello_world_agent
docker compose up
```

## 🔧 Version Management

This project includes an automated system for managing versions in both development and production.

### Version Manager

The `scripts/version_manager.py` script helps you manage your package versions locally.

#### Available Commands

##### 1. View current information
```bash
python scripts/version_manager.py show
```
**What it does:**
- Shows the current version in `pyproject.toml`
- Shows the current git branch
- Shows the current commit
- If you're not on `main`, suggests a development version

**Example output:**
```
Current version: 0.0.1
Branch: feature/new-agent
Commit: a1b2c3d
Suggested dev version: 0.0.1.dev20250409143022+feature/new-agent.a1b2c3d
```

##### 2. Create development version
```bash
python scripts/version_manager.py dev
```
**What it does:**
- Takes the current version and creates a development version
- Format: `version.devYYYYMMDDHHMMSS+branch.commit`
- Automatically updates the `pyproject.toml`

**Example:**
```bash
# If you're on branch "feature/auth" with commit "abc123"
python scripts/version_manager.py dev
# Result: 0.0.1.dev20250409143022
```

##### 3. Set specific version
```bash
python scripts/version_manager.py set --version "0.1.0"
```
**What it does:**
- Changes the version to the one you specify
- Useful for releases or to fix versions

**Examples:**
```bash
# Release version
python scripts/version_manager.py set --version "1.0.0"

# Beta version
python scripts/version_manager.py set --version "1.0.0b1"

# Alpha version
python scripts/version_manager.py set --version "1.0.0a1"
```

##### 4. Create Release Candidate version
```bash
python scripts/version_manager.py rc --version "1.0.1"
```
**What it does:**
- Creates an RC version with the format `version-rc<commit>`
- Useful for preparing releases on `release/*` branches

##### 5. Validate current version
```bash
python scripts/version_manager.py validate
```
**What it does:**
- Validates that the current version is appropriate for the branch
- Verifies semantic format on `main` and `release/*` branches

##### 6. Create dev with custom base version
```bash
python scripts/version_manager.py dev --base-version "0.2.0"
```
**What it does:**
- Uses a different base version than the current one
- Useful when you want to prepare a dev version for the next release

### 🚀 Recommended Workflow

#### For daily development:
```bash
# 1. View current status
python scripts/version_manager.py show

# 2. If you're on a feature branch, create dev version
python scripts/version_manager.py dev

# 3. Make your changes and commits
git add .
git commit -m "feat: new functionality"

# 4. If you need to update the dev version (optional)
python scripts/version_manager.py dev
```

#### For releases:
```bash
# 1. On main branch, set release version
python scripts/version_manager.py set --version "1.0.0"

# 2. Commit the version
git add pyproject.toml
git commit -m "bump: version 1.0.0"

# 3. Use GitHub workflow to publish
```

#### For testing:
```bash
# Create specific test version
python scripts/version_manager.py set --version "1.0.0rc1"
```

### ⚠️ PyPI Limitations

PyPI doesn't allow "local versions" (versions with `+` and local identifiers). That's why we've adapted the format:

- ❌ Not allowed: `1.0.0.dev20250409+feature.abc123`
- ✅ Allowed: `1.0.0.dev20250409`

**Solution for Release Candidates:**
- We convert the commit hash (hexadecimal) to decimal
- Example: commit `abc123` → `11256099` → version `1.0.1rc11256099`
- This maintains commit uniqueness in a PyPI-compatible format

**Result:**
- Dev versions include unique timestamp
- RC versions include commit hash (in decimal)
- We maintain traceability without using local versions

### 📋 Practical Use Cases

**Scenario 1: Working on a feature**
```bash
git checkout -b feature/new-auth
python scripts/version_manager.py dev
# Now you have: 0.0.1.dev20250409143022
```

**Scenario 2: Preparing release**
```bash
git checkout main
python scripts/version_manager.py set --version "1.0.0"
git add pyproject.toml
git commit -m "release: v1.0.0"
```

**Scenario 3: Preparing Release Candidate**
```bash
git checkout -b release/1.0.1
python scripts/version_manager.py rc --version "1.0.1"
# Result: 1.0.1rc12345678 (where 12345678 is the commit hash in decimal)
```

**Scenario 4: Urgent hotfix**
```bash
git checkout -b hotfix/critical-bug
python scripts/version_manager.py dev --base-version "1.0.1"
# Result: 1.0.1.dev20250409143022
```

## 🔄 Intelligent CI/CD Workflow

The project includes a single intelligent workflow (`python-publish.yml`) that automatically handles different version types based on the branch:

### Automatic behavior by branch:

#### 🚀 `main` Branch - Production Versions
- **Trigger**: Push to `main` or manual execution
- **Version**: Uses exactly the version from `pyproject.toml`
- **Validations**:
  - ✅ Verifies it's a valid semantic version (e.g.: `1.0.0`)
  - ✅ Verifies it doesn't already exist on PyPI
  - ❌ Fails if it contains development suffixes (`dev`, `rc`, `alpha`, `beta`)
- **Target**: PyPI production

#### 🎯 `release/*` Branches - Release Candidates
- **Trigger**: Push to `release/X.Y.Z` branch or manual execution
- **Version**: `X.Y.ZrcN` where N is the commit hash in decimal (e.g.: `1.0.1rc12345678`)
- **Validations**:
  - ✅ Verifies that `X.Y.Z` is a valid semantic version
  - ✅ Extracts version from branch name
  - ✅ Uses commit hash as unique identifier
  - ✅ PyPI-compatible format
- **Target**: PyPI production
- **Example**: Branch `release/1.0.1` + commit `abc123` → Version `1.0.1rc11256099`

#### 🔧 Other Branches - Development Versions
- **Trigger**: Push to any other branch or manual execution
- **Version**: `current.devYYYYMMDDHHMMSS` (e.g.: `0.0.1.dev20250409143022`)
- **Target**: PyPI production
- **Note**: No local versions for PyPI compatibility

### Recommended workflow:

```bash
# 1. Development on feature branch
git checkout -b feature/new-functionality
# Automatic version: 0.0.1.dev20250409143022+feature-new-functionality.abc123

# 2. Prepare release
git checkout -b release/1.0.0
git push origin release/1.0.0
# Automatic version: 1.0.0rc12345678

# 3. Final release
git checkout main
python scripts/version_manager.py set --version "1.0.0"
git add pyproject.toml
git commit -m "release: v1.0.0"
git push origin main
# Version: 1.0.0 (with validations)
```

## 📦 Installation

```bash
pip install aigency
```

## 🛠️ Development

1. Clone the repository
2. Install development dependencies
3. Use the version manager to manage versions during development

```bash
git clone <repo-url>
cd aigency-lib
pip install -e .
```