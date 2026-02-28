#!/usr/bin/env python3
"""
UML Diagram Generator Skill for GitCodeSkill Repository
Creates visual representations of system architecture, workflows, and component relationships.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass


@dataclass
class Component:
    """Represents a system component for diagram generation."""
    name: str
    type: str  # 'step', 'core', 'data', 'external'
    dependencies: List[str]
    description: str
    file_path: Optional[str] = None


@dataclass
class DataFlow:
    """Represents data flow between components."""
    source: str
    target: str
    data_type: str
    description: str


class GitCodeSkillUMLGenerator:
    """Advanced UML and diagram generator for GitCodeSkill system."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.components = self._analyze_system_components()
        self.data_flows = self._analyze_data_flows()
        
    def _analyze_system_components(self) -> Dict[str, Component]:
        """Analyze and categorize system components."""
        components = {}
        
        # Analyze step components
        for step_file in self.repo_path.glob('step_*.py'):
            step_num = int(step_file.name.split('_')[1])
            components[f"step_{step_num}"] = Component(
                name=f"Step {step_num}",
                type='step',
                dependencies=self._extract_dependencies(step_file),
                description=self._extract_step_purpose(step_num),
                file_path=str(step_file)
            )
        
        # Core system components
        core_files = {
            'orchestrator': 'Orchestrator',
            'app': 'Streamlit UI',
            'repo_discovery': 'Repository Discovery'
        }
        
        for file_key, name in core_files.items():
            file_path = self.repo_path / f"{file_key}.py"
            if file_path.exists():
                components[file_key] = Component(
                    name=name,
                    type='core',
                    dependencies=self._extract_dependencies(file_path),
                    description=self._extract_docstring_purpose(file_path),
                    file_path=str(file_path)
                )
        
        # External system components
        components['github'] = Component('GitHub API', 'external', [], 'Git provider and PR creation')
        components['bitbucket'] = Component('Bitbucket API', 'external', [], 'Git provider and PR creation')
        components['jira'] = Component('Jira API', 'external', [], 'Requirements and issue tracking')
        components['git'] = Component('Git CLI', 'external', [], 'Version control operations')
        
        return components
    
    def _extract_dependencies(self, file_path: Path) -> List[str]:
        """Extract dependencies from a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Find import statements
                import_patterns = [
                    r'import (subprocess|requests|pathlib|json)',
                    r'from (subprocess|requests|pathlib|json)',
                    r'step_\d+',
                    r'orchestrator',
                    r'repo_discovery'
                ]
                
                deps = set()
                for pattern in import_patterns:
                    matches = re.findall(pattern, content)
                    deps.update(matches)
                
                # Map to component names
                dep_mapping = {
                    'subprocess': 'system',
                    'requests': 'http_apis',
                    'pathlib': 'filesystem',
                    'json': 'data_processing'
                }
                
                return [dep_mapping.get(dep, dep) for dep in deps if dep]
        except Exception:
            return []
    
    def _extract_step_purpose(self, step_num: int) -> str:
        """Get step purpose description."""
        purposes = {
            0: "Configuration and credential management",
            1: "Repository cloning and code analysis",
            2: "Requirements gathering from Jira or manual input",
            3: "Semantic mapping of requirements to code",
            4: "Human review and change confirmation",
            5: "Automated code modification and testing",
            6: "Version control commit and PR creation"
        }
        return purposes.get(step_num, "Unknown step purpose")
    
    def _extract_docstring_purpose(self, file_path: Path) -> str:
        """Extract purpose from file docstring."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(r'"""([^"]*?)"""', content, re.DOTALL)
                if match:
                    return match.group(1).strip().split('\n')[0]
        except Exception:
            pass
        return "Core system component"
    
    def _analyze_data_flows(self) -> List[DataFlow]:
        """Analyze data flow between components."""
        flows = [
            # Configuration flow
            DataFlow('step_0', 'step_1', 'config.json', 'System configuration and credentials'),
            
            # Analysis flow
            DataFlow('step_1', 'step_3', 'analysis_report.json', 'Repository analysis and code index'),
            
            # Requirements flow
            DataFlow('step_2', 'step_3', 'requirement.json', 'Structured requirements'),
            DataFlow('jira', 'step_2', 'issue_data', 'Jira ticket information'),
            
            # Mapping and review flow
            DataFlow('step_3', 'step_4', 'change_proposal.json', 'Proposed code changes'),
            DataFlow('step_4', 'step_5', 'confirmed_proposal.json', 'Confirmed changes'),
            
            # Application flow
            DataFlow('step_5', 'step_6', 'apply_result.json', 'Applied changes and test results'),
            
            # Version control flow
            DataFlow('step_6', 'github', 'pull_request', 'GitHub pull request'),
            DataFlow('step_6', 'bitbucket', 'pull_request', 'Bitbucket pull request'),
            DataFlow('step_6', 'git', 'commits', 'Git commits and branch push'),
            
            # Discovery flows
            DataFlow('repo_discovery', 'github', 'api_calls', 'Repository listing requests'),
            DataFlow('repo_discovery', 'bitbucket', 'api_calls', 'Repository listing requests'),
            
            # UI orchestration
            DataFlow('app', 'orchestrator', 'commands', 'UI-driven step execution'),
            DataFlow('orchestrator', 'step_0', 'subprocess', 'Step execution'),
            DataFlow('orchestrator', 'step_1', 'subprocess', 'Step execution'),
            DataFlow('orchestrator', 'step_2', 'subprocess', 'Step execution'),
            DataFlow('orchestrator', 'step_3', 'subprocess', 'Step execution'),
            DataFlow('orchestrator', 'step_4', 'subprocess', 'Step execution'),
            DataFlow('orchestrator', 'step_5', 'subprocess', 'Step execution'),
            DataFlow('orchestrator', 'step_6', 'subprocess', 'Step execution'),
        ]
        return flows
    
    def generate_architecture_diagram(self) -> str:
        """Generate PlantUML architecture diagram."""
        plantuml = ["@startuml GitCodeSkill_Architecture"]
        plantuml.append("!theme plain")
        plantuml.append("skinparam backgroundColor #0E1117")
        plantuml.append("skinparam componentStyle rectangle")
        plantuml.append("")
        
        # Define component packages
        plantuml.append("package \"User Interfaces\" as UI {")
        plantuml.append("  [Streamlit Web UI] as WebUI #6C63FF")
        plantuml.append("  [CLI Orchestrator] as CLI #6C63FF")
        plantuml.append("}")
        plantuml.append("")
        
        plantuml.append("package \"Processing Pipeline\" as Pipeline {")
        plantuml.append("  [Step 0: Setup] as S0 #3fb950")
        plantuml.append("  [Step 1: Analysis] as S1 #3fb950") 
        plantuml.append("  [Step 2: Requirements] as S2 #3fb950")
        plantuml.append("  [Step 3: Mapping] as S3 #3fb950")
        plantuml.append("  [Step 4: Review] as S4 #3fb950")
        plantuml.append("  [Step 5: Apply] as S5 #3fb950")
        plantuml.append("  [Step 6: Commit] as S6 #3fb950")
        plantuml.append("}")
        plantuml.append("")
        
        plantuml.append("package \"External APIs\" as APIs {")
        plantuml.append("  [GitHub API] as GitHub #f85149")
        plantuml.append("  [Bitbucket API] as Bitbucket #f85149")
        plantuml.append("  [Jira API] as Jira #f85149")
        plantuml.append("  [Git CLI] as Git #f85149")
        plantuml.append("}")
        plantuml.append("")
        
        plantuml.append("package \"Data Storage\" as Data {")
        plantuml.append("  [config.json] as Config #21262d")
        plantuml.append("  [analysis_report.json] as Analysis #21262d")
        plantuml.append("  [requirement.json] as Requirement #21262d")
        plantuml.append("  [change_proposal.json] as Proposal #21262d")
        plantuml.append("  [apply_result.json] as ApplyResult #21262d")
        plantuml.append("  [commit_result.json] as CommitResult #21262d")
        plantuml.append("}")
        plantuml.append("")
        
        # Define relationships
        plantuml.append("' User Interface flows")
        plantuml.append("WebUI --> CLI : subprocess")
        plantuml.append("CLI --> S0 : execute")
        plantuml.append("CLI --> S1 : execute") 
        plantuml.append("CLI --> S2 : execute")
        plantuml.append("CLI --> S3 : execute")
        plantuml.append("CLI --> S4 : execute")
        plantuml.append("CLI --> S5 : execute")
        plantuml.append("CLI --> S6 : execute")
        plantuml.append("")
        
        plantuml.append("' Data flow pipeline")
        plantuml.append("S0 --> Config : creates")
        plantuml.append("S1 --> Analysis : creates")
        plantuml.append("S2 --> Requirement : creates")
        plantuml.append("S3 --> Proposal : creates")
        plantuml.append("S5 --> ApplyResult : creates")
        plantuml.append("S6 --> CommitResult : creates")
        plantuml.append("")
        
        plantuml.append("Config --> S1 : reads")
        plantuml.append("Analysis --> S3 : reads")
        plantuml.append("Requirement --> S3 : reads")
        plantuml.append("Proposal --> S4 : reads")
        plantuml.append("Proposal --> S5 : reads")
        plantuml.append("ApplyResult --> S6 : reads")
        plantuml.append("")
        
        plantuml.append("' External API integration")
        plantuml.append("S1 --> GitHub : repository discovery")
        plantuml.append("S1 --> Bitbucket : repository discovery")
        plantuml.append("S2 --> Jira : fetch requirements")
        plantuml.append("S5 --> Git : clone/branch/test")
        plantuml.append("S6 --> Git : commit/push")
        plantuml.append("S6 --> GitHub : create PR")
        plantuml.append("S6 --> Bitbucket : create PR")
        plantuml.append("")
        
        plantuml.append("@enduml")
        return '\n'.join(plantuml)
    
    def generate_dataflow_diagram(self) -> str:
        """Generate data flow diagram showing information movement."""
        plantuml = ["@startuml GitCodeSkill_DataFlow"]
        plantuml.append("!theme plain")
        plantuml.append("skinparam backgroundColor #0E1117")
        plantuml.append("")
        
        # Define actors and data stores
        plantuml.append("actor User as user")
        plantuml.append("actor \"Jira Admin\" as jira_admin")
        plantuml.append("database \"Local Workspace\" as workspace")
        plantuml.append("database \"Git Repository\" as git_repo")
        plantuml.append("cloud \"GitHub/Bitbucket\" as git_cloud")
        plantuml.append("cloud \"Jira Instance\" as jira_cloud")
        plantuml.append("")
        
        # Define processes (circles in DFD notation)
        for i in range(7):
            plantuml.append(f"circle \"Step {i}\" as step{i}")
        plantuml.append("")
        
        # User interactions
        plantuml.append("user --> step0 : credentials")
        plantuml.append("user --> step2 : manual requirements")
        plantuml.append("user --> step4 : change confirmation")
        plantuml.append("")
        
        # Configuration flow
        plantuml.append("step0 --> workspace : config.json")
        plantuml.append("workspace --> step1 : config.json")
        plantuml.append("")
        
        # Analysis flow 
        plantuml.append("step1 --> git_cloud : repository discovery")
        plantuml.append("git_cloud --> step1 : repository list")
        plantuml.append("step1 --> git_repo : clone/pull")
        plantuml.append("git_repo --> step1 : source code")
        plantuml.append("step1 --> workspace : analysis_report.json")
        plantuml.append("")
        
        # Requirements flow
        plantuml.append("jira_admin --> jira_cloud : create tickets")
        plantuml.append("step2 --> jira_cloud : fetch ticket")
        plantuml.append("jira_cloud --> step2 : ticket details")
        plantuml.append("step2 --> workspace : requirement.json")
        plantuml.append("")
        
        # Mapping and modification flow
        plantuml.append("workspace --> step3 : analysis + requirement")
        plantuml.append("step3 --> workspace : change_proposal.json")
        plantuml.append("workspace --> step4 : change_proposal.json")
        plantuml.append("step4 --> workspace : confirmed_proposal.json")
        plantuml.append("workspace --> step5 : confirmed_proposal.json")
        plantuml.append("step5 --> git_repo : code modifications")
        plantuml.append("step5 --> workspace : apply_result.json")
        plantuml.append("")
        
        # Version control flow
        plantuml.append("workspace --> step6 : apply_result.json")
        plantuml.append("step6 --> git_repo : commit")
        plantuml.append("step6 --> git_cloud : push + PR")
        plantuml.append("step6 --> workspace : commit_result.json")
        plantuml.append("")
        
        plantuml.append("@enduml")
        return '\n'.join(plantuml)
    
    def generate_sequence_diagram(self, start_step: int = 1, end_step: int = 6) -> str:
        """Generate sequence diagram for specified step range."""
        plantuml = [f"@startuml GitCodeSkill_Sequence_Steps_{start_step}_{end_step}"]
        plantuml.append("!theme plain")
        plantuml.append("skinparam backgroundColor #0E1117")
        plantuml.append("")
        
        # Define participants
        participants = ["User", "Orchestrator", "FileSystem"]
        
        # Add step participants
        for i in range(start_step, end_step + 1):
            participants.append(f"Step{i}")
        
        # Add external systems if relevant
        if start_step <= 1 <= end_step:
            participants.extend(["GitProvider", "RepoDiscovery"])
        if start_step <= 2 <= end_step:
            participants.append("JiraAPI")
        if start_step <= 6 <= end_step:
            participants.extend(["GitCLI", "GitProvider"])
        
        for participant in participants:
            plantuml.append(f"participant {participant}")
        plantuml.append("")
        
        # Generate sequence based on step range
        plantuml.append("User -> Orchestrator : start pipeline")
        plantuml.append("")
        
        for step in range(start_step, end_step + 1):
            plantuml.extend(self._generate_step_sequence(step))
            plantuml.append("")
        
        plantuml.append("Orchestrator -> User : pipeline complete")
        plantuml.append("")
        plantuml.append("@enduml")
        return '\n'.join(plantuml)
    
    def _generate_step_sequence(self, step_num: int) -> List[str]:
        """Generate sequence diagram commands for a specific step."""
        sequences = {
            1: [
                "Orchestrator -> Step1 : execute analysis",
                "Step1 -> FileSystem : read config.json",
                "Step1 -> GitProvider : discover repositories",
                "GitProvider -> Step1 : repository list",
                "Step1 -> GitProvider : clone repositories",
                "GitProvider -> Step1 : source code",
                "Step1 -> Step1 : analyze code structure",
                "Step1 -> FileSystem : write analysis_report.json",
                "Step1 -> Orchestrator : analysis complete"
            ],
            2: [
                "Orchestrator -> Step2 : fetch requirements",
                "Step2 -> FileSystem : read config.json",
                "alt Jira mode",
                "  Step2 -> JiraAPI : authenticate",
                "  Step2 -> JiraAPI : fetch ticket details",
                "  JiraAPI -> Step2 : ticket data",
                "else Manual mode",
                "  Step2 -> User : prompt for requirements",
                "  User -> Step2 : requirement details",
                "end",
                "Step2 -> FileSystem : write requirement.json",
                "Step2 -> Orchestrator : requirements ready"
            ],
            3: [
                "Orchestrator -> Step3 : map changes",
                "Step3 -> FileSystem : read analysis_report.json",
                "Step3 -> FileSystem : read requirement.json",
                "Step3 -> Step3 : extract keywords",
                "Step3 -> Step3 : score code elements",
                "Step3 -> Step3 : rank file relevance",
                "Step3 -> FileSystem : write change_proposal.json",
                "Step3 -> Orchestrator : mapping complete"
            ],
            4: [
                "Orchestrator -> Step4 : review changes",
                "Step4 -> FileSystem : read change_proposal.json",
                "Step4 -> User : display proposed changes",
                "User -> Step4 : confirm/modify changes",
                "Step4 -> FileSystem : update change_proposal.json",
                "Step4 -> Orchestrator : review complete"
            ],
            5: [
                "Orchestrator -> Step5 : apply changes",
                "Step5 -> FileSystem : read change_proposal.json",
                "Step5 -> GitCLI : create feature branch",
                "Step5 -> FileSystem : apply code modifications",
                "Step5 -> GitCLI : run formatters",
                "Step5 -> GitCLI : run tests",
                "Step5 -> FileSystem : write apply_result.json",
                "Step5 -> Orchestrator : changes applied"
            ],
            6: [
                "Orchestrator -> Step6 : commit and push",
                "Step6 -> FileSystem : read apply_result.json",
                "Step6 -> GitCLI : git add .",
                "Step6 -> GitCLI : git commit",
                "Step6 -> GitCLI : git push",
                "Step6 -> GitProvider : create pull request",
                "GitProvider -> Step6 : PR URL",
                "Step6 -> FileSystem : write commit_result.json",
                "Step6 -> Orchestrator : deployment complete"
            ]
        }
        return sequences.get(step_num, [f"Orchestrator -> Step{step_num} : execute step"])
    
    def generate_class_diagram(self, component: str) -> str:
        """Generate class diagram for a specific component."""
        plantuml = [f"@startuml GitCodeSkill_{component}_Classes"]
        plantuml.append("!theme plain")
        plantuml.append("skinparam backgroundColor #0E1117")
        plantuml.append("")
        
        if component == "orchestrator":
            plantuml.extend([
                "class Orchestrator {",
                "  -config: Dict",
                "  -steps: Dict[int, Tuple[str, str]]",
                "  +__init__()",
                "  +run_step(step_num: int, args: List): Tuple",
                "  +run_full_pipeline(args: Namespace): bool",
                "  +validate_prerequisites(step: int): bool",
                "  +handle_step_failure(step: int, error: str): None",
                "}",
                "",
                "class StepRunner {",
                "  +execute_subprocess(cmd: List[str]): subprocess.CompletedProcess",
                "  +capture_output(result: CompletedProcess): str",
                "  +handle_timeout(step: int): None",
                "}",
                "",
                "class ConfigManager {",
                "  +load_config(): Dict",
                "  +validate_config(config: Dict): List[str]",
                "  +check_file_exists(path: str): bool",
                "}",
                "",
                "Orchestrator --> StepRunner : uses",
                "Orchestrator --> ConfigManager : uses",
                "StepRunner --> ConfigManager : validates"
            ])
        
        elif component.startswith("step"):
            step_num = int(component.split("_")[1]) if "_" in component else 1
            step_classes = self._generate_step_class_diagram(step_num)
            plantuml.extend(step_classes)
        
        elif component == "app":
            plantuml.extend([
                "class StreamlitApp {",
                "  -config: Dict",
                "  -step_status: Dict[int, str]",
                "  +__init__()",
                "  +render_sidebar(): None",
                "  +render_step(step_num: int): None",
                "  +update_progress(step: int, status: str): None",
                "}",
                "",
                "class StepRenderer {",
                "  +render_setup_step(): None",
                "  +render_analysis_step(): None",
                "  +render_requirements_step(): None",
                "  +render_mapping_step(): None",
                "  +render_review_step(): None",
                "  +render_apply_step(): None",
                "  +render_commit_step(): None",
                "}",
                "",
                "class UIComponents {",
                "  +create_metric_card(title: str, value: str): None",
                "  +create_progress_bar(progress: float): None",
                "  +create_file_selector(files: List): str",
                "  +display_json_result(data: Dict): None",
                "}",
                "",
                "StreamlitApp --> StepRenderer : uses",
                "StepRenderer --> UIComponents : uses"
            ])
        
        elif component == "repo_discovery":
            plantuml.extend([
                "abstract class GitProvider {",
                "  #base_url: str",
                "  #credentials: Dict",
                "  +{abstract} authenticate(): bool",
                "  +{abstract} list_repositories(): List[Dict]",
                "  +{abstract} get_repository_details(repo: str): Dict",
                "}",
                "",
                "class GitHubProvider {",
                "  -token: str",
                "  +authenticate(): bool",
                "  +list_repositories(): List[Dict]",
                "  +list_org_repos(org: str): List[Dict]",
                "  +list_user_repos(user: str): List[Dict]",
                "}",
                "",
                "class BitbucketServerProvider {",
                "  -username: str",
                "  -app_password: str",
                "  +authenticate(): bool", 
                "  +list_repositories(): List[Dict]",
                "  +list_project_repos(project: str): List[Dict]",
                "}",
                "",
                "class BitbucketCloudProvider {",
                "  -username: str",
                "  -app_password: str",
                "  +authenticate(): bool",
                "  +list_repositories(): List[Dict]",
                "  +list_workspace_repos(workspace: str): List[Dict]",
                "}",
                "",
                "class RepositoryDiscovery {",
                "  -providers: List[GitProvider]",
                "  +discover_repositories(config: Dict): List[Dict]",
                "  +filter_repositories(repos: List, criteria: Dict): List[Dict]",
                "}",
                "",
                "GitProvider <|-- GitHubProvider",
                "GitProvider <|-- BitbucketServerProvider", 
                "GitProvider <|-- BitbucketCloudProvider",
                "RepositoryDiscovery --> GitProvider : uses"
            ])
        
        plantuml.append("")
        plantuml.append("@enduml")
        return '\n'.join(plantuml)
    
    def _generate_step_class_diagram(self, step_num: int) -> List[str]:
        """Generate class diagram content for a specific step."""
        step_classes = {
            1: [
                "class RepositoryAnalyzer {",
                "  -repo_path: Path",
                "  -gitignore_spec: PathSpec",
                "  +analyze(repo_path: str): Dict",
                "  +detect_languages(): Dict[str, int]",
                "  +detect_frameworks(): List[str]",
                "  +build_code_index(): Dict",
                "  +extract_configs(): List[Dict]",
                "}",
                "",
                "class CodeIndexer {",
                "  +index_classes(content: str): List[str]",
                "  +index_functions(content: str): List[str]", 
                "  +index_api_endpoints(content: str): List[str]",
                "  +index_database_entities(content: str): List[str]",
                "}",
                "",
                "class MultiRepoScanner {",
                "  -discovery: RepositoryDiscovery",
                "  +scan_repositories(config: Dict): Dict",
                "  +aggregate_results(results: List[Dict]): Dict",
                "  +cleanup_workspace(path: str): None",
                "}",
                "",
                "RepositoryAnalyzer --> CodeIndexer : uses",
                "MultiRepoScanner --> RepositoryAnalyzer : uses"
            ],
            2: [
                "class RequirementsFetcher {",
                "  -config: Dict",
                "  +fetch_from_jira(ticket_id: str): Dict",
                "  +collect_manual_input(): Dict",
                "  +normalize_requirement(data: Dict): Dict",
                "}",
                "",
                "class JiraClient {",
                "  -base_url: str",
                "  -credentials: Tuple[str, str]",
                "  +authenticate(): bool",
                "  +get_issue(ticket_id: str): Dict",
                "  +convert_adf_to_text(adf: Dict): str",
                "  +extract_acceptance_criteria(issue: Dict): List[str]",
                "}",
                "",
                "class ManualInputCollector {",
                "  +prompt_for_summary(): str",
                "  +prompt_for_description(): str",
                "  +prompt_for_type(): str",
                "  +validate_input(data: Dict): bool",
                "}",
                "",
                "RequirementsFetcher --> JiraClient : uses",
                "RequirementsFetcher --> ManualInputCollector : uses"
            ],
            3: [
                "class RequirementMapper {",
                "  -analysis_data: Dict",
                "  -requirement_data: Dict",
                "  +map_requirements_to_code(): Dict",
                "  +extract_keywords(): List[str]",
                "  +score_code_elements(): Dict[str, float]",
                "  +rank_files_by_relevance(): List[Tuple[str, float]]",
                "}",
                "",
                "class KeywordExtractor {",
                "  +extract_from_summary(text: str): List[str]",
                "  +extract_from_description(text: str): List[str]",
                "  +split_camel_case(text: str): List[str]",
                "  +remove_stop_words(words: List[str]): List[str]",
                "}",
                "",
                "class RelevanceScorer {",
                "  +score_exact_match(keyword: str, element: str): float",
                "  +score_substring_match(keyword: str, element: str): float",
                "  +score_frequency_match(keyword: str, content: str): float",
                "  +aggregate_scores(scores: List[float]): float",
                "}",
                "",
                "RequirementMapper --> KeywordExtractor : uses",
                "RequirementMapper --> RelevanceScorer : uses"
            ],
            5: [
                "class ChangeApplier {",
                "  -repo_path: str",
                "  -proposal: Dict",
                "  +apply_changes(): Dict",
                "  +create_feature_branch(): str",
                "  +apply_file_changes(): List[Dict]",
                "  +run_formatters(): bool",
                "  +run_tests(): Dict",
                "}",
                "",
                "class FileModifier {",
                "  +replace_text(content: str, old: str, new: str): str",
                "  +insert_after_line(content: str, after: str, text: str): str",
                "  +insert_before_line(content: str, before: str, text: str): str",
                "  +append_to_file(content: str, text: str): str",
                "}",
                "",
                "class ToolManager {",
                "  +find_formatter(language: str): Optional[str]",
                "  +run_formatter(tool: str, files: List[str]): bool",
                "  +find_test_runner(): Optional[str]",
                "  +run_tests(): Dict",
                "}",
                "",
                "ChangeApplier --> FileModifier : uses",
                "ChangeApplier --> ToolManager : uses"
            ]
        }
        return step_classes.get(step_num, [f"' Step {step_num} class diagram not implemented"])
    
    def generate_multi_repo_workflow(self) -> str:
        """Generate diagram showing multi-repository workflow."""
        plantuml = ["@startuml GitCodeSkill_MultiRepo_Workflow"]
        plantuml.append("!theme plain")
        plantuml.append("skinparam backgroundColor #0E1117")
        plantuml.append("")
        
        plantuml.extend([
            "start",
            "",
            ":Read configuration;",
            ":Determine scan scope;",
            "",
            "if (GitHub owner specified?) then (yes)",
            "  :Discover GitHub repositories;",
            "  :GET /orgs/{owner}/repos;",
            "elseif (Bitbucket projects specified?) then (yes)",
            "  :Discover Bitbucket repositories;",
            "  :GET /projects/{key}/repos;",
            "else (no)",
            "  :Use single repository from config;",
            "endif",
            "",
            ":Initialize progress tracking;",
            "",
            "while (More repositories to process?) is (yes)",
            "  :Clone repository to workspace;",
            "  :Analyze repository structure;",
            "  :Build code index;",
            "  :Extract configurations;", 
            "  :Calculate metrics;",
            "  if (Keep clones?) then (no)",
            "    :Delete repository clone;",
            "  endif",
            "  :Update progress;",
            "endwhile (no)",
            "",
            ":Aggregate all results;",
            ":Calculate totals and averages;",
            ":Write multi_analysis_report.json;",
            "",
            "stop"
        ])
        
        plantuml.append("@enduml")
        return '\n'.join(plantuml)
    
    def generate_component_interaction(self) -> str:
        """Generate component interaction diagram."""
        plantuml = ["@startuml GitCodeSkill_Component_Interactions"]
        plantuml.append("!theme plain")
        plantuml.append("skinparam backgroundColor #0E1117")
        plantuml.append("")
        
        plantuml.extend([
            "package \"User Layer\" {",
            "  [Web Browser] as browser",
            "  [Terminal/CLI] as terminal",
            "}",
            "",
            "package \"Application Layer\" {",
            "  [Streamlit UI] as ui",
            "  [Orchestrator] as orch",
            "}",
            "",
            "package \"Processing Layer\" {",
            "  [Step Scripts] as steps",
            "  [Repository Discovery] as discovery",
            "}",
            "",
            "package \"Integration Layer\" {",
            "  [GitHub Client] as github",
            "  [Bitbucket Client] as bitbucket",
            "  [Jira Client] as jira",
            "  [Git CLI Wrapper] as gitcli",
            "}",
            "",
            "package \"Storage Layer\" {",
            "  [Configuration Files] as config",
            "  [JSON Data Files] as data",
            "  [Local Git Repositories] as repos",
            "}",
            "",
            "package \"External Systems\" {",
            "  [GitHub API] as github_api",
            "  [Bitbucket API] as bb_api", 
            "  [Jira API] as jira_api",
            "  [Git Repositories] as git_repos",
            "}",
            "",
            "' User interactions",
            "browser --> ui : HTTP requests",
            "terminal --> orch : CLI commands",
            "",
            "' Application layer",
            "ui --> orch : subprocess calls",
            "orch --> steps : execute scripts",
            "",
            "' Processing layer", 
            "steps --> discovery : multi-repo mode",
            "steps --> config : read/write",
            "steps --> data : read/write",
            "",
            "' Integration layer",
            "discovery --> github : repository discovery",
            "discovery --> bitbucket : repository discovery",
            "steps --> jira : requirements fetching",
            "steps --> gitcli : version control ops",
            "",
            "' External API calls",
            "github --> github_api : REST API",
            "bitbucket --> bb_api : REST API",
            "jira --> jira_api : REST API",
            "gitcli --> git_repos : Git protocol",
            "",
            "' Local storage",
            "gitcli --> repos : clone/checkout",
            "steps --> repos : code analysis"
        ])
        
        plantuml.append("")
        plantuml.append("@enduml")
        return '\n'.join(plantuml)
    
    def generate_mermaid_architecture(self) -> str:
        """Generate Mermaid.js architecture diagram as alternative to PlantUML."""
        mermaid = ["graph TB"]
        mermaid.extend([
            "    subgraph UI[\"User Interfaces\"]",
            "        WEB[Streamlit Web UI]",
            "        CLI[CLI Orchestrator]",
            "    end",
            "",
            "    subgraph PIPELINE[\"7-Step Pipeline\"]",
            "        S0[Step 0: Setup]",
            "        S1[Step 1: Analysis]",
            "        S2[Step 2: Requirements]",
            "        S3[Step 3: Mapping]",
            "        S4[Step 4: Review]",
            "        S5[Step 5: Apply]",
            "        S6[Step 6: Commit]",
            "    end",
            "",
            "    subgraph DATA[\"Data Layer\"]",
            "        CONFIG[config.json]",
            "        ANALYSIS[analysis_report.json]",
            "        REQ[requirement.json]",
            "        PROPOSAL[change_proposal.json]",
            "        RESULT[apply_result.json]",
            "        COMMIT[commit_result.json]",
            "    end",
            "",
            "    subgraph EXTERNAL[\"External APIs\"]",
            "        GITHUB[GitHub API]",
            "        BITBUCKET[Bitbucket API]",
            "        JIRA[Jira API]",
            "        GIT[Git CLI]",
            "    end",
            "",
            "    %% User flows",
            "    WEB --> CLI",
            "    CLI --> S0",
            "",
            "    %% Pipeline sequence",
            "    S0 --> S1",
            "    S1 --> S2", 
            "    S2 --> S3",
            "    S3 --> S4",
            "    S4 --> S5",
            "    S5 --> S6",
            "",
            "    %% Data flows",
            "    S0 --> CONFIG",
            "    CONFIG --> S1",
            "    S1 --> ANALYSIS",
            "    S2 --> REQ",
            "    ANALYSIS --> S3",
            "    REQ --> S3",
            "    S3 --> PROPOSAL",
            "    PROPOSAL --> S4",
            "    PROPOSAL --> S5",
            "    S5 --> RESULT",
            "    RESULT --> S6",
            "    S6 --> COMMIT",
            "",
            "    %% External integrations", 
            "    S1 -.-> GITHUB",
            "    S1 -.-> BITBUCKET",
            "    S2 -.-> JIRA",
            "    S5 -.-> GIT",
            "    S6 -.-> GIT",
            "    S6 -.-> GITHUB",
            "    S6 -.-> BITBUCKET",
            "",
            "    %% Styling",
            "    classDef uiClass fill:#6C63FF,stroke:#fff,stroke-width:2px,color:#fff",
            "    classDef stepClass fill:#3fb950,stroke:#fff,stroke-width:2px,color:#fff",
            "    classDef dataClass fill:#21262d,stroke:#fff,stroke-width:1px,color:#fff", 
            "    classDef externalClass fill:#f85149,stroke:#fff,stroke-width:2px,color:#fff",
            "",
            "    class WEB,CLI uiClass",
            "    class S0,S1,S2,S3,S4,S5,S6 stepClass",
            "    class CONFIG,ANALYSIS,REQ,PROPOSAL,RESULT,COMMIT dataClass",
            "    class GITHUB,BITBUCKET,JIRA,GIT externalClass"
        ])
        return '\n'.join(mermaid)


def main():
    """Main function for testing the UML generator."""
    import sys
    import io
    
    # Set UTF-8 encoding for output
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    else:
        # For older Python versions, wrap stdout
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    if len(sys.argv) < 2:
        print("Usage: python uml_generator_skill.py <repo_path> [command]")
        print("Commands: architecture, dataflow, sequence, class <component>, multi-repo, mermaid")
        return
    
    repo_path = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else 'architecture'
    
    uml_gen = GitCodeSkillUMLGenerator(repo_path)
    
    if command == 'architecture':
        result = uml_gen.generate_architecture_diagram()
    elif command == 'dataflow':
        result = uml_gen.generate_dataflow_diagram()
    elif command == 'sequence':
        start = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        end = int(sys.argv[4]) if len(sys.argv) > 4 else 6
        result = uml_gen.generate_sequence_diagram(start, end)
    elif command == 'class':
        component = sys.argv[3] if len(sys.argv) > 3 else 'orchestrator'
        result = uml_gen.generate_class_diagram(component)
    elif command == 'multi-repo':
        result = uml_gen.generate_multi_repo_workflow()
    elif command == 'mermaid':
        result = uml_gen.generate_mermaid_architecture()
    elif command == 'components':
        result = uml_gen.generate_component_interaction()
    else:
        result = "Unknown command. Available: architecture, dataflow, sequence, class, multi-repo, mermaid, components"
    
    print(result)


if __name__ == "__main__":
    main()