"""Environment detection module for DBAnchor."""

from __future__ import annotations

import os
from enum import Enum


class EnvironmentTier(str, Enum):
    DEVELOPMENT = "development"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"
    UNKNOWN = "unknown"

    @property
    def is_production_like(self) -> bool:
        return self in {EnvironmentTier.PRODUCTION, EnvironmentTier.STAGING}

    @property
    def is_development_or_test(self) -> bool:
        return self in {EnvironmentTier.DEVELOPMENT, EnvironmentTier.TEST}


ENV_VARIABLE_NAMES = [
    "APP_ENV",
    "ENVIRONMENT",
    "ENV",
    "NODE_ENV",
    "PYTHON_ENV",
    "DJANGO_ENV",
    "FLASK_ENV",
    "FASTAPI_ENV",
    "STAGE",
]

DEV_ALIASES = {"dev", "development", "local", "docker", "sandbox"}
TEST_ALIASES = {"test", "testing", "ci", "unittest", "pytest"}
STAGING_ALIASES = {"staging", "stage", "uat", "preprod", "pre-prod"}
PROD_ALIASES = {"prod", "production", "live", "main"}


def detect_environment(hostname: str | None = None) -> EnvironmentTier:
    """Detect the application environment tier from env variables or host hints."""
    for var in ENV_VARIABLE_NAMES:
        val = os.getenv(var, "").strip().lower()
        if not val:
            continue

        if val in DEV_ALIASES:
            return EnvironmentTier.DEVELOPMENT
        if val in TEST_ALIASES:
            return EnvironmentTier.TEST
        if val in STAGING_ALIASES:
            return EnvironmentTier.STAGING
        if val in PROD_ALIASES:
            return EnvironmentTier.PRODUCTION

    # Host heuristics if no explicit environment variable
    if hostname:
        lower_host = hostname.lower()
        if lower_host in {"localhost", "127.0.0.1", "::1", "host.docker.internal"}:
            return EnvironmentTier.DEVELOPMENT

    return EnvironmentTier.UNKNOWN
