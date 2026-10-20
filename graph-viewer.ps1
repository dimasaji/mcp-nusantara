$ErrorActionPreference = "Stop"

$Root = "C:\Users\dmaza\mcp-starter"
$GraphFile = Join-Path $Root "graphify-out\graph.json"
$Port = 8080

if (!(Test-Path $GraphFile)) {
    Write-Host ""
    Write-Host "[ERROR] graph.json tidak ditemukan:" -ForegroundColor Red
    Write-Host $GraphFile
    exit 1
}

$graph = Get-Content $GraphFile -Raw -Encoding UTF8

# Lindungi JSON agar aman dimasukkan ke dalam <script>
$graph = $graph -replace "</script", "<\/script"

$html = @"
<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>Nusantara Core - Knowledge Graph</title>

<style>

* {
    box-sizing: border-box;
}

html,
body {
    margin: 0;
    width: 100%;
    height: 100%;
    overflow: hidden;
    font-family: Segoe UI, Arial, sans-serif;
    background: #0b1120;
    color: #e5e7eb;
}

#topbar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 58px;
    z-index: 20;

    display: flex;
    align-items: center;
    gap: 12px;

    padding: 0 16px;

    background: rgba(15,23,42,.96);
    border-bottom: 1px solid #334155;
}

#title {
    font-size: 18px;
    font-weight: 700;
    white-space: nowrap;
}

#subtitle {
    color: #94a3b8;
    font-size: 12px;
}

#search {
    margin-left: auto;
    width: 280px;

    padding: 9px 12px;

    border: 1px solid #475569;
    border-radius: 7px;

    background: #111827;
    color: white;

    outline: none;
}

#search:focus {
    border-color: #38bdf8;
}

button {
    padding: 9px 12px;

    border: 1px solid #475569;
    border-radius: 7px;

    background: #1e293b;
    color: white;

    cursor: pointer;
}

button:hover {
    background: #334155;
}

#stats {
    position: fixed;

    left: 15px;
    bottom: 15px;

    z-index: 20;

    padding: 12px 15px;

    border: 1px solid #334155;
    border-radius: 8px;

    background: rgba(15,23,42,.94);

    font-size: 13px;
    line-height: 1.7;
}

#info {
    position: fixed;

    right: 15px;
    top: 73px;

    width: 330px;
    max-height: calc(100vh - 95px);

    overflow: auto;

    z-index: 20;

    padding: 15px;

    border: 1px solid #334155;
    border-radius: 10px;

    background: rgba(15,23,42,.96);

    display: none;
}

#info h3 {
    margin-top: 0;
}

.info-label {
    color: #94a3b8;
    font-size: 11px;
    text-transform: uppercase;
}

.info-value {
    margin-bottom: 10px;
    word-break: break-word;
}

#graph {
    position: absolute;

    left: 0;
    top: 58px;

    width: 100%;
    height: calc(100% - 58px);

    background:
        radial-gradient(circle at center,
        rgba(30,41,59,.35),
        rgba(2,6,23,.95));
}

svg {
    width: 100%;
    height: 100%;
}

.edge {
    stroke: #475569;
    stroke-opacity: .20;
    stroke-width: 1;
}

.edge.highlight {
    stroke: #38bdf8;
    stroke-opacity: .8;
    stroke-width: 2;
}

.node {
    fill: #38bdf8;
    stroke: #0f172a;
    stroke-width: 1;
    cursor: pointer;
}

.node:hover {
    fill: #facc15;
}

.node.selected {
    fill: #facc15;
    stroke: white;
    stroke-width: 2;
}

.node.dim {
    opacity: .12;
}

.edge.dim {
    opacity: .03;
}

#loading {
    position: fixed;

    left: 50%;
    top: 50%;

    transform: translate(-50%, -50%);

    z-index: 100;

    padding: 20px 30px;

    background: rgba(15,23,42,.97);

    border: 1px solid #475569;
    border-radius: 10px;

    font-size: 16px;
}

</style>
</head>

<body>

