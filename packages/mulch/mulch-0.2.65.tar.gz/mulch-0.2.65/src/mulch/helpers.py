import datetime
from pathlib import Path
import platform
import os
import json
import toml
import typer
import logging
import sys
import string
import subprocess

from mulch.constants import FALLBACK_SCAFFOLD


logger = logging.getLogger(__name__)


def calculate_nowtime_foldername() -> str:
    now = datetime.datetime.now()
    # use an Obsidian-template-friendly hyphen between the month number and the month name.
    return now.strftime("%Y_%m-%B_%d")

def resolve_first_existing_path(bases: list[Path], filenames: list[str]) -> Path | None:
    for base in bases:
        for name in filenames:
            candidate = base / name
            if candidate.exists():
                return candidate
    return None
    
def resolve_scaffold(order_of_respect: list[Path], filenames_of_respect: list[str]) -> dict:
    for base_path in order_of_respect:
        logger.info(f"base_path = {base_path}")
        logger.info(f"type(base_path) = {type(base_path)}")
        if not isinstance(base_path, Path):
            continue

        for filename in filenames_of_respect:
            candidate = Path(base_path) / filename
            if candidate.exists():
                try:
                    if candidate.suffix == ".toml":
                        typer.secho(f"📄 Loading scaffold from: {candidate}", fg=typer.colors.CYAN)
                        return toml.load(candidate)
                    elif candidate.suffix == ".json":
                        typer.secho(f"📄 Loading scaffold from: {candidate}", fg=typer.colors.CYAN)
                        with candidate.open("r", encoding="utf-8") as f:
                            return json.load(f)
                except Exception as e:
                    typer.secho(f"⚠️ Error loading scaffold from {candidate}: {e}", fg=typer.colors.RED)
                    logger.warning(f"Failed to load scaffold: {candidate}, error: {e}")
                    continue

    typer.secho("📦 Falling back to embedded scaffold structure.", fg=typer.colors.YELLOW)
    return FALLBACK_SCAFFOLD

def index_to_letters(index: int) -> str:
    """Converts a 1-based index to a sequence of lowercase letters"""
    letters = string.ascii_lowercase
    result = ""
    while index > 0:
        index, remainder = divmod(index - 1,26)
        result = letters[remainder] + result
    return result

def get_local_appdata_path(appname=None) -> Path:
    if platform.system() == "Windows":
        # Local app data, e.g., C:\Users\User\AppData\Local
        return Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / appname
    else:
        # On Linux/macOS fallback to the same as get_global_config_path
        return get_global_config_path(appname)


def get_global_config_path(appname=None) -> Path:
    if platform.system() == "Windows":
        return Path(os.getenv("APPDATA", Path.home())) / appname
    else:
        return Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / appname
    
def get_user_root(appname=None) -> Path:
    """
    Return the user's home config path for mulch, e.g.:
    - Windows: %USERPROFILE%
    - Linux/macOS: ~/.config
    """
    if platform.system() == "Windows":
        return Path(os.environ.get("USERPROFILE", Path.home())) / appname
    else:
        # Unix-like systems
        return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / appname
    

def get_username_from_home_directory():
    home_dir = Path.home()  # Get the home directory
    return home_dir.name    # Extract the username from the home directory path

#VALID_EXTENSIONS = [".toml", ".json"]

def try_load_scaffold_file(path: Path) -> dict | None:
    try:
        if not path.exists():
            return None

        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                logger.warning(f"{path} is empty. Continuing to next scaffold source.")
                return None

            if path.suffix == ".json":
                return json.loads(content)
            elif path.suffix == ".toml":
                return toml.loads(content)
            else:
                logger.warning(f"Unsupported scaffold file type: {path}")
    except Exception as e:
        logger.warning(f"Failed to load scaffold from {path}: {e}")
    return None
def open_editor(file_path: Path):
    """Open the file in an appropriate system editor."""
    if sys.platform.startswith("win"):
        os.startfile(str(file_path))
    elif sys.platform == "darwin":
        subprocess.run(["open", str(file_path)])
    else:
        # For Linux: prefer $EDITOR, fallback to nano
        editor = os.getenv("EDITOR", "nano")
        subprocess.run([editor, str(file_path)])

def get_default_untitled_workspace_name_based_on_operating_system(workspaces_dir,override_os=None):
    os_name = platform.system()
    if override_os is not None:
        os_name = override_os
    if os_name == "Windows": 
        base_name = "New workspace"
        n = 1
        while True:
            suffix = f" ({n})" if n > 1 else ""
            folder_name = f"{base_name}{suffix}"
            if not (workspaces_dir / folder_name).exists(): # 
                return folder_name
            n+=1
    elif os_name == "Darwin":
        base_name = "untitled workspace"
        n = 1
        while True:
            suffix = f" {n}" if n > 1 else ""
            folder_name = f"{base_name}{suffix}"
            if not (workspaces_dir / folder_name).exists(): # 
                return folder_name
            n+=1
    elif os_name == "Linux":
        base_name = "New Workspace"
        n = 0
        while True:
            suffix = f" ({n})" if n > 0 else ""
            folder_name = f"{base_name}{suffix}"
            if not (workspaces_dir / folder_name).exists(): # 
                return folder_name
            n+=1
    else:
        return get_default_untitled_workspace_name_based_on_operating_system(workspaces_dir,override_os="Linux")

    
    
def dedupe_paths(paths):
    seen = set()
    unique = []
    for p in paths:
        resolved = str(p.resolve()) if p.exists() else str(p)
        if resolved not in seen:
            unique.append(p)
            seen.add(resolved)
    return unique

def seed(target_dir, scaffold_dict, skip_if_exists = False):
    """Write scaffold to target_dir/.mulch/mulch.toml"""
    output_path = target_dir / ".mulch" / "mulch.toml"
    should_write = False

    if output_path.exists and not(skip_if_exists):
        should_write = typer.confirm(f"⚠️ {output_path} already exists. Overwrite?")

    if should_write:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            toml.dump(scaffold_dict, f)
        typer.echo(f"✅ Wrote .mulch to: {output_path}")
        return True

    #typer.echo("❌ Skipped writing scaffold.")
    return False


def workspace(base_path, scaffold_filepath, workspace_path):
    """
    Initialize a new workspace folder, using the mulch.toml structure or the fallback structure embedded in WorkspaceManagerGenerator.
    """
    from mulch.cli import MULCH_VERSION 
    from mulch.workspace_instance_factory import WorkspaceInstanceFactory
    
    #if not scaffold_filepath.exists():

    with open(scaffold_filepath, "r", encoding="utf-8") as f:
        scaffold_data = toml.load(f)

    lock_data = {
        "scaffold": scaffold_data,
        "generated_by": f"mulch {MULCH_VERSION}",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "generated_by": get_username_from_home_directory()
    }

    name = workspace_path.name
    workspaces_dir = workspace_path.parent
    # I don't think basepath actually matters for what I am doing here, it apparently is only used in context, 
    # which in turn is only used in : 
    #   self.workspace_lock_path = self.context.workspace_lock_path
    #   self.flags_lock_path = self.context.flags_lock_path
    wif = WorkspaceInstanceFactory(workspaces_dir, name)
    wif.establish_lock_filepaths(base_path,lock_data) 
    # Proceed to generate, and set most recently generated file as the default
    wif.create_workspace(set_default=True)
    
def workspace_from_scaffold(workspace_dir, scaffold_dict):
    from mulch.workspace_instance_factory import create_workspace_dirs_from_scaffold_sans_lock
    create_workspace_dirs_from_scaffold_sans_lock(workspace_dir, scaffold_dict)