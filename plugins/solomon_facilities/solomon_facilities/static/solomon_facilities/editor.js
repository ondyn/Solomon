(function () {
  "use strict";

  const app = document.getElementById("schematic-editor");
  if (!app) return;

  const loading = document.getElementById("schematic-loading");
  const stage = document.getElementById("schematic-stage");
  const saveState = document.getElementById("save-state");
  const fields = {
    type: document.getElementById("element-type"),
    label: document.getElementById("element-label"),
    target: document.getElementById("element-target"),
    x: document.getElementById("element-x"),
    y: document.getElementById("element-y"),
    width: document.getElementById("element-width"),
    height: document.getElementById("element-height"),
    stroke: document.getElementById("element-stroke"),
    fill: document.getElementById("element-fill"),
    locked: document.getElementById("element-locked"),
  };
  const targetHelp = document.getElementById("element-target-help");
  const targetActions = document.getElementById("element-target-actions");
  let canvas;
  let planData;
  let zoom = 1;
  let panMode = false;
  let dragging = false;
  let lastPointer;

  function getCsrfToken() {
    const input = document.querySelector("#publish-form [name=csrfmiddlewaretoken]");
    if (input?.value) return input.value;
    const prefix = "csrftoken=";
    const cookie = document.cookie
      .split(";")
      .map((value) => value.trim())
      .find((value) => value.startsWith(prefix));
    return cookie ? decodeURIComponent(cookie.slice(prefix.length)) : "";
  }

  async function responseData(response) {
    const contentType = response.headers.get("Content-Type") || "";
    if (contentType.includes("application/json")) return response.json();
    const text = await response.text();
    if (!response.ok) throw new Error(`Plan request failed (${response.status})`);
    throw new Error(text || "Plan request returned an invalid response");
  }

  function targetFromElement(element) {
    if (element.space_id) return {kind: "space", id: element.space_id};
    if (element.door_id) return {kind: "door", id: element.door_id};
    if (element.technical_asset_id) return {kind: "technical_asset", id: element.technical_asset_id};
    return {kind: "", id: ""};
  }

  function objectFromElement(element) {
    const geometry = element.geometry;
    const style = element.style || {};
    const common = {
      fill: style.fill || "transparent",
      stroke: style.stroke || "#27343a",
      strokeWidth: Number(style.stroke_width || 2),
      opacity: style.opacity === undefined ? 1 : Number(style.opacity),
      angle: Number(style.angle || 0),
      selectable: !element.locked,
      lockMovementX: Boolean(element.locked),
      lockMovementY: Boolean(element.locked),
      hasControls: !element.locked,
      originX: "left",
      originY: "top",
    };
    let object;
    if (geometry.type === "rect") {
      object = new fabric.Rect({...common, left: geometry.x, top: geometry.y, width: geometry.width, height: geometry.height});
    } else if (geometry.type === "line") {
      object = new fabric.Line([geometry.x1, geometry.y1, geometry.x2, geometry.y2], {...common, fill: undefined});
    } else if (geometry.type === "polygon") {
      object = new fabric.Polygon(geometry.points, common);
    } else if (geometry.type === "polyline") {
      object = new fabric.Polyline(geometry.points, {...common, fill: "transparent"});
    } else if (geometry.type === "point") {
      const radius = Number(style.radius || 10);
      object = new fabric.Circle({...common, left: geometry.x - radius, top: geometry.y - radius, radius, fill: style.fill || "#b83f3f"});
    } else {
      object = new fabric.IText(geometry.text || element.label || "Label", {
        ...common,
        left: geometry.x || 0,
        top: geometry.y || 0,
        fill: style.fill || "#27343a",
        fontSize: Number(style.font_size || 18),
        fontFamily: "Avenir Next, Trebuchet MS, sans-serif",
      });
    }
    const target = targetFromElement(element);
    object.elementType = element.element_type;
    object.elementLabel = element.label || "";
    object.targetKind = target.kind;
    object.targetId = target.id ? String(target.id) : "";
    object.locked = Boolean(element.locked);
    return object;
  }

  function lineGeometry(object) {
    const points = object.calcLinePoints();
    const matrix = object.calcTransformMatrix();
    const start = fabric.util.transformPoint(new fabric.Point(points.x1, points.y1), matrix);
    const end = fabric.util.transformPoint(new fabric.Point(points.x2, points.y2), matrix);
    return {type: "line", x1: start.x, y1: start.y, x2: end.x, y2: end.y};
  }

  function serializeObject(object, index) {
    let geometry;
    if (object.type === "line") {
      geometry = lineGeometry(object);
    } else if (object.type === "circle") {
      geometry = {
        type: "point",
        x: object.left + object.radius * object.scaleX,
        y: object.top + object.radius * object.scaleY,
      };
    } else if (object.type === "i-text" || object.type === "text") {
      geometry = {type: "text", x: object.left, y: object.top, text: object.text};
    } else if (object.type === "polygon" || object.type === "polyline") {
      const matrix = object.calcTransformMatrix();
      geometry = {
        type: object.type,
        points: object.points.map((point) => {
          const transformed = fabric.util.transformPoint(
            new fabric.Point(point.x - object.pathOffset.x, point.y - object.pathOffset.y),
            matrix
          );
          return {x: transformed.x, y: transformed.y};
        }),
      };
    } else {
      geometry = {
        type: "rect",
        x: object.left,
        y: object.top,
        width: object.width * object.scaleX,
        height: object.height * object.scaleY,
      };
    }
    const item = {
      element_type: object.elementType || "line",
      label: object.elementLabel || (object.type === "i-text" ? object.text : ""),
      geometry,
      style: {
        stroke: object.stroke || "#27343a",
        stroke_width: object.strokeWidth || 2,
        fill: object.fill && object.fill !== "transparent" ? object.fill : "transparent",
        opacity: object.opacity,
        angle: object.angle || 0,
        radius: object.radius || undefined,
        font_size: object.fontSize || undefined,
      },
      z_index: index,
      locked: Boolean(object.locked),
      space_id: null,
      door_id: null,
      technical_asset_id: null,
    };
    if (object.targetKind === "space") item.space_id = Number(object.targetId);
    if (object.targetKind === "door") item.door_id = Number(object.targetId);
    if (object.targetKind === "technical_asset") item.technical_asset_id = Number(object.targetId);
    return item;
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
          opacity: 0.7,
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
    canvas.setDimensions({width: planData.plan.width * zoom, height: planData.plan.height * zoom});
    const transform = canvas.viewportTransform;
    canvas.setViewportTransform([zoom, 0, 0, zoom, transform[4] || 0, transform[5] || 0]);
    canvas.requestRenderAll();
  }

  function canvasCenter() {
    const inverse = fabric.util.invertTransform(canvas.viewportTransform);
    return fabric.util.transformPoint(
      new fabric.Point(canvas.getWidth() / 2, canvas.getHeight() / 2),
      inverse
    );
  }

  function addElement(elementType) {
    const center = canvasCenter();
    let object;
    if (["wall", "door", "window", "line", "dimension"].includes(elementType)) {
      const colors = {door: "#d08b27", window: "#2f7e9a", dimension: "#65757b"};
      object = new fabric.Line([center.x - 60, center.y, center.x + 60, center.y], {
        stroke: colors[elementType] || "#27343a",
        strokeWidth: elementType === "wall" ? 7 : 3,
      });
    } else if (elementType === "space") {
      object = new fabric.Rect({
        left: center.x - 70,
        top: center.y - 50,
        width: 140,
        height: 100,
        fill: "#dce9e4",
        opacity: 0.62,
        stroke: "#39806a",
        strokeWidth: 2,
      });
    } else if (elementType === "technical") {
      object = new fabric.Circle({
        left: center.x - 11,
        top: center.y - 11,
        radius: 11,
        fill: "#b83f3f",
        stroke: "#7d2525",
        strokeWidth: 2,
      });
    } else {
      object = new fabric.IText("Label", {
        left: center.x,
        top: center.y,
        fill: "#27343a",
        fontSize: 18,
        fontFamily: "Avenir Next, Trebuchet MS, sans-serif",
      });
    }
    object.elementType = elementType;
    object.elementLabel = elementType === "text" ? "Label" : "";
    object.targetKind = "";
    object.targetId = "";
    object.locked = false;
    canvas.discardActiveObject();
    canvas.add(object);
    canvas.setActiveObject(object);
    canvas.bringToFront(object);
    canvas.requestRenderAll();
    updateInspector(object);
  }

  function populateTargetOptions() {
    const selectedValue = fields.target.value;
    fields.target.replaceChildren();
    const empty = document.createElement("option");
    empty.value = "";
    empty.textContent = "No linked object";
    fields.target.appendChild(empty);
    const collections = [
      ["space", "Spaces", planData.targets.spaces],
      ["door", "Doors", planData.targets.doors],
      ["technical_asset", "Technical assets", planData.targets.technical_assets],
    ];
    let total = 0;
    collections.forEach(([kind, label, records]) => {
      const available = Object.values(records || {});
      if (!available.length) return;
      const group = document.createElement("optgroup");
      group.label = label;
      available.forEach((record) => {
        const option = document.createElement("option");
        option.value = `${kind}:${record.id}`;
        option.textContent = record.label;
        group.appendChild(option);
      });
      fields.target.appendChild(group);
      total += available.length;
    });
    empty.textContent = total
      ? `Select linked object (${total} available)`
      : "No linkable objects exist on this floor";
    fields.target.disabled = !canvas.getActiveObject() || total === 0;
    fields.target.value = selectedValue;
    targetHelp.textContent = total
      ? "Optional. Any painted element can link to a facility record on this floor."
      : "Create a space, door, or technical asset for this floor, then select Refresh.";
    targetActions.classList.toggle("is-empty", total === 0);
  }

  function updateInspector(selectedObject) {
    const object = typeof selectedObject?.set === "function"
      ? selectedObject
      : canvas.getActiveObject();
    const disabled = !object;
    Object.values(fields).forEach((field) => { field.disabled = disabled; });
    if (!object) return;
    fields.type.value = object.elementType || "line";
    fields.label.value = object.elementLabel || (object.type === "i-text" ? object.text : "");
    populateTargetOptions();
    fields.target.value = object.targetKind && object.targetId ? `${object.targetKind}:${object.targetId}` : "";
    fields.x.value = Number(object.left || 0).toFixed(1);
    fields.y.value = Number(object.top || 0).toFixed(1);
    fields.width.value = Number(object.width * object.scaleX || 0).toFixed(1);
    fields.height.value = Number(object.height * object.scaleY || 0).toFixed(1);
    fields.stroke.value = /^#[0-9a-f]{6}$/i.test(object.stroke) ? object.stroke : "#27343a";
    fields.fill.value = /^#[0-9a-f]{6}$/i.test(object.fill) ? object.fill : "#dce9e4";
    fields.locked.checked = Boolean(object.locked);
  }

  function updateObject() {
    const object = canvas.getActiveObject();
    if (!object) return;
    object.elementType = fields.type.value;
    object.elementLabel = fields.label.value;
    if (object.type === "i-text") object.set({text: fields.label.value || "Label"});
    const [targetKind = "", targetId = ""] = fields.target.value.split(":");
    object.targetKind = targetKind;
    object.targetId = targetId;
    object.set({
      left: Number(fields.x.value || 0),
      top: Number(fields.y.value || 0),
      stroke: fields.stroke.value,
      fill: object.type === "line" ? undefined : fields.fill.value,
      lockMovementX: fields.locked.checked,
      lockMovementY: fields.locked.checked,
      hasControls: !fields.locked.checked,
    });
    if (object.width && Number(fields.width.value) > 0) object.scaleX = Number(fields.width.value) / object.width;
    if (object.height && Number(fields.height.value) > 0) object.scaleY = Number(fields.height.value) / object.height;
    object.locked = fields.locked.checked;
    object.setCoords();
    canvas.requestRenderAll();
    saveState.textContent = "Changed";
  }

  async function savePlan() {
    saveState.textContent = "Saving...";
    const elements = canvas.getObjects().map(serializeObject);
    const response = await fetch(app.dataset.saveUrl, {
      method: "PUT",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({revision_id: Number(app.dataset.revisionId), elements}),
    });
    const result = await responseData(response);
    if (!response.ok) throw new Error(typeof result.detail === "string" ? result.detail : JSON.stringify(result.detail));
    saveState.textContent = "Saved";
    return result;
  }

  function setTool(tool) {
    panMode = tool === "pan";
    canvas.selection = !panMode;
    canvas.defaultCursor = panMode ? "grab" : "default";
    canvas.forEachObject((object) => { object.selectable = !panMode && !object.locked; });
    document.querySelectorAll("[data-tool]").forEach((button) => button.classList.toggle("active", button.dataset.tool === tool));
    canvas.discardActiveObject();
    canvas.requestRenderAll();
  }

  async function initialize() {
    if (!window.fabric) throw new Error("Fabric.js did not load");
    const response = await fetch(app.dataset.url, {headers: {Accept: "application/json"}});
    if (!response.ok) throw new Error(`Plan request failed (${response.status})`);
    planData = await responseData(response);
    canvas = new fabric.Canvas("schematic-canvas", {
      width: planData.plan.width,
      height: planData.plan.height,
      preserveObjectStacking: true,
    });
    addBackground(planData.revision.background_url, function () {
      planData.elements.forEach((element) => canvas.add(objectFromElement(element)));
      fitCanvas();
      loading.classList.add("is-hidden");
      updateInspector();
    });
    canvas.on("selection:created", updateInspector);
    canvas.on("selection:updated", updateInspector);
    canvas.on("selection:cleared", updateInspector);
    canvas.on("object:modified", () => { updateInspector(); saveState.textContent = "Changed"; });
    canvas.on("mouse:down", (event) => {
      if (!panMode) return;
      dragging = true;
      lastPointer = event.e;
      canvas.defaultCursor = "grabbing";
    });
    canvas.on("mouse:move", (event) => {
      if (!dragging || !panMode) return;
      const transform = canvas.viewportTransform;
      transform[4] += event.e.clientX - lastPointer.clientX;
      transform[5] += event.e.clientY - lastPointer.clientY;
      canvas.requestRenderAll();
      lastPointer = event.e;
    });
    canvas.on("mouse:up", () => { dragging = false; canvas.defaultCursor = panMode ? "grab" : "default"; });
    document.querySelectorAll("[data-add]").forEach((button) => button.addEventListener("click", (event) => {
      addElement(event.currentTarget.dataset.add);
    }));
    document.querySelectorAll("[data-tool]").forEach((button) => button.addEventListener("click", () => setTool(button.dataset.tool)));
    Object.entries(fields).forEach(([name, field]) => {
      if (name !== "type") field.addEventListener("change", updateObject);
    });
    fields.type.addEventListener("change", () => {
      const object = canvas.getActiveObject();
      if (!object) return;
      object.elementType = fields.type.value;
      updateObject();
    });
    document.getElementById("refresh-targets").addEventListener("click", async () => {
      const button = document.getElementById("refresh-targets");
      button.disabled = true;
      try {
        const response = await fetch(app.dataset.url, {headers: {Accept: "application/json"}});
        const refreshed = await responseData(response);
        planData.targets = refreshed.targets;
        populateTargetOptions();
      } catch (error) {
        targetHelp.textContent = error.message;
      } finally {
        button.disabled = false;
      }
    });
    document.getElementById("delete-element").addEventListener("click", () => {
      const object = canvas.getActiveObject();
      if (object) canvas.remove(object);
      updateInspector();
      saveState.textContent = "Changed";
    });
    document.getElementById("zoom-in").addEventListener("click", () => { zoom = Math.min(3, zoom * 1.2); applyZoom(); });
    document.getElementById("zoom-out").addEventListener("click", () => { zoom = Math.max(0.1, zoom / 1.2); applyZoom(); });
    document.getElementById("zoom-fit").addEventListener("click", fitCanvas);
    document.getElementById("save-plan").addEventListener("click", () => savePlan().catch((error) => { saveState.textContent = error.message; }));
    const publishForm = document.getElementById("publish-form");
    publishForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        await savePlan();
        HTMLFormElement.prototype.submit.call(publishForm);
      } catch (error) {
        saveState.textContent = error.message;
      }
    });
    document.addEventListener("keydown", (event) => {
      if ((event.key === "Delete" || event.key === "Backspace") && !["INPUT", "SELECT", "TEXTAREA"].includes(event.target.tagName)) {
        const object = canvas.getActiveObject();
        if (object) canvas.remove(object);
      }
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
        event.preventDefault();
        savePlan().catch((error) => { saveState.textContent = error.message; });
      }
    });
    window.addEventListener("resize", fitCanvas);
  }

  initialize().catch((error) => {
    loading.textContent = error.message;
    loading.classList.remove("is-hidden");
  });
})();