#!/usr/bin/env python3
"""Destroy the crypto-trader AWS infrastructure after explicit confirmation."""

import argparse
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TERRAFORM_DIR = PROJECT_ROOT / "terraform"
TFVARS_FILE = TERRAFORM_DIR / "terraform.tfvars"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip the interactive confirmation (still requires terraform's approval).",
    )
    args = parser.parse_args()

    if not shutil.which("terraform"):
        raise SystemExit("Terraform is required to destroy the infrastructure.")
    if not TFVARS_FILE.is_file():
        raise SystemExit(f"Terraform variables file not found: {TFVARS_FILE}")

    print(
        "WARNING: destroying this stack removes the Lambdas, schedules, queues, "
        "ElastiCache, and the S3 account database."
    )
    if not args.yes and input("Type DESTROY to continue: ").strip() != "DESTROY":
        print("Destroy cancelled.")
        return

    subprocess.run(["terraform", "init"], cwd=TERRAFORM_DIR, check=True)
    subprocess.run(
        ["terraform", "destroy", "-var-file", str(TFVARS_FILE)],
        cwd=TERRAFORM_DIR,
        check=True,
    )


if __name__ == "__main__":
    main()
