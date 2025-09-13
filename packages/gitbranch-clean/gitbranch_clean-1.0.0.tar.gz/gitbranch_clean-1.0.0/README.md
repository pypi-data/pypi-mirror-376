# git-branch-cleaner

Delete merged git branches. That's it.

## Installation

```bash
pip install git-branch-cleaner
```

## Usage

Delete local branches merged to main and older than 30 days:
```bash
branch-cleaner
```

Delete branches older than 7 days:
```bash
branch-cleaner --days 7
```

See what would be deleted without actually deleting:
```bash
branch-cleaner --dry-run
```

Include remote branches:
```bash
branch-cleaner --remote
```

Use a different base branch:
```bash
branch-cleaner --base develop
```

## Protected Branches

The following branches are protected and will never be deleted:
- main
- master  
- develop
- dev
- staging
- production

## License

MIT