# GitHub Repository Setup Guide

This guide helps you configure the GitHub repository with proper branch protection rules, workflows, and templates for the Plotari Chatbot project.

## Repository Settings

### 1. Branch Protection Rules

Navigate to **Settings > Branches** and add the following protection rules:

#### Main Branch Protection
- **Branch name pattern**: `main`
- **Require a pull request before merging**: ✅
  - Require approvals: 2
  - Dismiss stale PR approvals when new commits are pushed: ✅
- **Require status checks to pass before merging**: ✅
  - Require branches to be up to date before merging: ✅
  - Status checks: `test`, `lint`, `security`
- **Require conversation resolution before merging**: ✅
- **Restrict pushes that create files**: ✅
- **Require linear history**: ✅
- **Include administrators**: ✅

#### Staging Branch Protection
- **Branch name pattern**: `staging`
- **Require a pull request before merging**: ✅
  - Require approvals: 1
- **Require status checks to pass before merging**: ✅
  - Status checks: `test`, `lint`
- **Restrict pushes that create files**: ✅

#### Dev Branch Protection
- **Branch name pattern**: `dev`
- **Require a pull request before merging**: ✅
  - Require approvals: 1
- **Allow force pushes**: ✅ (for rebasing)

### 2. Repository Settings

#### General Settings
- **Repository name**: `plotari-ai`
- **Description**: `Plotari Chatbot Backend - AI-powered property search with Weaviate, OpenAI, and Supabase`
- **Visibility**: Private (or Public based on your needs)
- **Features**:
  - Issues: ✅
  - Projects: ✅
  - Wiki: ❌
  - Discussions: ✅

#### Security Settings
- **Dependency graph**: ✅
- **Dependabot alerts**: ✅
- **Dependabot security updates**: ✅
- **Code scanning**: ✅ (if available)

### 3. Environment Setup

Create the following environments in **Settings > Environments**:

#### Staging Environment
- **Name**: `staging`
- **Protection rules**:
  - Required reviewers: 1
  - Wait timer: 0 minutes
- **Environment secrets**: Add staging-specific secrets

#### Production Environment
- **Name**: `production`
- **Protection rules**:
  - Required reviewers: 2
  - Wait timer: 5 minutes
- **Environment secrets**: Add production-specific secrets

## Workflow Configuration

### 1. GitHub Actions

The repository includes the following workflows:

- **CI/CD Pipeline** (`.github/workflows/ci.yml`):
  - Runs on push to main, staging, dev branches
  - Runs on pull requests
  - Includes testing, linting, security checks, and Docker builds

### 2. Required Status Checks

Configure the following status checks as required:

- `test` - Python tests
- `lint` - Code linting
- `security` - Security scanning
- `build` - Docker build

## Issue and PR Templates

### 1. Issue Templates

The repository includes:
- **Bug Report** (`.github/ISSUE_TEMPLATE/bug_report.md`)
- **Feature Request** (`.github/ISSUE_TEMPLATE/feature_request.md`)

### 2. Pull Request Template

- **PR Template** (`.github/pull_request_template.md`)

## Labels Setup

Create the following labels in **Issues > Labels**:

### Priority Labels
- `priority: critical` (Red)
- `priority: high` (Orange)
- `priority: medium` (Yellow)
- `priority: low` (Green)

### Type Labels
- `type: bug` (Red)
- `type: feature` (Green)
- `type: enhancement` (Blue)
- `type: documentation` (Purple)
- `type: refactor` (Gray)

### Status Labels
- `status: in-progress` (Blue)
- `status: blocked` (Red)
- `status: needs-review` (Yellow)
- `status: ready-for-testing` (Green)

### Component Labels
- `component: api` (Blue)
- `component: chatbot` (Green)
- `component: weaviate` (Purple)
- `component: openai` (Orange)
- `component: supabase` (Cyan)
- `component: frontend` (Pink)

## Webhooks (Optional)

If you need to integrate with external services:

1. Go to **Settings > Webhooks**
2. Add webhook URL for your deployment system
3. Select events: Push, Pull request, Release

## Team Permissions

### Repository Roles

- **Maintainers**: Full access to repository
- **Developers**: Write access to dev and feature branches
- **Reviewers**: Read access with ability to review PRs

### Team Setup

1. Create teams in **Settings > Teams**
2. Assign appropriate permissions
3. Add team members

## Security Settings

### 1. Security Advisories

- Enable security advisories
- Configure vulnerability reporting

### 2. Code Scanning

- Enable CodeQL analysis (if available)
- Configure security scanning

### 3. Dependency Management

- Enable Dependabot
- Configure dependency updates

## Monitoring and Analytics

### 1. Insights

Monitor repository health through:
- **Pulse**: Recent activity
- **Contributors**: Contribution statistics
- **Community**: Health metrics
- **Traffic**: Clone and view statistics

### 2. Notifications

Configure notifications for:
- Security alerts
- Dependency updates
- Failed CI/CD runs
- Pull request reviews

## Backup and Recovery

### 1. Repository Backup

- Regular exports of repository data
- Backup of important branches
- Documentation of critical configurations

### 2. Disaster Recovery

- Document recovery procedures
- Test backup restoration
- Maintain offsite copies of critical data

## Documentation

### 1. Repository Documentation

- README.md (main project documentation)
- CONTRIBUTING.md (contribution guidelines)
- LICENSE (project license)
- CHANGELOG.md (version history)

### 2. API Documentation

- OpenAPI/Swagger documentation
- Code examples
- Integration guides

## Maintenance

### 1. Regular Tasks

- Review and update dependencies
- Clean up old branches
- Update documentation
- Review security settings

### 2. Monitoring

- Monitor CI/CD pipeline health
- Track issue resolution times
- Review code review metrics
- Monitor security alerts

---

For questions about this setup, please create an issue or contact the repository maintainers.
