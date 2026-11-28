"""Report the checks of a pull request in one comment on it, group by group.

The owner's request (2026-11-28): the pull request gets one comment that says
"1. ... done", "2. ... done" and so on as each group of checks ends. The groups
are the ones the owner chose (A to D of "A code checks, B build and content
checks, C browser checks, D publishing, E watching the live site"); E runs on a
schedule, never on a pull request, so it has no line here.

`.github/workflows/progress.yml` runs this when `site.yml` starts for a pull
request from this repository. It reads only what the other workflows publish
through the API (the names and results of their jobs and steps, and the preview
comment of `previews.yml`), never their files, and writes only its own comment
(marked COMMENT_MARKER). It runs from the default branch: no pull request code.

Environment: GITHUB_TOKEN (actions: read, pull-requests: write), PR_NUMBER,
HEAD_SHA and SITE_RUN_ID (from the workflow_run event).
"""

import calendar
import os
import re
import sys
import time

import github_api
from github_api import ApiError, repo_path

COMMENT_MARKER = "<!-- progress-bot -->"
# The preview comment of research-aide's cloudflare-previews.yml names the
# commit it shows as "from commit <first 7 characters>".
PREVIEW_MARKER = "<!-- preview-bot -->"
SHORT_SHA = 7

BROWSERS_WORKFLOW = "browsers.yml"
# Jobs of quality.yml, as site.yml calls it ("quality / prettier", ...).
QUALITY_JOB_PREFIX = "quality / "
# The job of site.yml that builds the site, and its steps for each group.
BUILD_JOB = "build"
BUILD_STEPS = ("Build and check the site", "Validate the built pages")
BROWSER_STEPS = ("Check the map view", "Try the release ZIP builder")
PREVIEW_STEPS = (
    "Make the preview (all but the record pages of other families)",
    "Upload the preview",
)

# Seconds between two looks at the runs: about three requests each time, well
# under the 1,000 requests an hour a workflow token may send.
POLL_S = 60
# Seconds to wait for the preview comment after site.yml passed, before the
# preview counts as failed (previews.yml usually links it within a few minutes).
PREVIEW_WAIT_S = 20 * 60

DONE, FAILED, NOT_RUN, RUNNING = "done", "failed", "not run", "running"
FINAL = (DONE, FAILED, NOT_RUN)

# The groups, in the owner's order; the number is the position.
GROUPS = (
    "Code checks",
    "Build and content checks",
    "Browser checks",
    "Publishing the preview",
)

SHA_RE = re.compile(r"[0-9a-f]{40}")


def item_state(item):
    """The state of one job, step or run ({"status", "conclusion"}), or RUNNING if missing."""
    if not isinstance(item, dict) or item.get("status") != "completed":
        return RUNNING
    conclusion = item.get("conclusion")
    if conclusion == "success":
        return DONE
    if conclusion == "skipped":
        return NOT_RUN
    return FAILED


def group_state(items):
    """One state for a group: failed if any item failed, running until all ended."""
    if not items:
        return RUNNING
    return combine(*[item_state(i) for i in items])


def steps_of(job, names):
    """The steps of `job` with these names, in that order (None for a missing one)."""
    steps = job.get("steps") if isinstance(job, dict) else None
    by_name = {s.get("name"): s for s in steps or [] if isinstance(s, dict)}
    return [by_name.get(n) for n in names]


def states(site_run, site_jobs, browsers_run, preview_linked, now):
    """The state of each group, in the order of GROUPS.

    `preview_linked` is whether the preview comment names this commit; `now` is
    the time in seconds, to give up waiting for it after PREVIEW_WAIT_S.
    """
    jobs = [j for j in site_jobs if isinstance(j, dict)]
    quality = [j for j in jobs if str(j.get("name", "")).startswith(QUALITY_JOB_PREFIX)]
    build = next((j for j in jobs if j.get("name") == BUILD_JOB), None)
    site_ended = item_state(site_run) != RUNNING
    a = _settled(group_state(quality), site_ended)
    if build is None:
        # The build job appears once the code checks pass; it never runs if they failed.
        b = c_build = d_build = NOT_RUN if a in (FAILED, NOT_RUN) or site_ended else RUNNING
    else:
        b = _settled(group_state(steps_of(build, BUILD_STEPS)), site_ended)
        c_build = _settled(group_state(steps_of(build, BROWSER_STEPS)), site_ended)
        d_build = _settled(group_state(steps_of(build, PREVIEW_STEPS)), site_ended)
    c = combine(c_build, item_state(browsers_run))
    d = d_build
    if d_build == DONE and not preview_linked:
        waited = now - _ended(site_run)
        if item_state(site_run) == FAILED or (site_ended and waited > PREVIEW_WAIT_S):
            d = FAILED
        else:
            d = RUNNING
    return [a, b, c, d]


