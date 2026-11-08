"""Create the GitHub Release of a version tag. Run by .github/workflows/release.yml.

The owner picks the version and pushes an annotated tag on a commit of main
(.claude/rules/releases.md):

    git tag -a v1.2.0 -m "Short summary of the release"
    git push origin v1.2.0

This script then checks the tag and creates the release; the site's Releases
page shows it after the next deployment (pages.yml runs when release.yml ends).

- The tag must be vMAJOR.MINOR.PATCH (Semantic Versioning, no pre-release or
  build part) and point at a commit that is on main; otherwise nothing is
  created and the run fails.
- A lightweight tag works but gives a warning: an annotated tag records who
  tagged it, when, and a message.
- If the tag already has a release, it is left as it is (the release history is
  never changed) and the run succeeds.
- The release is named after the tag. Its notes are the tag's message followed
  by the notes GitHub generates from the merged pull requests since the
  previous release. No AI writes or edits them.

Usage: python3 tools/release.py <tag>   (GITHUB_TOKEN with contents: write)
"""

import os
import re
import subprocess
import sys

import github_api

# vMAJOR.MINOR.PATCH, numbers without leading zeros (semver.org, item 2).
# Matched with fullmatch(), so a trailing newline does not pass.
VERSION_TAG = re.compile(r"v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)")
# The branch every release must come from.
RELEASE_BRANCH = "origin/main"


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def git_ok(*args):
    return subprocess.run(["git", *args], capture_output=True).returncode == 0


def warn(text):
    """A warning that GitHub Actions shows on the run."""
    print(f"::warning::{text}")


def check_tag(tag):
    """The commit SHA the tag points at. Raises ValueError when the tag may not be released."""
    if not VERSION_TAG.fullmatch(tag):
        raise ValueError(f"{tag!r} is not a version tag like v1.2.0")
    if not git_ok("rev-parse", "--verify", "--quiet", f"refs/tags/{tag}"):
        raise ValueError(f"tag {tag} not found")
    sha = git("rev-parse", f"refs/tags/{tag}^{{commit}}").strip()
    if not git_ok("merge-base", "--is-ancestor", sha, RELEASE_BRANCH):
        raise ValueError(f"{tag} points at {sha[:7]}, which is not on {RELEASE_BRANCH}")
    if git("cat-file", "-t", f"refs/tags/{tag}").strip() != "tag":
        warn(f"{tag} is a lightweight tag; use an annotated tag (git tag -a) next time")
    return sha


def tag_message(tag):
    """The message of an annotated tag (subject and body, no signature), or ""."""
    if git("cat-file", "-t", f"refs/tags/{tag}").strip() != "tag":
        return ""
    subject = git("for-each-ref", "--format=%(contents:subject)", f"refs/tags/{tag}").strip()
    body = git("for-each-ref", "--format=%(contents:body)", f"refs/tags/{tag}").strip()
    return "\n\n".join(p for p in (subject, body) if p)


def release_exists(tag):
    try:
        github_api.request("GET", github_api.repo_path(f"/releases/tags/{tag}"))
    except github_api.ApiError as e:
        if e.status == 404:
            return False
        raise
    return True


def create(tag, sha):
    _, _, generated = github_api.request(
        "POST",
        github_api.repo_path("/releases/generate-notes"),
        body={"tag_name": tag, "target_commitish": sha},
    )
    generated = generated.get("body") if isinstance(generated, dict) else None
    notes = "\n\n".join(p for p in (tag_message(tag), generated or "") if p.strip())
    _, _, made = github_api.request(
        "POST",
        github_api.repo_path("/releases"),
        body={"tag_name": tag, "name": tag, "body": notes, "draft": False, "prerelease": False},
    )
    return made.get("html_url") if isinstance(made, dict) else None


def summary(text):
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    print(text)
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(text + "\n")


def main(argv):
    if len(argv) != 2:
        print("usage: release.py <tag>", file=sys.stderr)
        return 2
    tag = argv[1]
    try:
        sha = check_tag(tag)
        if release_exists(tag):
            summary(f"{tag} already has a release; it was left as it is.")
            return 0
        url = create(tag, sha)
    except (ValueError, subprocess.CalledProcessError, github_api.ApiError) as e:
        print(f"::error::release {tag}: {e}")
        return 1
    summary(f"Released {tag} ({sha[:7]}): {url or 'created'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
