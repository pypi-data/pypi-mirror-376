import numpy as np
from typing import Tuple, Dict, Any


class RewardSystem:
    """Handles reward calculation for the soccer simulation."""

    def __init__(self, truncated_time: int = 3600):
        """Initialize reward system.

        Args:
            truncated_time: Maximum number of steps before truncation
        """
        self.truncated_time = truncated_time
        self.time_step = 0

    def reset(self):
        """Reset the reward system for a new episode."""
        self.time_step = 0

    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

    def calculate_reward(self, simulator) -> Tuple[float, bool, bool]:
        """Calculate reward, termination, and truncation status.

        Args:
            simulator: The game simulator instance

        Returns:
            Tuple of (reward, terminated, truncated)
        """
        # Goal reward
        ball_x = simulator.ball_body.position.x
        if ball_x < -0.765:
            r_goal = 0  # Goal for agent (left goal)
        elif ball_x > 0.765:
            r_goal = 1  # Goal for adversary (right goal)
        else:
            r_goal = 0

        terminated = r_goal != 0

        # Time penalty
        r_time = -1

        # Check truncation
        truncated = self.time_step >= self.truncated_time

        # Ball movement reward
        ball_velocity = simulator.ball_body.linearVelocity
        if np.linalg.norm(ball_velocity) > 0.05:
            # Reward ball movement toward adversary goal, penalize toward agent goal
            agent_goal = np.array([-0.8, 0])
            adversary_goal = np.array([0.8, 0])

            similarity_to_agent_goal = self._cosine_similarity(
                ball_velocity,
                agent_goal - simulator.ball_body.position
            )
            similarity_to_adversary_goal = self._cosine_similarity(
                ball_velocity,
                adversary_goal - simulator.ball_body.position
            )

            r_ball_movement = (
                np.tanh(similarity_to_adversary_goal) -
                np.tanh(similarity_to_agent_goal) -
                3 * np.tanh(1)
            )
        else:
            # Penalize stationary ball
            r_ball_movement = -5 * np.tanh(1)

        # Contact rewards
        r_contact_robot_ball = (
            0.5 if simulator.contact_listener.collision_robot_ball else 0
        )
        r_contact_robot_wall = (
            -1.0 if simulator.contact_listener.collision_robot_wall else 0
        )

        # Reset collision flags
        simulator.contact_listener.collision_robot_ball = False
        simulator.contact_listener.collision_robot_wall = False

        # Combine all reward components
        reward_components = {
            'time': r_time,
            'goal': r_goal * 10,
            'robot_ball_contact': r_contact_robot_ball,
            'robot_wall_contact': r_contact_robot_wall,
            'ball_movement': r_ball_movement,
        }

        total_reward = sum(reward_components.values())

        return total_reward, terminated, truncated

    def calculate_detailed_reward(self, simulator) -> Tuple[float, bool, bool, Dict[str, float]]:
        """Calculate reward with detailed breakdown.

        Args:
            simulator: The game simulator instance

        Returns:
            Tuple of (total_reward, terminated, truncated, reward_breakdown)
        """
        # Goal reward
        ball_x = simulator.ball_body.position.x
        if ball_x < -0.765:
            r_goal = 0  # Goal for agent (left goal)
        elif ball_x > 0.765:
            r_goal = 1  # Goal for adversary (right goal)
        else:
            r_goal = 0

        terminated = r_goal != 0

        # Time penalty
        r_time = -1

        # Check truncation
        truncated = self.time_step >= self.truncated_time

        # Ball movement reward
        ball_velocity = simulator.ball_body.linearVelocity
        if np.linalg.norm(ball_velocity) > 0.05:
            agent_goal = np.array([-0.8, 0])
            adversary_goal = np.array([0.8, 0])

            similarity_to_agent_goal = self._cosine_similarity(
                ball_velocity,
                agent_goal - simulator.ball_body.position
            )
            similarity_to_adversary_goal = self._cosine_similarity(
                ball_velocity,
                adversary_goal - simulator.ball_body.position
            )

            r_ball_movement = (
                np.tanh(similarity_to_adversary_goal) -
                np.tanh(similarity_to_agent_goal) -
                3 * np.tanh(1)
            )
        else:
            r_ball_movement = -5 * np.tanh(1)

        # Contact rewards
        r_contact_robot_ball = (
            0.5 if simulator.contact_listener.collision_robot_ball else 0
        )
        r_contact_robot_wall = (
            -1.0 if simulator.contact_listener.collision_robot_wall else 0
        )

        # Reset collision flags
        simulator.contact_listener.collision_robot_ball = False
        simulator.contact_listener.collision_robot_wall = False

        # Reward breakdown
        reward_breakdown = {
            'time': r_time,
            'goal': r_goal * 10,
            'robot_ball_contact': r_contact_robot_ball,
            'robot_wall_contact': r_contact_robot_wall,
            'ball_movement': r_ball_movement,
        }

        total_reward = sum(reward_breakdown.values())

        return total_reward, terminated, truncated, reward_breakdown

    def step(self):
        """Increment the time step."""
        self.time_step += 1


class CustomRewardSystem(RewardSystem):
    """Extended reward system with additional custom rewards."""

    def __init__(self, truncated_time: int = 3600, **kwargs):
        """Initialize custom reward system.

        Args:
            truncated_time: Maximum number of steps before truncation
            **kwargs: Additional configuration parameters
        """
        super().__init__(truncated_time)
        self.config = kwargs

    def calculate_reward(self, simulator) -> Tuple[float, bool, bool]:
        """Calculate reward with custom components."""
        # Get base reward
        base_reward, terminated, truncated = super().calculate_reward(simulator)

        # Add custom reward components here
        # Example: Distance-based reward
        if 'distance_reward' in self.config and self.config['distance_reward']:
            ball_pos = simulator.ball_body.position
            robot_pos = simulator.robots_agent[0].position
            distance = np.linalg.norm(np.array([ball_pos.x, ball_pos.y]) -
                                    np.array([robot_pos.x, robot_pos.y]))
            r_distance = -distance / 10  # Normalize distance reward
            base_reward += r_distance

        return base_reward, terminated, truncated