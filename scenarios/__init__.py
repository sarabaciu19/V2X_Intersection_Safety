"""
scenarios/__init__.py — Auto-discovers all scenario modules in this package.

Each scenario module must define:
  NAME        : str   — unique key used as scenario identifier
  DESCRIPTION : str   — human-readable description
  NO_SEMAPHORE: bool  — True if the scenario runs without a semaphore
  VEHICLES    : list  — list of vehicle definition dicts

Exported:
  SCENARIOS             : dict[str, list]  — NAME → VEHICLES
  NO_SEMAPHORE_SCENARIOS: set[str]         — set of scenario names without semaphore
  SCENARIO_DESCRIPTIONS : dict[str, str]   — NAME → DESCRIPTION
"""

import importlib
import pkgutil
from pathlib import Path

SCENARIOS: dict = {}
NO_SEMAPHORE_SCENARIOS: set = set()
SCENARIO_DESCRIPTIONS: dict = {}
AEB_DISABLED_SCENARIOS: set = set()

_package_dir = Path(__file__).parent

for _module_info in pkgutil.iter_modules([str(_package_dir)]):
    _name = _module_info.name
    if _name.startswith('_') or _name in ('scenario_base',):
        continue
    try:
        _mod = importlib.import_module(f'scenarios.{_name}')
        if hasattr(_mod, 'NAME') and hasattr(_mod, 'VEHICLES'):
            SCENARIOS[_mod.NAME] = _mod.VEHICLES
            SCENARIO_DESCRIPTIONS[_mod.NAME] = getattr(_mod, 'DESCRIPTION', '')
            if getattr(_mod, 'NO_SEMAPHORE', False):
                NO_SEMAPHORE_SCENARIOS.add(_mod.NAME)
            if getattr(_mod, 'AEB_DISABLED', False):
                AEB_DISABLED_SCENARIOS.add(_mod.NAME)
    except Exception as e:
        import warnings
        warnings.warn(f'Could not load scenario module "{_name}": {e}')

