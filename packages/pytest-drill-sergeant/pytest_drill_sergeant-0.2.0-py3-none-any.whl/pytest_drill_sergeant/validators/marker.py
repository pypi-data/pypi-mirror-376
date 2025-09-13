"""Marker validation for pytest-drill-sergeant."""

import pytest

from pytest_drill_sergeant.config import DrillSergeantConfig
from pytest_drill_sergeant.models import ValidationIssue
from pytest_drill_sergeant.utils import (
    detect_test_type_from_path,
    get_available_markers,
)


class MarkerValidator:
    """Validator for test marker enforcement and auto-detection."""

    def validate(
        self, item: pytest.Item, config: DrillSergeantConfig
    ) -> list[ValidationIssue]:
        """Validate markers and return issues (don't fail immediately)."""
        issues: list[ValidationIssue] = []

        if any(item.iter_markers()):
            return issues  # Test already has markers, no issues

        # Try auto-detection if enabled
        detected_type = None
        if config.auto_detect_markers:
            detected_type = detect_test_type_from_path(item, config)

        if detected_type:
            # Auto-decorate with helpful logging
            marker = getattr(pytest.mark, detected_type)
            item.function = marker(item.function)  # type: ignore[attr-defined]
            print(
                f"🔍 Auto-decorated test '{item.name}' with @pytest.mark.{detected_type}"
            )
            return issues  # No issues, auto-fixed

        # Collect the issue if no marker found
        available_markers = get_available_markers(item)
        marker_examples = ", ".join(
            f"@pytest.mark.{m}" for m in sorted(list(available_markers)[:3])
        )

        issues.append(
            ValidationIssue(
                issue_type="marker",
                message=f"Test '{item.name}' must have at least one marker",
                suggestion=f"Add {marker_examples} or move test to appropriate directory structure",
            )
        )

        return issues

    def is_enabled(self, config: DrillSergeantConfig) -> bool:
        """Check if marker validation is enabled."""
        return config.enforce_markers


def _validate_markers(
    item: pytest.Item, config: DrillSergeantConfig
) -> list[ValidationIssue]:
    """Validate markers and return issues (don't fail immediately)."""
    validator = MarkerValidator()
    return validator.validate(item, config)
