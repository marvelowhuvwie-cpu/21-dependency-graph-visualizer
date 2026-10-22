
"use strict";

function showDependencyDetails(selectedNode, graphData) {
    const container = document.getElementById("dependency-details");

    const dependencies = graphData.edges
        .filter(edge => edge.source === selectedNode.id)
        .map(edge => edge.target);

    const dependents = graphData.edges
        .filter(edge => edge.target === selectedNode.id)
        .map(edge => edge.source);

    container.replaceChildren();

    addDetail(container, "Package", selectedNode.label || selectedNode.id);
    addDetail(container, "Version", selectedNode.version || "unspecified");
    addDetail(container, "Type", selectedNode.type || "dependency");

    addList(container, "Dependencies", dependencies);
    addList(container, "Required by", dependents);
}

function addDetail(container, title, value) {
    const section = document.createElement("div");
    section.className = "detail-item";

    const heading = document.createElement("strong");
    heading.textContent = title;

    const paragraph = document.createElement("p");
    paragraph.textContent = value;

    section.append(heading, paragraph);
    container.appendChild(section);
}

function addList(container, title, items) {
    const section = document.createElement("div");
    section.className = "detail-item";

    const heading = document.createElement("strong");
    heading.textContent = `${title} (${items.length})`;
    section.appendChild(heading);

    if (items.length === 0) {
        const paragraph = document.createElement("p");
        paragraph.textContent = "None found.";
        section.appendChild(paragraph);
    } else {
        const list = document.createElement("ul");

        items.forEach(item => {
            const li = document.createElement("li");
            li.textContent = item;
            list.appendChild(li);
        });

        section.appendChild(list);
    }

    container.appendChild(section);
}

function clearDependencyDetails() {
    const container = document.getElementById("dependency-details");
    container.replaceChildren();

    const paragraph = document.createElement("p");
    paragraph.textContent = "Select a node to see its details.";

    container.appendChild(paragraph);
}

