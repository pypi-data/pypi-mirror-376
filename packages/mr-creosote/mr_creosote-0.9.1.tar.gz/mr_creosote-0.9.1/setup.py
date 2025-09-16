from setuptools import setup, find_packages
from urllib.request import urlopen
from urllib.request import Request
import json
import os
import sys
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed


def get_pypi_json():
    """
    Request the package list from PyPI and return the JSON data.
    Equivalent to running curl --header 'Accept: application/vnd.pypi.simple.v1+json' https://pypi.org/simple/
    """
    url = "https://pypi.org/simple/"
    req = Request(url, headers={"Accept": "application/vnd.pypi.simple.v1+json"})
    with urlopen(req) as f:
        return json.load(f)


def get_package_names():
    """ Parse the JSON data and yield package names. """
    json_data = get_pypi_json()
    # Use a generator expression for efficiency.
    return (pkg["name"] for pkg in json_data["projects"])


def get_all_packages_from_pypi():
    """ Get the list of all packages from PyPI, excluding this package to avoid circular dependencies. """
    all_packages = list(get_package_names())
    # Filter out ourselves to avoid circular dependency
    package_names_to_exclude = {'mr-creosote', 'mr_creosote'}
    return [pkg for pkg in all_packages if pkg not in package_names_to_exclude]


def is_building():
    """
    Check if we're building for distribution vs installing from PyPI.

    Uses MR_CREOSOTE_BUILD environment variable for reliable detection.
    Set MR_CREOSOTE_BUILD=1 when building packages for distribution.
    """
    return bool(os.environ.get('MR_CREOSOTE_BUILD'))


def test_package_install(package_name, timeout=30):
    """
    Test if a package can be installed without actually installing it permanently.
    Returns True if the package can be installed, False otherwise.
    """
    try:
        # Create a temporary directory for the test installation
        with tempfile.TemporaryDirectory() as temp_dir:
            # Try to download and check the package without installing
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'download',
                '--no-deps', '--dest', temp_dir, package_name
            ], capture_output=True, timeout=timeout, text=True)

            # If download succeeds, the package is likely installable
            return result.returncode == 0

    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
        return False


def get_installable_packages(package_list, max_workers=50, batch_size=100):
    """
    Filter package list to only include packages that can actually be installed.
    Uses threading for faster checking with batching to avoid overwhelming PyPI.
    """
    installable = []

    # Process packages in batches
    for i in range(0, len(package_list), batch_size):
        batch = package_list[i:i + batch_size]
        print(f"Testing batch {i//batch_size + 1}/{(len(package_list) + batch_size - 1)//batch_size} "
              f"({len(batch)} packages)...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all package tests in this batch
            future_to_package = {
                executor.submit(test_package_install, pkg): pkg
                for pkg in batch
            }

            # Collect results as they complete
            for future in as_completed(future_to_package):
                package = future_to_package[future]
                try:
                    if future.result():
                        installable.append(package)
                        print(f"✓ {package}")
                    else:
                        print(f"✗ {package}")
                except Exception as e:
                    print(f"✗ {package} (error: {e})")

    return installable


def debug_build_detection():
    """Debug function to show why we think we're in build mode or not"""
    reasons = []

    # Check direct commands
    build_commands = {'sdist', 'bdist', 'bdist_wheel', 'bdist_egg', 'build'}
    if any(cmd in sys.argv for cmd in build_commands):
        reasons.append(f"Direct command found: {[cmd for cmd in build_commands if cmd in sys.argv]}")

    # Check env vars
    build_env_vars = [
        'BUILD_FRONTEND', 'PEP517_BUILD_BACKEND',
        'SETUPTOOLS_SCM_PRETEND_VERSION', '_PYPROJECT_HOOKS_BUILD_BACKEND'
    ]
    found_envs = [var for var in build_env_vars if os.environ.get(var)]
    if found_envs:
        reasons.append(f"Build env vars found: {found_envs}")

    # Check process chain
    try:
        import psutil
        current_process = psutil.Process()
        parent_chain = []
        proc = current_process
        for _ in range(5):
            try:
                proc = proc.parent()
                if proc is None:
                    break
                parent_chain.append(proc.name().lower())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break

        build_tools = {'uv', 'build', 'pip', 'twine', 'hatch', 'pdm', 'poetry'}
        found_tools = [tool for tool in build_tools if tool in ' '.join(parent_chain)]
        if found_tools:
            reasons.append(f"Build tools in process chain: {found_tools} (chain: {parent_chain})")
    except ImportError:
        reasons.append("psutil not available for process chain check")

    # Check other indicators
    if 'egg_info' in sys.argv:
        reasons.append("egg_info command found")
    if any('wheel' in arg for arg in sys.argv):
        reasons.append("wheel-related args found")

    print(f"sys.argv: {sys.argv}")
    print(f"Build detection reasons: {reasons}")
    return bool(reasons)


def get_dependencies():
    """
    Smart dependency resolution:
    - During build: return only techdragon package (to keep metadata size reasonable)
    - During install: return only packages that can actually be installed
    """
    building = is_building()

    # Debug output
    print(f"=== MR CREOSOTE BUILD DETECTION ===")
    debug_build_detection()
    print(f"Final decision: {'BUILD' if building else 'INSTALL'} context")
    print(f"=====================================")

    if building:
        print("Build context detected - using only techdragon package for reasonable metadata size")
        return ["techdragon"]
    else:
        print("Install context detected - filtering for installable packages")
        all_packages = get_all_packages_from_pypi()
        print(f"Found {len(all_packages)} packages on PyPI")
        print("Testing package installability (this may take a while)...")

        installable = get_installable_packages(all_packages)
        print(f"Found {len(installable)} installable packages out of {len(all_packages)}")
        return installable


setup(
    name="mr-creosote",
    version="1.0.0",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=get_dependencies(),
)