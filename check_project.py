"""Check whether the NovaShop project is ready to run.

This script only inspects the local computer. It does not download files,
install packages or change the project.
"""

import importlib.util
import os
import sys


ROOT = os.path.dirname(os.path.abspath(__file__))

CORE_PACKAGES = {
    "numpy": "numpy",
    "sentence-transformers": "sentence_transformers",
    "scikit-learn": "sklearn",
    "joblib": "joblib",
    "torch": "torch",
    "transformers": "transformers",
}

VOICE_PACKAGES = {
    "funasr": "funasr",
    "torchaudio": "torchaudio",
    "soundfile": "soundfile",
    "librosa": "librosa",
}

INTERFACE_PACKAGES = {
    "tkinter": "tkinter",
}

REQUIRED_FILES = (
    "run_app.py",
    "run_scenario.py",
    "requirements.txt",
    os.path.join("engine", "engine.py"),
    os.path.join("engine", "models", "text", "regressor.joblib"),
    os.path.join("engine", "models", "text", "encoder", "model.safetensors"),
)

OPTIONAL_VOICE_FILES = (
    os.path.join("engine", "models", "voice", "voice_classifier.joblib"),
    os.path.join("engine", "models", "voice", "prosody_activity.joblib"),
    os.path.join("engine", "models", "voice", "encoder", "emotion2vec_base.pt"),
)


def package_is_installed(import_name):
    """Return True when Python can find a package."""
    return importlib.util.find_spec(import_name) is not None


def file_exists(relative_path):
    """Return True when a project file exists."""
    return os.path.isfile(os.path.join(ROOT, relative_path))


def show_result(ok, name, optional=False):
    """Print one readable check result."""
    if ok:
        status = "OK"
    elif optional:
        status = "OPTIONAL MISSING"
    else:
        status = "MISSING"
    print("[%s] %s" % (status, name))


def check_python():
    """Check the minimum Python version required by the brief."""
    version = sys.version_info
    ok = version >= (3, 9)
    show_result(ok, "Python %d.%d" % (version.major, version.minor))
    return ok


def check_packages(packages, optional=False):
    """Check a group of Python packages and return missing names."""
    missing = []
    for display_name, import_name in packages.items():
        ok = package_is_installed(import_name)
        show_result(ok, "package: " + display_name, optional)
        if not ok:
            missing.append(display_name)
    return missing


def check_files(paths, optional=False):
    """Check a group of files and return missing paths."""
    missing = []
    for path in paths:
        ok = file_exists(path)
        show_result(ok, "file: " + path, optional)
        if not ok:
            missing.append(path)
    return missing


def main():
    """Run every check and return a shell exit code."""
    print("NovaShop project check")
    print("Project:", ROOT)
    print()

    python_ok = check_python()

    print("\nCore packages")
    missing_core_packages = check_packages(CORE_PACKAGES)

    print("\nGraphical interface")
    missing_interface_packages = check_packages(INTERFACE_PACKAGES)

    print("\nRequired files")
    missing_required_files = check_files(REQUIRED_FILES)

    print("\nOptional voice channel")
    missing_voice_packages = check_packages(VOICE_PACKAGES, optional=True)
    missing_voice_files = check_files(OPTIONAL_VOICE_FILES, optional=True)

    core_ready = (
        python_ok
        and not missing_core_packages
        and not missing_interface_packages
        and not missing_required_files
    )

    print("\nSummary")
    if core_ready:
        print("[READY] Text mode is ready.")
    else:
        print("[NOT READY] Text mode still has missing requirements.")
        if missing_core_packages:
            print("Run: python -m pip install -r requirements.txt")
        if missing_interface_packages:
            print("Install Tkinter (on Linux: sudo apt install python3-tk).")
        if missing_required_files:
            print("Add the required model files listed in README.md.")

    if not missing_voice_packages and not missing_voice_files:
        print("[READY] Optional voice mode is ready.")
    else:
        print("[OPTIONAL] Voice mode is not complete; text mode can still be used once ready.")

    return 0 if core_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
