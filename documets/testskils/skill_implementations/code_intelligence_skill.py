#!/usr/bin/env python3
"""
Code Intelligence & Query Skill for GitCodeSkill Repository
Advanced code understanding, querying, and analysis capabilities with natural language interface.
"""

import ast
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from dataclasses import dataclass
from collections import defaultdict, Counter
import importlib.util


@dataclass
class CodeElement:
    """Represents a code element (class, function, variable, etc.)."""
    name: str
    type: str  # 'class', 'function', 'method', 'variable', 'import'
    file_path: str
    line_number: int
    signature: str
    docstring: Optional[str]
    complexity_score: int
    dependencies: List[str]
    usage_count: int


@dataclass
class RelationshipEdge:
    """Represents a relationship between code elements."""
    source: str
    target: str
    relationship_type: str  # 'calls', 'inherits', 'imports', 'instantiates', 'uses'
    strength: float  # 0.0 to 1.0


@dataclass
class QueryResult:
    """Result of a code intelligence query."""
    query: str
    answer: str
    confidence: float
    supporting_evidence: List[str]
    related_elements: List[CodeElement]
    suggestions: List[str]


class GitCodeSkillIntelligence:
    """Advanced code intelligence system for GitCodeSkill repository."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.code_graph = {}  # element_id -> CodeElement
        self.relationships = []  # List of RelationshipEdge
        self.file_contents = {}  # file_path -> content
        self.analysis_cache = {}
        
        # Build comprehensive code graph
        self._build_code_graph()
        self._analyze_relationships()
    
    def _build_code_graph(self):
        """Build comprehensive graph of all code elements."""
        print("Building code intelligence graph...")
        
        for py_file in self.repo_path.rglob('*.py'):
            try:
                content = py_file.read_text(encoding='utf-8')
                self.file_contents[str(py_file)] = content
                
                # Parse AST for detailed analysis
                try:
                    tree = ast.parse(content)
                    self._extract_elements_from_ast(tree, py_file, content)
                except SyntaxError as e:
                    print(f"Syntax error in {py_file}: {e}")
                    
            except Exception as e:
                print(f"Error processing {py_file}: {e}")
    
    def _extract_elements_from_ast(self, tree: ast.AST, file_path: Path, content: str):
        """Extract code elements from AST."""
        lines = content.split('\n')
        
        class CodeElementExtractor(ast.NodeVisitor):
            def __init__(self, intelligence_system):
                self.intelligence = intelligence_system
                self.current_class = None
                self.scope_stack = []
            
            def visit_ClassDef(self, node):
                class_id = f"{file_path.relative_to(self.intelligence.repo_path)}::{node.name}"
                
                # Extract base classes
                bases = [self._get_node_name(base) for base in node.bases]
                
                # Calculate complexity (simplified)
                complexity = len([n for n in ast.walk(node) if isinstance(n, (ast.FunctionDef, ast.If, ast.For, ast.While))])
                
                element = CodeElement(
                    name=node.name,
                    type='class',
                    file_path=str(file_path.relative_to(self.intelligence.repo_path)),
                    line_number=node.lineno,
                    signature=f"class {node.name}({', '.join(bases)})" if bases else f"class {node.name}",
                    docstring=ast.get_docstring(node),
                    complexity_score=complexity,
                    dependencies=bases,
                    usage_count=0  # Will be calculated later
                )
                
                self.intelligence.code_graph[class_id] = element
                
                # Visit class methods
                old_class = self.current_class
                self.current_class = node.name
                self.scope_stack.append(node.name)
                self.generic_visit(node)
                self.scope_stack.pop()
                self.current_class = old_class
            
            def visit_FunctionDef(self, node):
                func_type = 'method' if self.current_class else 'function'
                full_name = f"{self.current_class}.{node.name}" if self.current_class else node.name
                func_id = f"{file_path.relative_to(self.intelligence.repo_path)}::{full_name}"
                
                # Extract function signature
                args = []
                for arg in node.args.args:
                    args.append(arg.arg)
                if node.args.vararg:
                    args.append(f"*{node.args.vararg.arg}")
                if node.args.kwarg:
                    args.append(f"**{node.args.kwarg.arg}")
                
                signature = f"def {node.name}({', '.join(args)})"
                
                # Calculate cyclomatic complexity
                complexity = 1  # Base complexity
                complexity += len([n for n in ast.walk(node) if isinstance(n, (ast.If, ast.For, ast.While, ast.ExceptHandler))])
                
                # Extract function calls (dependencies)
                dependencies = self._extract_function_calls(node)
                
                element = CodeElement(
                    name=full_name,
                    type=func_type,
                    file_path=str(file_path.relative_to(self.intelligence.repo_path)),
                    line_number=node.lineno,
                    signature=signature,
                    docstring=ast.get_docstring(node),
                    complexity_score=complexity,
                    dependencies=dependencies,
                    usage_count=0
                )
                
                self.intelligence.code_graph[func_id] = element
                
                self.scope_stack.append(node.name)
                self.generic_visit(node)
                self.scope_stack.pop()
            
            def visit_Import(self, node):
                for alias in node.names:
                    import_id = f"{file_path.relative_to(self.intelligence.repo_path)}::import_{alias.name}"
                    element = CodeElement(
                        name=alias.name,
                        type='import',
                        file_path=str(file_path.relative_to(self.intelligence.repo_path)),
                        line_number=node.lineno,
                        signature=f"import {alias.name}",
                        docstring=None,
                        complexity_score=0,
                        dependencies=[],
                        usage_count=0
                    )
                    self.intelligence.code_graph[import_id] = element
                
                self.generic_visit(node)
            
            def visit_ImportFrom(self, node):
                if node.module:
                    for alias in node.names:
                        import_name = f"{node.module}.{alias.name}" if alias.name != '*' else node.module
                        import_id = f"{file_path.relative_to(self.intelligence.repo_path)}::import_{import_name}"
                        element = CodeElement(
                            name=import_name,
                            type='import',
                            file_path=str(file_path.relative_to(self.intelligence.repo_path)),
                            line_number=node.lineno,
                            signature=f"from {node.module} import {alias.name}",
                            docstring=None,
                            complexity_score=0,
                            dependencies=[],
                            usage_count=0
                        )
                        self.intelligence.code_graph[import_id] = element
                
                self.generic_visit(node)
            
            def _extract_function_calls(self, node):
                """Extract function calls from a node."""
                calls = []
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        call_name = self._get_node_name(child.func)
                        if call_name:
                            calls.append(call_name)
                return list(set(calls))
            
            def _get_node_name(self, node):
                """Get the name of an AST node."""
                if isinstance(node, ast.Name):
                    return node.id
                elif isinstance(node, ast.Attribute):
                    value_name = self._get_node_name(node.value)
                    return f"{value_name}.{node.attr}" if value_name else node.attr
                elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                    return node.value
                return None
        
        extractor = CodeElementExtractor(self)
        extractor.visit(tree)
    
    def _analyze_relationships(self):
        """Analyze relationships between code elements."""
        print("Analyzing code relationships...")
        
        # Build relationships based on dependencies
        for element_id, element in self.code_graph.items():
            for dep in element.dependencies:
                # Find matching elements
                matching_elements = self._find_elements_by_name(dep)
                for match_id in matching_elements:
                    if match_id != element_id:
                        relationship_type = self._determine_relationship_type(element, self.code_graph[match_id])
                        self.relationships.append(RelationshipEdge(
                            source=element_id,
                            target=match_id,
                            relationship_type=relationship_type,
                            strength=0.8
                        ))
        
        # Calculate usage counts
        self._calculate_usage_counts()
    
    def _find_elements_by_name(self, name: str) -> List[str]:
        """Find elements matching a given name."""
        matches = []
        for element_id, element in self.code_graph.items():
            if element.name == name or element.name.endswith(f".{name}"):
                matches.append(element_id)
        return matches
    
    def _determine_relationship_type(self, source: CodeElement, target: CodeElement) -> str:
        """Determine the type of relationship between two elements."""
        if source.type == 'class' and target.type == 'class':
            return 'inherits'
        elif source.type in ['function', 'method'] and target.type in ['function', 'method']:
            return 'calls'
        elif source.type == 'import':
            return 'imports'
        else:
            return 'uses'
    
    def _calculate_usage_counts(self):
        """Calculate how often each element is used."""
        usage_counts = defaultdict(int)
        
        for relationship in self.relationships:
            usage_counts[relationship.target] += 1
        
        # Update usage counts in code graph
        for element_id, count in usage_counts.items():
            if element_id in self.code_graph:
                self.code_graph[element_id].usage_count = count
    
    def query_natural_language(self, query: str) -> QueryResult:
        """Process natural language queries about the codebase."""
        query_lower = query.lower().strip()
        
        # Pattern matching for common query types
        if any(phrase in query_lower for phrase in ['what does', 'how does', 'explain']):
            return self._handle_explanation_query(query)
        elif any(phrase in query_lower for phrase in ['find', 'where is', 'show me']):
            return self._handle_search_query(query)
        elif any(phrase in query_lower for phrase in ['list', 'show all', 'get all']):
            return self._handle_listing_query(query)
        elif any(phrase in query_lower for phrase in ['relationship', 'depends', 'calls', 'uses']):
            return self._handle_relationship_query(query)
        elif any(phrase in query_lower for phrase in ['complexity', 'metrics', 'analysis']):
            return self._handle_metrics_query(query)
        else:
            return self._handle_general_query(query)
    
    def _handle_explanation_query(self, query: str) -> QueryResult:
        """Handle 'what does X do' or 'how does X work' queries."""
        # Extract the component being asked about
        query_words = query.lower().split()
        
        # Look for step references
        if 'step' in query:
            step_match = re.search(r'step\s*(\d+)', query.lower())
            if step_match:
                step_num = int(step_match.group(1))
                return self._explain_step(step_num, query)
        
        # Look for specific components
        components = ['orchestrator', 'app', 'repo_discovery', 'streamlit']
        for component in components:
            if component in query.lower():
                return self._explain_component(component, query)
        
        # Look for general workflow explanations
        if any(word in query.lower() for word in ['workflow', 'pipeline', 'process', 'system']):
            return self._explain_system_workflow(query)
        
        return QueryResult(
            query=query,
            answer="I can explain various components of GitCodeSkill. Try asking about specific steps (e.g., 'explain step 1'), components (orchestrator, app), or the overall workflow.",
            confidence=0.6,
            supporting_evidence=[],
            related_elements=[],
            suggestions=[
                "explain step 1 analysis process",
                "how does orchestrator.py work",
                "explain the overall workflow",
                "what does the mapping step do"
            ]
        )
    
    def _explain_step(self, step_num: int, query: str) -> QueryResult:
        """Explain a specific pipeline step."""
        step_descriptions = {
            0: "Step 0 (Setup) handles configuration and credential management. It creates the config.json file with Git provider settings, repository URLs, authentication tokens, and workspace paths. This step ensures secure credential storage with platform-appropriate file permissions.",
            
            1: "Step 1 (Analysis) performs comprehensive repository analysis. It clones repositories, detects programming languages and frameworks, builds a code index of classes/functions/APIs, extracts configuration files, and supports multi-repository scanning. The output is analysis_report.json containing the complete codebase structure.",
            
            2: "Step 2 (Requirements) gathers requirements either from Jira tickets or manual input. For Jira mode, it authenticates with the API, fetches ticket details, converts ADF format to text, and extracts acceptance criteria. Manual mode allows direct requirement input. Output is requirement.json.",
            
            3: "Step 3 (Mapping) uses semantic analysis to map requirements to relevant code. It extracts keywords from requirements, scores code elements for relevance using exact/substring/frequency matching, and identifies the top 30 most relevant files with specific line ranges. Output is change_proposal.json.",
            
            4: "Step 4 (Review) enables human review and change specification. Users can confirm files, cherry-pick specific items, and add detailed change instructions (replace, insert_after, insert_before, append, full_replace). Updates change_proposal.json with confirmation flags.",
            
            5: "Step 5 (Apply) implements the confirmed changes automatically. It creates a feature branch, applies all specified modifications, runs code formatters (black, prettier, etc.), executes tests, and generates git diffs. Output is apply_result.json with change summaries.",
            
            6: "Step 6 (Commit) handles version control operations. It commits changes with conventional commit messages, pushes the feature branch, and creates pull requests on GitHub or Bitbucket. Includes provider-specific PR creation logic. Output is commit_result.json."
        }
        
        if step_num in step_descriptions:
            # Find related code elements
            step_file_pattern = f"step_{step_num}"
            related_elements = [
                element for element in self.code_graph.values()
                if step_file_pattern in element.file_path
            ]
            
            evidence = [
                f"Located in step_{step_num}_*.py",
                f"Found {len(related_elements)} related functions/classes",
                "Part of the 7-step automated development pipeline"
            ]
            
            if step_num == 1:
                evidence.extend([
                    "Supports GitHub and Bitbucket repository discovery",
                    "Uses pathspec for .gitignore-aware file walking",
                    "Detects 15+ programming languages and frameworks"
                ])
            elif step_num == 3:
                evidence.extend([
                    "Implements keyword extraction and relevance scoring",
                    "Uses camelCase/snake_case splitting for better matching",
                    "Scores files with exact match (+10), substring (+5), frequency (+0.5) points"
                ])
            
            return QueryResult(
                query=query,
                answer=step_descriptions[step_num],
                confidence=0.9,
                supporting_evidence=evidence,
                related_elements=related_elements[:5],  # Top 5 related elements
                suggestions=[
                    f"show me step {step_num} implementation details",
                    f"what files does step {step_num} create",
                    f"how does step {step_num} integrate with other steps"
                ]
            )
        
        return QueryResult(
            query=query,
            answer=f"Step {step_num} is not part of the GitCodeSkill pipeline. The system has steps 0-6.",
            confidence=0.8,
            supporting_evidence=[],
            related_elements=[],
            suggestions=["explain step 1", "explain step 3 mapping", "list all pipeline steps"]
        )
    
    def _explain_component(self, component: str, query: str) -> QueryResult:
        """Explain a specific system component."""
        component_explanations = {
            'orchestrator': "The orchestrator.py is the central coordination system that chains all 7 steps together. It supports both full pipeline execution (--full) and individual step execution (--step N). It handles subprocess execution, timeout management, prerequisite validation, and error recovery. The orchestrator enables both CLI and UI-driven workflows.",
            
            'app': "The app.py provides a comprehensive Streamlit web interface with a dark GitHub-inspired theme. It features sidebar navigation, step-by-step progress tracking, interactive forms for configuration, real-time terminal output display, and provider-specific UI elements. Supports both single and multi-repository workflows.",
            
            'repo_discovery': "The repo_discovery.py handles multi-repository discovery across GitHub and Bitbucket. It uses REST APIs to list repositories under organizations or project keys, handles pagination, supports both cloud and server deployments, and enables enterprise-scale repository scanning.",
            
            'streamlit': "The Streamlit UI (app.py) provides a user-friendly web interface for the entire pipeline. Features include dark theme styling, progress visualization, interactive configuration forms, real-time output streaming, and provider-specific workflows for GitHub and Bitbucket integration."
        }
        
        if component in component_explanations:
            # Find related elements
            related_elements = [
                element for element in self.code_graph.values()
                if component in element.file_path.lower()
            ]
            
            evidence = [
                f"Implemented in {component}.py",
                f"Contains {len(related_elements)} functions and classes",
                "Core component of GitCodeSkill architecture"
            ]
            
            if component == 'orchestrator':
                evidence.extend([
                    "Supports timeout management for subprocess execution",
                    "Enables both --full and --step N execution modes",
                    "Integrates with Streamlit UI via subprocess calls"
                ])
            elif component == 'app':
                evidence.extend([
                    "Built with Streamlit framework",
                    "Features GitHub-inspired dark theme",
                    "Supports multi-repository scanning UI"
                ])
            
            return QueryResult(
                query=query,
                answer=component_explanations[component],
                confidence=0.9,
                supporting_evidence=evidence,
                related_elements=related_elements[:5],
                suggestions=[
                    f"show me {component} functions",
                    f"how does {component} integrate with other components",
                    f"what APIs does {component} use"
                ]
            )
        
        return QueryResult(
            query=query,
            answer=f"Component '{component}' not found. Available components: orchestrator, app, repo_discovery, and the 7 step scripts.",
            confidence=0.8,
            supporting_evidence=[],
            related_elements=[],
            suggestions=["explain orchestrator", "explain app.py", "explain repo_discovery"]
        )
    
    def _handle_search_query(self, query: str) -> QueryResult:
        """Handle search and 'where is' queries."""
        query_lower = query.lower()
        
        # Extract search terms
        search_terms = []
        if 'find' in query_lower:
            search_terms = query_lower.split('find')[1].strip().split()
        elif 'where is' in query_lower:
            search_terms = query_lower.split('where is')[1].strip().split()
        elif 'show me' in query_lower:
            search_terms = query_lower.split('show me')[1].strip().split()
        
        if not search_terms:
            return QueryResult(
                query=query,
                answer="Please specify what you're looking for. Example: 'find error handling' or 'where is the authentication code'",
                confidence=0.3,
                supporting_evidence=[],
                related_elements=[],
                suggestions=["find authentication", "where is error handling", "find subprocess calls"]
            )
        
        # Search for matching elements
        matching_elements = []
        for element_id, element in self.code_graph.items():
            element_text = f"{element.name} {element.signature} {element.docstring or ''} {element.file_path}".lower()
            
            score = 0
            for term in search_terms:
                if term in element_text:
                    score += element_text.count(term)
                    if term in element.name.lower():
                        score += 5  # Boost for name matches
            
            if score > 0:
                matching_elements.append((element, score))
        
        # Sort by relevance
        matching_elements.sort(key=lambda x: x[1], reverse=True)
        top_matches = matching_elements[:10]
        
        if top_matches:
            answer_parts = [f"Found {len(top_matches)} matching elements:"]
            evidence = []
            
            for i, (element, score) in enumerate(top_matches[:5], 1):
                answer_parts.append(f"{i}. **{element.name}** in `{element.file_path}:{element.line_number}`")
                if element.docstring:
                    answer_parts.append(f"   {element.docstring[:100]}...")
                evidence.append(f"{element.name} (relevance score: {score})")
            
            if len(top_matches) > 5:
                answer_parts.append(f"... and {len(top_matches) - 5} more matches")
            
            return QueryResult(
                query=query,
                answer='\n'.join(answer_parts),
                confidence=0.8,
                supporting_evidence=evidence,
                related_elements=[match[0] for match in top_matches[:5]],
                suggestions=[
                    "show implementation details",
                    "find related functions",
                    "explain how this works"
                ]
            )
        
        return QueryResult(
            query=query,
            answer=f"No matches found for '{' '.join(search_terms)}'. Try broader search terms or check spelling.",
            confidence=0.6,
            supporting_evidence=[],
            related_elements=[],
            suggestions=[
                "find error",
                "find subprocess",
                "find authentication",
                "list all functions"
            ]
        )
    
    def _handle_relationship_query(self, query: str) -> QueryResult:
        """Handle queries about relationships between components."""
        query_lower = query.lower()
        
        if 'depends' in query_lower or 'dependency' in query_lower:
            return self._analyze_dependencies(query)
        elif 'calls' in query_lower:
            return self._analyze_function_calls(query)
        elif 'uses' in query_lower:
            return self._analyze_usage_patterns(query)
        else:
            return self._analyze_general_relationships(query)
    
    def _analyze_dependencies(self, query: str) -> QueryResult:
        """Analyze dependency relationships."""
        # Count dependencies by type
        dependency_stats = defaultdict(list)
        
        for element in self.code_graph.values():
            if element.dependencies:
                dependency_stats[element.type].extend(element.dependencies)
        
        answer_parts = ["## Dependency Analysis\n"]
        
        for element_type, deps in dependency_stats.items():
            unique_deps = set(deps)
            answer_parts.append(f"**{element_type.title()}s**: {len(unique_deps)} unique dependencies")
            
            # Show top dependencies
            dep_counts = Counter(deps)
            top_deps = dep_counts.most_common(5)
            for dep, count in top_deps:
                answer_parts.append(f"  - {dep}: used {count} times")
            answer_parts.append("")
        
        # External dependencies
        external_deps = set()
        for element in self.code_graph.values():
            if element.type == 'import':
                external_deps.add(element.name)
        
        answer_parts.append(f"**External Dependencies**: {len(external_deps)} total")
        for dep in sorted(external_deps)[:10]:
            answer_parts.append(f"  - {dep}")
        
        evidence = [
            f"Analyzed {len(self.code_graph)} code elements",
            f"Found {len(self.relationships)} relationships",
            f"Identified {len(external_deps)} external dependencies"
        ]
        
        return QueryResult(
            query=query,
            answer='\n'.join(answer_parts),
            confidence=0.8,
            supporting_evidence=evidence,
            related_elements=[],
            suggestions=[
                "show function call relationships",
                "find circular dependencies",
                "analyze import usage patterns"
            ]
        )
    
    def _handle_metrics_query(self, query: str) -> QueryResult:
        """Handle queries about code metrics and complexity."""
        # Calculate various metrics
        total_elements = len(self.code_graph)
        
        # Complexity analysis
        complexity_stats = []
        for element in self.code_graph.values():
            if element.type in ['function', 'method', 'class']:
                complexity_stats.append(element.complexity_score)
        
        if complexity_stats:
            avg_complexity = sum(complexity_stats) / len(complexity_stats)
            max_complexity = max(complexity_stats)
            high_complexity_count = len([c for c in complexity_stats if c > 10])
        else:
            avg_complexity = max_complexity = high_complexity_count = 0
        
        # Type distribution
        type_counts = Counter(element.type for element in self.code_graph.values())
        
        # Usage analysis
        usage_stats = [element.usage_count for element in self.code_graph.values()]
        highly_used = [element for element in self.code_graph.values() if element.usage_count > 5]
        
        answer_parts = [
            "## Code Metrics Analysis\n",
            f"**Total Code Elements**: {total_elements}",
            f"**Average Complexity**: {avg_complexity:.1f}",
            f"**Maximum Complexity**: {max_complexity}",
            f"**High Complexity Elements**: {high_complexity_count}",
            "",
            "### Element Type Distribution"
        ]
        
        for element_type, count in type_counts.most_common():
            answer_parts.append(f"- **{element_type.title()}**: {count}")
        
        answer_parts.extend([
            "",
            f"### Usage Statistics",
            f"- **Highly Used Elements** (>5 references): {len(highly_used)}"
        ])
        
        if highly_used:
            answer_parts.append("\n**Most Referenced Elements**:")
            for element in sorted(highly_used, key=lambda x: x.usage_count, reverse=True)[:5]:
                answer_parts.append(f"- {element.name}: {element.usage_count} references")
        
        evidence = [
            f"Analyzed {total_elements} code elements across {len(set(e.file_path for e in self.code_graph.values()))} files",
            f"Calculated complexity for {len(complexity_stats)} functions/methods/classes",
            f"Found {len(self.relationships)} inter-element relationships"
        ]
        
        return QueryResult(
            query=query,
            answer='\n'.join(answer_parts),
            confidence=0.9,
            supporting_evidence=evidence,
            related_elements=highly_used[:5],
            suggestions=[
                "find high complexity functions",
                "show dependency relationships",
                "analyze test coverage"
            ]
        )
    
    def _handle_general_query(self, query: str) -> QueryResult:
        """Handle general queries that don't fit specific patterns."""
        return QueryResult(
            query=query,
            answer="I can help you understand the GitCodeSkill codebase. Try asking specific questions like:\n"
                   "- 'explain step 1' (for pipeline steps)\n"
                   "- 'find authentication' (to search for code)\n"
                   "- 'show dependencies' (for relationship analysis)\n"
                   "- 'analyze complexity' (for metrics)\n"
                   "- 'how does orchestrator work' (for component explanations)",
            confidence=0.5,
            supporting_evidence=[],
            related_elements=[],
            suggestions=[
                "explain the overall workflow",
                "find error handling patterns",
                "show me step 3 implementation",
                "analyze security patterns",
                "list all external dependencies"
            ]
        )
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get comprehensive system overview."""
        overview = {
            'total_files': len(set(element.file_path for element in self.code_graph.values())),
            'total_elements': len(self.code_graph),
            'element_types': dict(Counter(element.type for element in self.code_graph.values())),
            'total_relationships': len(self.relationships),
            'complexity_stats': {
                'average': 0,
                'maximum': 0,
                'high_complexity_count': 0
            },
            'top_functions': [],
            'external_dependencies': [],
            'architecture_summary': self._generate_architecture_summary()
        }
        
        # Calculate complexity stats
        complexity_scores = [e.complexity_score for e in self.code_graph.values() 
                           if e.type in ['function', 'method', 'class']]
        if complexity_scores:
            overview['complexity_stats'] = {
                'average': sum(complexity_scores) / len(complexity_scores),
                'maximum': max(complexity_scores),
                'high_complexity_count': len([c for c in complexity_scores if c > 10])
            }
        
        # Top functions by usage
        functions = [e for e in self.code_graph.values() if e.type in ['function', 'method']]
        overview['top_functions'] = sorted(functions, key=lambda x: x.usage_count, reverse=True)[:10]
        
        # External dependencies
        imports = [e for e in self.code_graph.values() if e.type == 'import']
        overview['external_dependencies'] = [imp.name for imp in imports]
        
        return overview
    
    def _generate_architecture_summary(self) -> str:
        """Generate a high-level architecture summary."""
        return """GitCodeSkill implements a 7-step automated development pipeline:
