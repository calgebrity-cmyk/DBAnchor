"""Unit tests for environment detection."""

import os
import pytest
from dbanchor.environments.detector import EnvironmentTier, detect_environment


def test_detect_environment_from_app_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    tier = detect_environment()
    assert tier == EnvironmentTier.PRODUCTION
    assert tier.is_production_like is True
    assert tier.is_development_or_test is False


def test_detect_staging(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "staging")
    tier = detect_environment()
    assert tier == EnvironmentTier.STAGING
    assert tier.is_production_like is True


def test_detect_development_from_localhost(monkeypatch):
    # clear env vars
    for k in ["APP_ENV", "ENVIRONMENT", "ENV", "NODE_ENV"]:
        monkeypatch.delenv(k, raising=False)
    tier = detect_environment("localhost")
    assert tier == EnvironmentTier.DEVELOPMENT
    assert tier.is_development_or_test is True


def test_detect_unknown(monkeypatch):
    for k in ["APP_ENV", "ENVIRONMENT", "ENV", "NODE_ENV"]:
        monkeypatch.delenv(k, raising=False)
    tier = detect_environment("random-host.com")
    assert tier == EnvironmentTier.UNKNOWN
