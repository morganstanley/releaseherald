import pluggy

from releaseherald.plugins.interface import CommitInfo  # noqa: F401

hookimpl = pluggy.HookimplMarker("releaseherald")
