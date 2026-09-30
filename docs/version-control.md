# Version control and portfolio evidence

Repository: [Anikethupadhya/retail-sales-forecasting-analytics](https://github.com/Anikethupadhya/retail-sales-forecasting-analytics).

The repository was created private. Changing its visibility to public later preserves the existing commits, their dates, messages, and file changes. Public visibility lets employers inspect that history. A private repository link is accessible only to people granted access.

## What the first commit means

The first Git commit imports the completed and verified project. It does not reconstruct a development timeline from before Git was used. Earlier benchmark artifacts and the saved implementation checkpoint are included under `archives/`, with checksums and their historical limitations documented. They are evidence of earlier project states, not earlier Git commits.

New commits should record real changes when they happen. Commit count alone does not establish authorship, skill, or model quality. Useful portfolio evidence includes readable changes, reproducible results, tests, screenshots, and an explanation of the decisions and limitations.

## Save each meaningful improvement

From the project folder in PowerShell:

```powershell
git status
git diff
# Run the checks appropriate to the change before committing.
git add -- <changed-files>
git diff --cached
git commit -m "Describe the change and its purpose"
git push
```

A commit saves a version locally. A successful push copies the commits to GitHub. Uncommitted changes and ignored files are not included in that backup. Use an explicit file list when staging and inspect the staged diff.

Examples of worthwhile future commits are a prespecified training-window experiment, a fix for an observed data edge case, a dashboard usability improvement, or a verified explanation of a result. Group related changes together; keep commit dates truthful and avoid empty commits or arbitrary file splitting to inflate the count.

## Backup scope and integrity

Git includes the source, SQL, frozen protocol, immutable historical archives, customer-free aggregates and predictions, reports, screenshots, and saved verification evidence. The raw workbook and customer-level extracts, environments, caches, generated database, credentials, and review bundles are ignored. The README explains how to acquire the official workbook and reproduce the project.

`.gitattributes` preserves exact file bytes, including line endings, because the archive and protocol manifests contain SHA-256 checksums. Do not rewrite the immutable archives. Commit attribution uses the account's GitHub no-reply email address.

To check the local version and remote backup:

```powershell
git log --oneline -5
git status --short --branch
git remote -v
git rev-parse HEAD
git ls-remote origin refs/heads/main
```

After a successful push, the local `HEAD` and remote `main` hashes should agree. A clean working tree means there are no outstanding tracked or untracked changes; ignored local files can still exist.

## Before sharing on a resume

Make the repository public when the project is ready to share, then verify the README and evidence links as a visitor. Review the entire history before changing visibility, because earlier committed files also become visible. Put the repository link next to the project on the resume and be prepared to explain the forecasting comparison, ingestion correction, and retrospective limitations.

GitHub also supports showing anonymized private contribution counts before publication. Commit attribution and contribution-graph credit depend on GitHub's email and branch rules; the repository's own commit history is the direct record of file changes.

References: [repository visibility](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility), [commit dates and contribution rules](https://docs.github.com/en/account-and-profile/reference/profile-contributions-reference), [private contribution visibility](https://docs.github.com/en/account-and-profile/how-tos/contribution-settings/manage-visibility-settings-for-private-contributions-and-achievements).
