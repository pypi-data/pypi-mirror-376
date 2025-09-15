from .vsss_base_env import BaseVSSSEnv
from .vsss_gym_env import VSSSGymEnv
from .vsss_simple_env import SimpleVSSSEnv

# Optional PettingZoo environment (only available if PettingZoo is installed)
try:
    from .vsss_pettingzoo_env import VSSSPettingZooEnv
    PETTINGZOO_ENV_AVAILABLE = True
except ImportError:
    VSSSPettingZooEnv = None
    PETTINGZOO_ENV_AVAILABLE = False

from gymnasium.envs.registration import register

# Register Gymnasium environment
register(
    id="VSSS/Env-v0",
    entry_point="pSim.vsss_gym_env:VSSSGymEnv",
    max_episode_steps=3600,
)

# Register PettingZoo environment (if available)
if PETTINGZOO_ENV_AVAILABLE:
    try:
        from pettingzoo.utils import wrappers
        # PettingZoo environments don't need explicit registration like Gymnasium
        # They are instantiated directly
        pass
    except ImportError:
        pass

# Main exports
__all__ = ['BaseVSSSEnv', 'SimpleVSSSEnv', 'VSSSGymEnv']

# Add PettingZoo environment to exports if available
if PETTINGZOO_ENV_AVAILABLE:
    __all__.append('VSSSPettingZooEnv')
