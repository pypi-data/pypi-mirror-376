#!/usr/bin/env python3
"""
HMI Control Example for Agent Team Robots

This example demonstrates using the Human-Machine Interface (HMI) for manual
control of individual agent team robots. You can switch between robots in your
team and control each one independently. Supports keyboard and joystick input.
"""

from pSim.vsss_simple_env import SimpleVSSSEnv
from pSim.modules.hmi import HMI
import numpy as np

def main():
    """Run HMI control example for agent team robots."""

    # Create environment for agent team control
    env = SimpleVSSSEnv(
        render_mode="human",
        scenario="formation",
        num_agent_robots=3,
        num_adversary_robots=3,
        color_team="blue"
    )

    print("=== HMI Agent Team Individual Control Example ===")
    print("Controls:")
    print("  Movement: WASD or controller sticks")
    print("  Robot selection: Q (next robot), E (previous robot)")
    print("  Reset: R, Exit: ESC")
    print("Note: Switch between agent robots and control each one individually")
    print()

    # Initialize HMI (use simple_mode=False for advanced features)
    hmi = HMI(dead_zone=0.1, simple_mode=False)

    # Reset environment
    obs, info = env.reset()
    print(f"Agent team: {env.num_agent_robots} robots")
    print(f"Adversary team: {env.num_adversary_robots} robots")

    # Initialize robot selection
    current_robot_id = 0
    print(f"Starting with Agent Robot {current_robot_id}")

    print("Starting control loop... (ESC to exit)")

    # Track key states for robot switching
    prev_q_pressed = False
    prev_e_pressed = False

    # Main control loop
    while hmi.active:
        # Get HMI input (simplified mode returns 3 values)
        actions, reset, active = hmi()

        if not active:  # Exit when HMI indicates exit
            break

        if reset:
            obs, info = env.reset()
            print("Environment reset!")
            continue

        # Check for robot switching using pygame directly
        import pygame
        pygame.event.pump()  # Process events
        keys = pygame.key.get_pressed()

        # Robot switching logic
        q_pressed = keys[pygame.K_q]
        e_pressed = keys[pygame.K_e]

        if q_pressed and not prev_q_pressed:
            # Next robot
            current_robot_id = (current_robot_id + 1) % env.num_agent_robots
            print(f"Switched to Agent Robot {current_robot_id}")

        if e_pressed and not prev_e_pressed:
            # Previous robot
            current_robot_id = (current_robot_id - 1) % env.num_agent_robots
            print(f"Switched to Agent Robot {current_robot_id}")

        prev_q_pressed = q_pressed
        prev_e_pressed = e_pressed

        # Create actions for all agent robots
        # Current robot gets HMI actions, others get zero actions
        team_actions = np.zeros((env.num_agent_robots, 2))
        team_actions[current_robot_id] = actions
        # Step environment with team actions
        obs, reward, terminated, truncated, info = env.step(team_actions)

        print(f"Agent Robot {current_robot_id} action: [{actions[0]:.2f}, {actions[1]:.2f}] - Reward: {reward:.3f}")

        # Handle episode termination
        if terminated or truncated:
            print("Episode ended - resetting...")
            obs, info = env.reset()

    print("✅ HMI agent team individual control example completed!")
    hmi.quit()
    env.close()

if __name__ == "__main__":
    main()