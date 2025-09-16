# Copyright (C) 2025 Justin Lange
# SPDX-License-Identifier: MIT

import platform
import sys
import subprocess

# gets versions of all installed packages using pip freeze
def get_package_versions():
    print("debug: get packages")

    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], capture_output=True, text=True, check=True)
        packages = {}
        for line in result.stdout.strip().split('\n'):
            if '==' in line:
                name, version = line.split('==')
                packages[name] = version
        return packages
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {}

# our env
def capture_environment():
    return {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "architecture": platform.machine(),
        "cpu": platform.processor(),
        "package_versions": get_package_versions(),
    }