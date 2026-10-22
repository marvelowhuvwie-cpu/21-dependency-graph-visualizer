from collections.abc import Callable, Mapping
from typing import Any


class AnalysisError(Exception):
    """An expected error during dependency analysis."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 422,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def validate_analysis_result(result: Any) -> dict:
    """Validate and normalize the public API response structure."""

    if not isinstance(result, Mapping):
        raise AnalysisError(
            "INVALID_ANALYSIS_RESULT",
            "The analyzer returned an invalid result.",
            500,
        )

    nodes = result.get("nodes")
    edges = result.get("edges")
    cycles = result.get("cycles")
    summary = result.get("summary")

    if not isinstance(nodes, list):
        raise AnalysisError(
            "INVALID_ANALYSIS_RESULT",
            "The analyzer returned invalid nodes.",
            500,
        )

    if not isinstance(edges, list):
        raise AnalysisError(
            "INVALID_ANALYSIS_RESULT",
            "The analyzer returned invalid edges.",
            500,
        )

    if not isinstance(cycles, list):
        raise AnalysisError(
            "INVALID_ANALYSIS_RESULT",
            "The analyzer returned invalid cycles.",
            500,
        )

    if not isinstance(summary, Mapping):
        raise AnalysisError(
            "INVALID_ANALYSIS_RESULT",
            "The analyzer returned an invalid summary.",
            500,
        )

    normalized_nodes = []
    node_ids = set()

    for node in nodes:
        if not isinstance(node, Mapping):
            raise AnalysisError(
                "INVALID_ANALYSIS_RESULT",
                "A graph node is invalid.",
                500,
            )

        node_id = node.get("id")
        label = node.get("label")
        node_type = node.get("type")
        version = node.get("version")

        if (
            not isinstance(node_id, str)
            or not node_id
            or len(node_id) > 2048
            or not isinstance(label, str)
            or not label
            or node_type not in {"project", "package"}
            or (
                version is not None
                and not isinstance(version, str)
            )
        ):
            raise AnalysisError(
                "INVALID_ANALYSIS_RESULT",
                "A graph node contains invalid fields.",
                500,
            )

        if node_id in node_ids:
            raise AnalysisError(
                "INVALID_ANALYSIS_RESULT",
                "Graph node IDs must be unique.",
                500,
            )

        node_ids.add(node_id)

        normalized_nodes.append({
            "id": node_id,
            "label": label,
            "type": node_type,
            "version": version,
        })

    normalized_edges = []
    edge_pairs = set()

    for edge in edges:
        if not isinstance(edge, Mapping):
            raise AnalysisError(
                "INVALID_ANALYSIS_RESULT",
                "A graph edge is invalid.",
                500,
            )

        source = edge.get("source")
        target = edge.get("target")

        if (
            not isinstance(source, str)
            or not isinstance(target, str)
            or source not in node_ids
            or target not in node_ids
        ):
            raise AnalysisError(
                "INVALID_ANALYSIS_RESULT",
                "An edge references an unknown node.",
                500,
            )

        pair = (source, target)

        if pair in edge_pairs:
            raise AnalysisError(
                "INVALID_ANALYSIS_RESULT",
                "Duplicate graph edges are not allowed.",
                500,
            )

        edge_pairs.add(pair)
        normalized_edges.append({
            "source": source,
            "target": target,
        })

    normalized_cycles = []

    for cycle in cycles:
        if (
            not isinstance(cycle, list)
            or not cycle
            or any(
                not isinstance(node_id, str)
                or node_id not in node_ids
                for node_id in cycle
            )
        ):
            raise AnalysisError(
                "INVALID_ANALYSIS_RESULT",
                "A detected cycle references invalid nodes.",
                500,
            )

        normalized_cycles.append(cycle)

    project_name = summary.get("projectName")

    if not isinstance(project_name, str) or not project_name:
        raise AnalysisError(
            "INVALID_ANALYSIS_RESULT",
            "The analyzer did not return a valid project name.",
            500,
        )

    return {
        "summary": {
            "projectName": project_name,
            "nodeCount": len(normalized_nodes),
            "edgeCount": len(normalized_edges),
            "cycleCount": len(normalized_cycles),
        },
        "nodes": normalized_nodes,
        "edges": normalized_edges,
        "cycles": normalized_cycles,
    }


def analyze_manifest(
    manifest: dict,
    filename: str,
    analyzer: Callable | None = None,
) -> dict:
    """Delegate manifest analysis to the team's integrated analyzer."""

    if not isinstance(manifest, dict):
        raise AnalysisError(
            "INVALID_MANIFEST",
            "The manifest must be a JSON object.",
        )

    if filename not in {"package.json", "package-lock.json"}:
        raise AnalysisError(
            "UNSUPPORTED_FILE",
            "The manifest format is not supported.",
            415,
        )

    if analyzer is None:
        raise AnalysisError(
            "ANALYZER_NOT_CONFIGURED",
            (
                "The manifest parser, graph builder, and cycle detector "
                "have not yet been connected to the Flask application."
            ),
            503,
        )

    try:
        result = analyzer(
            manifest=manifest,
            filename=filename,
        )
    except AnalysisError:
        raise
    except ValueError as exc:
        raise AnalysisError(
            "INVALID_MANIFEST",
            "The manifest could not be analyzed.",
            422,
        ) from exc

    return validate_analysis_result(result)