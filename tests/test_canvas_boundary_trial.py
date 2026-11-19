"""Guardrails for the isolated host-side canvas boundary trial.

No live connections; tests never pass --execute with a valid connection set.
"""
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "run_canvas_boundary_trial.py"

def launch(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(ROOT), capture_output=True, text=True, timeout=5)

class CanvasBoundaryTrialTests(unittest.TestCase):
    def test_default_is_offline(self):
        r = launch("--canvas-dim", "150x72")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Offline plan only", r.stdout)
        self.assertIn("NOT a PiP upload", r.stdout)

    def test_execute_refuses_missing_clean_stop(self):
        r = launch("--canvas-dim", "150x72", "--execute")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--v1-stopped-clean", r.stderr)

    def test_execute_refuses_live_worker_options(self):
        r = launch("--canvas-dim", "150x72", "--execute",
                   "--v1-stopped-clean", "--guidance-stopped",
                   "--double-buffer", "--live-rpm-local", "169.254.106.96")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("forbids RPM", r.stderr)

    def test_only_explicit_small_size_steps(self):
        r = launch("--canvas-dim", "320x320")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("invalid choice", r.stderr)

    def test_stages_each_emit_offline_plan(self):
        for pair in ("150x48", "150x72", "150x144"):
            with self.subTest(pair=pair):
                r=launch("--canvas-dim", pair)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertIn(pair, r.stdout)

if __name__ == "__main__":
    unittest.main()
