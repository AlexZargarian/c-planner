#!/usr/bin/env python3
"""
schedule_automation.py

Defines ScheduleAutomation, which runs in sequence:
  1) cleaingAndmerger.py
  2) scraper_jenzabar.py
  3) cleaingAndmerger.py (final schedule builder)
"""

import subprocess
import sys
import os

class ScheduleAutomation:
    def __init__(
        self,
        cluster_script: str = "cleaingAndmerger.py",
        scraper_script: str = "scraper_jenzabar.py",
        builder_script: str = "cleaingAndmerger.py"
    ):
        """
        :param cluster_script: Path to your initial clustering script.
        :param scraper_script: Path to your Jenzabar scraper script.
        :param builder_script: Path to your final schedule builder (reuse of findingClusters).
        """
        self.cluster_script = cluster_script
        self.scraper_script = scraper_script
        self.builder_script = builder_script

    def _run_script(self, script_path: str):
        """Helper to invoke a Python script and wait for it to finish."""
        if not os.path.isfile(script_path):
            raise FileNotFoundError(f"Script not found: {script_path}")
        print(f"\n▶ Running `{script_path}`...")
        result = subprocess.run([sys.executable, script_path], check=False)
        if result.returncode != 0:
            raise RuntimeError(f"`{script_path}` exited with code {result.returncode}")
        print(f"✔ `{script_path}` completed successfully.")

    def run_all(self):
        """
        Run the three steps in order:
          1) clustering
          2) scraping
          3) final schedule build
        """
        # Step 1: initial clustering
        self._run_script(self.cluster_script)

        # Step 2: scrape Jenzabar data
        self._run_script(self.scraper_script)

        # Step 3: final schedule builder
        self._run_script(self.builder_script)

if __name__ == "__main__":
    try:
        sa = ScheduleAutomation(
            cluster_script="cleaingAndmerger.py",
            scraper_script="scraper_jenzabar.py",
            builder_script="cleaingAndmerger.py"
        )
        sa.run_all()
        print("\n🎉 All steps completed.")
    except Exception as e:
        print(f"\n❌ Error during automation: {e}", file=sys.stderr)
        sys.exit(1)
