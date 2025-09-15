#!/usr/bin/env python3
"""
pSim Configuration System Demo

This script demonstrates the configuration system for pSim environments,
optimized for PyPI distribution. It shows:

1. Interactive configuration setup for new users
2. Automatic config file management (project root vs package default)
3. Dynamic robot behavior switching (action ↔ ou/no_move)
4. Configuration system suitable for PyPI distribution

For PyPI users, run:
    python -m pSim.setup_config

Or use this demo script to explore the system.
"""

import numpy as np
from pSim.vsss_simple_env import SimpleVSSSEnv
from pSim.modules.config_manager import ConfigManager


def demo_config_system():
    """Demonstrate configuration system functionality."""
    print("=== Configuration System Demo ===\n")

    # 1. Show configuration manager info
    config_manager = ConfigManager()
    info = config_manager.get_info()

    print("📁 Configuration System Info:")
    for key, value in info.items():
        print(f"  {key}: {value}")

    # 2. Show setup script option for PyPI users
    print(f"\n🚀 For PyPI users, run the interactive setup:")
    print(f"   python -m pSim.setup_config")
    print(f"   # or")
    print(f"   python -c \"from pSim.setup_config import main; main()\"")

    # 3. Create user config if it doesn't exist
    if not info['user_config_exists']:
        print(f"\n📝 Creating user config in project root...")
        config_manager.create_user_config()
        print(f"✅ User config created at: {config_manager.user_config_path}")
        print(f"💡 You can now edit this file to customize robot behaviors!")
    else:
        print(f"\n📁 User config already exists: {config_manager.user_config_path}")

    print("\n" + "="*50)


def demo_dynamic_control():
    """Demonstrate dynamic robot control switching."""
    print("=== Dynamic Robot Control Demo ===\n")

    # Create environment
    env = SimpleVSSSEnv(
        render_mode="human",
        scenario="formation",
        num_agent_robots=3,
        num_adversary_robots=2,
        multi_agent_mode=True
    )

    print(f"🔧 Initial Configuration:")
    for team_key in ['agent_movement_types', 'adversary_movement_types']:
        team_name = team_key.replace('_movement_types', '')
        movement_types = env.movement_configs[team_key]
        for robot_id, movement_type in enumerate(movement_types):
            print(f"  {team_name} robot {robot_id}: {movement_type}")

    print(f"\n🎮 Controllable robots: {env.movement_configs['action_robots']}")

    # Test basic simulation
    print(f"\n🔀 Testing Basic Simulation...")

    # Reset environment first
    obs, info = env.reset()
    print(f"   Environment reset successfully")

    # Run a few steps with random actions
    print(f"   Testing 3 simulation steps...")
    for i in range(3):
        # Generate actions for all agent robots
        actions = np.random.uniform(-0.3, 0.3, (env.num_agent_robots, 2))
        obs, reward, terminated, truncated, info = env.step(actions)
        print(f"   Step {i+1}: Reward {reward:.3f}")

        if terminated or truncated:
            obs, info = env.reset()
            print(f"   Episode reset")

    env.close()
    print(f"\n✅ Basic simulation demo completed!")


def demo_config_vs_original():
    """Compare behavior with original configuration vs modified."""
    print("\n=== Configuration vs Original Comparison ===\n")

    # Show current behaviors
    env = SimpleVSSSEnv(scenario="formation", num_agent_robots=3, num_adversary_robots=2)
    print(f"🔧 Current Behaviors:")
    for team_key in ['agent_movement_types', 'adversary_movement_types']:
        print(f"  {team_key}: {env.movement_configs[team_key]}")

    print(f"\n💡 To modify behaviors, edit the game_config.json file in your project root")
    print(f"   Available movement types: 'action', 'ou', 'no_move'")

    env.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Configuration System Demo")
    parser.add_argument("--demo", choices=["config", "dynamic", "compare", "all"],
                       default="all", help="Which demo to run")
    args = parser.parse_args()

    if args.demo in ["config", "all"]:
        demo_config_system()

    if args.demo in ["dynamic", "all"]:
        demo_dynamic_control()

    if args.demo in ["compare", "all"]:
        demo_config_vs_original()

    print("\n🎉 All demos completed!")
    print("\n💡 Tips for PyPI users:")
    print("  - Run 'python -m pSim.setup_config' to create custom configuration")
    print("  - Edit game_config.json in your project root to customize behaviors")
    print("  - Use 'action' for agent-controlled robots")
    print("  - Use 'ou' for Ornstein-Uhlenbeck automatic movement")
    print("  - Use 'no_move' for stationary robots")
    print("  - Run 'python -m pSim.setup_config --summary' to see current config")