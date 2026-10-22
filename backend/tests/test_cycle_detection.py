"""Tests for directed dependency cycle detection."""

import unittest

from app.graph import build_dependency_graph, find_cycles, has_cycle


class CycleDetectionTests(unittest.TestCase):
    def test_acyclic_chain_has_no_cycle(self):
        graph = build_dependency_graph({"app": ["lib"], "lib": ["core"], "core": []})
        self.assertFalse(has_cycle(graph))
        self.assertEqual(find_cycles(graph), [])

    def test_detects_two_node_cycle(self):
        graph = build_dependency_graph({"a": ["b"], "b": ["a"]})
        self.assertTrue(has_cycle(graph))
        self.assertEqual(find_cycles(graph), [["a", "b", "a"]])

    def test_detects_self_loop(self):
        graph = build_dependency_graph({"a": ["a"]})
        self.assertTrue(has_cycle(graph))
        self.assertEqual(find_cycles(graph), [["a", "a"]])

    def test_detects_cycle_in_disconnected_component(self):
        graph = build_dependency_graph({"app": ["lib"], "x": ["y"], "y": ["x"]})
        self.assertTrue(has_cycle(graph))
        self.assertEqual(find_cycles(graph), [["x", "y", "x"]])

    def test_detects_cycle_with_tail(self):
        graph = build_dependency_graph({"app": ["a"], "a": ["b"], "b": ["c"], "c": ["a"]})
        self.assertTrue(has_cycle(graph))
        self.assertEqual(find_cycles(graph), [["a", "b", "c", "a"]])

    def test_empty_graph_has_no_cycle(self):
        graph = build_dependency_graph({})
        self.assertFalse(has_cycle(graph))
        self.assertEqual(find_cycles(graph), [])

    def test_multiple_disjoint_cycles(self):
        graph = build_dependency_graph({"a": ["b"], "b": ["a"], "x": ["y"], "y": ["x"]})
        self.assertEqual(find_cycles(graph), [["a", "b", "a"], ["x", "y", "x"]])

    def test_handles_deep_graph_without_recursion_error(self):
        size = 1500
        dependencies = {f"n{i}": [f"n{i + 1}"] for i in range(size - 1)}
        dependencies[f"n{size - 1}"] = []
        graph = build_dependency_graph(dependencies)
        self.assertFalse(has_cycle(graph))
        self.assertEqual(find_cycles(graph), [])

    def test_rejects_wrong_argument_type(self):
        with self.assertRaises(TypeError):
            has_cycle({})  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            find_cycles({})  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
