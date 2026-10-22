
"use strict";

const fileInput = document.getElementById("manifest-file");
const uploadButton = document.getElementById("upload-button");
const sampleButton = document.getElementById("sample-button");
const fileName = document.getElementById("file-name");
const message = document.getElementById("message");
const status = document.getElementById("app-status");
const searchInput = document.getElementById("package-search");

fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];

    fileName.textContent = file ? file.name : "No file selected";
    message.textContent = "";
});

uploadButton.addEventListener("click", async () => {
    const file = fileInput.files[0];

    if (!file) {
        showMessage("Please select a manifest first.");
        return;
    }

    uploadButton.disabled = true;
    status.textContent = "Processing...";
    showMessage("Reading manifest...");

    try {
        const graphData = await getGraphFromManifest(file);

        displayGraph(graphData);

        showMessage("Dependency graph generated successfully.");
        status.textContent = "Graph ready";
    } catch (error) {
        showMessage(error.message || "Could not generate the graph.");
        status.textContent = "Error";
    } finally {
        uploadButton.disabled = false;
    }
});

sampleButton.addEventListener("click", () => {
    const sampleGraph = {
        nodes: [
            {
                id: "my-project",
                label: "my-project",
                version: "1.0.0",
                type: "root"
            },
            {
                id: "react",
                label: "react",
                version: "^18.0.0"
            },
            {
                id: "vite",
                label: "vite",
                version: "^6.0.0"
            },
            {
                id: "lodash",
                label: "lodash",
                version: "^4.0.0"
            },
            {
                id: "typescript",
                label: "typescript",
                version: "^5.0.0"
            }
        ],

        edges: [
            { source: "my-project", target: "react" },
            { source: "my-project", target: "vite" },
            { source: "react", target: "lodash" },
            { source: "vite", target: "typescript" }
        ]
    };

    displayGraph(sampleGraph);
    showMessage("Sample graph loaded.");
    status.textContent = "Sample ready";
});

searchInput.addEventListener("input", event => {
    searchPackages(event.target.value);
});

document.getElementById("zoom-in").addEventListener("click", () => {
    zoomGraph(0.2);
});

document.getElementById("zoom-out").addEventListener("click", () => {
    zoomGraph(-0.2);
});

document.getElementById("reset-graph").addEventListener("click", () => {
    resetGraphView();
    searchInput.value = "";
    searchPackages("");
});

function displayGraph(graphData) {
    renderGraph(graphData);
    clearDependencyDetails();

    searchInput.value = "";
    status.textContent = "Graph ready";
}

function showMessage(text) {
    message.textContent = text;
}

