# pSim Documentation

[![PyPI version](https://badge.fury.io/py/pSim.svg)](https://badge.fury.io/py/pSim)
[![License: GPLv3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python versions](https://img.shields.io/pypi/pyversions/pSim.svg)](https://pypi.org/project/pSim)
[![Documentation](https://img.shields.io/badge/docs-mkdocs-blue)](https://juliodltv.github.io/pSim/)

<div align="center">
    <img
        src="docs/assets/logov2.png"
        alt="pSim Logo"
        width="500"
        onerror="this.onerror=null; this.src='assets/logov2.png';"
    />
    <br>
    <h1>pSim: Very Small Size Soccer Simulation Environment</h1>
    <p><em>Comprehensive simulation platform for autonomous robotic soccer development</em></p>
</div>

---

## Welcome to pSim

**pSim** is a comprehensive, pythonic simulation environment specifically designed for the Very Small Size Soccer (VSSS) competition. It provides researchers, students, and developers with powerful tools to develop, test, and validate autonomous robotic soccer strategies and algorithms.

Whether you're working on traditional control algorithms, reinforcement learning, or multi-agent coordination, pSim offers the flexibility and performance you need.

---

## Quick Start

### Installation

pSim uses [uv](https://docs.astral.sh/uv/) for fast, reliable package management. See the [installation guide](https://juliodltv.github.io/pSim/installation/) for complete setup instructions including uv installation.

```bash
# Quick install with uv
uv pip install pSim

# Or with optional dependencies
uv pip install pSim[gym]   # For Gymnasium support
uv pip install pSim[zoo]   # For PettingZoo support
uv pip install pSim[all]   # For all optional dependencies
```

### First Simulation

```python
from pSim.simple_env import SimpleEnv

# Create your first simulation
env = SimpleEnv(render_mode="human", scenario="formation")
obs, info = env.reset()

# Run simulation steps
for step in range(1000):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        obs, info = env.reset()
```

---

## Environment Types

pSim provides three main environment types, each designed for different use cases:

### SimpleEnv - Traditional Control
Perfect for traditional control algorithms, manual testing, and educational purposes:

```python
from pSim.simple_env import SimpleEnv
import numpy as np

env = SimpleEnv(
    render_mode="human",
    scenario="formation",
    num_agent_robots=3,
    num_adversary_robots=3
)

obs, info = env.reset()
for step in range(1000):
    action = np.random.uniform(-1, 1, (env.action_robots, 2))
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        obs, info = env.reset()
```

#### Manual Control with Joystick

<!-- ```python title="Manual Control with Joystick" linenums="1" hl_lines="2 6 10-16 22-23" -->
```python hl_lines="2 4 17-21 28"
from pSim.simple_env import SimpleEnv
from pSim.modules.hmi import HMI

hmi = HMI()

env = SimpleEnv(
    render_mode="human",
    scenario="formation",
    num_agent_robots=3,
    num_adversary_robots=3
)

obs, info = env.reset()
while hmi.active:
    actions, reset, exit_requested = hmi()

    if exit_requested:
        break
    if reset:
        obs, info = env.reset()
        continue

    obs, reward, terminated, truncated, info = env.step(actions)

    if terminated or truncated:
        obs, info = env.reset()

hmi.quit()
env.close()
```

### VSSSGymEnv - Reinforcement Learning
Full Gymnasium compatibility for single-agent reinforcement learning:

```python
from pSim.vsss_gym import VSSSGymEnv
from gymnasium.wrappers import FlattenObservation

env = FlattenObservation(VSSSGymEnv(
    render_mode="human",
    scenario="formation",
    num_agent_robots=3,
    num_adversary_robots=3
))

obs, info = env.reset()
for step in range(1000):
    action = env.action_space.sample()
    obs, reward, terminated, truncated, info = env.step(action)
    if terminated or truncated:
        obs, info = env.reset()
```

### VSSSPettingZooEnv - Multi-Agent Learning
PettingZoo interface for multi-agent reinforcement learning:

```python
from pSim.vsss_pettingzoo import VSSSPettingZooEnv

env = VSSSPettingZooEnv(
    render_mode="human",
    scenario="formation",
    num_agent_robots=3,
    num_adversary_robots=3
)

obs, info = env.reset()
for step in range(1000):
    actions = {agent: env.action_space(agent).sample() for agent in env.agents}
    obs, rewards, terminations, truncations, infos = env.step(actions)
    if any(terminations.values()) or any(truncations.values()):
        obs, info = env.reset()
```

---

## Key Features

### Flexible Robot Control
Easy-to-use JSON-based configuration for scenarios, robot behaviors, and simulation parameters. Mix controllable agents with automatic behaviors:

```json
{
  "scenarios": {
    "formation": {
      "agent_robots": {
        "movement_types": ["action", "ou", "no_move"]
      },
      "adversary_robots": {
        "movement_types": ["ou", "ou", "ou"]
      }
    }
  }
}
```

- **`"action"`**: Controllable by your agent/algorithm
- **`"ou"`**: Ornstein-Uhlenbeck automatic movement
- **`"no_move"`**: Stationary robots

### Realistic Physics
Box2D-powered physics simulation with customizable parameters for accurate robot and ball dynamics.

### Human-Machine Interface

- **Keyboard Controls**: Full keyboard input with intuitive mappings
- **Joystick Support**: Universal controller compatibility
- **Robot Switching**: Dynamic selection between controllable robots
- **Team Management**: Control different teams independently
- **Ball Control Mode**: Direct ball manipulation

---

## Use Cases

### Traditional Control
- PID controllers, MPC, and other traditional methods
- Path planning and trajectory optimization
- Formation control and cooperative behaviors

### Reinforcement Learning
- Compatible with Stable Baselines 3, Ray RLlib, and other RL libraries
- Customizable reward functions and observation spaces
- Curriculum learning through scenario configuration

### Research & Education
- Multi-agent coordination studies
- Emergent behavior analysis
- Algorithm benchmarking and comparison

### Competition Preparation
- Strategy development and testing
- Opponent modeling and adaptation
- Performance analysis and optimization

---

## Documentation Structure

### Getting Started
- **[Installation](https://juliodltv.github.io/pSim/installation/)**: Complete setup instructions
- **[Usage Guide](https://juliodltv.github.io/pSim/usage/)**: Comprehensive usage examples and tutorials
- **[Configuration](https://juliodltv.github.io/pSim/usage/#configuration-system)**: Detailed configuration options

### Examples
- **[Configuration Demo](https://juliodltv.github.io/pSim/examples/configuration_demo/)**: Setting up robot behaviors
- **[HMI Control](https://juliodltv.github.io/pSim/examples/hmi_control/)**: Manual control examples
- **[Simple Environment](https://juliodltv.github.io/pSim/examples/simple_env/)**: Traditional control examples
- **[Gym Environment](https://juliodltv.github.io/pSim/examples/gym_env/)**: Reinforcement learning examples
- **[PettingZoo Environment](https://juliodltv.github.io/pSim/examples/pettingzoo_env/)**: Multi-agent examples

### API Reference
- **[API Documentation](https://juliodltv.github.io/pSim/api/)**: Complete API reference

---

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/juliodltv/pSim/issues)
- **Discussions**: [GitHub Discussions](https://github.com/juliodltv/pSim/discussions)
- **Documentation**: [Full Documentation](https://juliodltv.github.io/pSim/)

---

## Contributing

We welcome contributions! Please see our [Contributing Guide](https://github.com/juliodltv/pSim/blob/main/CONTRIBUTING.md) for details.

---

<div align="center">
    <h2>Ready to start developing robotic soccer strategies?</h2>
    <p>
        <a href="https://juliodltv.github.io/pSim/installation/" class="md-button md-button--primary">Get Started</a>
        <a href="https://juliodltv.github.io/pSim/examples/" class="md-button">View Examples</a>
        <a href="https://github.com/juliodltv/pSim" class="md-button">GitHub Repository</a>
    </p>
</div>