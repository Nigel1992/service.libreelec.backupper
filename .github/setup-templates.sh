#!/bin/bash
# LibreELEC Backupper - GitHub Templates Setup Script
# This script helps set up GitHub templates using GitHub CLI

# Set colors
GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}GitHub CLI not found. Please install GitHub CLI from https://cli.github.com/${NC}"
    exit 1
else
    GH_VERSION=$(gh --version | head -n 1)
    echo -e "${GREEN}GitHub CLI detected: $GH_VERSION${NC}"
fi

# Check if user is authenticated with GitHub
if ! gh auth status &> /dev/null; then
    echo -e "${RED}Not authenticated with GitHub. Please run 'gh auth login' first.${NC}"
    exit 1
else
    echo -e "${GREEN}GitHub authentication verified.${NC}"
fi

# Get repository information
REPO_NAME=$(gh repo view --json nameWithOwner -q .nameWithOwner)

echo -e "${CYAN}Setting up templates for repository: $REPO_NAME${NC}"

# Function to create a wiki page from template
create_wiki_page() {
    local template_path=$1
    local wiki_page_name=$2
    
    if [ -f "$template_path" ]; then
        # Create a temporary file with the content
        local temp_file=$(mktemp)
        cat "$template_path" > "$temp_file"
        
        # Use GitHub CLI to create/update the wiki page
        echo -e "${YELLOW}Creating/updating wiki page: $wiki_page_name${NC}"
        gh api --method PUT "repos/$REPO_NAME/wiki/$wiki_page_name" -F content=@"$temp_file"
        
        # Clean up
        rm "$temp_file"
        
        echo -e "${GREEN}Wiki page '$wiki_page_name' created/updated successfully.${NC}"
    else
        echo -e "${RED}Template file not found: $template_path${NC}"
    fi
}

# Setup issue templates
echo -e "\n${CYAN}Setting up issue templates...${NC}"
ISSUE_TEMPLATE_DIR=".github/ISSUE_TEMPLATE"
if [ -d "$ISSUE_TEMPLATE_DIR" ]; then
    echo -e "${GREEN}Issue templates are already set up in $ISSUE_TEMPLATE_DIR${NC}"
else
    echo -e "${RED}Issue template directory not found. Please run this script from the repository root.${NC}"
fi

# Setup pull request templates
echo -e "\n${CYAN}Setting up pull request templates...${NC}"
PR_TEMPLATE_DIR=".github/PULL_REQUEST_TEMPLATE"
if [ -d "$PR_TEMPLATE_DIR" ]; then
    echo -e "${GREEN}Pull request templates are already set up in $PR_TEMPLATE_DIR${NC}"
else
    echo -e "${RED}Pull request template directory not found. Please run this script from the repository root.${NC}"
fi

# Setup wiki templates
echo -e "\n${CYAN}Would you like to set up wiki pages from templates? (y/n)${NC}"
read -r SETUP_WIKI
if [ "$SETUP_WIKI" = "y" ]; then
    WIKI_TEMPLATE_DIR=".github/wiki-templates"
    if [ -d "$WIKI_TEMPLATE_DIR" ]; then
        # Create Home page
        create_wiki_page "$WIKI_TEMPLATE_DIR/home.md" "Home"
        
        # Create Feature Documentation page
        create_wiki_page "$WIKI_TEMPLATE_DIR/feature_documentation.md" "Feature-Documentation-Template"
        
        # Create Installation Guide page
        create_wiki_page "$WIKI_TEMPLATE_DIR/installation_guide.md" "Installation-Guide-Template"
        
        # Create Troubleshooting Guide page
        create_wiki_page "$WIKI_TEMPLATE_DIR/troubleshooting_guide.md" "Troubleshooting-Guide-Template"
        
        echo -e "\n${GREEN}Wiki pages have been created/updated from templates.${NC}"
        echo -e "${CYAN}You can view them at: https://github.com/$REPO_NAME/wiki${NC}"
    else
        echo -e "${RED}Wiki template directory not found. Please run this script from the repository root.${NC}"
    fi
fi

echo -e "\n${GREEN}Template setup complete!${NC}"
echo -e "${CYAN}You can now use these templates for issues, pull requests, and wiki pages.${NC}"
echo -e "${CYAN}For more information, see .github/README.md${NC}" 