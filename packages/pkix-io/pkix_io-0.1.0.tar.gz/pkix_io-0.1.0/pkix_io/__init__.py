"""
PKIX Certificate Lifecycle Management Platform

A modern, cloud-native implementation of PKIX standards for
enterprise certificate lifecycle management.

This package is currently reserved for the PKIX platform.
Full implementation coming soon.

For more information:
- Website: https://pkix.io
- Documentation: https://docs.pkix.io
- Source Code: https://github.com/pkix-io/pkix
"""

__version__ = "0.1.0"
__author__ = "Evan Nevermore"
__email__ = "pkix-pypi@pkix.io"
__url__ = "https://pkix.io"

# Package metadata
__title__ = "pkix"
__description__ = "PKIX Certificate Lifecycle Management Platform"
__license__ = "TBD"  # License to be determined
__copyright__ = "Copyright (c) 2025 Evan Nevermore"

# Version info tuple for programmatic access
VERSION_INFO = tuple(map(int, __version__.split('.')))


def get_version():
    """
    Get the package version string.

    Returns:
        str: The current package version
    """
    return __version__


def get_info():
    """
    Get package information.

    Returns:
        dict: Package metadata
    """
    return {
        "name": __title__,
        "version": __version__,
        "description": __description__,
        "author": __author__,
        "email": __email__,
        "url": __url__,
        "license": __license__,
        "copyright": __copyright__,
    }


# Reserved namespace - implementation coming soon
class PKIXReserved:
    """
    Reserved placeholder for PKIX functionality.

    This class serves as a placeholder to reserve the package namespace.
    Full implementation will be available in future releases.
    """

    def __init__(self):
        self.version = __version__
        self.status = "reserved"

    def __str__(self):
        return f"PKIX v{self.version} - Package Reserved"

    def __repr__(self):
        return f"PKIXReserved(version='{self.version}')"


# Default instance for basic usage
pkix = PKIXReserved()

# Export main components
__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__url__",
    "get_version",
    "get_info",
    "PKIXReserved",
    "pkix",
]