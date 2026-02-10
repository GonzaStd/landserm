import subprocess
import sys
import os
from pathlib import Path
try:
    import tomlkit
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "--no-cache-dir", "tomlkit"], check=True)
    import tomlkit

script_dir = Path(__file__).parent.resolve()
project_root = script_dir.parent
pyproject_path = project_root / "pyproject.toml"
requirements_path = project_root / "requirements.pipreqs.txt"

try:
    import pipreqs
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "--no-cache-dir", "pipreqs"], check=True)

pipreqs_bin = str(Path(sys.executable).parent / "pipreqs")
source_code_path = project_root / "landserm"
subprocess.run([
    pipreqs_bin,
    str(source_code_path),
    "--force",
    "--savepath", str(requirements_path)
], check=True)

with requirements_path.open() as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

with pyproject_path.open("r") as f:
    pyproject_data = tomlkit.parse(f.read())

if "project" not in pyproject_data:
    print("[project] section not found in pyproject.toml")
    sys.exit(1)

pyproject_data["project"]["dependencies"] = requirements

with pyproject_path.open("w") as f:
    f.write(tomlkit.dumps(pyproject_data))

requirements_path.unlink()

print("[project][dependencies] updated in pyproject.toml. Please review for version accuracy.")
