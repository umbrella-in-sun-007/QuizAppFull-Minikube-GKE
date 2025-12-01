# Git Repository Migration Guide

This guide documents the steps to migrate an existing local repository to a new remote repository (e.g., moving from `QuizAppFull` to `QuizAppFull-private-repo`).

## 1. Check Current Remotes
First, verify the current remote configuration.

```bash
git remote -v
# Output example:
# origin  https://github.com/neerajadhav/QuizAppFull.git (fetch)
# origin  https://github.com/neerajadhav/QuizAppFull.git (push)
```

## 2. Change Remote URL
To point the local repository to the new remote repository URL.

```bash
# Set the new URL for 'origin'
git remote set-url origin https://github.com/neerajadhav/QuizAppFull-private-repo.git

# Verify the change
git remote -v
```

## 3. Rename Branch (Optional)
If you need to rename the default branch (e.g., from `master` to `main`).

```bash
git branch -m master main
```

## 4. Push to New Remote
Push the local branches to the new remote repository.

```bash
# Push the 'main' branch and set the upstream tracking
git push -u origin main
```

## 5. Troubleshooting
If you encounter errors like "refusing to merge unrelated histories" (if the new repo was initialized with a README/License):

```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```
