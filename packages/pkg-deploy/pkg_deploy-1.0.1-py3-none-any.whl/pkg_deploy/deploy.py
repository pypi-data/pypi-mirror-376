import os
import sys
import glob
import shutil
import logging
import argparse
import subprocess
from pathlib import Path

from .upload import Upload, NexusUpload
from .version_managment import VersionManager
from .build import DeployConfig, CythonBuildStrategy, StandardBuildStrategy
from .utils import get_pypirc_info, get_credentials, is_uv_venv, validate_version_arg


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-5.5s] [%(name)-30.30s] [%(lineno)-4.4s] [%(processName)-12.12s]: %(message)s"
)
logger = logging.getLogger(__name__)


def parse_args(args):
    parser = argparse.ArgumentParser(
        description="Modern Python Package Deployment Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
          # Deploy to PyPI, patch version
          python deploy.py --package-name my-package --version-type patch

          # Deploy to private Nexus, using cython
          python deploy.py --package-name my-package --version-type minor
              --repository-url https://nexus.example.com/repository/pypi-internal/
              --username admin
              --password secret

          # Dry run
          python deploy.py --package-name my-package --version-type patch --dry-run
          """)

    parser.add_argument(
        "--project-dir",
        type=Path,
        default=Path.cwd(),
        help="Project directory (default: current directory)"
    )

    parser.add_argument(
        "--version-type", "-vt",
        default="patch",
        help="Version bump type (default: patch)"
    )

    parser.add_argument(
        "--new-version", "-v",
        type=validate_version_arg,
        help="New version number, if not specified, a new version will be resolved by version-type"
    )

    parser.add_argument(
        "--cython", "-c",
        action="store_true",
        help="Use Cython for compilation"
    )

    parser.add_argument(
        "--repository-name", "-rn",
        help="Repository name (.pypirc)"
    )

    parser.add_argument(
        "--repository-url", "-rl",
        help="Repository URL"
    )

    parser.add_argument(
        "--username", "-u",
        help="Username for authentication"
    )

    parser.add_argument(
        "--password", "-p",
        help="Password for authentication"
    )

    parser.add_argument(
        "--no-git-push",
        action="store_true",
        help="Push local changes to Git repository after build"
    )

    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Force interactive credential input (useful for Nexus)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without actual deployment"
    )

    parser.add_argument(
        "--verbose", "-V",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args(args)
    if not args.repository_url and not args.repository_name:
        parser.error("Either --repository-url or --repository-name must be provided.")
    return args


class PackageDeploy:
    def __init__(self):
        args = sys.argv[1:]
        self.args = parse_args(args)
        if not (self.args.project_dir / "pyproject.toml").exists():
            raise ValueError("pyproject.toml not found")

        if self.args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        self.check_require_package(self.args.cython)

        pypirc_info = get_pypirc_info()
        repos = pypirc_info["repositories"]
        if self.args.repository_name and self.args.repository_name in repos:
            repository_info = repos[self.args.repository_name]
            url = repository_info["repository"]
            username = repository_info["username"]
            password = repository_info["password"]
        elif self.args.repository_name:
            raise ValueError("Repository name is provided but not found in .pypirc")
        else:
            url = self.args.repository_url
            username, password = get_credentials(self.args)

        pyproject_path = self.args.project_dir / "pyproject.toml"

        self.version_manager = VersionManager(pyproject_path)
        self.config = DeployConfig(
            package_name=self.version_manager.toml_config["project"]["name"],
            project_dir=self.args.project_dir,
            pyproject_path=pyproject_path,
            version_type=self.args.version_type,
            new_version=self.args.new_version,
            use_cython=self.args.cython,
            is_uv_venv=is_uv_venv(),
            repository_name=self.args.repository_name,
            repository_url=url,
            username=username,
            password=password,
            dry_run=self.args.dry_run
        )
        self.setup_file_exist = (self.config.project_dir / "setup.py").exists()

    def deploy(self):
        logger.info("=== Deployment Configuration ===")
        for arg_name, arg_value in vars(self.args).items():
            display_value = arg_value
            if arg_name in ('username', 'password') and arg_value is not None:
                display_value = '***MASKED***'
            logger.info(f"{arg_name}: {display_value}")
        logger.info("=================================")
        
        if self.config.dry_run:
            logger.info("DRY RUN: Starting deployment simulation")
        else:
            logger.info(f"Starting deployment")
            
        try:
            self.check_git_status()

            new_version = self.version_manager.bump_version(
                version_type=self.config.version_type,
                new_version=self.config.new_version,
                dry_run=self.config.dry_run
            )
            
            if self.config.dry_run:
                logger.info(f"DRY RUN: Would bump version to: {new_version}")
            else:
                logger.info(f"New version: {new_version}")

            if self.config.use_cython:
                build_strategy = CythonBuildStrategy()
            else:
                build_strategy = StandardBuildStrategy()

            uploaded = False
            if build_strategy.build(self.config, self.version_manager.toml_config):
                upload_strategy = self.get_upload_strategy(self.config)
                dist_dir = self.config.project_dir / "dist"
                uploaded = upload_strategy.upload(self.config, dist_dir)

            self.cleanup_build_files()

            if uploaded and not self.args.no_git_push:
                self.git_push(new_version=new_version, dry_run=self.config.dry_run)
            else:
                self.git_roll_back()

            logger.info('Deploy completed')
        except Exception as e:
            logger.error(f"Deployment failed: {e}", exc_info=True)
            return False

    @staticmethod
    def check_require_package(cython: bool):
        required_packages = ["build", "twine", "toml", "tomlkit"]
        if cython:
            required_packages.append("Cython")

        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            logger.error(f"Missing required packages: {', '.join(missing_packages)}")
            logger.error(f"Install them with: pip install {' '.join(missing_packages)}")
            raise ValueError("Missing required packages")

    def cleanup_build_files(self):
        logger.info('Deleting build, dist and egg-info files after deployment')
        shutil.rmtree('dist', ignore_errors=True)
        shutil.rmtree('build', ignore_errors=True)
        shutil.rmtree(f'src/{self.config.package_name}.egg-info', ignore_errors=True)
        egg_info_name = self.config.package_name.replace("-", "_")
        shutil.rmtree(f'src/{egg_info_name}.egg-info', ignore_errors=True)
        launcher_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        directory = os.path.join(launcher_dir, 'src', self.config.package_name.replace("-", "_"))
        c_files = glob.glob(os.path.join(directory, '**', '*.c'), recursive=True)
        if not self.setup_file_exist:
            Path("setup.py").unlink(missing_ok=True)
        for file_path in c_files:
            Path(file_path).unlink(missing_ok=True)

    def check_git_status(self):
        logger.info("Checking git status, --porcelain to make sure git repo is clean")
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.config.project_dir,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise IOError(f"Git command failed: {result.stderr.strip()}")
        if result.stdout.strip():
            raise IOError(f"Git repo is NOT clean: \n{result.stdout}")

    @staticmethod
    def git_push(new_version: str, dry_run: bool = False):
        try:
            if dry_run:
                logger.info("DRY RUN: Would run: git add .")
                logger.info(f"DRY RUN: Would run: git commit -m 'Bump version to {new_version}'")
                tag_name = f"v{new_version}"
                logger.info(f"DRY RUN: Would create Git tag: {tag_name}")
                logger.info("DRY RUN: Would run: git push --follow-tags")
                logger.info('DRY RUN: Git push simulation completed')
            else:
                subprocess.check_output(['git', 'add', '.'], stderr=subprocess.STDOUT)
                subprocess.check_output(['git', 'commit', '-m', f'Bump version to {new_version}'], stderr=subprocess.STDOUT)
                tag_name = f"v{new_version}"
                subprocess.check_output(['git', 'tag', '-a', tag_name, '-m', f'Release {tag_name}'], stderr=subprocess.STDOUT)
                logger.info(f"Created Git tag: {tag_name}")
                subprocess.check_output(['git', 'push', '--follow-tags'], stderr=subprocess.STDOUT)
                logger.info('Pushing to github')
        except subprocess.CalledProcessError as ex:
            logger.error(f"Git command failed: {ex.output.decode()}")
            logger.warning('Failed to push bump version commit. Please push manually.')
        except Exception as ex:
            logger.error(f"Unexpected error: {ex}")
            logger.warning('Failed to push bump version commit. Please push manually.')

    @staticmethod
    def git_roll_back():
        try:
            subprocess.check_output(['git', 'restore', '.'], stderr=subprocess.STDOUT)
            logger.info('Restored changes')
        except subprocess.CalledProcessError as ex:
            logger.error(f"Git command failed: {ex.output.decode()}")
        except Exception as ex:
            logger.error(f"Unexpected error: {ex}")
            logger.warning('Failed to roll back changes. Please roll back manually.')

    @staticmethod
    def get_upload_strategy(config) -> Upload:
        return NexusUpload()


