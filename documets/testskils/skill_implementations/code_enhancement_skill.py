#!/usr/bin/env python3
"""
Code Enhancement & Bug Fixing Skill for GitCodeSkill Repository
Analyzes, enhances, and fixes issues in the GitCodeSkill codebase with advanced capabilities.
"""

import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum


class IssueType(Enum):
    """Types of code issues that can be detected and fixed."""
    SECURITY_VULNERABILITY = "security"
    PERFORMANCE_ISSUE = "performance"
    CODE_QUALITY = "quality"
    ERROR_HANDLING = "error_handling"
    COMPATIBILITY = "compatibility"
    FUNCTIONALITY = "functionality"
    MAINTAINABILITY = "maintainability"


class SeverityLevel(Enum):
    """Severity levels for issues."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class CodeIssue:
    """Represents a code issue found during analysis."""
    file_path: str
    line_number: int
    issue_type: IssueType
    severity: SeverityLevel
    description: str
    suggested_fix: str
    code_snippet: str
    confidence: float  # 0.0 to 1.0


@dataclass
class Enhancement:
    """Represents a code enhancement opportunity."""
    file_path: str
    enhancement_type: str
    description: str
    implementation: str
    impact: str
    effort_estimate: str


class GitCodeSkillCodeEnhancer:
    """Advanced code analysis and enhancement system for GitCodeSkill."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.issues = []
        self.enhancements = []
        
        # Security patterns to detect
        self.security_patterns = {
            r'subprocess\.(?:run|call|check_output|Popen)\([^)]*shell=True': {
                'description': 'Shell injection vulnerability',
                'severity': SeverityLevel.HIGH,
                'fix': 'Use shell=False and pass command as list'
            },
            r'eval\s*\(': {
                'description': 'Code injection vulnerability with eval()',
                'severity': SeverityLevel.CRITICAL,
                'fix': 'Replace eval() with safer alternatives like ast.literal_eval()'
            },
            r'exec\s*\(': {
                'description': 'Code injection vulnerability with exec()',
                'severity': SeverityLevel.CRITICAL,
                'fix': 'Avoid exec() or use safer alternatives'
            },
            r'pickle\.loads?\s*\(': {
                'description': 'Insecure deserialization with pickle',
                'severity': SeverityLevel.HIGH,
                'fix': 'Use json or other safe serialization formats'
            },
            r'input\s*\([^)]*\)': {
                'description': 'Potential code injection with input()',
                'severity': SeverityLevel.MEDIUM,
                'fix': 'Validate and sanitize input()'
            }
        }
        
        # Performance patterns
        self.performance_patterns = {
            r'for\s+\w+\s+in\s+range\(len\([^)]+\)\)': {
                'description': 'Inefficient range(len()) iteration',
                'severity': SeverityLevel.MEDIUM,
                'fix': 'Use enumerate() or iterate directly over the sequence'
            },
            r'\.append\([^)]+\)\s*$': {
                'description': 'Potential list comprehension opportunity',
                'severity': SeverityLevel.LOW,
                'fix': 'Consider using list comprehension for better performance'
            },
            r'open\s*\([^)]*\)(?!\s*as|\s*with)': {
                'description': 'File not closed properly',
                'severity': SeverityLevel.MEDIUM,
                'fix': 'Use with statement for automatic file closing'
            }
        }
        
        # Error handling patterns
        self.error_handling_patterns = {
            r'except\s*:\s*$': {
                'description': 'Bare except clause catches all exceptions',
                'severity': SeverityLevel.MEDIUM,
                'fix': 'Specify specific exception types'
            },
            r'except\s+Exception\s*:\s*pass': {
                'description': 'Silent exception handling',
                'severity': SeverityLevel.MEDIUM,
                'fix': 'Add logging or specific error handling'
            },
            r'raise\s*$': {
                'description': 'Re-raising without preserving traceback',
                'severity': SeverityLevel.LOW,
                'fix': 'Use raise from original_exception'
            }
        }
    
    def analyze_security_vulnerabilities(self) -> List[CodeIssue]:
        """Analyze code for security vulnerabilities."""
        security_issues = []
        
        for py_file in self.repo_path.rglob('*.py'):
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for pattern, info in self.security_patterns.items():
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line):
                            security_issues.append(CodeIssue(
                                file_path=str(py_file.relative_to(self.repo_path)),
                                line_number=line_num,
                                issue_type=IssueType.SECURITY_VULNERABILITY,
                                severity=info['severity'],
                                description=info['description'],
                                suggested_fix=info['fix'],
                                code_snippet=line.strip(),
                                confidence=0.8
                            ))
            except Exception as e:
                print(f"Error analyzing {py_file}: {e}")
        
        return security_issues
    
    def analyze_performance_issues(self) -> List[CodeIssue]:
        """Analyze code for performance bottlenecks."""
        performance_issues = []
        
        for py_file in self.repo_path.rglob('*.py'):
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                # Check for performance anti-patterns
                for pattern, info in self.performance_patterns.items():
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line):
                            performance_issues.append(CodeIssue(
                                file_path=str(py_file.relative_to(self.repo_path)),
                                line_number=line_num,
                                issue_type=IssueType.PERFORMANCE_ISSUE,
                                severity=info['severity'],
                                description=info['description'],
                                suggested_fix=info['fix'],
                                code_snippet=line.strip(),
                                confidence=0.7
                            ))
                
                # Analyze AST for more complex patterns
                try:
                    tree = ast.parse(content)
                    ast_issues = self._analyze_ast_performance(tree, py_file, content)
                    performance_issues.extend(ast_issues)
                except SyntaxError:
                    pass  # Skip files with syntax errors
                    
            except Exception as e:
                print(f"Error analyzing performance in {py_file}: {e}")
        
        return performance_issues
    
    def _analyze_ast_performance(self, tree: ast.AST, file_path: Path, content: str) -> List[CodeIssue]:
        """Analyze AST for performance issues."""
        issues = []
        lines = content.split('\n')
        
        class PerformanceVisitor(ast.NodeVisitor):
            def visit_For(self, node):
                # Detect nested loops that could be optimized
                for child in ast.walk(node):
                    if isinstance(child, ast.For) and child != node:
                        issues.append(CodeIssue(
                            file_path=str(file_path.relative_to(self.repo_path)),
                            line_number=node.lineno,
                            issue_type=IssueType.PERFORMANCE_ISSUE,
                            severity=SeverityLevel.MEDIUM,
                            description="Nested loop detected - consider optimization",
                            suggested_fix="Consider using list comprehensions, itertools, or algorithmic optimization",
                            code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                            confidence=0.6
                        ))
                        break
                self.generic_visit(node)
            
            def visit_ListComp(self, node):
                # Check for complex list comprehensions
                if len(node.generators) > 2:
                    issues.append(CodeIssue(
                        file_path=str(file_path.relative_to(self.repo_path)),
                        line_number=node.lineno,
                        issue_type=IssueType.CODE_QUALITY,
                        severity=SeverityLevel.LOW,
                        description="Complex list comprehension may hurt readability",
                        suggested_fix="Consider breaking into simpler loops or functions",
                        code_snippet=lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                        confidence=0.5
                    ))
                self.generic_visit(node)
        
        visitor = PerformanceVisitor()
        visitor.visit(tree)
        return issues
    
    def analyze_error_handling(self) -> List[CodeIssue]:
        """Analyze error handling patterns."""
        error_issues = []
        
        for py_file in self.repo_path.rglob('*.py'):
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for pattern, info in self.error_handling_patterns.items():
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line):
                            error_issues.append(CodeIssue(
                                file_path=str(py_file.relative_to(self.repo_path)),
                                line_number=line_num,
                                issue_type=IssueType.ERROR_HANDLING,
                                severity=info['severity'],
                                description=info['description'],
                                suggested_fix=info['fix'],
                                code_snippet=line.strip(),
                                confidence=0.8
                            ))
                
                # Check for missing error handling in subprocess calls
                if 'subprocess.' in content:
                    self._check_subprocess_error_handling(py_file, content, error_issues)
                    
            except Exception as e:
                print(f"Error analyzing error handling in {py_file}: {e}")
        
        return error_issues
    
    def _check_subprocess_error_handling(self, file_path: Path, content: str, issues: List[CodeIssue]):
        """Check subprocess calls for proper error handling."""
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            if re.search(r'subprocess\.(run|call|check_output)', line):
                # Look for try-catch block around this line
                has_error_handling = False
                start_line = max(0, line_num - 5)
                end_line = min(len(lines), line_num + 5)
                
                for check_line in lines[start_line:end_line]:
                    if re.search(r'try\s*:|except\s+.*:', check_line):
                        has_error_handling = True
                        break
                
                if not has_error_handling:
                    issues.append(CodeIssue(
                        file_path=str(file_path.relative_to(self.repo_path)),
                        line_number=line_num,
                        issue_type=IssueType.ERROR_HANDLING,
                        severity=SeverityLevel.MEDIUM,
                        description="Subprocess call without error handling",
                        suggested_fix="Wrap subprocess calls in try-except block",
                        code_snippet=line.strip(),
                        confidence=0.7
                    ))
    
    def analyze_code_quality(self) -> List[CodeIssue]:
        """Analyze general code quality issues."""
        quality_issues = []
        
        for py_file in self.repo_path.rglob('*.py'):
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                # Check for long functions
                function_lines = self._count_function_lengths(content)
                for func_name, (start_line, length) in function_lines.items():
                    if length > 50:  # Functions longer than 50 lines
                        quality_issues.append(CodeIssue(
                            file_path=str(py_file.relative_to(self.repo_path)),
                            line_number=start_line,
                            issue_type=IssueType.CODE_QUALITY,
                            severity=SeverityLevel.LOW,
                            description=f"Long function '{func_name}' ({length} lines)",
                            suggested_fix="Consider breaking into smaller functions",
                            code_snippet=f"def {func_name}(...)",
                            confidence=0.8
                        ))
                
                # Check for code duplication
                duplication_issues = self._detect_code_duplication(py_file, content)
                quality_issues.extend(duplication_issues)
                
                # Check for unused imports (simplified)
                unused_imports = self._detect_unused_imports(py_file, content)
                quality_issues.extend(unused_imports)
                
            except Exception as e:
                print(f"Error analyzing code quality in {py_file}: {e}")
        
        return quality_issues
    
    def _count_function_lengths(self, content: str) -> Dict[str, Tuple[int, int]]:
        """Count lines in functions."""
        function_info = {}
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Calculate function length (simplified)
                    if hasattr(node, 'end_lineno') and node.end_lineno:
                        length = node.end_lineno - node.lineno + 1
                    else:
                        length = 10  # Default estimate
                    function_info[node.name] = (node.lineno, length)
        except SyntaxError:
            pass  # Skip files with syntax errors
        
        return function_info
    
    def _detect_code_duplication(self, file_path: Path, content: str) -> List[CodeIssue]:
        """Detect potential code duplication within a file."""
        issues = []
        lines = content.split('\n')
        
        # Simple duplication detection - look for repeated line patterns
        line_groups = {}
        for i, line in enumerate(lines):
            stripped = line.strip()
            if len(stripped) > 20 and not stripped.startswith('#'):  # Skip short lines and comments
                if stripped in line_groups:
                    line_groups[stripped].append(i + 1)
                else:
                    line_groups[stripped] = [i + 1]
        
        for line_content, line_numbers in line_groups.items():
            if len(line_numbers) > 2:  # Line appears more than twice
                for line_num in line_numbers[1:]:  # Report duplicates
                    issues.append(CodeIssue(
                        file_path=str(file_path.relative_to(self.repo_path)),
                        line_number=line_num,
                        issue_type=IssueType.CODE_QUALITY,
                        severity=SeverityLevel.LOW,
                        description="Potential code duplication detected",
                        suggested_fix="Consider extracting common code into a function",
                        code_snippet=line_content[:100],
                        confidence=0.4
                    ))
        
        return issues
    
    def _detect_unused_imports(self, file_path: Path, content: str) -> List[CodeIssue]:
        """Detect potentially unused imports."""
        issues = []
        
        try:
            tree = ast.parse(content)
            imports = []
            
            # Collect all imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append((alias.name, node.lineno, alias.asname or alias.name))
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for alias in node.names:
                            import_name = f"{node.module}.{alias.name}"
                            imports.append((import_name, node.lineno, alias.asname or alias.name))
            
            # Check if imports are used (simplified check)
            for import_path, line_num, import_name in imports:
                if import_name not in content.replace(f"import {import_name}", ""):
                    # Very basic check - could have false positives
                    if content.count(import_name) <= 2:  # Only appears in import statement
                        issues.append(CodeIssue(
                            file_path=str(file_path.relative_to(self.repo_path)),
                            line_number=line_num,
                            issue_type=IssueType.CODE_QUALITY,
                            severity=SeverityLevel.LOW,
                            description=f"Potentially unused import: {import_name}",
                            suggested_fix="Remove unused import or add usage",
                            code_snippet=f"import {import_name}",
                            confidence=0.3
                        ))
        
        except SyntaxError:
            pass  # Skip files with syntax errors
        
        return issues
    
    def suggest_enhancements(self) -> List[Enhancement]:
        """Suggest code enhancements and new features."""
        enhancements = []
        
        # Analyze each component for enhancement opportunities
        for py_file in self.repo_path.rglob('*.py'):
            try:
                content = py_file.read_text(encoding='utf-8')
                file_enhancements = self._analyze_file_for_enhancements(py_file, content)
                enhancements.extend(file_enhancements)
            except Exception as e:
                print(f"Error analyzing enhancements for {py_file}: {e}")
        
        # Add system-wide enhancements
        system_enhancements = self._suggest_system_enhancements()
        enhancements.extend(system_enhancements)
        
        return enhancements
    
    def _analyze_file_for_enhancements(self, file_path: Path, content: str) -> List[Enhancement]:
        """Analyze a single file for enhancement opportunities."""
        enhancements = []
        
        # Step-specific enhancements
        if file_path.name.startswith('step_'):
            step_num = int(file_path.name.split('_')[1])
            step_enhancements = self._suggest_step_enhancements(file_path, content, step_num)
            enhancements.extend(step_enhancements)
        
        # General enhancements based on content analysis
        if 'subprocess.run' in content and 'timeout=' not in content:
            enhancements.append(Enhancement(
                file_path=str(file_path.relative_to(self.repo_path)),
                enhancement_type="Robustness",
                description="Add timeout protection to subprocess calls",
                implementation="Add timeout parameter to subprocess.run() calls",
                impact="Prevents hanging processes and improves reliability",
                effort_estimate="Low - 1-2 hours"
            ))
        
        if 'requests.get' in content or 'requests.post' in content:
            if 'timeout=' not in content:
                enhancements.append(Enhancement(
                    file_path=str(file_path.relative_to(self.repo_path)),
                    enhancement_type="Reliability",
                    description="Add timeout and retry logic to HTTP requests",
                    implementation="Add timeout and retry decorator for HTTP calls",
                    impact="Improves resilience to network issues",
                    effort_estimate="Medium - 3-4 hours"
                ))
        
        if 'print(' in content and 'logging' not in content:
            enhancements.append(Enhancement(
                file_path=str(file_path.relative_to(self.repo_path)),
                enhancement_type="Observability",
                description="Replace print statements with proper logging",
                implementation="Add logging configuration and replace print() calls",
                impact="Better debugging and production monitoring",
                effort_estimate="Low - 2-3 hours"
            ))
        
        return enhancements
    
    def _suggest_step_enhancements(self, file_path: Path, content: str, step_num: int) -> List[Enhancement]:
        """Suggest enhancements specific to pipeline steps."""
        enhancements = []
        
        step_specific = {
            1: [
                Enhancement(
                    file_path=str(file_path.relative_to(self.repo_path)),
                    enhancement_type="Performance",
                    description="Add parallel repository analysis for multi-repo scans",
                    implementation="Use ThreadPoolExecutor for concurrent repository processing",
                    impact="Significantly faster multi-repository analysis",
                    effort_estimate="Medium - 4-6 hours"
                ),
                Enhancement(
                    file_path=str(file_path.relative_to(self.repo_path)),
                    enhancement_type="Caching",
                    description="Cache repository analysis results",
                    implementation="Add file-based or Redis caching for analysis reports",
                    impact="Faster re-analysis of unchanged repositories",
                    effort_estimate="Medium - 5-7 hours"
                )
            ],
            2: [
                Enhancement(
                    file_path=str(file_path.relative_to(self.repo_path)),
                    enhancement_type="Integration",
                    description="Support additional issue tracking systems",
                    implementation="Add plugins for Azure DevOps, Linear, GitHub Issues",
                    impact="Broader enterprise compatibility",
                    effort_estimate="High - 2-3 days"
                )
            ],
            3: [
                Enhancement(
                    file_path=str(file_path.relative_to(self.repo_path)),
                    enhancement_type="AI Enhancement",
                    description="Use machine learning for better requirement mapping",
                    implementation="Integrate NLP libraries for semantic similarity",
                    impact="More accurate requirement-to-code mapping",
                    effort_estimate="High - 5-7 days"
                )
            ],
            5: [
                Enhancement(
                    file_path=str(file_path.relative_to(self.repo_path)),
                    enhancement_type="Safety",
                    description="Add rollback mechanism for failed changes",
                    implementation="Create backup branches and automatic rollback on test failure",
                    impact="Safer automated code changes",
                    effort_estimate="Medium - 4-5 hours"
                )
            ]
        }
        
        return step_specific.get(step_num, [])
    
    def _suggest_system_enhancements(self) -> List[Enhancement]:
        """Suggest system-wide enhancements."""
        return [
            Enhancement(
                file_path="system_wide",
                enhancement_type="Monitoring",
                description="Add comprehensive metrics and monitoring",
                implementation="Integrate with Prometheus/Grafana for system metrics",
                impact="Better operational visibility and debugging",
                effort_estimate="High - 1-2 weeks"
            ),
            Enhancement(
                file_path="system_wide", 
                enhancement_type="Testing",
                description="Add comprehensive test suite",
                implementation="Unit tests, integration tests, and end-to-end testing",
                impact="Higher code quality and confidence in changes",
                effort_estimate="High - 2-3 weeks"
            ),
            Enhancement(
                file_path="system_wide",
                enhancement_type="Documentation",
                description="Add interactive API documentation",
                implementation="OpenAPI/Swagger documentation for REST endpoints",
                impact="Better developer experience and adoption",
                effort_estimate="Medium - 1 week"
            ),
            Enhancement(
                file_path="system_wide",
                enhancement_type="Containerization",
                description="Add Docker support and container orchestration",
                implementation="Dockerfile, docker-compose, and Kubernetes manifests",
                impact="Easier deployment and scaling",
                effort_estimate="Medium - 1-2 weeks"
            )
        ]
    
    def generate_fix_implementations(self, issues: List[CodeIssue]) -> Dict[str, str]:
        """Generate actual code implementations for fixes."""
        implementations = {}
        
        for issue in issues:
            if issue.issue_type == IssueType.SECURITY_VULNERABILITY:
                implementations[f"{issue.file_path}:{issue.line_number}"] = self._generate_security_fix(issue)
            elif issue.issue_type == IssueType.PERFORMANCE_ISSUE:
                implementations[f"{issue.file_path}:{issue.line_number}"] = self._generate_performance_fix(issue)
            elif issue.issue_type == IssueType.ERROR_HANDLING:
                implementations[f"{issue.file_path}:{issue.line_number}"] = self._generate_error_handling_fix(issue)
        
        return implementations
    
    def _generate_security_fix(self, issue: CodeIssue) -> str:
        """Generate specific security fix implementation."""
        if 'shell=True' in issue.code_snippet:
            return f"""
# BEFORE:
{issue.code_snippet}

# AFTER (Fixed):
# Split command into list and use shell=False
import shlex
cmd_list = shlex.split('{issue.code_snippet.replace("shell=True", "").strip()}')
result = subprocess.run(cmd_list, capture_output=True, text=True)
"""
        
        elif 'eval(' in issue.code_snippet:
            return f"""
# BEFORE:
{issue.code_snippet}

# AFTER (Fixed):
# Use ast.literal_eval for safe evaluation
import ast
try:
    result = ast.literal_eval(expression)
except (ValueError, SyntaxError):
    # Handle invalid expressions
    result = None
"""
        
        return f"# Fix needed for: {issue.description}\n# Original: {issue.code_snippet}"
    
    def _generate_performance_fix(self, issue: CodeIssue) -> str:
        """Generate specific performance fix implementation."""
        if 'range(len(' in issue.code_snippet:
            return f"""
# BEFORE:
{issue.code_snippet}

# AFTER (Optimized):
# Use enumerate instead of range(len())
for index, item in enumerate(collection):
    # Process item directly
    pass
"""
        
        elif '.append(' in issue.code_snippet and 'for' in issue.code_snippet:
            return f"""
# BEFORE:
{issue.code_snippet}

# AFTER (Optimized):
# Use list comprehension for better performance
result = [process(item) for item in collection if condition(item)]
"""
        
        return f"# Performance optimization needed\n# Original: {issue.code_snippet}"
    
    def _generate_error_handling_fix(self, issue: CodeIssue) -> str:
        """Generate specific error handling fix implementation."""
        if 'except:' in issue.code_snippet:
            return f"""
# BEFORE:
{issue.code_snippet}

# AFTER (Fixed):
try:
    # Original code here
    pass
except SpecificException as e:
    # Handle specific exception
    logging.error(f"Specific error: {{e}}")
    raise
except Exception as e:
    # Handle other exceptions
    logging.error(f"Unexpected error: {{e}}")
    raise
"""
        
        elif 'subprocess.' in issue.code_snippet:
            return f"""
# BEFORE:
{issue.code_snippet}

# AFTER (Fixed with error handling):
try:
    result = {issue.code_snippet.strip()}
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, result.args)
except subprocess.CalledProcessError as e:
    logging.error(f"Command failed: {{e}}")
    raise
except FileNotFoundError as e:
    logging.error(f"Command not found: {{e}}")
    raise
"""
        
        return f"# Error handling improvement needed\n# Original: {issue.code_snippet}"
    
    def run_comprehensive_analysis(self) -> Dict[str, List]:
        """Run all analysis types and return comprehensive results."""
        results = {
            'security_issues': self.analyze_security_vulnerabilities(),
            'performance_issues': self.analyze_performance_issues(),
            'error_handling_issues': self.analyze_error_handling(),
            'code_quality_issues': self.analyze_code_quality(),
            'enhancements': self.suggest_enhancements()
        }
        
        # Generate fix implementations
        all_issues = (results['security_issues'] + results['performance_issues'] + 
                     results['error_handling_issues'] + results['code_quality_issues'])
        results['fix_implementations'] = self.generate_fix_implementations(all_issues)
        
        return results
    
    def generate_analysis_report(self) -> str:
        """Generate a comprehensive analysis report."""
        results = self.run_comprehensive_analysis()
        
        report = []
        report.append("# GitCodeSkill - Code Analysis & Enhancement Report\n")
        
        # Summary
        total_issues = sum(len(issues) for key, issues in results.items() 
                          if key.endswith('_issues'))
        total_enhancements = len(results['enhancements'])
        
        report.append(f"## Executive Summary\n")
        report.append(f"- **Total Issues Found**: {total_issues}")
        report.append(f"- **Enhancement Opportunities**: {total_enhancements}")
        report.append(f"- **Files Analyzed**: {len(list(self.repo_path.rglob('*.py')))}")
        
        # Severity breakdown
        severity_counts = {}
        for category in ['security_issues', 'performance_issues', 'error_handling_issues', 'code_quality_issues']:
            for issue in results[category]:
                severity = issue.severity.value
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        report.append(f"\n### Issue Severity Breakdown")
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = severity_counts.get(severity, 0)
            if count > 0:
                report.append(f"- **{severity.title()}**: {count} issues")
        
        # Security Issues
        if results['security_issues']:
            report.append(f"\n## Security Vulnerabilities ({len(results['security_issues'])} found)")
            for issue in sorted(results['security_issues'], key=lambda x: x.severity.value):
                report.append(f"\n### {issue.severity.value.title()}: {issue.description}")
                report.append(f"**File**: `{issue.file_path}:{issue.line_number}`")
                report.append(f"**Code**: `{issue.code_snippet}`")
                report.append(f"**Fix**: {issue.suggested_fix}")
        
        # Performance Issues
        if results['performance_issues']:
            report.append(f"\n## Performance Issues ({len(results['performance_issues'])} found)")
            for issue in results['performance_issues'][:10]:  # Show top 10
                report.append(f"\n### {issue.description}")
                report.append(f"**File**: `{issue.file_path}:{issue.line_number}`")
                report.append(f"**Code**: `{issue.code_snippet}`")
                report.append(f"**Optimization**: {issue.suggested_fix}")
        
        # Error Handling
        if results['error_handling_issues']:
            report.append(f"\n## Error Handling Issues ({len(results['error_handling_issues'])} found)")
            for issue in results['error_handling_issues'][:10]:  # Show top 10
                report.append(f"\n### {issue.description}")
                report.append(f"**File**: `{issue.file_path}:{issue.line_number}`")
                report.append(f"**Code**: `{issue.code_snippet}`")
                report.append(f"**Improvement**: {issue.suggested_fix}")
        
        # Enhancements
        if results['enhancements']:
            report.append(f"\n## Enhancement Opportunities ({len(results['enhancements'])} found)")
            
            # Group by type
            enhancement_groups = {}
            for enhancement in results['enhancements']:
                etype = enhancement.enhancement_type
                if etype not in enhancement_groups:
                    enhancement_groups[etype] = []
                enhancement_groups[etype].append(enhancement)
            
            for etype, enhancements in enhancement_groups.items():
                report.append(f"\n### {etype} Enhancements")
                for enhancement in enhancements:
                    report.append(f"\n#### {enhancement.description}")
                    report.append(f"**File**: `{enhancement.file_path}`")
                    report.append(f"**Implementation**: {enhancement.implementation}")
                    report.append(f"**Impact**: {enhancement.impact}")
                    report.append(f"**Effort**: {enhancement.effort_estimate}")
        
        # Recommendations
        report.append("\n## Priority Recommendations")
        report.append("1. **Address Critical Security Issues First** - Fix any critical/high severity security vulnerabilities")
        report.append("2. **Improve Error Handling** - Add comprehensive error handling and logging")
        report.append("3. **Optimize Performance** - Focus on high-impact performance improvements")
        report.append("4. **Add Testing Infrastructure** - Implement comprehensive test coverage")
        report.append("5. **Enhance Monitoring** - Add observability and metrics collection")
        
        return '\n'.join(report)


