"""Allow core tests to run in minimal build containers without runtime wheels."""
import sys
import types

try:
    import psutil  # noqa: F401
except ImportError:
    module = types.ModuleType("psutil")
    class Error(Exception): pass
    class NoSuchProcess(Error): pass
    class AccessDenied(Error): pass
    class ZombieProcess(Error): pass
    module.Error = Error
    module.NoSuchProcess = NoSuchProcess
    module.AccessDenied = AccessDenied
    module.ZombieProcess = ZombieProcess
    module.Process = object
    module.process_iter = lambda *_args, **_kwargs: []
    module.wait_procs = lambda processes, timeout: (processes, [])
    sys.modules["psutil"] = module
