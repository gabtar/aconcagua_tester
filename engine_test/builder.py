"""Engine builder - handles cloning and building Aconcagua branches."""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional
import logging

from .config import ACONCAGUA_REPO, ACONCAGUA_MAIN_BRANCH, ENGINES_DIR

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def sanitize_branch_name(branch: str) -> str:
    """Convert branch name or URL to a safe directory name."""
    if branch.startswith("https://github.com/gabtar/aconcagua/tree/"):
        return branch.split("/tree/")[-1]
    if branch.startswith("git@github.com:gabtar/aconcagua.git"):
        return branch.split("/")[-1].replace(".git", "")
    return branch.replace("/", "_").replace(" ", "_")


def get_engine_path(branch: str) -> Path:
    """Get the path to the built engine binary for a branch."""
    safe_name = sanitize_branch_name(branch)
    return Path(ENGINES_DIR) / safe_name / "bin" / "aconcagua-linux-x86_64"


def branch_exists(branch: str) -> bool:
    """Check if branch source code already exists and is built."""
    return get_engine_path(branch).exists()


def clone_branch(branch: str, force: bool = False) -> Path:
    """Clone a branch from the Aconcagua repository."""
    safe_name = sanitize_branch_name(branch)
    target_dir = Path(ENGINES_DIR) / safe_name

    if target_dir.exists() and not force:
        if (target_dir / ".git").exists():
            logger.info(f"Branch '{branch}' already cloned at {target_dir}")
            return target_dir
        shutil.rmtree(target_dir)

    logger.info(f"Cloning branch '{branch}'...")

    os.makedirs(target_dir, exist_ok=True)

    if branch.startswith("feature/") or branch == "main" or "/" not in branch:
        subprocess.run(
            ["git", "clone", "--branch", branch, ACONCAGUA_REPO, str(target_dir)],
            check=True,
            capture_output=True,
        )
    else:
        subprocess.run(
            ["git", "clone", ACONCAGUA_REPO, str(target_dir)],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "checkout", branch],
            cwd=target_dir,
            check=True,
            capture_output=True,
        )

    logger.info(f"Cloned branch '{branch}' successfully")
    return target_dir


def build_engine(branch: str, force: bool = False) -> Path:
    """Build the engine binary for a branch."""
    safe_name = sanitize_branch_name(branch)
    engine_path = get_engine_path(branch)

    if engine_path.exists() and not force:
        logger.info(f"Engine binary already exists at {engine_path}")
        return engine_path

    branch_dir = clone_branch(branch, force=force)

    logger.info(f"Building engine for branch '{branch}'...")
    result = subprocess.run(
        ["make", "build"],
        cwd=branch_dir,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Build failed: {result.stderr}")

    if not engine_path.exists():
        raise RuntimeError(f"Build succeeded but binary not found at {engine_path}")

    logger.info(f"Built engine binary at {engine_path}")
    return engine_path


def ensure_main_engine() -> Path:
    """Ensure the main branch is built with latest code and return its path."""
    safe_name = sanitize_branch_name(ACONCAGUA_MAIN_BRANCH)
    engine_path = get_engine_path(ACONCAGUA_MAIN_BRANCH)
    target_dir = Path(ENGINES_DIR) / safe_name

    if target_dir.exists() and (target_dir / ".git").exists():
        result = subprocess.run(
            ["git", "fetch", "origin", "main"],
            cwd=target_dir,
            capture_output=True,
            text=True,
        )
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=target_dir,
            capture_output=True,
            text=True,
        )
        local_head = result.stdout.strip()

        result = subprocess.run(
            ["git", "rev-parse", "origin/main"],
            cwd=target_dir,
            capture_output=True,
            text=True,
        )
        origin_head = result.stdout.strip()

        if local_head != origin_head:
            logger.info(f"Main branch has new commits, rebuilding...")
            return build_engine(ACONCAGUA_MAIN_BRANCH, force=True)

    return build_engine(ACONCAGUA_MAIN_BRANCH)


def cleanup_engines(branch: Optional[str] = None):
    """Remove built engine directories."""
    if branch:
        safe_name = sanitize_branch_name(branch)
        target_dir = Path(ENGINES_DIR) / safe_name
        if target_dir.exists():
            shutil.rmtree(target_dir)
            logger.info(f"Removed engine directory: {target_dir}")
    else:
        if Path(ENGINES_DIR).exists():
            for item in Path(ENGINES_DIR).iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
            logger.info("Removed all engine directories")