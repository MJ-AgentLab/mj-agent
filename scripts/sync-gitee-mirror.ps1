#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Fast-forward the gitee mirror of a base branch (default: develop) to match origin.

.DESCRIPTION
  gitee is a PASSIVE redundancy mirror. The current CI (GitHub-hosted `actions/checkout`)
  reads origin (GitHub), NOT gitee. GitHub PR merges advance origin/<branch> only, so
  gitee/<branch> lags after every merge. This script keeps the mirror consistent
  (redundancy + a possible future in-country CI that pulls gitee, per
  docs/infrastructure/git/[GUIDE]_Git_Push_Workflow.md sec 6.5).

  Guarded:
    - no-op (exit 0) when the mirror is already in sync;
    - fast-forward ONLY: pushes origin/<branch> -> gitee/<branch>, never with --force;
    - refuses (exit 3) if gitee/<branch> has diverged (is not an ancestor of
      origin/<branch>), leaving it for a human to resolve.

  Intended for the /mj-agent-flow-post-merge Step 8 develop-sync step. Operates on refs, so
  it is safe to run from any worktree; it never touches a working tree.

  Exit codes: 0 ok/in-sync | 2 missing remote | 3 diverged (non-ff) | 4 fetch failed |
  5 push failed.

.EXAMPLE
  pwsh scripts/sync-gitee-mirror.ps1

.EXAMPLE
  pwsh scripts/sync-gitee-mirror.ps1 -Branch develop -Remote gitee -Source origin
#>
[CmdletBinding()]
param(
    [string]$Branch = "develop",
    [string]$Remote = "gitee",
    [string]$Source = "origin"
)

$ErrorActionPreference = "Stop"

function Fail([string]$Message, [int]$Code) {
    Write-Error $Message
    exit $Code
}

# 1. Both remotes must exist.
$remotes = @(git remote)
if ($remotes -notcontains $Remote) { Fail "remote '$Remote' not configured (see: git remote -v)" 2 }
if ($remotes -notcontains $Source) { Fail "remote '$Source' not configured (see: git remote -v)" 2 }

# 2. Refresh both refs.
git fetch $Source $Branch --quiet
if ($LASTEXITCODE -ne 0) { Fail "git fetch $Source $Branch failed" 4 }
git fetch $Remote $Branch --quiet
if ($LASTEXITCODE -ne 0) { Fail "git fetch $Remote $Branch failed" 4 }

# 3. Resolve commits.
$src = (git rev-parse "$Source/$Branch").Trim()
$mir = (git rev-parse "$Remote/$Branch").Trim()
$srcShort = $src.Substring(0, 7)
$mirShort = $mir.Substring(0, 7)

if ($src -eq $mir) {
    Write-Host "OK: $Remote/$Branch already in sync with $Source/$Branch ($srcShort) - nothing to push."
    exit 0
}

# 4. Fast-forward safety: the mirror commit must be an ancestor of the source commit.
git merge-base --is-ancestor $mir $src
if ($LASTEXITCODE -ne 0) {
    Fail "DIVERGED: $Remote/$Branch ($mirShort) is not an ancestor of $Source/$Branch ($srcShort). Refusing non-fast-forward push - resolve manually." 3
}

# 5. Fast-forward the mirror: push the source commit onto the mirror branch (no --force).
$lag = (git rev-list --count "$Remote/$Branch..$Source/$Branch").Trim()
Write-Host "$Remote/$Branch is behind $Source/$Branch by $lag commit(s); fast-forwarding $mirShort -> $srcShort ..."
git push $Remote "$Source/${Branch}:refs/heads/$Branch"
if ($LASTEXITCODE -ne 0) { Fail "git push $Remote failed" 5 }
Write-Host "OK: $Remote/$Branch fast-forwarded to $srcShort."
exit 0