<div id="topbar">

    <div id="title">
        Nusantara Core
    </div>

    <div id="subtitle">
        Developer Knowledge Graph
    </div>

    <input
        id="search"
        placeholder="Cari node / file / class / function..."
    >

    <button onclick="resetView()">
        Reset
    </button>

</div>

<div id="graph">
    <svg id="svg"></svg>
</div>

<div id="stats">
    <b>Knowledge Graph</b><br>
    Nodes: <span id="nodeCount">0</span><br>
    Edges: <span id="edgeCount">0</span><br>
    FPS: <span id="fps">-</span>
</div>

<div id="info">
    <h3 id="infoTitle">Node</h3>

    <div class="info-label">ID</div>
    <div class="info-value" id="infoId"></div>

    <div class="info-label">Label</div>
    <div class="info-value" id="infoLabel"></div>

    <div class="info-label">Type</div>
    <div class="info-value" id="infoType"></div>

    <div class="info-label">File</div>
    <div class="info-value" id="infoFile"></div>

    <div class="info-label">Connections</div>
    <div class="info-value" id="infoConnections"></div>
</div>

<div id="loading">
    Memuat Knowledge Graph...
</div>

<script>

const GRAPH = $graph;

const svg = document.getElementById("svg");

const NS = "http://www.w3.org/2000/svg";

const nodes =
    (GRAPH.nodes || []).map((n, i) => ({
        ...n,
        _i: i,
        x: 100 + Math.random() * 1000,
        y: 100 + Math.random() * 600,
        vx: 0,
        vy: 0
    }));

let rawEdges =
    GRAPH.edges ||
    GRAPH.links ||
    [];

const nodeMap = new Map();

nodes.forEach(n => {

    nodeMap.set(String(n.id), n);

    if (n.name)
        nodeMap.set(String(n.name), n);

});

const edges = [];

rawEdges.forEach(e => {

    let source =
        typeof e.source === "object"
            ? e.source.id
            : e.source;

    let target =
        typeof e.target === "object"
            ? e.target.id
            : e.target;

    source = nodeMap.get(String(source));
    target = nodeMap.get(String(target));

    if (source && target) {

        edges.push({
            source,
            target,
            raw: e
        });

    }

});

document.getElementById("nodeCount").textContent =
    nodes.length.toLocaleString();

document.getElementById("edgeCount").textContent =
    edges.length.toLocaleString();

const edgeGroup =
    document.createElementNS(NS, "g");

const nodeGroup =
    document.createElementNS(NS, "g");

svg.appendChild(edgeGroup);
svg.appendChild(nodeGroup);

const edgeElements = [];

edges.forEach(e => {

    const line =
        document.createElementNS(NS, "line");

    line.setAttribute("class", "edge");

    edgeGroup.appendChild(line);

    edgeElements.push({
        element: line,
        data: e
    });

});

const nodeElements = [];

nodes.forEach(n => {

    const circle =
        document.createElementNS(NS, "circle");

    circle.setAttribute("class", "node");

    let degree = 0;

    edges.forEach(e => {

        if (e.source === n || e.target === n)
            degree++;

    });

    const radius =
        Math.min(10, 3 + Math.sqrt(degree));

    circle.setAttribute("r", radius);

    circle.addEventListener("mousedown", e => {

        selectedNode = n;

        selectNode(n);

        dragNode = n;

        dragStartX = e.clientX;

        dragStartY = e.clientY;

        e.preventDefault();

    });

    circle.addEventListener("click", e => {

        e.stopPropagation();

        selectNode(n);

    });

    nodeGroup.appendChild(circle);

    nodeElements.push({
        element: circle,
        data: n
    });

});

let selectedNode = null;

function getNodeText(n) {

    return (
        n.label ||
        n.name ||
        n.title ||
        n.id ||
        ""
    );

}

function getNodeType(n) {

    return (
        n.type ||
        n.kind ||
        n.node_type ||
        "node"
    );

}

function getNodeFile(n) {

    return (
        n.file ||
        n.path ||
        n.file_path ||
        n.filename ||
        ""
    );

}

