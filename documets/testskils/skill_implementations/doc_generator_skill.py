#!/usr/bin/env python3
"""
Documentation Generator Skill for GitCodeSkill Repository
Generates comprehensive documentation for the enterprise development automation system.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re


class GitCodeSkillDocGenerator:
    """Advanced documentation generator for GitCodeSkill system."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.components = self._analyze_components()
        
    def _analyze_components(self) -> Dict:
        """Analyze repository structure and components."""
        components = {
            'steps': [],
            'core_files': [],
            'config_files': [],
            'documentation': [],
            'dependencies': []
        }
        
        # Analyze step files
        for step_file in self.repo_path.glob('step_*.py'):
            components['steps'].append({
                'file': step_file.name,
                'path': str(step_file),
                'step_number': int(step_file.name.split('_')[1]),
                'purpose': self._extract_docstring_purpose(step_file)
            })
        
        # Core system files
        core_files = ['orchestrator.py', 'app.py', 'repo_discovery.py']
        for core_file in core_files:
            file_path = self.repo_path / core_file
            if file_path.exists():
                components['core_files'].append({
                    'file': core_file,
                    'path': str(file_path),
                    'purpose': self._extract_docstring_purpose(file_path)
                })
        
        # Configuration and documentation files
        components['config_files'] = list(self.repo_path.glob('*config*'))
        components['documentation'] = list(self.repo_path.glob('*.md'))
        
        return components
    
    def _extract_docstring_purpose(self, file_path: Path) -> str:
        """Extract purpose from Python file docstring."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # Look for module docstring
                docstring_pattern = r'"""([^"]*?)"""'
                match = re.search(docstring_pattern, content, re.DOTALL)
                if match:
                    return match.group(1).strip().split('\n')[0]
        except Exception:
            pass
        return "No description available"
    
    def generate_full_documentation(self) -> str:
        """Generate comprehensive system documentation."""
        doc = []
        
        # Header
        doc.append("# GitCodeSkill - Enterprise Development Automation System")
        doc.append("## Complete System Documentation\n")
        
        # System Overview
        doc.append(self._generate_system_overview())
        
        # Architecture Section
        doc.append(self._generate_architecture_docs())
        
        # Step-by-step Documentation
        doc.append(self._generate_step_documentation())
        
        # Configuration Documentation
        doc.append(self._generate_configuration_docs())
        
        # API Documentation
        doc.append(self._generate_api_documentation())
        
        # Integration Guide
        doc.append(self._generate_integration_guide())
        
        # Troubleshooting
        doc.append(self._generate_troubleshooting_guide())
        
        return '\n\n'.join(doc)
    
    def _generate_system_overview(self) -> str:
        """Generate system overview documentation."""
        return """## System Overview

GitCodeSkill is a production-ready enterprise automation system that transforms development workflows from requirement gathering to code deployment. The system implements a sophisticated 7-step pipeline that handles:

### Key Capabilities
- **Multi-Repository Analysis**: Scan and analyze hundreds of repositories across GitHub and Bitbucket
- **Intelligent Code Mapping**: Semantic analysis to map requirements to relevant code components
- **Automated Change Application**: Precise code modifications with quality assurance
- **Cross-Platform Support**: Windows, Linux, and macOS compatibility
- **Enterprise Integration**: Jira, GitHub, Bitbucket Server/Cloud support

### Technology Foundation
- **Core**: Python 3.8+ with modern async capabilities
- **Web UI**: Streamlit with custom dark theme
- **APIs**: REST integration with GitHub, Bitbucket, and Jira
- **Security**: Secure credential storage with platform-appropriate permissions
- **Quality**: Automated testing, formatting, and code analysis"""
    
    def _generate_architecture_docs(self) -> str:
        """Generate architecture documentation."""
        return """## System Architecture

### Pipeline Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                    GitCodeSkill Pipeline                    │
├─────────────────────────────────────────────────────────────┤
│  Step 0: Setup & Config     │  Credential management        │
│  Step 1: Clone & Analyze    │  Multi-repo code analysis     │
│  Step 2: Fetch Requirements │  Jira integration or manual   │
│  Step 3: Map Changes        │  Semantic requirement mapping │
│  Step 4: Review & Confirm   │  Human approval workflow      │
│  Step 5: Apply Changes      │  Automated code modification  │
│  Step 6: Commit & Push      │  Version control & PR creation│
└─────────────────────────────────────────────────────────────┘
```

### Data Flow Architecture
Each step produces structured JSON output consumed by subsequent steps:
- `config.json` → System configuration and credentials
- `analysis_report.json` → Repository analysis and code index
- `requirement.json` → Structured requirement specification
- `change_proposal.json` → Mapped changes with relevance scores
- `apply_result.json` → Application results and test outcomes
- `commit_result.json` → Version control and deployment status

### Component Interaction Model
- **Modular Design**: Each step is completely standalone
- **Process Isolation**: Steps communicate via JSON files and subprocess calls
- **Fault Tolerance**: Individual step failures don't cascade
- **Extensibility**: Easy to add new providers or modify individual components"""
    
    def _generate_step_documentation(self) -> str:
        """Generate detailed step documentation."""
        doc = ["## Step-by-Step Documentation"]
        
        # Sort steps by number
        sorted_steps = sorted(self.components['steps'], key=lambda x: x['step_number'])
        
        for step in sorted_steps:
            doc.append(f"""### Step {step['step_number']}: {step['file']}

**Purpose**: {step['purpose']}

**Key Functions**:
{self._analyze_step_functions(step['path'])}

**Input/Output**:
{self._analyze_step_io(step['step_number'])}

**CLI Usage**:
```bash
python {step['file']} --help
```

**Integration Points**:
{self._analyze_step_integrations(step['step_number'])}""")
        
        return '\n\n'.join(doc)
    
    def _analyze_step_functions(self, step_path: str) -> str:
        """Analyze key functions in a step file."""
        try:
            with open(step_path, 'r', encoding='utf-8') as f:
                content = f.read()
                functions = re.findall(r'def ([a-zA-Z_][a-zA-Z0-9_]*)\(', content)
                # Filter out private functions and common ones
                key_functions = [f for f in functions if not f.startswith('_') and f != 'main'][:5]
                if key_functions:
                    return '- ' + '\n- '.join([f"`{func}()`" for func in key_functions])
                return "- Main processing function"
        except Exception:
            return "- Core step processing logic"
    
    def _analyze_step_io(self, step_num: int) -> str:
        """Analyze input/output for each step."""
        io_mapping = {
            0: "Input: User credentials | Output: config/config.json",
            1: "Input: config.json | Output: analysis_report.json",
            2: "Input: config.json | Output: requirement.json", 
            3: "Input: analysis_report.json, requirement.json | Output: change_proposal.json",
            4: "Input: change_proposal.json | Output: Updated change_proposal.json",
            5: "Input: change_proposal.json | Output: apply_result.json",
            6: "Input: apply_result.json | Output: commit_result.json"
        }
        return io_mapping.get(step_num, "Input/Output analysis not available")
    
    def _analyze_step_integrations(self, step_num: int) -> str:
        """Analyze integration points for each step."""
        integrations = {
            0: "File system (config storage), User interaction",
            1: "Git (clone/pull), File system analysis, REST APIs (multi-repo discovery)",
            2: "Jira REST API, User input validation",
            3: "Natural language processing, Code indexing algorithms", 
            4: "User interaction, Change specification parsing",
            5: "Git (branch creation), File manipulation, Testing frameworks, Code formatters",
            6: "Git (commit/push), GitHub API, Bitbucket API, Pull request creation"
        }
        return integrations.get(step_num, "Integration analysis not available")
    
    def _generate_configuration_docs(self) -> str:
        """Generate configuration documentation."""
        return """## Configuration Management

### Configuration File Structure
```json
{
  "git_provider": "github|bitbucket",
  "repo_url": "Repository clone URL",
  "git_username": "Username for Git operations",
  "git_password": "Personal Access Token or App Password",
  "git_branch": "Default branch (main/develop)",
  "github_owner": "Optional: GitHub org for multi-repo scan",
  "project_keys": ["Optional: Bitbucket project keys"],
  "jira_url": "Optional: Jira instance URL",
  "jira_email": "Optional: Jira authentication email",
  "jira_token": "Optional: Jira API token",
  "workspace_dir": "Local workspace directory"
}
```

### Security Considerations
- **Credential Storage**: Platform-appropriate file permissions (chmod 600 on Unix)
- **Token Management**: Uses modern API tokens, never passwords
- **Display Masking**: Credentials displayed as first4****last4 format
- **Location**: Stored in project-relative config/ directory (not home directory)

### Multi-Repository Configuration
For enterprise environments with multiple repositories:
- **GitHub**: Set `github_owner` to scan all repositories under an organization
- **Bitbucket**: Set `project_keys` array to scan across multiple project keys
- **Scaling**: Automatic cleanup prevents disk space issues during mass scanning"""
    
    def _generate_api_documentation(self) -> str:
        """Generate API integration documentation."""
        return """## API Integration Documentation

### GitHub Integration
**Authentication**: Personal Access Token (Bearer)
**Endpoints Used**:
- `GET /orgs/{owner}/repos` - Organization repository listing
- `GET /users/{owner}/repos` - User repository listing  
- `POST /repos/{owner}/{repo}/pulls` - Pull request creation

**Required Scopes**:
- `repo` (for private repositories)
- `public_repo` (for public repositories)
- `pull_requests:write` (for PR creation)

### Bitbucket Integration
**Authentication**: App Password (Basic Auth)
**Server Endpoints**:
- `GET /rest/api/1.0/projects/{key}/repos` - Project repository listing
- `POST /rest/api/1.0/projects/{key}/repos/{slug}/pull-requests` - PR creation

**Cloud Endpoints**:
- `GET /2.0/repositories/{workspace}` - Workspace repository listing
- `POST /2.0/repositories/{workspace}/{repo}/pullrequests` - PR creation

**Required Permissions**:
- `Repositories: Read, Write`
- `Pull Requests: Read, Write`

### Jira Integration  
**Authentication**: API Token (Basic Auth with email)
**Endpoints Used**:
- `GET /rest/api/3/issue/{key}?expand=renderedFields,names,changelog` - Issue details
- `GET /rest/api/3/myself` - Connection testing

**Token Generation**: 
- Jira Cloud: https://id.atlassian.net/manage-profile/security/api-tokens
- Jira Server: Regular password used as token

### Error Handling Patterns
All API integrations implement:
- **Pagination**: Automatic handling of paginated responses
- **Rate Limiting**: Respect for API rate limits with backoff
- **Retry Logic**: Automatic retry on transient failures
- **Error Classification**: Differentiation between auth, network, and data errors"""
    
    def _generate_integration_guide(self) -> str:
        """Generate integration guide."""
        return """## Integration Guide

### Enterprise CI/CD Integration

#### Jenkins Integration
```groovy
pipeline {
    stages {
        stage('Automated Development') {
            steps {
                script {
                    sh '''
                        python orchestrator.py --full --ticket ${JIRA_TICKET} 
                            --auto-apply --push --create-pr
                    '''
                    // Parse commit_result.json for PR URL
                    def result = readJSON file: 'commit_result.json'
                    env.PR_URL = result.pr_url
                }
            }
        }
    }
}
```

#### GitHub Actions Integration
```yaml
name: Automated Feature Development
on:
  workflow_dispatch:
    inputs:
      jira_ticket:
        description: 'Jira ticket ID'
        required: true
jobs:
  develop:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run GitCodeSkill Pipeline
        run: |
          python orchestrator.py --full --ticket ${{ github.event.inputs.jira_ticket }} 
            --auto-apply --push --create-pr
```

### Multi-Environment Deployment

#### Development Environment
- **Mode**: Interactive with manual review (Step 4 confirmation)
- **Testing**: Full test suite execution
- **Formatting**: All code formatters enabled

#### Staging Environment  
- **Mode**: `--auto-apply` with human oversight
- **Branch Strategy**: Feature branches with PR to develop
- **Validation**: Integration tests and code quality gates

#### Production Environment
- **Mode**: Fully automated with approval workflows
- **Branch Strategy**: PR to main with required reviews
- **Rollback**: Automatic branch creation for easy rollback

### Scaling Considerations

#### Large Organization (100+ Repositories)
```bash
# Multi-repo analysis with resource management
python step_1_analyze.py --multi-repo --github-owner large-org --no-cleanup
# Process results in batches to prevent memory issues
```

#### High-Frequency Development
- **Parallel Processing**: Multiple workspace directories for concurrent pipelines
- **Resource Limits**: Configure workspace cleanup policies
- **Caching**: Repository analysis caching for frequently modified repos"""
    
    def _generate_troubleshooting_guide(self) -> str:
        """Generate troubleshooting guide."""
        return """## Troubleshooting Guide

### Common Issues and Solutions

#### Configuration Problems
**Issue**: "No configuration found"
```bash
# Solution: Run interactive setup
python step_0_setup.py
# Or verify config file exists
ls config/config.json
```

**Issue**: "Authentication failed"
```bash
# GitHub: Verify PAT has correct scopes
# Bitbucket: Ensure App Password has repository permissions
# Test connection:
python step_0_setup.py --show
```

#### Repository Analysis Issues
**Issue**: "Clone failed" 
```bash
# Check URL format and credentials
git clone {your_repo_url}
# Verify network access to Git provider
```

**Issue**: "No files analyzed"
```bash
# Check .gitignore patterns aren't too restrictive
# Verify repository has supported file types
python step_1_analyze.py --local-path /path/to/repo
```

#### Multi-Repository Problems
**Issue**: "No repositories found in organization"
```bash
# Verify organization name and PAT permissions
python repo_discovery.py --github-owner your-org
# Check API access:
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.github.com/orgs/your-org/repos
```

**Issue**: "Disk space issues during multi-repo scan"
```bash
# Enable automatic cleanup (default behavior)
python step_1_analyze.py --multi-repo --github-owner org
# Monitor disk usage in workspace directory
```

#### Mapping and Application Issues
**Issue**: "No relevant files found in mapping"
```bash
# Ensure requirement has detailed description
# Check that analysis_report.json was generated correctly
# Add more specific keywords to requirement description
```

**Issue**: "Changes failed to apply"
```bash
# Check file permissions and git status
# Verify branch creation succeeded
# Review apply_result.json for detailed error information
```

#### Integration Failures
**Issue**: "Jira connection failed"
```bash
# Test Jira connectivity
python step_2_jira.py --test-connection
# Verify API token at: https://id.atlassian.net/manage-profile/security/api-tokens
```

**Issue**: "Pull request creation failed"
```bash
# Verify push succeeded first
# Check API token has PR creation permissions
# Review commit_result.json for specific error details
```

### Debug Mode
Enable verbose logging for any step:
```bash
python step_N_name.py --verbose
```

### Log Analysis
Check step outputs for detailed error information:
- Each step produces JSON output with success/failure status
- Error messages include specific failure reasons and suggested fixes
- Use `--show-only` flags where available for dry-run testing

### Performance Optimization
For large repositories or organizations:
```bash
# Use local analysis to skip cloning
python step_1_analyze.py --local-path /existing/repo/path

# Limit multi-repo scan scope  
python step_1_analyze.py --multi-repo --project-keys SPECIFIC_PROJECT

# Skip tests during development iterations
python step_5_apply.py --no-tests
```"""
    
    def generate_step_specific_docs(self, step_number: int) -> str:
        """Generate documentation for a specific step."""
        step_info = next((s for s in self.components['steps'] if s['step_number'] == step_number), None)
        if not step_info:
            return f"Step {step_number} not found."
        
        return f"""# Step {step_number}: {step_info['file']} Documentation

## Purpose
{step_info['purpose']}

## Detailed Analysis
{self._analyze_step_functions(step_info['path'])}

## Input/Output Flow
{self._analyze_step_io(step_number)}

## Integration Points
{self._analyze_step_integrations(step_number)}

## Usage Examples
```bash
# Basic usage
python {step_info['file']}

# With specific options (see --help for full list)
python {step_info['file']} --help
```

## Code Structure
{self._get_code_structure(step_info['path'])}"""
    
    def _get_code_structure(self, file_path: str) -> str:
        """Analyze code structure of a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Extract classes
                classes = re.findall(r'class ([a-zA-Z_][a-zA-Z0-9_]*)', content)
                
                # Extract functions
                functions = re.findall(r'def ([a-zA-Z_][a-zA-Z0-9_]*)', content)
                
                # Extract imports
                imports = re.findall(r'^(import|from) ([a-zA-Z_][a-zA-Z0-9_\.]*)', content, re.MULTILINE)
                
                structure = []
                
                if classes:
                    structure.append("**Classes**: " + ', '.join(classes))
                
                if functions:
                    public_functions = [f for f in functions if not f.startswith('_')][:10]
                    structure.append("**Public Functions**: " + ', '.join(public_functions))
                
                if imports:
                    import_modules = list(set([imp[1] for imp in imports]))[:10]
                    structure.append("**Key Dependencies**: " + ', '.join(import_modules))
                
                return '\n'.join(structure) if structure else "Code structure analysis not available"
                
        except Exception:
            return "Unable to analyze code structure"
    
    def generate_configuration_guide(self) -> str:
        """Generate configuration-specific documentation."""
        return """# GitCodeSkill Configuration Guide

## Quick Setup

### Interactive Setup (Recommended for first-time users)
```bash
python step_0_setup.py
```
The system will prompt you for all required information with helpful explanations.

### Command Line Setup (For automation/CI)
```bash
# GitHub setup
python step_0_setup.py \
  --git-provider github \
  --repo-url https://github.com/your-org/your-repo.git \
  --git-username your-username \
  --git-password ghp_your_personal_access_token \
  --workspace-dir /path/to/workspace

# Bitbucket with Jira setup  
python step_0_setup.py \
  --git-provider bitbucket \
  --repo-url https://bitbucket.company.com/scm/PROJ/repo.git \
  --git-username your-username \
  --git-password your-app-password \
  --jira-url https://company.atlassian.net \
  --jira-email your-email@company.com \
  --jira-token your-api-token \
  --workspace-dir /path/to/workspace
```

## Advanced Configuration

### Multi-Repository Setup
```bash
# GitHub organization scanning
python step_0_setup.py \
  --github-owner your-organization \
  --git-provider github

# Multiple Bitbucket projects
python step_0_setup.py \
  --project-keys "PROJ1,PROJ2,PROJ3" \
  --git-provider bitbucket
```

### Environment-Specific Configurations

#### Development Environment
```json
{
  "git_provider": "github",
  "repo_url": "https://github.com/company/project.git",
  "git_branch": "develop",
  "jira_url": "https://company-dev.atlassian.net",
  "workspace_dir": "./dev-workspace"
}
```

#### Production Environment
```json
{
  "git_provider": "bitbucket", 
  "repo_url": "https://bitbucket.company.com/scm/PROD/service.git",
  "git_branch": "main",
  "jira_url": "https://company.atlassian.net",
  "workspace_dir": "/opt/gitcodeskill/workspace"
}
```

## Security Best Practices

### Credential Management
- **Never use passwords**: Always use API tokens/Personal Access Tokens
- **Scope limitation**: Grant only necessary permissions to tokens
- **Rotation**: Regularly rotate API tokens
- **Environment separation**: Use different tokens for dev/staging/prod

### Token Generation Guides

#### GitHub Personal Access Token
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Required scopes:
   - `repo` (for private repositories)
   - `workflow` (if using GitHub Actions)
   - `read:org` (for organization scanning)

#### Bitbucket App Password  
1. Go to Bitbucket Settings → Personal settings → App passwords
2. Create app password with permissions:
   - Repositories: Read, Write
   - Pull requests: Read, Write
   - Projects: Read (for multi-project scanning)

#### Jira API Token
1. Go to https://id.atlassian.net/manage-profile/security/api-tokens
2. Create token with access to relevant projects
3. For Jira Server: use regular password as token

## Troubleshooting Configuration Issues

### Common Problems
**Problem**: Config file not found
**Solution**: Ensure config/config.json exists in project directory

**Problem**: Permission denied on config file
**Solution**: Check file permissions, should be 600 on Unix systems

**Problem**: API authentication failures
**Solution**: Verify tokens are current and have required scopes

### Validation Commands
```bash
# Show current configuration (credentials masked)
python step_0_setup.py --show

# Test Git connectivity
git ls-remote {your_repo_url}

# Test Jira connection
python step_2_jira.py --test-connection
```"""


def main():
    """Main function for testing the documentation generator."""
    import sys
    import io
    
    # Set UTF-8 encoding for output
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    else:
        # For older Python versions, wrap stdout
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    if len(sys.argv) < 2:
        print("Usage: python doc_generator_skill.py <repo_path> [command]")
        print("Commands: full, step<N>, config, api, troubleshoot")
        return
    
    repo_path = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else 'full'
    
    doc_gen = GitCodeSkillDocGenerator(repo_path)
    
    if command == 'full':
        result = doc_gen.generate_full_documentation()
    elif command.startswith('step') and len(command) > 4:
        step_num = int(command[4:])
        result = doc_gen.generate_step_specific_docs(step_num)
    elif command == 'config':
        result = doc_gen.generate_configuration_guide()
    elif command == 'api':
        result = doc_gen._generate_api_documentation()
    elif command == 'troubleshoot':
        result = doc_gen._generate_troubleshooting_guide()
    else:
        result = "Unknown command. Available: full, step<N>, config, api, troubleshoot"
    
    print(result)


if __name__ == "__main__":
    main()