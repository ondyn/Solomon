(function () {
  "use strict";

  const app = document.getElementById("schematic-app");
  if (!app) return;

  const loading = document.getElementById("schematic-loading");
  const inspector = document.getElementById("schematic-inspector");
  const stage = document.getElementById("schematic-stage");
  let canvas;
  let planData;
  let zoom = 1;

  function objectTarget(element) {
    if (element.space_id) return planData.targets.spaces[String(element.space_id)];
    if (element.door_id) return planData.targets.doors[String(element.door_id)];
    if (element.technical_asset_id) return planData.targets.technical_assets[String(element.technical_asset_id)];
    return null;
  }

  function objectFromElement(element, selectable) {
    const geometry = element.geometry;
    const style = element.style || {};
    const common = {
      fill: style.fill || "transparent",
      stroke: style.stroke || "#27343a",
      strokeWidth: Number(style.stroke_width || 2),
      opacity: style.opacity === undefined ? 1 : Number(style.opacity),
      angle: Number(style.angle || 0),
      selectable: Boolean(selectable && !element.locked),
      evented: true,
      hasControls: Boolean(selectable),
      lockMovementX: Boolean(element.locked),
      lockMovementY: Boolean(element.locked),
    };
    let object;
    if (geometry.type === "rect") {
      object = new fabric.Rect({
        ...common,
        left: geometry.x,
        top: geometry.y,
        width: geometry.width,
        height: geometry.height,
        originX: "left",
        originY: "top",
      });
    } else if (geometry.type === "line") {
      object = new fabric.Line(
        [geometry.x1, geometry.y1, geometry.x2, geometry.y2],
        {...common, fill: undefined}
      );
    } else if (geometry.type === "polygon") {
      object = new fabric.Polygon(geometry.points, common);
    } else if (geometry.type === "polyline") {
      object = new fabric.Polyline(geometry.points, {...common, fill: "transparent"});
    } else if (geometry.type === "point") {
      const radius = Number(style.radius || 10);
      object = new fabric.Circle({
        ...common,
        left: geometry.x - radius,
        top: geometry.y - radius,
        radius,
        fill: style.fill || "#b83f3f",
      });
    } else {
      object = new fabric.Text(geometry.text || element.label || "Label", {
        ...common,
        left: geometry.x || 0,
        top: geometry.y || 0,
        fill: style.fill || "#27343a",
        fontSize: Number(style.font_size || 18),
        fontFamily: "Avenir Next, Trebuchet MS, sans-serif",
      });
    }
    object.facilityElement = element;
    object.elementType = element.element_type;
    object.target = objectTarget(element);
    return object;
  }

  function addBackground(url, done) {
    if (!url) {
      done();
      return;
    }
    fabric.Image.fromURL(
      url,
      function (image) {
        const rotation = Number(planData.revision.background_rotation || 0);
        const quarterTurn = Math.abs(rotation) % 180 === 90;
        image.set({
          selectable: false,
          evented: false,
          opacity: 0.82,
          angle: rotation,
          left: rotation === 90 ? planData.plan.width : 0,
          top: rotation === -90 || Math.abs(rotation) === 180 ? planData.plan.height : 0,
        });
        image.scaleX = (quarterTurn ? planData.plan.height : planData.plan.width) / image.width;
        image.scaleY = (quarterTurn ? planData.plan.width : planData.plan.height) / image.height;
        canvas.setBackgroundImage(image, done);
      },
      {crossOrigin: "anonymous"}
    );
  }

  function fitCanvas() {
    const available = Math.max(stage.clientWidth - 36, 280);
    zoom = Math.min(1, available / planData.plan.width);
    applyZoom();
  }

  function applyZoom() {
    const width = planData.plan.width * zoom;
    const height = planData.plan.height * zoom;
    canvas.setDimensions({width, height});
    canvas.setViewportTransform([zoom, 0, 0, zoom, 0, 0]);
    canvas.requestRenderAll();
  }

  function addDetailRow(list, label, value) {
    if (!value) return;
    const term = document.createElement("dt");
    const detail = document.createElement("dd");
    term.textContent = label;
    detail.textContent = value;
    list.append(term, detail);
  }

  function addLinkList(container, title, entries, formatter) {
    if (!entries || !entries.length) return;
    const heading = document.createElement("h3");
    heading.textContent = title;
    heading.className = "h6 mt-4";
    const list = document.createElement("ul");
    entries.forEach((entry) => {
      const item = document.createElement("li");
      const link = document.createElement("a");
      link.href = entry.url;
      link.textContent = formatter(entry);
      item.appendChild(link);
      list.appendChild(item);
    });
    container.append(heading, list);
  }

  function showTarget(target) {
    if (!target) return;
    inspector.replaceChildren();
    const heading = document.createElement("h2");
    const link = document.createElement("a");
    link.href = target.url;
    link.textContent = target.label;
    heading.appendChild(link);
    inspector.appendChild(heading);
    const details = document.createElement("dl");
    addDetailRow(details, "Type", target.kind_label || target.type);
    addDetailRow(details, "System", target.system);
    addDetailRow(details, "Area", target.area_m2 ? `${target.area_m2} m²` : null);
    addDetailRow(details, "Space", target.space);
    addDetailRow(details, "Serves", target.serves_flats ? target.serves_flats.join(", ") : null);
    inspector.appendChild(details);
    addLinkList(inspector, "Flat assignments", target.assignments, (entry) => `${entry.flat} - ${entry.role}`);
    addLinkList(inspector, "Current use", target.usages, (entry) => `${entry.holder} - ${entry.type}`);
    if (target.locks && target.locks.length) {
      target.locks.forEach((lock) => addLinkList(inspector, lock.name, lock.keys, (entry) => entry.label));
    }
    if (target.emergency_instructions) {
      const heading = document.createElement("h3");
      heading.className = "h6 mt-4";
      heading.textContent = "Emergency instructions";
      const text = document.createElement("p");
      text.textContent = target.emergency_instructions;
      inspector.append(heading, text);
    }
  }

  function layerFor(elementType) {
    if (elementType === "space") return "space";
    if (elementType === "door") return "door";
    if (elementType === "technical") return "technical";
    return "structure";
  }

  function exportSvg() {
    const blob = new Blob([canvas.toSVG()], {type: "image/svg+xml;charset=utf-8"});
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `${planData.plan.name}.svg`;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  async function initialize() {
    if (!window.fabric) throw new Error("Fabric.js did not load");
    const response = await fetch(app.dataset.url, {headers: {Accept: "application/json"}});
    if (!response.ok) throw new Error(`Plan request failed (${response.status})`);
    planData = await response.json();
    canvas = new fabric.Canvas("schematic-canvas", {
      width: planData.plan.width,
      height: planData.plan.height,
      selection: false,
      preserveObjectStacking: true,
    });
    const highlights = new Set(app.dataset.highlight.split(",").filter(Boolean));
    addBackground(planData.revision.background_url, function () {
      planData.elements.forEach((element) => {
        const object = objectFromElement(element, false);
        if (element.space_id && highlights.has(String(element.space_id))) {
          object.set({stroke: "#efb419", strokeWidth: 5, opacity: 1});
        }
        canvas.add(object);
      });
      fitCanvas();
      loading.classList.add("is-hidden");
    });
    canvas.on("mouse:down", (event) => {
      if (event.target && event.target.target) showTarget(event.target.target);
    });
    canvas.on("mouse:dblclick", (event) => {
      if (event.target && event.target.target) window.location.assign(event.target.target.url);
    });
    document.querySelectorAll("[data-layer]").forEach((input) => {
      input.addEventListener("change", () => {
        canvas.getObjects().forEach((object) => {
          if (layerFor(object.elementType) === input.dataset.layer) object.visible = input.checked;
        });
        canvas.requestRenderAll();
      });
    });
    document.getElementById("zoom-in").addEventListener("click", () => { zoom = Math.min(3, zoom * 1.2); applyZoom(); });
    document.getElementById("zoom-out").addEventListener("click", () => { zoom = Math.max(0.1, zoom / 1.2); applyZoom(); });
    document.getElementById("zoom-fit").addEventListener("click", fitCanvas);
    document.getElementById("export-svg").addEventListener("click", exportSvg);
    window.addEventListener("resize", fitCanvas);
  }

  initialize().catch((error) => {
    loading.textContent = error.message;
    loading.classList.remove("is-hidden");
  });
})();