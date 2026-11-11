# Issue tracker: GitHub

Issues and specs for this repo live as GitHub issues. Use the `gh` CLI for all operations.

## Conventions

- **Create an issue**: `gh issue create --title "..." --body "..."`. Use a heredoc for multi-line bodies.
- **Read an issue**: `gh issue view <number> --json number,title,body,labels,comments`.
- **List issues**: `gh issue list --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` with appropriate `--label` and `--state` filters.
- **Make an issue a sub-issue of a parent**: `gh issue create --parent <parent> ...`, or `gh issue edit <parent> --add-sub-issue <child>` afterwards (`gh` 2.94+). Older `gh`: `gh api --method POST repos/<owner>/<repo>/issues/<parent>/sub_issues -F sub_issue_id=<child-db-id>` (database id, as in **Blocking** below). Without sub-issues, put `Part of #<parent>` at the top of the child body.
- **Check sub-issues and open blockers** (the ticket-pick rule in `CLAUDE.md`): `gh api repos/duncan-wen/ai-news-mcp/issues/<n> --jq '{sub_issues: .sub_issues_summary.total, open_blockers: .issue_dependencies_summary.blocked_by}'`. Both 0: the issue is neither a spec nor blocked.
- **Comment on an issue**: `gh issue comment <number> --body "..."`
- **Apply / remove labels**: `gh issue edit <number> --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --comment "..."`
- **Record an open decision**: when implementing forces behaviour the issue doesn't settle (for example, a case that an old failure path used to cover), post it as a comment headed `## Decisions` (`gh issue comment <number>`) before the review starts, and name it in the final report. A decision made while fixing review findings is appended to the same comment. `--edit-last` replaces the whole body, so resend the old body with the new bullets: `body=$(gh api repos/duncan-wen/ai-news-mcp/issues/comments/<comment-id> --jq .body)`, then `gh issue comment <number> --edit-last --body "$body
- <new decision>"`. The comment id ends the URL that `gh issue comment` printed (`#issuecomment-<comment-id>`). The Spec reviewer reads issue comments, so it judges the decision instead of flagging it as scope creep.

Infer the repo from `git remote -v`; `gh` does this automatically when run inside a clone.

## Pull requests as a triage surface

**PRs as a request surface: no.** _(Set to `yes` if this repo treats external PRs as feature requests; `/triage` reads this flag.)_

When set to `yes`, PRs run through the same labels and states as issues, using the `gh pr` equivalents:

- **Read a PR**: `gh pr view <number> --comments` and `gh pr diff <number>` for the diff.
- **List external PRs for triage**: `gh api --paginate 'repos/{owner}/{repo}/pulls?state=open' --jq '.[] | select(.author_association | IN("OWNER","MEMBER","COLLABORATOR") | not) | {number, title, author: .user.login, author_association, labels: [.labels[].name]}'`.
- **Comment / label / close**: `gh pr comment`, `gh pr edit --add-label`/`--remove-label`, `gh pr close`.

GitHub shares one number space across issues and PRs, so a bare `#42` may be either: resolve with `gh pr view 42` and fall back to `gh issue view 42`.

## Waiting on CI and Dependabot

- **Wait on CI**: `gh pr checks <n> --watch` for a PR, `gh run watch <run-id> --exit-status` for a run. A check still running reports an empty `conclusion`, so a hand-written poll that reads `.conclusion // .status` stops early.
- **Just pushed**: checks take a few seconds to register, and `--watch` exits at once with "no checks reported" until they do. Retry it until it lists them.
- **A job that a skipped job feeds**: give its `if:` a status function (`!cancelled() && !failure() && ...`). Without one, the job skips whenever a job in its `needs` chain skipped (publish.yml's `download`).
- **Merge as each turns green**: Dependabot PRs are independent; merge each when its checks pass rather than waiting on the batch.
- **Stale base**: `@dependabot rebase` sometimes goes unanswered. Dependabot rebases its open PRs by itself once `main` changes, so merging another PR first usually unsticks it; `@dependabot recreate` is the fallback.

## When a skill says "publish to the issue tracker"

Create a GitHub issue.

## When a skill says "fetch the relevant ticket"

Read it as in **Read an issue** above.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a single issue with **child** issues as tickets.

- **Map**: a single issue labelled `wayfinder:map`, holding the Notes / Decisions-so-far / Fog body. `gh issue create --label wayfinder:map`.
- **Child ticket**: an issue linked to the map as a GitHub sub-issue (see **Make an issue a sub-issue of a parent**). Where sub-issues aren't enabled, add the child to a task list in the map body and put `Part of #<map>` at the top of the child body. Labels: `wayfinder:<type>` (`research`/`prototype`/`grilling`/`task`). Once claimed, the ticket is assigned to the driving dev.
- **Blocking**: GitHub's **native issue dependencies**, the canonical, UI-visible representation. Add an edge with `gh api --method POST repos/<owner>/<repo>/issues/<child>/dependencies/blocked_by -F issue_id=<blocker-db-id>`, where `<blocker-db-id>` is the blocker's numeric **database id** (`gh api repos/<owner>/<repo>/issues/<n> --jq .id`, _not_ the `#number` or `node_id`). GitHub reports `issue_dependencies_summary.blocked_by` (open blockers only, the live gate). Where dependencies aren't available, fall back to a `Blocked by: #<n>, #<n>` line at the top of the child body. A ticket is unblocked when every blocker is closed.
- **Frontier query**: list the map's open children (`gh issue list --state open`, scoped to the map's sub-issues / task list), drop any with an open blocker (`issue_dependencies_summary.blocked_by > 0`, or an open issue in the `Blocked by` line) or an assignee; first in map order wins.
- **Claim**: `gh issue edit <n> --add-assignee @me`, the session's first write.
- **Resolve**: `gh issue comment <n> --body "<answer>"`, then `gh issue close <n>`, then append a context pointer (gist + link) to the map's Decisions-so-far.
