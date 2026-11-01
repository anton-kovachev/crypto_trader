#!/usr/bin/env python3
"""Package the Lambda apps and deploy the AWS infrastructure with Terraform."""

import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TERRAFORM_DIR = PROJECT_ROOT / "terraform"
TFVARS_FILE = TERRAFORM_DIR / "terraform.tfvars"
PACKAGE_SCRIPT = Path(__file__).with_name("package_lambda_zips.py")


def run(command: list[str], cwd: Path = PROJECT_ROOT) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=cwd, check=True)


def main() -> None:
    missing_tools = [name for name in ("uv", "terraform", "aws") if not shutil.which(name)]
    if missing_tools:
        raise SystemExit("Required tools not found on PATH: " + ", ".join(missing_tools))

    if not TFVARS_FILE.is_file():
        raise SystemExit(
            f"Create {TFVARS_FILE} from terraform.tfvars.example and fill in the "
            "required resource ARNs and configuration."
        )

    run([sys.executable, str(PACKAGE_SCRIPT)])
    run(["terraform", "fmt", "-check", "-recursive"], cwd=TERRAFORM_DIR)
    run(["terraform", "init"], cwd=TERRAFORM_DIR)
    run(["terraform", "validate"], cwd=TERRAFORM_DIR)
    run(["terraform", "apply", "-var-file", str(TFVARS_FILE)], cwd=TERRAFORM_DIR)

    outputs = subprocess.run(
        ["terraform", "output", "-json"],
        cwd=TERRAFORM_DIR,
        check=True,
        capture_output=True,
        text=True,
    )
    print("\nDeployment outputs:")
    print(outputs.stdout)


if __name__ == "__main__":
    main()
