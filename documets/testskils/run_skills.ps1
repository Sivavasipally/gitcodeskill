# GitCodeSkill Claude Skills Runner for PowerShell
# Provides easy access to all skills with proper UTF-8 encoding

param(
    [string]$Skill = "",
    [string]$Command = "",
    [string]$OutputFile = ""
)

# Set UTF-8 encoding
$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::new()
[Console]::InputEncoding = [Text.UTF8Encoding]::new()

# Configuration
$RepoPath = "D:\testgitcloneandremove\gitcodeskill"
$SkillsPath = "D:\testgitcloneandremove\skill_implementations"

function Show-Help {
    Write-Host ""
    Write-Host "GitCodeSkill Claude Skills Runner" -ForegroundColor Cyan
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\run_skills.ps1 [skill] [command] [output_file]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Available Skills:" -ForegroundColor Green
    Write-Host "  doc      - Documentation Generator"
    Write-Host "  uml      - UML Diagram Generator"
    Write-Host "  fix      - Code Enhancement and Bug Fixer"
    Write-Host "  query    - Code Intelligence and Query"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Green
    Write-Host "  .\run_skills.ps1 doc full"
    Write-Host "  .\run_skills.ps1 uml architecture"
    Write-Host "  .\run_skills.ps1 fix security"
    Write-Host "  .\run_skills.ps1 query 'explain step 1'"
    Write-Host ""
    Write-Host "Save to file:" -ForegroundColor Green
    Write-Host "  .\run_skills.ps1 doc full documentation.md"
    Write-Host "  .\run_skills.ps1 fix full-report analysis.md"
    Write-Host ""
}

if ($Skill -eq "") {
    Show-Help
    exit
}

# Map skills to script files
$ScriptName = switch ($Skill) {
    "doc" { "doc_generator_skill.py"; if ($Command -eq "") { $Command = "full" } }
    "uml" { "uml_generator_skill.py"; if ($Command -eq "") { $Command = "architecture" } }
    "fix" { "code_enhancement_skill.py"; if ($Command -eq "") { $Command = "full-report" } }
    "query" { "code_intelligence_skill.py"; if ($Command -eq "") { $Command = "system overview" } }
    default { 
        Write-Host "Error: Unknown skill '$Skill'" -ForegroundColor Red
        Write-Host "Available skills: doc, uml, fix, query" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "Running $Skill skill with command: $Command" -ForegroundColor Green
Write-Host "Repository: $RepoPath" -ForegroundColor Gray
Write-Host ""

$ScriptPath = Join-Path $SkillsPath $ScriptName

if ($OutputFile -eq "") {
    # Output to console
    & python $ScriptPath $RepoPath $Command
} else {
    # Output to file with UTF-8 encoding
    try {
        $result = & python $ScriptPath $RepoPath $Command 2>&1
        $result | Out-File -FilePath $OutputFile -Encoding UTF8
        
        Write-Host ""
        Write-Host "Output saved to: $OutputFile" -ForegroundColor Green
        $fileInfo = Get-Item $OutputFile
        Write-Host "File size: $($fileInfo.Length) bytes" -ForegroundColor Gray
    }
    catch {
        Write-Host "Error saving to file: $_" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green