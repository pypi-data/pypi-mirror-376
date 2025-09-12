# Copyright (c) QuantCo and pydiverse contributors 2024-2025
# SPDX-License-Identifier: BSD-3-Clause

import pydiverse.common as pdc
from pydiverse.colspec.exc import (
    DtypeValidationError,
    RuleValidationError,
    ValidationError,
)


def test_validation_error_str():
    message = "validation failed"
    exc = ValidationError(message)
    assert str(exc) == message


def test_dtype_validation_error_str():
    exc = DtypeValidationError(
        errors={"a": (pdc.Int64(), pdc.String()), "b": (pdc.Bool(), pdc.String())}
    )
    assert str(exc).split("\n") == [
        "2 columns have an invalid dtype:",
        " - 'a': got dtype 'Int64' but expected 'String(None)'",
        " - 'b': got dtype 'Bool' but expected 'String(None)'",
    ]


def test_rule_validation_error_str():
    exc = RuleValidationError(
        {
            "b|max_length": 1500,
            "a|nullability": 2,
            "primary_key": 2000,
            "a|min_length": 5,
        },
    )
    assert str(exc).split("\n") == [
        "4 rules failed validation:",
        " - 'primary_key' failed validation for 2,000 rows",
        " * Column 'a' failed validation for 2 rules:",
        "   - 'min_length' failed for 5 rows",
        "   - 'nullability' failed for 2 rows",
        " * Column 'b' failed validation for 1 rules:",
        "   - 'max_length' failed for 1,500 rows",
    ]
