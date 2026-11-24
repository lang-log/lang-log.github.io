"""Tests for tools/certificate_renewal.py: which Cloudflare records it turns off and on.
No network.

Run from the repository root (tools/build_site.sh does):
    python3 -m unittest discover -s tools -p 'test_*.py'
"""

import unittest

import certificate_renewal as cr

HOST = "example.org"


def record(rid, name, rtype="A", proxied=True, comment=""):
    return {"id": rid, "name": name, "type": rtype, "proxied": proxied, "comment": comment}


class PlanTest(unittest.TestCase):
    def setUp(self):
        self.records = [
            record("a", HOST),
            record("aaaa", HOST, "AAAA"),
            record("www", f"www.{HOST}", "CNAME"),
            record("mx", HOST, "MX", proxied=False),
            record("other", f"mail.{HOST}"),
            record("left-off", f"www.{HOST}", "A", proxied=False),
        ]

    def test_stuck_turns_off_only_proxied_site_records(self):
        for days in (None, cr.RENEW_BELOW_DAYS - 1):
            changes = cr.plan(days, self.records, HOST)
            self.assertEqual(
                changes,
                [("a", False, cr.MARKER), ("aaaa", False, cr.MARKER), ("www", False, cr.MARKER)],
            )

    def test_fine_and_nothing_marked_changes_nothing(self):
        self.assertEqual(cr.plan(cr.RENEW_BELOW_DAYS, self.records, HOST), [])

    def test_renewed_turns_back_on_only_marked_records(self):
        records = [
            record("a", HOST, proxied=False, comment=cr.MARKER),
            record("left-off", f"www.{HOST}", proxied=False, comment="owner's own"),
            record("other", f"mail.{HOST}", proxied=False, comment=cr.MARKER),
        ]
        self.assertEqual(cr.plan(cr.RENEW_BELOW_DAYS + 30, records, HOST), [("a", True, "")])


if __name__ == "__main__":
    unittest.main()
