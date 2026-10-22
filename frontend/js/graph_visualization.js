
"use strict";

let cy = null;

function renderGraph(graphData) {
    if (typeof cytoscape === "undefined") {
        throw new Error(
            "Cytoscape failed to load. Check your internet connection."
        );
    }

    if (cy) {
        cy.destroy();
    }

    const elements = [
        ...graphData.nodes.map(node => ({
            data: {
                id: node.id,
                label: node.label || node.id,
                version: node.version || "unspecified",
                type: node.type || "dependency"
            }
        })),

        ...graphData.edges.map((edge, index) => ({
            data: {
                id: `edge-${index}`,
                source: edge.source,
                target: edge.target
            }
        }))
    ];

    cy = cytoscape({
        container: document.getElementById("graph"),
        elements: elements,

        layout: {
            name: "breadthfirst",
            directed: true,
            padding: 30,
            spacingFactor: 1.2
        },

        minZoom: 0.2,
        maxZoom: 3,

        style: [
            {
                selector: "node",
                style: {
                    "background-color": "#7c83ff",
                    "label": "data(label)",
                    "color": "#ffffff",
                    "font-size": 11,
                    "text-wrap": "wrap",
                    "text-max-width": 100,
                    "text-valign": "center",
                    "text-halign": "center",
                    "width": 48,
                    "height": 48
                }
            },
            {
                selector: 'node[type = "root"]',
                style: {
                    "background-color": "#159b82",
                    "width": 60,
                    "height": 60
                }
            },
            {
                selector: "edge",
                style: {
                    "width": 2,
                    "line-color": "#65718e",
                    "target-arrow-color": "#a5b4d1",
                    "target-arrow-shape": "triangle",
                    "curve-style": "bezier"
                }
            },
            {
                selector: "node:selected",
                style: {
                    "border-color": "#ffffff",
                    "border-width": 4
                }
            },
            {
                selector: ".search-match",
                style: {
                    "border-color": "#fbbf24",
                    "border-width": 5
                }
            },
            {
                selector: ".search-dim",
                style: {
                    "opacity": 0.2
                }
            }
        ]
    });

    document.getElementById("node-count").textContent =
        graphData.nodes.length;

    document.getElementById("edge-count").textContent =
        graphData.edges.length;

    cy.on("tap", "node", event => {
        showDependencyDetails(event.target.data(), graphData);
    });

    cy.on("tap", event => {
        if (event.target === cy) {
            clearDependencyDetails();
        }
    });

    return cy;
}

function searchPackages(query) {
    if (!cy) return;

    cy.elements().removeClass("search-match search-dim");

    const searchTerm = query.trim().toLowerCase();

    if (!searchTerm) return;

    cy.nodes().forEach(node => {
        const name = String(node.data("label")).toLowerCase();

        if (name.includes(searchTerm)) {
            node.addClass("search-match");
        } else {
            node.addClass("search-dim");
        }
    });
}

function zoomGraph(amount) {
    if (!cy) return;

    cy.zoom({
        level: Math.max(0.2, Math.min(3, cy.zoom() + amount)),
        renderedPosition: {
            x: cy.width() / 2,
            y: cy.height() / 2
        }
    });
}

function resetGraphView() {
    if (!cy) return;

    cy.fit(undefined, 30);
    cy.center();
}

