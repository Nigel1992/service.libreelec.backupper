# LibreELEC Backupper - GitHub Templates Setup Script
# This script helps set up GitHub templates using GitHub CLI

# Check if GitHub CLI is installed
try {
    $ghVersion = gh --version
    Write-Host "GitHub CLI detected: $ghVersion" -ForegroundColor Green
}
catch {
    Write-Host "GitHub CLI not found. Please install GitHub CLI from https://cli.github.com/" -ForegroundColor Red
    exit 1
}

# Check if user is authenticated with GitHub
try {
    $status = gh auth status
    Write-Host "GitHub authentication verified." -ForegroundColor Green
}
catch {
    Write-Host "Not authenticated with GitHub. Please run 'gh auth login' first." -ForegroundColor Red
    exit 1
}

# Get repository information
$repoInfo = gh repo view --json nameWithOwner
$repoName = ($repoInfo | ConvertFrom-Json).nameWithOwner

Write-Host "Setting up templates for repository: $repoName" -ForegroundColor Cyan

# Function to create a wiki page from template
function Create-WikiPage {
    param (
        [string]$templatePath,
        [string]$wikiPageName
    )
    
    if (Test-Path $templatePath) {
        $content = Get-Content -Path $templatePath -Raw
        
        # Create a temporary file with the content
        $tempFile = [System.IO.Path]::GetTempFileName()
        Set-Content -Path $tempFile -Value $content
        
        # Use GitHub CLI to create/update the wiki page
        Write-Host "Creating/updating wiki page: $wikiPageName" -ForegroundColor Yellow
        gh api --method PUT "repos/$repoName/wiki/$wikiPageName" -F content=@"$tempFile"
        
        # Clean up
        Remove-Item $tempFile
        
        Write-Host "Wiki page '$wikiPageName' created/updated successfully." -ForegroundColor Green
    }
    else {
        Write-Host "Template file not found: $templatePath" -ForegroundColor Red
    }
}

# Setup issue templates
Write-Host "`nSetting up issue templates..." -ForegroundColor Cyan
$issueTemplateDir = ".github/ISSUE_TEMPLATE"
if (Test-Path $issueTemplateDir) {
    Write-Host "Issue templates are already set up in $issueTemplateDir" -ForegroundColor Green
}
else {
    Write-Host "Issue template directory not found. Please run this script from the repository root." -ForegroundColor Red
}

# Setup pull request templates
Write-Host "`nSetting up pull request templates..." -ForegroundColor Cyan
$prTemplateDir = ".github/PULL_REQUEST_TEMPLATE"
if (Test-Path $prTemplateDir) {
    Write-Host "Pull request templates are already set up in $prTemplateDir" -ForegroundColor Green
}
else {
    Write-Host "Pull request template directory not found. Please run this script from the repository root." -ForegroundColor Red
}

# Setup wiki templates
Write-Host "`nWould you like to set up wiki pages from templates? (y/n)" -ForegroundColor Cyan
$setupWiki = Read-Host
if ($setupWiki -eq "y") {
    $wikiTemplateDir = ".github/wiki-templates"
    if (Test-Path $wikiTemplateDir) {
        # Create Home page
        Create-WikiPage -templatePath "$wikiTemplateDir/home.md" -wikiPageName "Home"
        
        # Create Feature Documentation page
        Create-WikiPage -templatePath "$wikiTemplateDir/feature_documentation.md" -wikiPageName "Feature-Documentation-Template"
        
        # Create Installation Guide page
        Create-WikiPage -templatePath "$wikiTemplateDir/installation_guide.md" -wikiPageName "Installation-Guide-Template"
        
        # Create Troubleshooting Guide page
        Create-WikiPage -templatePath "$wikiTemplateDir/troubleshooting_guide.md" -wikiPageName "Troubleshooting-Guide-Template"
        
        Write-Host "`nWiki pages have been created/updated from templates." -ForegroundColor Green
        Write-Host "You can view them at: https://github.com/$repoName/wiki" -ForegroundColor Cyan
    }
    else {
        Write-Host "Wiki template directory not found. Please run this script from the repository root." -ForegroundColor Red
    }
}

Write-Host "`nTemplate setup complete!" -ForegroundColor Green
Write-Host "You can now use these templates for issues, pull requests, and wiki pages." -ForegroundColor Cyan
Write-Host "For more information, see .github/README.md" -ForegroundColor Cyan 