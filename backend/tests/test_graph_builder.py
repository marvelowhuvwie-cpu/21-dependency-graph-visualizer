"""Tests for dependency graph construction and graph statistics."""

import unittest

from backend.app.graph import DependencyGraph, build_dependency_graph


class GraphBuilderTests(unittest.TestCase):
    def test_builds_nodes_and_directed_edges(self):
        graph = build_dependency_graph({"app": ["requests", "click"], "requests": ["urllib3"]})
        self.assertEqual(graph.nodes, frozenset({"app", "requests", "click", "urllib3"}))
        self.assertEqual(
            graph.edges(),
            (("app", "click"), ("app", "requests"), ("requests", "urllib3")),
        )

    def test_dependency_only_nodes_become_leaves(self):
        graph = build_dependency_graph({"app": ["missing-from-keys"]})
        self.assertEqual(graph.neighbors("missing-from-keys"), frozenset())
        self.assertTrue(graph.has_node("missing-from-keys"))

    def test_duplicate_edges_are_collapsed(self):
        graph = build_dependency_graph({"app": ["lib", "lib", "lib"]})
        self.assertEqual(graph.edge_count, 1)

    def test_whitespace_is_trimmed_and_colliding_keys_are_merged(self):
        graph = build_dependency_graph({" app ": [" lib "], "app": ["tool"]})
        self.assertEqual(graph.neighbors("app"), frozenset({"lib", "tool"}))

    def test_empty_mapping_produces_empty_graph(self):
        graph = build_dependency_graph({})
        self.assertEqual(graph.nodes, frozenset())
        self.assertEqual(graph.statistics(), {"node_count": 0, "edge_count": 0})

    def test_isolated_node_is_preserved(self):
        graph = build_dependency_graph({"standalone": []})
        self.assertEqual(graph.statistics(), {"node_count": 1, "edge_count": 0})

    def test_input_is_not_mutated(self):
        source = {"app": ["lib"]}
        build_dependency_graph(source)
        self.assertEqual(source, {"app": ["lib"]})

    def test_rejects_non_mapping_input(self):
        with self.assertRaises(TypeError):
            build_dependency_graph([("app", ["lib"])])  # type: ignore[arg-type]

    def test_rejects_string_as_dependency_collection(self):
        with self.assertRaises(TypeError):
            build_dependency_graph({"app": "lib"})  # type: ignore[dict-item]

    def test_rejects_empty_package_or_dependency_name(self):
        with self.assertRaises(ValueError):
            build_dependency_graph({"  ": []})
        with self.assertRaises(ValueError):
            build_dependency_graph({"app": ["  "]})

    def test_rejects_non_string_dependency_name(self):
        with self.assertRaises(TypeError):
            build_dependency_graph({"app": [42]})  # type: ignore[list-item]

    def test_graph_is_immutable(self):
        graph = DependencyGraph(nodes=frozenset({"app"}), adjacency={"app": frozenset()})
        with self.assertRaises(TypeError):
            graph.adjacency["app"] = frozenset({"other"})  # type: ignore[index]


if __name__ == "__main__":
    unittest.main()