function selectNode(n) {

    selectedNode = n;

    document.getElementById("info").style.display =
        "block";

    document.getElementById("infoTitle").textContent =
        getNodeText(n);

    document.getElementById("infoId").textContent =
        n.id ?? "";

    document.getElementById("infoLabel").textContent =
        getNodeText(n);

    document.getElementById("infoType").textContent =
        getNodeType(n);

    document.getElementById("infoFile").textContent =
        getNodeFile(n);

    let connections = 0;

    edges.forEach(e => {

        if (e.source === n || e.target === n)
            connections++;

    });

    document.getElementById("infoConnections").textContent =
        connections;

    nodeElements.forEach(o => {

        o.element.classList.remove("selected");

        if (o.data === n)
            o.element.classList.add("selected");

    });

    edgeElements.forEach(o => {

        const active =
            o.data.source === n ||
            o.data.target === n;

        o.element.classList.toggle(
            "highlight",
            active
        );

        o.element.classList.toggle(
            "dim",
            !active
        );

    });

}

svg.addEventListener("click", () => {

    document.getElementById("info").style.display =
        "none";

    nodeElements.forEach(o =>
        o.element.classList.remove("selected")
    );

    edgeElements.forEach(o => {

        o.element.classList.remove("highlight");
        o.element.classList.remove("dim");

    });

    selectedNode = null;

});

let zoom = 1;

let panX = 0;

let panY = 0;

function updateTransform() {

    nodeGroup.setAttribute(
        "transform",
        `translate(${panX},${panY}) scale(${zoom})`
    );

    edgeGroup.setAttribute(
        "transform",
        `translate(${panX},${panY}) scale(${zoom})`
    );

}

let panStart = null;

svg.addEventListener("mousedown", e => {

    if (e.target !== svg)
        return;

    panStart = {
        x: e.clientX - panX,
        y: e.clientY - panY
    };

});

window.addEventListener("mousemove", e => {

    if (dragNode) {

        const rect =
            svg.getBoundingClientRect();

        dragNode.x =
            (e.clientX - rect.left - panX) / zoom;

        dragNode.y =
            (e.clientY - rect.top - panY) / zoom;

        dragNode.vx = 0;
        dragNode.vy = 0;

        return;

    }

    if (panStart) {

        panX = e.clientX - panStart.x;
        panY = e.clientY - panStart.y;

        updateTransform();

    }

});

window.addEventListener("mouseup", () => {

    dragNode = null;

    panStart = null;

});

svg.addEventListener("wheel", e => {

    e.preventDefault();

    const factor =
        e.deltaY < 0
            ? 1.12
            : 0.89;

    zoom *= factor;

    zoom =
        Math.max(.08, Math.min(8, zoom));

    updateTransform();

});

let dragNode = null;

let dragStartX = 0;

let dragStartY = 0;

function resetView() {

    zoom = 1;

    panX = 0;

    panY = 0;

    updateTransform();

    nodes.forEach(n => {

        n.x =
            100 + Math.random() * 1000;

        n.y =
            100 + Math.random() * 600;

        n.vx = 0;
        n.vy = 0;

    });

}

document.getElementById("search")
.addEventListener("input", function() {

    const q =
        this.value
        .trim()
        .toLowerCase();

    if (!q) {

        nodeElements.forEach(o =>
            o.element.classList.remove("dim")
        );

        edgeElements.forEach(o =>
            o.element.classList.remove("dim")
        );

        return;

    }

    nodeElements.forEach(o => {

        const text =
            (
                getNodeText(o.data) +
                " " +
                getNodeType(o.data) +
                " " +
                getNodeFile(o.data) +
                " " +
                String(o.data.id || "")
            ).toLowerCase();

        o.element.classList.toggle(
            "dim",
            !text.includes(q)
        );

    });

});

