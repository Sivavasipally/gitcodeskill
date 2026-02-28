# GitCodeSkill Claude Skills - Windows Usage Guide

## ✅ Fixed Unicode Issues

All skills have been updated to handle Windows UTF-8 encoding properly. No more Unicode errors!

## 🚀 Quick Usage Methods

### Method 1: Use the Windows Batch File (Easiest)
```batch
# Show help
run_skills.bat

# Run skills with automatic UTF-8 handling
run_skills.bat doc full
run_skills.bat uml architecture
run_skills.bat fix security
run_skills.bat query "explain step 1"

# Save output to file
run_skills.bat doc full documentation.md
run_skills.bat fix full-report analysis.md
```

### Method 2: Use PowerShell Script (Recommended)
```powershell
# Show help
.\run_skills.ps1

# Run skills
.\run_skills.ps1 doc full
.\run_skills.ps1 uml architecture
.\run_skills.ps1 fix security
.\run_skills.ps1 query "explain step 1"

# Save output to file
.\run_skills.ps1 doc full documentation.md
.\run_skills.ps1 fix full-report analysis.md
```

### Method 3: Direct Python Commands
```bash
# Set UTF-8 encoding first
set PYTHONIOENCODING=utf-8
chcp 65001

# Then run normally
python skill_implementations/code_enhancement_skill.py D:\testgitcloneandremove\gitcodeskill full-report > analysis.md
python skill_implementations/doc_generator_skill.py D:\testgitcloneandremove\gitcodeskill full > documentation.md
python skill_implementations/uml_generator_skill.py D:\testgitcloneandremove\gitcodeskill architecture > architecture.puml
python skill_implementations/code_intelligence_skill.py D:\testgitcloneandremove\gitcodeskill "explain step 1"
```

### Method 4: PowerShell with UTF-8 (Alternative)
```powershell
# For file output with UTF-8
python skill_implementations/code_enhancement_skill.py D:\testgitcloneandremove\gitcodeskill full-report | Out-File -FilePath analysis.md -Encoding UTF8
```

## 📁 Available Skills and Commands

### Documentation Generator
```batch
run_skills.bat doc full              # Complete documentation
run_skills.bat doc step1             # Step 1 documentation
run_skills.bat doc config            # Configuration guide
run_skills.bat doc api               # API documentation
run_skills.bat doc troubleshoot      # Troubleshooting guide
```

### UML Generator
```batch
run_skills.bat uml architecture      # Architecture diagram
run_skills.bat uml dataflow          # Data flow diagram
run_skills.bat uml sequence          # Sequence diagram (steps 1-6)
run_skills.bat uml "sequence 1 3"    # Sequence diagram (steps 1-3)
run_skills.bat uml "class orchestrator"  # Class diagram
run_skills.bat uml multi-repo        # Multi-repo workflow
run_skills.bat uml mermaid           # Mermaid format
```

### Code Enhancement
```batch
run_skills.bat fix security          # Security analysis
run_skills.bat fix performance       # Performance analysis
run_skills.bat fix error-handling    # Error handling analysis
run_skills.bat fix quality          # Code quality analysis
run_skills.bat fix enhancements     # Enhancement suggestions
run_skills.bat fix full-report      # Complete analysis report
```

### Code Intelligence
```batch
run_skills.bat query "system overview"
run_skills.bat query "explain step 1"
run_skills.bat query "find authentication"
run_skills.bat query "show dependencies"
run_skills.bat query "analyze complexity"
run_skills.bat query "how does orchestrator work"
```

## 🎯 Real-World Usage Examples

### Complete Documentation Package
```batch
mkdir GitCodeSkill_Documentation
run_skills.bat doc full GitCodeSkill_Documentation\complete_docs.md
run_skills.bat doc config GitCodeSkill_Documentation\setup_guide.md
run_skills.bat doc troubleshoot GitCodeSkill_Documentation\troubleshooting.md
run_skills.bat uml architecture GitCodeSkill_Documentation\architecture.puml
run_skills.bat fix full-report GitCodeSkill_Documentation\code_analysis.md
```

### Security Review Workflow
```batch
# Step 1: Run security analysis
run_skills.bat fix security security_issues.md

# Step 2: Find specific security patterns
run_skills.bat query "find all subprocess calls" subprocess_analysis.md

# Step 3: Get security recommendations
run_skills.bat query "security best practices" security_recommendations.md

# Step 4: Generate security documentation
run_skills.bat doc security-guide security_guide.md
```

### New Developer Onboarding
```batch
# Step 1: System overview
run_skills.bat query "system overview" system_overview.md

# Step 2: Architecture visualization
run_skills.bat uml architecture architecture.puml

# Step 3: Step-by-step explanation
run_skills.bat doc full complete_documentation.md

# Step 4: Common issues and solutions
run_skills.bat doc troubleshoot troubleshooting.md
```

## 🔧 Troubleshooting Windows Issues

### Issue: "python: command not found"
**Solution**: 
```batch
# Use full Python path
C:\Python313\python.exe skill_implementations\code_enhancement_skill.py ...

# Or add Python to PATH and restart command prompt
```

### Issue: Still getting Unicode errors
**Solution**:
```batch
# Method 1: Use the batch/PowerShell scripts (they handle encoding)
run_skills.bat fix full-report analysis.md

# Method 2: Set environment variables
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8
chcp 65001

# Method 3: Use PowerShell UTF-8 output
python script.py | Out-File -FilePath output.md -Encoding UTF8
```

### Issue: Output file is empty or corrupted
**Solution**:
```batch
# Use the PowerShell method for reliable file output
.\run_skills.ps1 fix full-report analysis.md
```

### Issue: Scripts not executing
**Solution**:
```powershell
# For PowerShell scripts, you may need to change execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then run the script
.\run_skills.ps1 doc full
```

## ⚡ Performance Tips

1. **Use Batch/PowerShell Scripts**: They handle encoding automatically
2. **Save Large Outputs to Files**: Console output can be slow for large reports
3. **Use Specific Commands**: Instead of `full-report`, use targeted analysis like `security` or `performance`
4. **Cache Results**: Save outputs to files and reuse instead of re-running

## 📊 Output File Sizes (Approximate)

- **Documentation (full)**: 50-100 KB
- **UML Diagrams**: 5-20 KB  
- **Security Analysis**: 10-50 KB
- **Full Code Analysis**: 100-500 KB
- **Code Intelligence Queries**: 1-10 KB

## 🎉 You're All Set!

Your GitCodeSkill Claude Skills are now fully Windows-compatible and ready to use. Try this command to get started:

```batch
run_skills.bat query "system overview"
```

This will give you a comprehensive overview of the GitCodeSkill system to get you started!