def main():
    """Main function for testing the code enhancement skill."""
    if len(sys.argv) < 2:
        print("Usage: python code_enhancement_skill.py <repo_path> [command]")
        print("Commands: security, performance, error-handling, quality, enhancements, full-report")
        return
    
    repo_path = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else 'full-report'
    
    # Set UTF-8 encoding for output
    import io
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    else:
        # For older Python versions, wrap stdout
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    enhancer = GitCodeSkillCodeEnhancer(repo_path)
    
    if command == 'security':
        issues = enhancer.analyze_security_vulnerabilities()
        for issue in issues:
            print(f"{issue.severity.value.upper()}: {issue.description}")
            print(f"  File: {issue.file_path}:{issue.line_number}")
            print(f"  Fix: {issue.suggested_fix}\n")
    
    elif command == 'performance':
        issues = enhancer.analyze_performance_issues()
        for issue in issues:
            print(f"{issue.severity.value.upper()}: {issue.description}")
            print(f"  File: {issue.file_path}:{issue.line_number}")
            print(f"  Optimization: {issue.suggested_fix}\n")
    
    elif command == 'error-handling':
        issues = enhancer.analyze_error_handling()
        for issue in issues:
            print(f"{issue.severity.value.upper()}: {issue.description}")
            print(f"  File: {issue.file_path}:{issue.line_number}")
            print(f"  Improvement: {issue.suggested_fix}\n")
    
    elif command == 'quality':
        issues = enhancer.analyze_code_quality()
        for issue in issues:
            print(f"{issue.severity.value.upper()}: {issue.description}")
            print(f"  File: {issue.file_path}:{issue.line_number}")
            print(f"  Improvement: {issue.suggested_fix}\n")
    
    elif command == 'enhancements':
        enhancements = enhancer.suggest_enhancements()
        for enhancement in enhancements:
            print(f"{enhancement.enhancement_type}: {enhancement.description}")
            print(f"  File: {enhancement.file_path}")
            print(f"  Impact: {enhancement.impact}")
            print(f"  Effort: {enhancement.effort_estimate}\n")
    
    elif command == 'full-report':
        report = enhancer.generate_analysis_report()
        print(report)
    
    else:
        print("Unknown command. Available: security, performance, error-handling, quality, enhancements, full-report")


if __name__ == "__main__":
    main()