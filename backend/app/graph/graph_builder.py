"""Build dependency graphs from parsed manifest data."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from .models import DependencyGraph


def build_dependency_graph(
    dependencies: Mapping[str, Iterable[str]],
) -> DependencyGraph:
    """Convert ``{package: iterable_of_dependencies}`` into a graph.

    Dependency targets not present as keys are added as leaf nodes. Duplicate
    dependencies are collapsed into one edge. Input is read-only and is never
    modified. This function expects already-parsed data; it does not execute or
    evaluate manifest contents.

    Raises:
        TypeError: If the input or any dependency collection has an invalid type.
        ValueError: If a package/dependency name is empty after trimming.
    """
    if not isinstance(dependencies, Mapping):
        raise TypeError("dependencies must be a mapping of package names to dependency iterables")

    adjacency: dict[str, set[str]] = {}
    all_nodes: set[str] = set()

    for raw_package, raw_dependencies in dependencies.items():
        if not isinstance(raw_package, str):
            raise TypeError("package names must be strings")
        package = raw_package.strip()
        if not package:
            raise ValueError("package names must not be empty")
        if isinstance(raw_dependencies, (str, bytes)) or not isinstance(raw_dependencies, Iterable):
            raise TypeError(f"dependencies for {package!r} must be an iterable of names, not a string")

        package_dependencies: set[str] = set()
        for raw_dependency in raw_dependencies:
            if not isinstance(raw_dependency, str):
                raise TypeError(f"dependency names for {package!r} must be strings")
            dependency = raw_dependency.strip()
            if not dependency:
                raise ValueError(f"dependency names for {package!r} must not be empty")
            package_dependencies.add(dependency)
            all_nodes.add(dependency)

        all_nodes.add(package)
        if package in adjacency:
            # Trimming can make distinct raw keys normalize to the same name.
            # Merge rather than silently discard either key's dependencies.
            adjacency[package].update(package_dependencies)
        else:
            adjacency[package] = package_dependencies

    for node in all_nodes:
        adjacency.setdefault(node, set())

    return DependencyGraph(
        nodes=frozenset(all_nodes),
        adjacency={node: frozenset(targets) for node, targets in adjacency.items()},
    )
