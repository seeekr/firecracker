# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Tests pertaining to line/branch test coverage for the Firecracker code base.

# TODO

- Put the coverage in `s3://spec.firecracker` and update it automatically.
  target should be put in `s3://spec.firecracker` and automatically updated.
"""


import os
import platform
import re

from subprocess import run

import pytest

import host_tools.cargo_build as host  # pylint: disable=import-error

COVERAGE_TARGET_PCT = 84.0
COVERAGE_MAX_DELTA = 0.01

CARGO_KCOV_REL_PATH = os.path.join(host.CARGO_BUILD_REL_PATH, 'kcov')

KCOV_COVERAGE_FILE = 'index.js'
"""kcov will aggregate coverage data in this file."""

KCOV_COVERAGE_REGEX = r'"covered":"(\d+\.\d)"'
"""Regex for extracting coverage data from a kcov output file."""


@pytest.mark.timeout(400)
@pytest.mark.skipif(
    platform.machine() != "x86_64",
    reason="kcov hangs on aarch64"
)
def test_coverage(test_session_root_path, test_session_tmp_path):
    """Test line coverage with kcov.

    The result is extracted from the $KCOV_COVERAGE_FILE file created by kcov
    after a coverage run.
    """
    exclude_pattern = (
        '${CARGO_HOME:-$HOME/.cargo/},'
        'build/,'
        'tests/,'
        'usr/lib/gcc,'
        'lib/x86_64-linux-gnu/,'
        'pnet,'
        # The following files/directories are auto-generated
        'bootparam.rs,'
        'elf.rs,'
        'mpspec.rs,'
        'msr_index.rs,'
        '_gen'
    )
    exclude_region = '\'mod tests {\''

    cmd = (
        'CARGO_TARGET_DIR={} cargo kcov --all '
        '--output {} -- '
        '--exclude-pattern={} '
        '--exclude-region={} --verify'
    ).format(
        os.path.join(test_session_root_path, CARGO_KCOV_REL_PATH),
        test_session_tmp_path,
        exclude_pattern,
        exclude_region
    )
    # By default, `cargo kcov` passes `--exclude-pattern=$CARGO_HOME --verify`
    # to kcov. To pass others arguments, we need to include the defaults.
    run(cmd, shell=True, check=True)

    coverage_file = os.path.join(test_session_tmp_path, KCOV_COVERAGE_FILE)
    with open(coverage_file) as cov_output:
        coverage = float(re.findall(KCOV_COVERAGE_REGEX, cov_output.read())[0])
    print("Coverage is: " + str(coverage))

    coverage_low_msg = (
        'Current code coverage is below the target of {}%'
        .format(COVERAGE_TARGET_PCT)
    )

    assert coverage >= COVERAGE_TARGET_PCT, coverage_low_msg

    coverage_high_msg = (
        'Please update the value of COVERAGE_TARGET_PCT '
        'in test_coverage.py such that current_coverage - '
        'COVERAGE_TARGET_PCT <= {}'.format(COVERAGE_MAX_DELTA)
    )

    assert coverage - COVERAGE_TARGET_PCT <= COVERAGE_MAX_DELTA,\
        coverage_high_msg
