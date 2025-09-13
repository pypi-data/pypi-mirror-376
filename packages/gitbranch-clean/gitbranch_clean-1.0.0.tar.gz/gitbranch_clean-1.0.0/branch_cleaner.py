#!/usr/bin/env python3
"""
Delete merged git branches. That's it.
"""
import subprocess
import argparse
from datetime import datetime, timedelta
import sys

PROTECTED = {'main', 'master', 'develop', 'dev', 'staging', 'production'}

def run_git(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except:
        return ""

def get_branches(remote=False):
    if remote:
        branches = run_git("git branch -r").split('\n')
        return [b.strip().replace('origin/', '') for b in branches 
                if b.strip() and '->' not in b]
    else:
        branches = run_git("git branch").split('\n')
        return [b.strip().replace('* ', '') for b in branches if b.strip()]

def is_merged(branch, base='main'):
    merged = run_git(f"git branch --merged {base}").split('\n')
    merged = [b.strip().replace('* ', '') for b in merged]
    return branch in merged

def get_age_days(branch):
    timestamp = run_git(f"git log -1 --format=%ct {branch}")
    if timestamp:
        commit_date = datetime.fromtimestamp(int(timestamp))
        age = datetime.now() - commit_date
        return age.days
    return 0

def delete_branch(branch, remote=False, dry_run=False):
    if branch.lower() in PROTECTED:
        print(f"⚠️  Skipping protected branch: {branch}")
        return False
    
    if dry_run:
        print(f"[DRY RUN] Would delete: {branch}")
        return True
    
    if remote:
        result = run_git(f"git push origin --delete {branch}")
        print(f"Deleted remote branch: {branch}")
    else:
        result = run_git(f"git branch -D {branch}")
        print(f"Deleted local branch: {branch}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Delete merged git branches")
    parser.add_argument("--days", type=int, default=30, 
                       help="Delete branches older than N days")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be deleted")
    parser.add_argument("--remote", action="store_true",
                       help="Include remote branches")
    parser.add_argument("--base", default="main",
                       help="Base branch to check merges against")
    
    args = parser.parse_args()
    
    branches = get_branches(args.remote)
    deleted = 0
    
    for branch in branches:
        if branch == args.base or branch in PROTECTED:
            continue
            
        if is_merged(branch, args.base):
            age = get_age_days(branch)
            if age > args.days:
                if delete_branch(branch, args.remote, args.dry_run):
                    deleted += 1
    
    print(f"\n{'Would delete' if args.dry_run else 'Deleted'}: {deleted} branches")

if __name__ == "__main__":
    main()