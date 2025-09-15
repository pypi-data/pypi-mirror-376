#!/usr/bin/env python3
"""
pSim Configuration Setup Script

This script helps users configure pSim environments when installed via PyPI.
It creates a user configuration file in the project root with customizable
robot behaviors and scenarios.

Usage:
    python -m pSim.setup_config
    # or
    python -c "from pSim.setup_config import main; main()"

The script will:
1. Detect if a user config already exists
2. Guide through configuration options interactively
3. Create/update game_config.json in the project root
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import shutil


class ConfigSetup:
    """Interactive configuration setup for pSim."""

    def __init__(self):
        self.project_root = self._find_project_root()
        self.package_config_path = Path(__file__).parent / 'config' / 'game_config.json'
        self.user_config_path = self.project_root / 'game_config.json'

    def _find_project_root(self) -> Path:
        """Find project root by looking for common indicators."""
        current = Path.cwd()

        indicators = [
            'pyproject.toml', 'setup.py', 'setup.cfg',
            '.git', 'README.md', 'requirements.txt'
        ]

        for parent in [current] + list(current.parents):
            if any((parent / indicator).exists() for indicator in indicators):
                return parent

        return current

    def check_existing_config(self) -> bool:
        """Check if user config already exists."""
        if self.user_config_path.exists():
            print(f"📁 Found existing config: {self.user_config_path}")
            response = input("Do you want to update it? (y/N): ").strip().lower()
            return response in ['y', 'yes']
        return True

    def load_base_config(self) -> Dict[str, Any]:
        """Load base configuration from package."""
        if self.package_config_path.exists():
            with open(self.package_config_path, 'r') as f:
                return json.load(f)
        else:
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "scenarios": {
                "information": [
                    "action, ou, no_move are valid movement types.",
                    "'action' means the robot will be controlled by the action input.",
                    "'ou' means the robot will move according to an Ornstein-Uhlenbeck process.",
                    "'no_move' means the robot will stay stationary."
                ],
                "formation": {
                    "ball_velocity": [0.0, 0.0],
                    "ball_position_type": "fixed",
                    "ball_position": [0.0, 0.0],
                    "agent_robots": {
                        "position_type": "fixed",
                        "positions": [
                            [-0.1, 0.0, 0.0],
                            [-0.2, 0.2, 0.0],
                            [-0.7, 0.0, -1.571]
                        ],
                        "movement_types": ["action", "action", "ou"]
                    },
                    "adversary_robots": {
                        "position_type": "fixed",
                        "positions": [
                            [0.25, 0.0, 3.14159],
                            [0.2, -0.2, 3.14159],
                            [0.7, 0.0, 1.571]
                        ],
                        "movement_types": ["ou", "ou", "ou"]
                    }
                }
            }
        }

    def configure_scenario(self, config: Dict[str, Any], scenario_name: str) -> Dict[str, Any]:
        """Configure a specific scenario interactively."""
        if scenario_name not in config["scenarios"]:
            print(f"❌ Scenario '{scenario_name}' not found in config")
            return config

        scenario = config["scenarios"][scenario_name]
        print(f"\n🎯 Configuring scenario: {scenario_name}")

        # Configure agent robots
        if "agent_robots" in scenario:
            print(f"\n🤖 Agent Robots (Blue Team):")
            scenario["agent_robots"]["movement_types"] = self._configure_robot_team(
                "agent", len(scenario["agent_robots"]["positions"])
            )

        # Configure adversary robots
        if "adversary_robots" in scenario:
            print(f"\n🤖 Adversary Robots (Yellow Team):")
            scenario["adversary_robots"]["movement_types"] = self._configure_robot_team(
                "adversary", len(scenario["adversary_robots"]["positions"])
            )

        return config

    def _configure_robot_team(self, team_name: str, num_robots: int) -> List[str]:
        """Configure movement types for a robot team."""
        movement_types = []

        print(f"  Configure {num_robots} {team_name} robots:")
        print(f"  Options: 'action' (controlled), 'ou' (automatic), 'no_move' (stationary)")

        for i in range(num_robots):
            while True:
                default = "action" if i < 2 else "ou"  # First 2 robots controllable by default
                response = input(f"  Robot {i} movement type [{default}]: ").strip().lower()

                if not response:
                    response = default

                if response in ['action', 'ou', 'no_move']:
                    movement_types.append(response)
                    break
                else:
                    print("❌ Invalid option. Choose: action, ou, or no_move")

        return movement_types

    def create_config(self) -> bool:
        """Create or update user configuration."""
        print("🚀 pSim Configuration Setup")
        print("=" * 40)

        if not self.check_existing_config():
            print("❌ Configuration cancelled")
            return False

        # Load base config
        config = self.load_base_config()

        # Configure scenarios
        scenarios = list(config["scenarios"].keys())
        scenarios.remove("information")  # Skip info

        print(f"\n📋 Available scenarios: {', '.join(scenarios)}")

        for scenario in scenarios:
            config = self.configure_scenario(config, scenario)

        # Save config
        with open(self.user_config_path, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"\n✅ Configuration saved to: {self.user_config_path}")
        print("💡 You can edit this file directly or run this setup again to modify it")

        return True

    def show_summary(self):
        """Show configuration summary."""
        if not self.user_config_path.exists():
            print("❌ No user configuration found")
            return

        with open(self.user_config_path, 'r') as f:
            config = json.load(f)

        print("📊 Configuration Summary:")
        print("-" * 30)

        for scenario_name, scenario in config["scenarios"].items():
            if scenario_name == "information":
                continue

            print(f"\n🎯 Scenario: {scenario_name}")

            for team in ["agent_robots", "adversary_robots"]:
                if team in scenario:
                    movement_types = scenario[team]["movement_types"]
                    controllable = movement_types.count("action")
                    automatic = movement_types.count("ou")
                    stationary = movement_types.count("no_move")

                    team_display = "Agent (Blue)" if team == "agent_robots" else "Adversary (Yellow)"
                    print(f"  {team_display}: {controllable} controllable, {automatic} automatic, {stationary} stationary")


def main():
    """Main setup function."""
    setup = ConfigSetup()

    # Check if run with arguments
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "--summary":
            setup.show_summary()
            return
        elif sys.argv[1] == "--help":
            print(__doc__)
            return

    # Run interactive setup
    success = setup.create_config()
    if success:
        setup.show_summary()


if __name__ == "__main__":
    main()