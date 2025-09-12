"""
Bindings for planetary constants
"""
from __future__ import annotations
__all__: list[str] = ['Earth', 'Moon', 'Planet']
class Earth(Planet):
    def __init__(self) -> None:
        ...
class Moon(Planet):
    def __init__(self) -> None:
        ...
class Planet:
    @property
    def j2(self) -> float:
        ...
    @property
    def j3(self) -> float:
        ...
    @property
    def mu(self) -> float:
        ...
    @property
    def name(self) -> str:
        ...
    @property
    def radius(self) -> float:
        ...
    @property
    def spice_id(self) -> int:
        ...
