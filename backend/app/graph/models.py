"""Immutable data model for a directed package-dependency graph."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


def _validate_name(name: object, *, field: str = "package name") -> str:
    """Return a normalized graph identifier or raise a useful error."""
    if not isinstance(name, str):
        raise TypeError(f"{field} must be a string, got {type(name).__name__}")
    normalized = name.strip()
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    return normalized


@dataclass(frozen=True, slots=True)
class DependencyGraph:
    """A directed graph where ``A -> B`` means package A depends on B.

    The graph is immutable after construction. Dependency targets that have no
    own dependency list are still represented as nodes with no outgoing edges.
    """

    nodes: frozenset[str]
    adjacency: Mapping[str, frozenset[str]]

    def __post_init__(self) -> None:
        if not isinstance(self.nodes, (set, frozenset, list, tuple)):
            raise TypeError("nodes must be a collection of package names")
        normalized_nodes = frozenset(_validate_name(node) for node in self.nodes)
        if not isinstance(self.adjacency, Mapping):
            raise TypeError("adjacency must be a mapping of nodes to dependencies")

        normalized_adjacency: dict[str, frozenset[str]] = {}
        for raw_source, raw_targets in self.adjacency.items():
            source = _validate_name(raw_source, field="source node")
            if isinstance(raw_targets, (str, bytes)):
                raise TypeError(f"dependencies for {source!r} must be a collection, not a string")
            try:
                targets = frozenset(_validate_name(target, field="dependency name") for target in raw_targets)
            except TypeError as exc:
                raise TypeError(f"dependencies for {source!r} must be iterable") from exc
            normalized_adjacency[source] = targets

        if set(normalized_adjacency) - normalized_nodes:
            unknown = sorted(set(normalized_adjacency) - normalized_nodes)
            raise ValueError(f"adjacency contains nodes missing from nodes: {unknown}")
        for source, targets in normalized_adjacency.items():
            missing = targets - normalized_nodes
            if missing:
                raise ValueError(f"dependencies of {source!r} are missing graph nodes: {sorted(missing)}")

        # Ensure every node has an adjacency entry, including isolated nodes.
        complete_adjacency = {
            node: normalized_adjacency.get(node, frozenset()) for node in normalized_nodes
        }
        object.__setattr__(self, "nodes", normalized_nodes)
        object.__setattr__(self, "adjacency", MappingProxyType(complete_adjacency))

    @property
    def node_count(self) -> int:
        """Number of distinct package nodes."""
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        """Number of distinct directed dependency edges."""
        return sum(len(targets) for targets in self.adjacency.values())

    def neighbors(self, package: str) -> frozenset[str]:
        """Return the dependencies of *package*, or raise ``KeyError`` if absent."""
        name = _validate_name(package)
        try:
            return self.adjacency[name]
        except KeyError:
            raise KeyError(f"package {name!r} is not in the graph") from None

    def has_node(self, package: str) -> bool:
        """Return whether *package* is represented in the graph."""
        return _validate_name(package) in self.nodes

    def edges(self) -> tuple[tuple[str, str], ...]:
        """Return all directed edges in deterministic lexicographic order."""
        return tuple(
            (source, target)
            for source in sorted(self.nodes)
            for target in sorted(self.adjacency[source])
        )

    def statistics(self) -> dict[str, int]:
        """Return basic graph statistics in a serialization-friendly mapping."""
        return {"node_count": self.node_count, "edge_count": self.edge_count}