def _settled(state, site_ended):
    """A group of site.yml still running when site.yml has ended lost a job or a step
    (renamed or removed): report it as failed rather than wait for ever."""
    return FAILED if state == RUNNING and site_ended else state


def combine(*group_states):
    """One state for several parts: failed, then running, then not run, else done."""
    for state in (FAILED, RUNNING, NOT_RUN):
        if state in group_states:
            return state
    return DONE


def _ended(run):
    """When a run ended, in seconds since the epoch (its updated_at)."""
    stamp = run.get("updated_at") if isinstance(run, dict) else None
    try:
        return calendar.timegm(time.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ"))
    except (TypeError, ValueError):
        return 0


def render(sha, group_states, run_url):
    """The comment: one line per group that has ended, in order, as they end."""
    lines = [COMMENT_MARKER, "### Checks", "", f"Commit {sha[:SHORT_SHA]} ([runs]({run_url})):", ""]
    for number, (name, state) in enumerate(zip(GROUPS, group_states, strict=True), start=1):
        if state in FINAL:
            lines.append(f"{number}. {name}: {state}")
    if all(s in FINAL for s in group_states):
        lines += ["", "All groups have ended."]
    return "\n".join(lines) + "\n"


def finished(group_states):
    return all(s in FINAL for s in group_states)


def preview_names(comments, sha):
    """Whether the preview comment shows this commit."""
    words = f"from commit {sha[:SHORT_SHA]}"
    return any(
        isinstance(c, dict)
        and str(c.get("body", "")).startswith(PREVIEW_MARKER)
        and words in str(c.get("body", ""))
        for c in comments
    )


def own_comment(comments):
    return next(
        (
            c
            for c in comments
            if isinstance(c, dict) and str(c.get("body", "")).startswith(COMMENT_MARKER)
        ),
        None,
    )


def _get(path):
    _, _, data = github_api.request("GET", path)
    if not isinstance(data, dict):
        raise ApiError(f"GET {path}: expected an object")
    return data


def look(number, sha, run_id):
    """Read the runs and comments once; returns (site run, group states, comments)."""
    site_run = _get(repo_path(f"/actions/runs/{run_id}"))
    jobs = _get(repo_path(f"/actions/runs/{run_id}/jobs?per_page=100")).get("jobs") or []
    found = _get(
        repo_path(f"/actions/workflows/{BROWSERS_WORKFLOW}/runs?event=pull_request&head_sha={sha}")
    ).get("workflow_runs")
    browsers_run = found[0] if isinstance(found, list) and found else None
    comments = github_api.get_all(repo_path(f"/issues/{number}/comments"))
    linked = preview_names(comments, sha)
    return site_run, states(site_run, jobs, browsers_run, linked, time.time()), comments


def write(number, comments, body):
    old = own_comment(comments)
    if old is None:
        github_api.request("POST", repo_path(f"/issues/{number}/comments"), body={"body": body})
    elif old.get("body") != body:
        github_api.request("PATCH", repo_path(f"/issues/comments/{old['id']}"), body={"body": body})


def main():
    number = os.environ.get("PR_NUMBER", "")
    sha = os.environ.get("HEAD_SHA", "")
    run_id = os.environ.get("SITE_RUN_ID", "")
    if not (number.isdigit() and run_id.isdigit() and SHA_RE.fullmatch(sha)):
        sys.exit("PR_NUMBER, HEAD_SHA and SITE_RUN_ID must be set")
    pull = _get(repo_path(f"/pulls/{number}"))
    if (pull.get("head") or {}).get("sha") != sha or pull.get("state") != "open":
        print(f"{sha} is not the latest commit of open pull request {number}; nothing to report")
        return
    while True:
        site_run, group_states, comments = look(number, sha, run_id)
        write(number, comments, render(sha, group_states, site_run.get("html_url", "")))
        print(", ".join(f"{n}: {s}" for n, s in zip(GROUPS, group_states, strict=True)))
        if finished(group_states):
            return
        time.sleep(POLL_S)


if __name__ == "__main__":
    main()
