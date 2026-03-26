# Git hooks for local quality gate

Enable hooks for this repository:

```bash
git config core.hooksPath .githooks
```

After enabling, every `git push` will run backend tests via `.githooks/pre-push`.
If tests fail, push is blocked.
