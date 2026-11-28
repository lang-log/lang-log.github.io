"""Tests for tools/ci_progress.py (the progress comment on pull requests). No network:
the runs and jobs are made up here, in the shape the GitHub API gives them.

Run from the repository root (tools/build_site.sh does):
    python3 -m unittest discover -s tools -p 'test_*.py'
"""

import unittest

import yaml

import ci_progress as cp
from locations import ROOT

SHA = "0123456789abcdef0123456789abcdef01234567"
NOW = 1_800_000_000
ENDED = "2027-01-15T08:00:00Z"


def done(name=None):
    item = {"status": "completed", "conclusion": "success"}
    return {**item, "name": name} if name else item


def failed(name=None):
    item = {"status": "completed", "conclusion": "failure"}
    return {**item, "name": name} if name else item


def running(name=None):
    item = {"status": "in_progress", "conclusion": None}
    return {**item, "name": name} if name else item


def skipped(name):
    return {"status": "completed", "conclusion": "skipped", "name": name}


def build_job(b=done, c=done, d=done):
    steps = (
        [b(n) for n in cp.BUILD_STEPS]
        + [c(n) for n in cp.BROWSER_STEPS]
        + [d(n) for n in cp.PREVIEW_STEPS]
    )
    return {"name": cp.BUILD_JOB, "steps": steps}


QUALITY = [done("quality / prettier"), done("quality / ruff")]


class States(unittest.TestCase):
    def test_all_done(self):
        got = cp.states(done(), QUALITY + [build_job()], done(), True, NOW)
        self.assertEqual(got, [cp.DONE] * 4)

    def test_code_checks_running(self):
        jobs = [done("quality / prettier"), running("quality / ruff")]
        got = cp.states(running(), jobs, running(), False, NOW)
        self.assertEqual(got, [cp.RUNNING] * 4)

    def test_code_checks_failed(self):
        jobs = [done("quality / prettier"), failed("quality / ruff")]
        got = cp.states(failed(), jobs, done(), False, NOW)
        self.assertEqual(got, [cp.FAILED, cp.NOT_RUN, cp.NOT_RUN, cp.NOT_RUN])

    def test_build_running(self):
        job = build_job(b=running, c=running, d=running)
        got = cp.states(running(), QUALITY + [job], done(), False, NOW)
        self.assertEqual(got, [cp.DONE, cp.RUNNING, cp.RUNNING, cp.RUNNING])

    def test_build_failed(self):
        job = build_job(b=failed, c=skipped, d=skipped)
        got = cp.states(failed(), QUALITY + [job], done(), False, NOW)
        self.assertEqual(got, [cp.DONE, cp.FAILED, cp.NOT_RUN, cp.NOT_RUN])

    def test_browser_check_failed(self):
        got = cp.states(done(), QUALITY + [build_job()], failed(), True, NOW)
        self.assertEqual(got[2], cp.FAILED)

    def test_browser_check_still_running(self):
        got = cp.states(done(), QUALITY + [build_job()], running(), True, NOW)
        self.assertEqual(got, [cp.DONE, cp.DONE, cp.RUNNING, cp.DONE])

    def test_preview_waits_for_its_comment(self):
        site = {**done(), "updated_at": ENDED}
        got = cp.states(site, QUALITY + [build_job()], done(), False, cp._ended(site) + 60)
        self.assertEqual(got[3], cp.RUNNING)
        late = cp._ended(site) + cp.PREVIEW_WAIT_S + 1
        got = cp.states(site, QUALITY + [build_job()], done(), False, late)
        self.assertEqual(got[3], cp.FAILED)

    def test_missing_step_fails_once_site_ended(self):
        job = {"name": cp.BUILD_JOB, "steps": [done(n) for n in cp.BUILD_STEPS]}
        got = cp.states(done(), QUALITY + [job], done(), False, NOW)
        self.assertEqual(got[2:], [cp.FAILED, cp.FAILED])

    def test_ended(self):
        self.assertEqual(cp._ended({"updated_at": "1970-01-01T00:01:00Z"}), 60)
        self.assertEqual(cp._ended({}), 0)


class Comment(unittest.TestCase):
    def test_lists_ended_groups_in_order(self):
        body = cp.render(SHA, [cp.DONE, cp.DONE, cp.RUNNING, cp.RUNNING], "https://x")
        self.assertTrue(body.startswith(cp.COMMENT_MARKER))
        self.assertIn("Commit 0123456", body)
        self.assertIn("1. Code checks: done\n2. Build and content checks: done\n", body)
        self.assertNotIn("3.", body)
        self.assertNotIn("All groups", body)

    def test_says_when_all_ended(self):
        body = cp.render(SHA, [cp.DONE, cp.FAILED, cp.NOT_RUN, cp.NOT_RUN], "https://x")
        self.assertIn("2. Build and content checks: failed", body)
        self.assertIn("4. Publishing the preview: not run", body)
        self.assertIn("All groups have ended.", body)

    def test_finds_comments(self):
        preview = {"body": f"{cp.PREVIEW_MARKER}\n### Preview\n\nfrom commit {SHA[:7]}:"}
        old = {"body": f"{cp.PREVIEW_MARKER}\nfrom commit 7654321:"}
        own = {"id": 5, "body": f"{cp.COMMENT_MARKER}\n### Checks"}
        self.assertTrue(cp.preview_names([old, preview], SHA))
        self.assertFalse(cp.preview_names([old, own], SHA))
        self.assertIs(cp.own_comment([preview, own]), own)
        self.assertIsNone(cp.own_comment([preview, "not a comment"]))


class Workflows(unittest.TestCase):
    """The names ci_progress.py reads are the ones the workflows use."""

    def test_site_yml_has_the_jobs_and_steps(self):
        site = yaml.safe_load((ROOT / ".github/workflows/site.yml").read_text(encoding="utf-8"))
        jobs = site["jobs"]
        self.assertIn(cp.QUALITY_JOB_PREFIX.split(" / ")[0], jobs)
        steps = [s.get("name") for s in jobs[cp.BUILD_JOB]["steps"]]
        for name in cp.BUILD_STEPS + cp.BROWSER_STEPS + cp.PREVIEW_STEPS:
            self.assertIn(name, steps)
        order = [steps.index(n) for n in cp.BUILD_STEPS + cp.BROWSER_STEPS + cp.PREVIEW_STEPS]
        self.assertEqual(order, sorted(order))

    def test_browsers_yml_exists(self):
        self.assertTrue((ROOT / ".github/workflows" / cp.BROWSERS_WORKFLOW).is_file())

    def test_progress_yml_follows_site_yml(self):
        path = ROOT / ".github/workflows/progress.yml"
        progress = yaml.safe_load(path.read_text(encoding="utf-8"))
        site = yaml.safe_load((ROOT / ".github/workflows/site.yml").read_text(encoding="utf-8"))
        # PyYAML reads the key "on" as True.
        self.assertEqual(progress[True]["workflow_run"]["workflows"], [site["name"]])


if __name__ == "__main__":
    unittest.main()