1. Configuration management and credential storage
2. Multi-repository analysis and code indexing
3. Requirement gathering from Jira or manual input
4. Semantic mapping of requirements to relevant code
5. Human review and change specification
6. Automated code modification with quality assurance
7. Version control operations and pull request creation

The system supports GitHub and Bitbucket integration, features a Streamlit web UI, 
handles enterprise-scale multi-repository scanning, and provides comprehensive 
automation from requirements to deployed code changes."""


def main():
    """Main function for testing the code intelligence skill."""
    import io
    
    # Set UTF-8 encoding for output
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    else:
        # For older Python versions, wrap stdout
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    if len(sys.argv) < 2:
        print("Usage: python code_intelligence_skill.py <repo_path> [query]")
        print("Example queries:")
        print("  'explain step 1'")
        print("  'find authentication code'")
        print("  'show dependencies'")
        print("  'analyze complexity'")
        return
    
    repo_path = sys.argv[1]
    query = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else "system overview"
    
    intelligence = GitCodeSkillIntelligence(repo_path)
    
    if query == "system overview":
        overview = intelligence.get_system_overview()
        print("# GitCodeSkill System Overview\n")
        print(f"**Files Analyzed**: {overview['total_files']}")
        print(f"**Code Elements**: {overview['total_elements']}")
        print(f"**Relationships**: {overview['total_relationships']}")
        print(f"**Average Complexity**: {overview['complexity_stats']['average']:.1f}")
        print(f"**External Dependencies**: {len(overview['external_dependencies'])}")
        print(f"\n## Architecture Summary")
        print(overview['architecture_summary'])
    else:
        result = intelligence.query_natural_language(query)
        print(f"# Query: {result.query}\n")
        print(f"**Confidence**: {result.confidence:.1%}\n")
        print(result.answer)
        
        if result.supporting_evidence:
            print(f"\n## Supporting Evidence")
            for evidence in result.supporting_evidence:
                print(f"- {evidence}")
        
        if result.related_elements:
            print(f"\n## Related Code Elements")
            for element in result.related_elements:
                print(f"- **{element.name}** ({element.type}) in `{element.file_path}:{element.line_number}`")
        
        if result.suggestions:
            print(f"\n## Suggested Queries")
            for suggestion in result.suggestions:
                print(f"- {suggestion}")


if __name__ == "__main__":
    main()