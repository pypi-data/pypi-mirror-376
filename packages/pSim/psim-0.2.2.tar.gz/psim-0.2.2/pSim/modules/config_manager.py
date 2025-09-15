"""
Configuration Manager for pSim

Handles configuration file:
1. Check project root for game_config.json (user customization)
2. Automatically copy package default config if not found
"""

import json
import shutil
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """Manages game configuration files with fallback system."""

    def __init__(self, project_root: Optional[str] = None):
        """Initialize configuration manager.

        Args:
            project_root: Root directory to search for config. If None, auto-detects.
        """
        self.project_root = self._find_project_root() if project_root is None else Path(project_root)
        self.package_config_path = Path(__file__).parent.parent / 'config' / 'game_config.json'
        self.user_config_path = self.project_root / 'game_config.json'

        # Load configuration using priority system
        self.config_path = self._get_active_config_path()
        self.config = self._load_config()

    def _find_project_root(self) -> Path:
        """Find project root by looking for common indicators."""
        current = Path.cwd()

        # Look for common project root indicators
        indicators = [
            "pyproject.toml",   # Modern Python project
            "game_config.json", # pSim-specific config
            ".venv"             # Virtual environment (fallback)
        ]

        # Search upwards from current directory
        for parent in [current] + list(current.parents):
            if any((parent / indicator).exists() for indicator in indicators):
                return parent

        # Fallback to current directory
        return current

    def _get_active_config_path(self) -> Path:
        """Determine which config file to use based on priority."""
        # Priority 1: User config in project root
        if self.user_config_path.exists():
            print(f"Using user config: {self.user_config_path}")
            return self.user_config_path

        # Priority 2: Copy package default to user location if it exists
        if self.package_config_path.exists():
            print(f"Package config found, copying to user location: {self.user_config_path}")
            self.create_user_config()
            return self.user_config_path

        # No config found - raise error
        raise FileNotFoundError(
            f"No configuration file found. Package default config is missing."
        )

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from determined path."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Re-raise the error with helpful message
            raise FileNotFoundError(
                f"No configuration file found. The package default config is missing or corrupted."
            )



    def get_config(self) -> Dict[str, Any]:
        """Get loaded configuration."""
        return self.config

    def get_config_path(self) -> Path:
        """Get path of active configuration file."""
        return self.config_path

    def reload_config(self):
        """Reload configuration from file."""
        self.config = self._load_config()
        print(f"Configuration reloaded from: {self.config_path}")

    def create_user_config(self, force: bool = False) -> bool:
        """Create user configuration file in project root.

        Args:
            force: If True, overwrites existing user config.

        Returns:
            True if config was created/updated, False if already exists.
        """
        if self.user_config_path.exists() and not force:
            print(f"User config already exists at: {self.user_config_path}")
            return False

        # Copy from package default (should always exist)
        shutil.copy2(self.package_config_path, self.user_config_path)
        action = "Updated" if force else "Created"
        print(f"{action} user config at: {self.user_config_path}")

        return True

    def update_movement_type(self, scenario: str, team: str, robot_idx: int, movement_type: str):
        """Update movement type for a specific robot.

        Args:
            scenario: Scenario name (e.g. "formation")
            team: "agent_robots" or "adversary_robots"
            robot_idx: Robot index
            movement_type: "action", "ou", or "no_move"
        """
        if scenario not in self.config["scenarios"]:
            raise ValueError(f"Scenario '{scenario}' not found")

        if team not in self.config["scenarios"][scenario]:
            raise ValueError(f"Team '{team}' not found in scenario '{scenario}'")

        movement_types = self.config["scenarios"][scenario][team]["movement_types"]

        if robot_idx >= len(movement_types):
            raise ValueError(f"Robot index {robot_idx} out of range")

        old_type = movement_types[robot_idx]
        movement_types[robot_idx] = movement_type

        # Save updated config
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)

        print(f"🔧 Updated {team} robot {robot_idx}: {old_type} → {movement_type}")

    def get_info(self) -> Dict[str, Any]:
        """Get configuration system information."""
        return {
            "project_root": str(self.project_root),
            "active_config": str(self.config_path),
            "user_config_exists": self.user_config_path.exists(),
            "package_config_exists": self.package_config_path.exists(),
            "config_source": "user" if self.config_path == self.user_config_path else "package"
        }