function simulate() {

    const width =
        svg.clientWidth || window.innerWidth;

    const height =
        svg.clientHeight || window.innerHeight;

    const centerX = width / 2;
    const centerY = height / 2;

    // Center gravity
    nodes.forEach(n => {

        n.vx +=
            (centerX - n.x) * 0.00015;

        n.vy +=
            (centerY - n.y) * 0.00015;

    });

    // Link force
    edges.forEach(e => {

        const dx =
            e.target.x - e.source.x;

        const dy =
            e.target.y - e.source.y;

        const distance =
            Math.sqrt(dx * dx + dy * dy) || 1;

        const desired = 70;

        const force =
            (distance - desired) * 0.0008;

        const fx =
            dx / distance * force;

        const fy =
            dy / distance * force;

        e.source.vx += fx;
        e.source.vy += fy;

        e.target.vx -= fx;
        e.target.vy -= fy;

    });

    // Sampled repulsion for large graphs
    const maxPairs = 18000;

    let pairCount = 0;

    const step =
        Math.max(
            1,
            Math.floor(
                nodes.length /
                Math.sqrt(maxPairs)
            )
        );

    for (
        let i = 0;
        i < nodes.length;
        i += step
    ) {

        const a = nodes[i];

        for (
            let j = i + step;
            j < nodes.length;
            j += step
        ) {

            if (++pairCount > maxPairs)
                break;

            const b = nodes[j];

            const dx =
                b.x - a.x;

            const dy =
                b.y - a.y;

            const d2 =
                dx * dx +
                dy * dy +
                100;

            const force =
                300 / d2;

            a.vx -= dx * force;
            a.vy -= dy * force;

            b.vx += dx * force;
            b.vy += dy * force;

        }

        if (pairCount > maxPairs)
            break;

    }

    nodes.forEach(n => {

        if (n === dragNode)
            return;

        n.vx *= .90;
        n.vy *= .90;

        n.x += n.vx;
        n.y += n.vy;

        n.x =
            Math.max(-1000, Math.min(width + 1000, n.x));

        n.y =
            Math.max(-1000, Math.min(height + 1000, n.y));

    });

}

function render() {

    edgeElements.forEach(o => {

        const e = o.data;

        o.element.setAttribute(
            "x1",
            e.source.x
        );

        o.element.setAttribute(
            "y1",
            e.source.y
        );

        o.element.setAttribute(
            "x2",
            e.target.x
        );

        o.element.setAttribute(
            "y2",
            e.target.y
        );

    });

    nodeElements.forEach(o => {

        o.element.setAttribute(
            "cx",
            o.data.x
        );

        o.element.setAttribute(
            "cy",
            o.data.y
        );

    });

}

let frames = 0;

let lastFPS = performance.now();

function loop() {

    simulate();

    render();

    frames++;

    const now =
        performance.now();

    if (now - lastFPS > 1000) {

        document.getElementById("fps")
            .textContent = frames;

        frames = 0;

        lastFPS = now;

    }

    requestAnimationFrame(loop);

}

document.getElementById("loading")
    .style.display = "none";

updateTransform();

loop();

</script>

</body>
</html>
"@

$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://127.0.0.1:$Port/")
$listener.Start()

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " NUSANTARA CORE - KNOWLEDGE GRAPH VIEWER" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Graph :" -ForegroundColor Yellow
Write-Host $GraphFile
Write-Host ""
Write-Host "Browser :" -ForegroundColor Green
Write-Host "http://127.0.0.1:$Port"
Write-Host ""
Write-Host "Status : RUNNING" -ForegroundColor Green
Write-Host ""
Write-Host "Tekan CTRL+C untuk menghentikan viewer." -ForegroundColor Yellow
Write-Host ""

try {

    while ($listener.IsListening) {

        $context = $listener.GetContext()

        $path = $context.Request.Url.AbsolutePath

        if ($path -eq "/" -or $path -eq "/index.html") {

            $bytes =
                [System.Text.Encoding]::UTF8.GetBytes($html)

            $context.Response.ContentType =
                "text/html; charset=utf-8"

            $context.Response.ContentLength64 =
                $bytes.Length

            $context.Response.StatusCode = 200

            $context.Response.OutputStream.Write(
                $bytes,
                0,
                $bytes.Length
            )

        }
        else {

            $context.Response.StatusCode = 404

            $message =
                [System.Text.Encoding]::UTF8.GetBytes(
                    "404 Not Found"
                )

            $context.Response.OutputStream.Write(
                $message,
                0,
                $message.Length
            )

        }

        $context.Response.OutputStream.Close()
    }

}
finally {

    $listener.Stop()
    $listener.Close()

}
