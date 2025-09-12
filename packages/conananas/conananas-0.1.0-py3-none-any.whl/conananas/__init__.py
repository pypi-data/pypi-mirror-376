""" conananas module """
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("conananas")
except PackageNotFoundError:
    __version__ = "0.0.0.dev"
