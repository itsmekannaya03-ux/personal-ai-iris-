"""
PluginSystem — Extensible plugin architecture for the AI.

Allows third-party extensions to register capabilities:
  - Tools (calculator, weather, stocks, etc.)
  - Skills (new behaviors)
  - Data sources (APIs, databases)
  - UI components (future)
"""

import logging
import importlib
import inspect
import os
import sys
from typing import Any, Callable, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("iris.plugins")


@dataclass
class PluginManifest:
    name: str
    version: str
    author: str
    description: str
    entry_point: str
    dependencies: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)


@dataclass
class Plugin:
    manifest: PluginManifest
    module: Any = None
    instance: Any = None
    enabled: bool = True
    hooks: dict[str, Callable] = field(default_factory=dict)


class PluginSystem:
    """
    Manages plugin lifecycle: discovery, loading, enabling,
    disabling, and hook registration.
    """

    def __init__(self, plugin_dir: Optional[str] = None):
        self.plugin_dir = plugin_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "plugins"
        )
        self._plugins: dict[str, Plugin] = {}
        self._hooks: dict[str, list[Callable]] = {}
        self._discovered = False

        os.makedirs(self.plugin_dir, exist_ok=True)
        logger.info(f"Plugin system initialized (dir: {self.plugin_dir})")

    def discover_plugins(self):
        """Scan the plugin directory for installable plugins."""
        self._discovered = True
        if not os.path.exists(self.plugin_dir):
            return

        for item in os.listdir(self.plugin_dir):
            plugin_path = os.path.join(self.plugin_dir, item)
            if os.path.isdir(plugin_path) and os.path.exists(os.path.join(plugin_path, "__init__.py")):
                manifest_file = os.path.join(plugin_path, "manifest.json")
                if os.path.exists(manifest_file):
                    try:
                        import json
                        with open(manifest_file, "r") as f:
                            data = json.load(f)
                        manifest = PluginManifest(**data)
                        self._plugins[manifest.name] = Plugin(manifest=manifest)
                        logger.info(f"Discovered plugin: {manifest.name} v{manifest.version}")
                    except Exception as e:
                        logger.error(f"Failed to load plugin manifest '{item}': {e}")

        logger.info(f"Plugin discovery complete: {len(self._plugins)} found")

    def load_plugin(self, name: str) -> bool:
        """Load and initialize a plugin."""
        if name not in self._plugins:
            logger.error(f"Plugin '{name}' not found")
            return False

        plugin = self._plugins[name]
        if plugin.instance is not None:
            logger.info(f"Plugin '{name}' already loaded")
            return True

        try:
            plugin_path = os.path.join(self.plugin_dir, name)
            if plugin_path not in sys.path:
                sys.path.insert(0, plugin_path)

            module = importlib.import_module(name)
            plugin.module = module

            if hasattr(module, "create_plugin"):
                plugin.instance = module.create_plugin()
            elif hasattr(module, "Plugin"):
                plugin.instance = module.Plugin()

            if plugin.instance and hasattr(plugin.instance, "on_load"):
                plugin.instance.on_load()

            plugin.enabled = True
            logger.info(f"Plugin loaded: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to load plugin '{name}': {e}")
            return False

    def unload_plugin(self, name: str) -> bool:
        if name not in self._plugins:
            return False
        plugin = self._plugins[name]
        if plugin.instance and hasattr(plugin.instance, "on_unload"):
            try:
                plugin.instance.on_unload()
            except Exception as e:
                logger.error(f"Plugin unload error '{name}': {e}")
        plugin.instance = None
        plugin.enabled = False
        logger.info(f"Plugin unloaded: {name}")
        return True

    def enable_plugin(self, name: str) -> bool:
        if name not in self._plugins:
            return False
        self._plugins[name].enabled = True
        logger.info(f"Plugin enabled: {name}")
        return True

    def disable_plugin(self, name: str) -> bool:
        if name not in self._plugins:
            return False
        self._plugins[name].enabled = False
        logger.info(f"Plugin disabled: {name}")
        return True

    def register_hook(self, plugin_name: str, event: str, callback: Callable):
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(callback)
        if plugin_name in self._plugins:
            self._plugins[plugin_name].hooks[event] = callback

    def trigger_hook(self, event: str, *args, **kwargs) -> list[Any]:
        results = []
        for callback in self._hooks.get(event, []):
            try:
                results.append(callback(*args, **kwargs))
            except Exception as e:
                logger.error(f"Hook error '{event}': {e}")
        return results

    def get_plugin(self, name: str) -> Optional[Plugin]:
        return self._plugins.get(name)

    def list_plugins(self) -> list[dict]:
        return [
            {
                "name": p.manifest.name,
                "version": p.manifest.version,
                "author": p.manifest.author,
                "description": p.manifest.description,
                "enabled": p.enabled,
                "loaded": p.instance is not None,
            }
            for p in self._plugins.values()
        ]

    def get_status(self) -> dict:
        return {
            "plugin_dir": self.plugin_dir,
            "total": len(self._plugins),
            "loaded": sum(1 for p in self._plugins.values() if p.instance is not None),
            "enabled": sum(1 for p in self._plugins.values() if p.enabled),
            "plugins": self.list_plugins(),
        }
