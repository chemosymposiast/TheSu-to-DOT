"""Dependency checks and Graphviz path setup.

Key functions: ensure_module, run_runtime_checks, setup_graphviz_path_and_check
"""
from .primary_imports import importlib, os, subprocess, sys
import json


def ensure_module(module_name, package_name=None):
    """Check if a module is installed; install it via pip if not. Returns True if available."""
    if package_name is None:
        package_name = module_name
    
    try:
        # Actually try to import the module, not just find the spec
        importlib.import_module(module_name)
        return True
    except ImportError:
        print(f"Module {module_name} not found. Installing {package_name}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            print(f"Successfully installed {package_name}.")
            # Verify the installation was successful
            try:
                importlib.import_module(module_name)
                return True
            except ImportError:
                print(f"ERROR: Module {module_name} still not available after installation.")
                return False
        except subprocess.CalledProcessError:
            print(f"ERROR: Failed to install {package_name}.")
            return False


def run_runtime_checks():
    """Verify all required modules (math, re, subprocess, webcolors, graphviz, lxml, ipython) are available. Exit if not."""
    # Standard library modules (should always be available)
    math_ok = ensure_module("math")
    re_ok = ensure_module("re")
    subprocess_ok = ensure_module("subprocess")

    # External dependencies
    webcolors_ok = ensure_module("webcolors")
    graphviz_ok = ensure_module("graphviz")
    lxml_ok = ensure_module("lxml")
    ipython_ok = ensure_module("IPython.display", "ipython")

    # Check if all required modules are available
    all_modules_ok = all([math_ok, re_ok, subprocess_ok, webcolors_ok, graphviz_ok, lxml_ok, ipython_ok])
    if not all_modules_ok:
        print("ERROR: Not all required modules could be installed. Please install them manually.")
        print("Required packages: webcolors, graphviz, lxml, ipython")
        sys.exit(1)


def setup_graphviz_path_and_check():
    """Use Graphviz from PATH by default; if system.graphviz_path is set, prepend that to PATH and verify dot is available."""
    from config.runtime_settings import GRAPHVIZ_PATH

    # Load persisted state (stored alongside this module) to see if we've
    # already confirmed Graphviz at least once.
    state = {}
    state_path = os.path.join(os.path.dirname(__file__), ".thesu_runtime_state.json")
    if os.path.exists(state_path):
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    state = loaded
        except Exception:
            state = {}
    already_confirmed = bool(state.get("graphviz_confirmed"))

    # Only prepend to PATH when user explicitly set graphviz_path; otherwise rely on system PATH.
    added_path = False
    if GRAPHVIZ_PATH:
        path = GRAPHVIZ_PATH.strip()
        if path and os.path.exists(path):
            os.environ["PATH"] = path + os.pathsep + os.environ.get("PATH", "")
            added_path = True

    if GRAPHVIZ_PATH and not added_path:
        print("Warning: Graphviz directory not found at configured location.")
        print("If you encounter Graphviz-related errors, please install Graphviz from https://graphviz.org/download/")
        print("and set system.graphviz_path in settings_user.toml.")

    # Check if Graphviz executable is in PATH
    try:
        subprocess.run(["dot", "-V"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        # Mark Graphviz as confirmed so we never ask again on future successful runs.
        if not already_confirmed:
            state["graphviz_confirmed"] = True
            try:
                with open(state_path, "w", encoding="utf-8") as f:
                    json.dump(state, f)
            except Exception:
                # Non-fatal: continue even if we cannot persist the state.
                pass
    except (subprocess.SubprocessError, FileNotFoundError):
        print("WARNING: Graphviz dot executable not found in PATH.")
        print("This script requires the Graphviz software to be installed, not just the Python package.")
        print("This project has been developed and tested with Graphviz 14.1.2; other versions may work but are not guaranteed.")
        print("Please download and install Graphviz from https://graphviz.org/download/")
        print("After installation, you may need to restart your computer or update the PATH manually.")
        # Only ask the interactive question on the very first startup (before any
        # successful run with Graphviz installed). Once confirmed, we fail fast.
        if already_confirmed:
            sys.exit(1)
        user_input = input("Do you want to continue anyway? (y/n): ")
        if user_input.lower() != 'y':
            sys.exit(1)
