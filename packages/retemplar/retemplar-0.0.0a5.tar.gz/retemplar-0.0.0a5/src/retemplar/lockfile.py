# src/retemplar/lockfile.py
"""Lockfile management for .retemplar.lock files (MVP).

Simple read/write/validate operations for MVP RAT lockfiles.
"""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import yaml
from pydantic import ValidationError

from retemplar.constants import LOCKFILE_NAME
from retemplar.logging import get_logger
from retemplar.schema import RetemplarLock

logger = get_logger(__name__)


class LockfileError(Exception):
    """Base exception for lockfile operations."""


class LockfileNotFoundError(LockfileError):
    """Raised when lockfile doesn't exist."""


class LockfileValidationError(LockfileError):
    """Raised when lockfile validation fails."""


class LockfileManager:
    """Manages .retemplar.lock file operations."""

    def __init__(self, repo_root: Path):
        self.repo_root = Path(repo_root).resolve()
        self.lockfile_path = self.repo_root / LOCKFILE_NAME

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        # No cleanup needed for this simple case
        return False

    # ------------------------
    # Basic ops
    # ------------------------

    def exists(self) -> bool:
        return self.lockfile_path.exists()

    def read(self) -> RetemplarLock:
        """Read and parse lockfile."""
        if not self.exists():
            raise LockfileNotFoundError(
                f'Lockfile not found at {self.lockfile_path}',
            )

        try:
            content = self.lockfile_path.read_text(encoding='utf-8')
            data = yaml.safe_load(content)
            if data is None:
                raise LockfileValidationError('Lockfile is empty.')

            lock = RetemplarLock.model_validate(data)
            logger.debug(
                'lockfile_read',
                template_ref=lock.template_ref,
                managed_paths_count=len(lock.managed_paths),
            )
            return lock
        except yaml.YAMLError as e:
            raise LockfileValidationError(
                f'Invalid YAML in lockfile: {e}',
            ) from e
        except ValidationError as e:
            raise LockfileValidationError(
                f'Invalid lockfile schema: {e}',
            ) from e
        except Exception as e:
            raise LockfileError(f'Failed to read lockfile: {e}') from e

    def write(self, lock: RetemplarLock) -> None:
        """Atomically write lockfile to disk."""
        # Validate first (Pydantic + business rules)
        errors = self.validate(lock)
        if errors:
            raise LockfileValidationError(f'Validation errors: {errors}')

        self.lockfile_path.parent.mkdir(parents=True, exist_ok=True)

        # Dump as YAML (safe_dump, stable order off for readability)
        payload = lock.model_dump(by_alias=True, exclude_none=True)
        content = yaml.safe_dump(
            payload,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )

        # Atomic replace dance
        tmp_dir = self.lockfile_path.parent
        with NamedTemporaryFile(
            'w',
            delete=False,
            dir=tmp_dir,
            prefix='.retemplar.',
            suffix='.tmp',
            encoding='utf-8',
        ) as tf:
            tmp_name = tf.name
            tf.write(content)
            tf.flush()
            os.fsync(tf.fileno())

        try:
            os.replace(
                tmp_name,
                self.lockfile_path,
            )  # atomic on same filesystem
            # fsync the directory to persist the rename on POSIX
            dir_fd = os.open(tmp_dir, os.O_DIRECTORY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)

            logger.debug('lockfile_write', template_ref=lock.template_ref)
        except Exception as e:
            # best-effort cleanup
            try:
                os.unlink(tmp_name)
            except Exception:
                pass
            raise LockfileError(f'Failed to write lockfile: {e}') from e

    def validate(self, lock: RetemplarLock) -> list[str]:
        """Validate lockfile and return list of error messages."""
        errs: list[str] = []
        try:
            # Pydantic roundtrip check
            RetemplarLock.model_validate(lock.model_dump())
        except ValidationError as e:
            for error in e.errors():
                errs.append(
                    f'{".".join(map(str, error.get("loc", [])))}: {error.get("msg")}',
                )

        # Business rules: duplicate managed paths (shouldn't happen due to schema dedupe but double-check)
        seen = set()
        for mp in lock.managed_paths or []:
            if mp.path in seen:
                errs.append(f'Duplicate managed path: {mp.path}')
            seen.add(mp.path)

        if errs:
            logger.warning(
                'lockfile_validation_errors',
                template_ref=lock.template_ref,
                error_count=len(errs),
            )

        return errs
