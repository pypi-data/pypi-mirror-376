"""Update repositories with fancy output
"""
import git
import subprocess
import hashlib
from pathlib import Path
from machineconfig.utils.path_reduced import PathExtended as PathExtended
from machineconfig.utils.utils import DEFAULTS_PATH
from machineconfig.utils.utils2 import read_ini


def _get_file_hash(file_path: Path) -> str | None:
    """Get SHA256 hash of a file, return None if file doesn't exist."""
    if not file_path.exists():
        return None
    return hashlib.sha256(file_path.read_bytes()).hexdigest()


def _set_permissions_recursive(path: Path, executable: bool = True) -> None:
    """Set permissions recursively for a directory."""
    if not path.exists():
        return
    
    if path.is_file():
        if executable:
            path.chmod(0o755)
        else:
            path.chmod(0o644)
    elif path.is_dir():
        path.chmod(0o755)
        for item in path.rglob('*'):
            _set_permissions_recursive(item, executable)


def _run_uv_sync(repo_path: Path) -> None:
    """Run uv sync in the given repository path."""
    try:
        print(f"🔄 Running uv sync in {repo_path}")
        result = subprocess.run(
            ["uv", "sync"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ uv sync completed successfully")
        if result.stdout:
            print(f"📝 Output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        print(f"❌ uv sync failed: {e}")
        if e.stderr:
            print(f"📝 Error: {e.stderr}")
    except FileNotFoundError:
        print("⚠️  uv command not found. Please install uv first.")


def _update_repository(repo: git.Repo) -> bool:
    """Update a single repository and return True if pyproject.toml or uv.lock changed."""
    repo_path = Path(repo.working_dir)
    print(f"🔄 {'Updating ' + str(repo_path):.^80}")
    
    # Check if this repo has pyproject.toml or uv.lock
    pyproject_path = repo_path / "pyproject.toml"
    uv_lock_path = repo_path / "uv.lock"
    
    # Get hashes before pull
    pyproject_hash_before = _get_file_hash(pyproject_path)
    uv_lock_hash_before = _get_file_hash(uv_lock_path)
    
    try:
        # Perform git pull for each remote
        dependencies_changed = False
        for remote in repo.remotes:
            try:
                print(f"📥 Pulling from {remote.name} {repo.active_branch.name}")
                pull_info = remote.pull(repo.active_branch.name)
                for info in pull_info:
                    if info.flags & info.FAST_FORWARD:
                        print("✅ Fast-forward pull completed")
                    elif info.flags & info.NEW_HEAD:
                        print("✅ Repository updated")
                    else:
                        print(f"✅ Pull completed: {info.flags}")
            except Exception as e:
                print(f"⚠️  Failed to pull from {remote.name}: {e}")
                continue
        
        # Check if pyproject.toml or uv.lock changed after pull
        pyproject_hash_after = _get_file_hash(pyproject_path)
        uv_lock_hash_after = _get_file_hash(uv_lock_path)
        
        if pyproject_hash_before != pyproject_hash_after:
            print("📋 pyproject.toml has changed")
            dependencies_changed = True
            
        if uv_lock_hash_before != uv_lock_hash_after:
            print("🔒 uv.lock has changed")
            dependencies_changed = True
        
        # Special handling for machineconfig repository
        if "machineconfig" in str(repo_path):
            print("🛠  Special handling for machineconfig repository...")
            scripts_path = Path.home() / "scripts"
            if scripts_path.exists():
                _set_permissions_recursive(scripts_path)
                print(f"✅ Set permissions for {scripts_path}")
            
            linux_jobs_path = repo_path / "src" / "machineconfig" / "jobs" / "linux"
            if linux_jobs_path.exists():
                _set_permissions_recursive(linux_jobs_path)
                print(f"✅ Set permissions for {linux_jobs_path}")
            
            lf_exe_path = repo_path / "src" / "machineconfig" / "settings" / "lf" / "linux" / "exe"
            if lf_exe_path.exists():
                _set_permissions_recursive(lf_exe_path)
                print(f"✅ Set permissions for {lf_exe_path}")
        
        return dependencies_changed
        
    except Exception as e:
        print(f"❌ Error updating repository {repo_path}: {e}")
        return False


def main(verbose: bool = True) -> str:
    """Main function to update all configured repositories."""
    _ = verbose
    repos: list[str] = ["~/code/machineconfig", "~/code/machineconfig", ]
    try:
        tmp = read_ini(DEFAULTS_PATH)['general']['repos'].split(",")
        if tmp[-1] == "": 
            tmp = tmp[:-1]
        repos += tmp
    except (FileNotFoundError, KeyError, IndexError):
        print(f"""
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┃ 🚫 Configuration Error: Missing {DEFAULTS_PATH} or section [general] or key repos
┃ ℹ️  Using default repositories instead
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━""")
        print("""
┌────────────────────────────────────────────────────────────────
│ ✨ Example Configuration:
│
│ [general]
│ repos = ~/code/repo1,~/code/repo2
│ rclone_config_name = onedrivePersonal
│ email_config_name = Yahoo3
│ to_email = myemail@email.com
└────────────────────────────────────────────────────────────────""")

    # Process repositories
    repos_with_changes = []
    for a_package_path in repos:
        try:
            expanded_path = PathExtended(a_package_path).expanduser()
            repo = git.Repo(str(expanded_path), search_parent_directories=True)
            
            # Update repository and check if dependencies changed
            dependencies_changed = _update_repository(repo)
            
            if dependencies_changed:
                repos_with_changes.append(Path(repo.working_dir))
                
        except Exception as ex:
            print(f"""❌ Repository Error: Path: {a_package_path}
Exception: {ex}
{'-' * 50}""")

    # Run uv sync for repositories where pyproject.toml or uv.lock changed
    for repo_path in repos_with_changes:
        _run_uv_sync(repo_path)

    # print("\n🎉 All repositories updated successfully!")
    return """echo "🎉 All repositories updated successfully!" """


if __name__ == '__main__':
    main()
