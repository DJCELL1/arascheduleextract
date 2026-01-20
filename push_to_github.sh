#!/bin/bash
# Instructions:
# 1. Create a new repository on GitHub (https://github.com/new)
# 2. Copy the repository URL (should be like: https://github.com/yourusername/repo-name.git)
# 3. Replace YOUR_REPO_URL below with your actual repository URL
# 4. Run: bash push_to_github.sh

REPO_URL="YOUR_REPO_URL"  # Replace this with your GitHub repository URL

cd "C:\Users\selwy\OneDrive\Desktop\PROJECTS HDL\Extract"

# Add remote
git remote add origin "$REPO_URL"

# Push to GitHub
git branch -M main
git push -u origin main

echo "Successfully pushed to GitHub!"
echo "Your app is now at: $REPO_URL"
