"""Core Matrix — Central coordinator of all IGRIS subsystems.

RULE: No component talks to another directly.
All communication passes through Core Matrix.

Architecture:
    Core Matrix
    ├── Module Registry
    ├── Communication Bus
    ├── Health Monitor
    ├── Event Dispatcher
    └── Interfaces (Memory, Vision, Voice, Automation, Plugin, Skills, Security, Runtime, Communication)
"""

from .message_bus import MessageBus, Message
from .module_registry import ModuleRegistry, ModuleInfo, ModuleState
from .event_dispatcher import EventDispatcher
from .health_monitor import HealthMonitor
from .interfaces import (
    MemoryInterface,
    VisionInterface,
    VoiceInterface,
    AutomationInterface,
    PluginInterface,
    SkillsInterface,
    SecurityInterface,
    RuntimeInterface,
    CommunicationInterface,
)


class CoreMatrix:
    """Central coordinator.

    Every subsystem registers with Core Matrix.
    Every subsystem communicates through Core Matrix.
    No subsystem talks directly to another.
    """

    def __init__(self):
        self.bus = MessageBus()
        self.registry = ModuleRegistry()
        self.events = EventDispatcher()
        self.health = HealthMonitor()

        # All 9 Interfaces
        self.memory = None
        self.vision = VisionInterface()
        self.voice = None
        self.automation = None
        self.plugins = PluginInterface()
        self.skills = SkillsInterface()
        self.security = None
        self.runtime = RuntimeInterface()
        self.communication = CommunicationInterface()

        self._modules: dict[str, object] = {}
        self._boot_complete = False

    # ── Module Registration ────────────────────────────────────────────

    def register_module(self, id: str, instance: object, name: str = None, version: str = "1.0.0", metadata: dict = None):
        self._modules[id] = instance
        info = self.registry.register(id=id, name=name or id, version=version, metadata=metadata)
        self.registry.set_state(id, ModuleState.REGISTERED)
        self.events.dispatch("module.registered", {"module_id": id})
        return info

    def get_module(self, id: str) -> object | None:
        return self._modules.get(id)

    def start_module(self, id: str):
        module = self._modules.get(id)
        if module and hasattr(module, "start"):
            module.start()
        self.registry.set_state(id, ModuleState.RUNNING)
        self.events.dispatch("module.started", {"module_id": id})

    def stop_module(self, id: str):
        module = self._modules.get(id)
        if module and hasattr(module, "stop"):
            module.stop()
        self.registry.set_state(id, ModuleState.STOPPED)
        self.events.dispatch("module.stopped", {"module_id": id})

    def restart_module(self, id: str) -> bool:
        try:
            self.stop_module(id)
            self.start_module(id)
            return True
        except Exception:
            self.registry.mark_failed(id)
            return False

    def module_heartbeat(self, id: str):
        self.registry.heartbeat(id)

    def list_modules(self) -> list:
        return self.registry.to_dict()

    def get_module_state(self, id: str) -> str:
        info = self.registry.get(id)
        return info.state.value if info else "unknown"

    # ── Communication ──────────────────────────────────────────────────

    def send(self, target: str, body: dict) -> Message:
        msg = Message("command", "core_matrix", target, body)
        self.bus.publish(msg)
        return msg

    async def request(self, target: str, body: dict, timeout: float = 30.0) -> dict:
        return await self.bus.request(target, body, timeout)

    def broadcast(self, event: str, data: dict = None):
        self.bus.broadcast(event, data)
        self.events.dispatch(event, data)

    # ── Health ─────────────────────────────────────────────────────────

    def start_health_monitor(self):
        self.health.start()

    def stop_health_monitor(self):
        self.health.stop()

    def register_health_check(self, module_id: str, check_fn):
        self.health.register_check(module_id, check_fn)

    def set_health(self, module_id: str, is_healthy: bool):
        if is_healthy:
            self.registry.heartbeat(module_id)
        else:
            self.registry.mark_failed(module_id)

    # ── Interface Wires ────────────────────────────────────────────────

    def wire_memory(self, memory_manager):
        self.memory = MemoryInterface(memory_manager)

    def wire_voice(self, voice_backend):
        self.voice = VoiceInterface(voice_backend)

    def wire_automation(self, pc_control):
        self.automation = AutomationInterface(pc_control)

    def wire_security(self, pie_router, pie_anonymizer, privacy_profile):
        self.security = SecurityInterface(pie_router, pie_anonymizer, privacy_profile)

    # ── Status ─────────────────────────────────────────────────────────

    def get_status(self) -> dict:
        return {
            "modules": self.registry.to_dict(),
            "health": self.health.get_status_summary(),
            "module_count": len(self._modules),
            "boot_complete": self._boot_complete,
            "interfaces": {
                "memory": self.memory is not None,
                "vision": self.vision.is_enabled,
                "voice": self.voice.is_enabled if self.voice else False,
                "automation": self.automation is not None,
                "plugins": len(self.plugins.list_plugins()),
                "security": self.security is not None,
            },
        }

    def set_boot_complete(self):
        self._boot_complete = True
        self.broadcast("boot_complete", {"status": "ready"})
