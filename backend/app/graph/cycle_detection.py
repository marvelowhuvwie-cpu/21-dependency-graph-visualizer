"""Cycle detection for directed dependency graphs."""

from __future__ import annotations

from collections.abc import Iterator

from .models import DependencyGraph


def has_cycle(graph: DependencyGraph) -> bool:
    """Return ``True`` if the directed graph contains at least one cycle.

    Uses iterative depth-first search with three states: unseen, active, and
    complete. An edge to an active node proves a directed cycle exists. The
    iterative implementation avoids Python recursion-depth failures on large
    dependency graphs. Runtime is O(V + E).
    """
    if not isinstance(graph, DependencyGraph):
        raise TypeError("graph must be a DependencyGraph")

    unseen, active, complete = 0, 1, 2
    state: dict[str, int] = {node: unseen for node in graph.nodes}

    for start in sorted(graph.nodes):
        if state[start] != unseen:
            continue
        state[start] = active
        stack: list[tuple[str, Iterator[str]]] = [(start, iter(sorted(graph.adjacency[start])))]

        while stack:
            node, neighbors = stack[-1]
            try:
                neighbor = next(neighbors)
            except StopIteration:
                state[node] = complete
                stack.pop()
                continue

            if state[neighbor] == active:
                return True
            if state[neighbor] == unseen:
                state[neighbor] = active
                stack.append((neighbor, iter(sorted(graph.adjacency[neighbor]))))

    return False

def find_cycles(graph: DependencyGraph) -> list[list[str]]:
    """Return deterministic cycle witnesses discovered by DFS.

    Each returned path starts and ends at the same node. This returns useful
    witnesses for detected back edges rather than promising every possible
    simple cycle (which can be exponentially numerous in a dense graph).
    A self-loop is represented as ``[node, node]``. Duplicate witnesses are
    removed by canonicalizing their rotations. Traversal is iterative to avoid
    recursion-depth failures on deep graphs.
    """
    if not isinstance(graph, DependencyGraph):
        raise TypeError("graph must be a DependencyGraph")

    state: dict[str, int] = {node: 0 for node in graph.nodes}  # 0 unseen, 1 active, 2 complete
    path: list[str] = []
    path_positions: dict[str, int] = {}
    witnesses: dict[tuple[str, ...], list[str]] = {}

    def canonical_cycle(cycle_without_repeat: list[str]) -> tuple[str, ...]:
        rotations = [
            tuple(cycle_without_repeat[index:] + cycle_without_repeat[:index])
            for index in range(len(cycle_without_repeat))
        ]
        return min(rotations)

    for start in sorted(graph.nodes):
        if state[start] != 0:
            continue
        state[start] = 1
        path_positions[start] = len(path)
        path.append(start)
        stack: list[tuple[str, Iterator[str]]] = [(start, iter(sorted(graph.adjacency[start])))]

        while stack:
            node, neighbors = stack[-1]
            try:
                neighbor = next(neighbors)
            except StopIteration:
                stack.pop()
                state[node] = 2
                path.pop()
                path_positions.pop(node, None)
                continue

            if state[neighbor] == 0:
                state[neighbor] = 1
                path_positions[neighbor] = len(path)
                path.append(neighbor)
                stack.append((neighbor, iter(sorted(graph.adjacency[neighbor]))))
            elif state[neighbor] == 1:
                cycle = path[path_positions[neighbor]:] + [neighbor]
                key = canonical_cycle(cycle[:-1])
                witnesses.setdefault(key, cycle)

    return [witnesses[key] for key in sorted(witnesses)]

