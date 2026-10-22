
"use strict";

async function getGraphFromManifest(file) {
    if (!file) {
        throw new Error("Please select a manifest file.");
    }

    if (!file.name.toLowerCase().endsWith(".json")) {
        throw new Error("Please upload a .json manifest file.");
    }

    const text = await file.text();
    let manifest;

    try {
        manifest = JSON.parse(text);
    } catch {
        throw new Error("Invalid JSON. Check your manifest file.");
    }

    if (
        !manifest ||
        typeof manifest !== "object" ||
        Array.isArray(manifest)
    ) {
        throw new Error("The manifest must contain a JSON object.");
    }

    const groups = [
        "dependencies",
        "devDependencies",
        "peerDependencies",
        "optionalDependencies"
    ];

    const rootId = manifest.name || "my-project";

    const nodes = [{
        id: rootId,
        label: rootId,
        version: manifest.version || "unspecified",
        type: "root"
    }];

    const edges = [];
    const added = new Set([rootId]);

    for (const group of groups) {
        const dependencies = manifest[group] || {};

        if (
            typeof dependencies !== "object" ||
            dependencies === null ||
            Array.isArray(dependencies)
        ) {
            throw new Error(`Invalid ${group} section.`);
        }

        for (const [name, version] of Object.entries(dependencies)) {
            if (!name.trim() || typeof version !== "string") {
                throw new Error(`Invalid dependency in ${group}.`);
            }

            if (!added.has(name)) {
                nodes.push({
                    id: name,
                    label: name,
                    version: version,
                    type: group
                });

                added.add(name);
            }

            edges.push({
                source: rootId,
                target: name,
                type: group
            });
        }
    }

    if (nodes.length === 1) {
        throw new Error("No dependencies found in this manifest.");
    }

    return validateGraph({ nodes, edges });
}

function validateGraph(data) {
    if (
        !data ||
        !Array.isArray(data.nodes) ||
        !Array.isArray(data.edges)
    ) {
        throw new Error("Invalid graph data.");
    }

    const ids = new Set();

    for (const node of data.nodes) {
        if (!node.id || ids.has(node.id)) {
            throw new Error("Every graph node needs a unique ID.");
        }

        ids.add(node.id);
    }

    for (const edge of data.edges) {
        if (!ids.has(edge.source) || !ids.has(edge.target)) {
            throw new Error("A connection references an unknown node.");
        }
    }

    return data;
}

