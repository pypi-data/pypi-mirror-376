"""
VirtueRed - CLI tool and Model Server for VirtueAI VirtueRed
"""
# Optionally expose commonly used classes/functions
from .client import ModelServer
from .cli import main

__version__ = "2.1.1"

__all__ = ['ModelServer', 'main']