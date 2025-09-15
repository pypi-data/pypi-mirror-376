import importlib.metadata

try:
    __version__ = importlib.metadata.version("soika-memory")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.1.0"  # fallback version

from soika_memory.client.main import AsyncMemoryClient, MemoryClient  # noqa
from soika_memory.memory.main import AsyncMemory, Memory  # noqa
