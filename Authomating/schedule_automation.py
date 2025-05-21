#!/usr/bin/env python3
"""
schedule_automation.py

Defines ScheduleAutomation, which runs in sequence:
  1) aua.am_scraper.py (AUA scraper)
  2) scraper_jenzabar.py (Jenzabar scraper)
  3) cleaingAndmerger.py (clean and merge)

Place this alongside your scripts and run to orchestrate all steps.
"""

import subprocess
import sys
import os

class ScheduleAutomation:
    def __init__(
        self,
        aua_scraper: str = "aua.am_scraper.py",
        jenzabar_scraper: str = "scraper_jenzabar.py",
        cleaner: str = "cleaingAndmerger.py"
    ):
        """
        :param aua_scraper: Path to the AUA course scraper script.
        :param jenzabar_scraper: Path to the Jenzabar scraper script.
        :param cleaner: Path to the clean and merge script ("cleaingAndmerger.py").
        """
        self.aua_scraper = aua_scraper
        self.jenzabar_scraper = jenzabar_scraper
        self.cleaner = cleaner

    def _run_script(self, script_path: str):
        """Helper: invoke a Python script and wait for completion."""
        if not os.path.isfile(script_path):
            raise FileNotFoundError(f"Script not found: {script_path}")
        print(f"\n▶ Running `{script_path}`...")
        result = subprocess.run([sys.executable, script_path], check=False)
        if result.returncode != 0:
            raise RuntimeError(f"`{script_path}` exited with code {result.returncode}")
        print(f"✔ `{script_path}` completed successfully.")

    def run_all(self):
        """
        Execute all steps in order:
          1) AUA scraper
          2) Jenzabar scraper
          3) Cleaner & merger
        """
        # Step 1: AUA scraping
        self._run_script(self.aua_scraper)

        # Step 2: Jenzabar scraping
        self._run_script(self.jenzabar_scraper)

        # Step 3: Cleaning and merging
        self._run_script(self.cleaner)

if __name__ == "__main__":
    try:
        sa = ScheduleAutomation(
            aua_scraper="aua.am_scraper.py",
            jenzabar_scraper="scraper_jenzabar.py",
            cleaner="cleaingAndmerger.py"
        )
        sa.run_all()
        print("\n🎉 All tasks completed successfully.")
    except Exception as e:
        print(f"\n❌ Automation error: {e}", file=sys.stderr)
        sys.exit(1)
