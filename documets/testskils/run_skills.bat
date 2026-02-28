@echo off
REM GitCodeSkill Claude Skills Runner for Windows
REM This batch file provides easy access to all skills with proper UTF-8 encoding

setlocal enabledelayedexpansion
set PYTHONIOENCODING=utf-8
chcp 65001 >nul

REM Set the repository path
set REPO_PATH=D:\testgitcloneandremove\gitcodeskill
set SKILLS_PATH=D:\testgitcloneandremove\skill_implementations

if "%1"=="" (
    echo.
    echo GitCodeSkill Claude Skills Runner
    echo ================================
    echo.
    echo Usage: run_skills.bat [skill] [command] [output_file]
    echo.
    echo Available Skills:
    echo   doc      - Documentation Generator
    echo   uml      - UML Diagram Generator  
    echo   fix      - Code Enhancement and Bug Fixer
    echo   query    - Code Intelligence and Query
    echo.
    echo Examples:
    echo   run_skills.bat doc full
    echo   run_skills.bat uml architecture
    echo   run_skills.bat fix security
    echo   run_skills.bat query "explain step 1"
    echo.
    echo Save to file:
    echo   run_skills.bat doc full documentation.md
    echo   run_skills.bat fix full-report analysis.md
    echo.
    goto :eof
)

set SKILL=%1
set COMMAND=%2
set OUTPUT_FILE=%3

if "%SKILL%"=="doc" (
    set SCRIPT_NAME=doc_generator_skill.py
    if "%COMMAND%"=="" set COMMAND=full
)

if "%SKILL%"=="uml" (
    set SCRIPT_NAME=uml_generator_skill.py
    if "%COMMAND%"=="" set COMMAND=architecture
)

if "%SKILL%"=="fix" (
    set SCRIPT_NAME=code_enhancement_skill.py
    if "%COMMAND%"=="" set COMMAND=full-report
)

if "%SKILL%"=="query" (
    set SCRIPT_NAME=code_intelligence_skill.py
    if "%COMMAND%"=="" set COMMAND=system overview
)

if not defined SCRIPT_NAME (
    echo Error: Unknown skill '%SKILL%'
    echo Available skills: doc, uml, fix, query
    goto :eof
)

echo Running %SKILL% skill with command: %COMMAND%
echo Repository: %REPO_PATH%
echo.

if "%OUTPUT_FILE%"=="" (
    REM Output to console
    python "%SKILLS_PATH%\%SCRIPT_NAME%" "%REPO_PATH%" %COMMAND%
) else (
    REM Output to file with UTF-8 encoding
    python "%SKILLS_PATH%\%SCRIPT_NAME%" "%REPO_PATH%" %COMMAND% > "%OUTPUT_FILE%" 2>&1
    echo.
    echo Output saved to: %OUTPUT_FILE%
    echo File size: 
    for %%F in ("%OUTPUT_FILE%") do echo   %%~zF bytes
)

echo.
echo Done!