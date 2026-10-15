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
    labelVisible: document.getElementById("element-label-visible"),
    fontSize: document.getElementById("element-font-size"),
    labelAngle: document.getElementById("element-label-angle"),
    target: document.getElementById("element-target"),
    x: document.getElementById("element-x"),
    y: document.getElementById("element-y"),
    width: document.getElementById("element-width"),
    height: document.getElementById("element-height"),
    stroke: document.getElementById("element-stroke"),
    fill: document.getElementById("element-fill"),
    locked: document.getElementById("element-locked"),
    transparent: document.getElementById("element-transparent"),
  };
  const targetHelp = document.getElementById("element-target-help");
  const targetActions = document.getElementById("element-target-actions");
  let canvas;
  let planData;
  let zoom = 1;
  let panMode = false;
  let dragging = false;
  let lastPointer;
  let dirty = false;
  let leavingEditor = false;
  let seeThrough = SolomonPlanLabels.loadSeeThrough();
  const TRANSPARENT_OPACITY = 0.62;
  const GRID_SIZE = 5;
  const ROTATION_STEP = 15;
  let snapToGrid = true;

  function snapPosition(object) {
    if (!snapToGrid || panMode || object.locked) return;
    if (!object.lockMovementX) object.set({left: Math.round(object.left / GRID_SIZE) * GRID_SIZE});
    if (!object.lockMovementY) object.set({top: Math.round(object.top / GRID_SIZE) * GRID_SIZE});
    object.setCoords();
  }

  function snapResize(event) {
    const object = event.target;
    const transform = event.transform;
    if (!snapToGrid || panMode || object.locked || !transform) return;
    const scaleX = transform.action !== "scaleY" && !object.lockScalingX;
    const scaleY = transform.action !== "scaleX" && !object.lockScalingY;
    if (!scaleX && !scaleY) return;
    const anchor = object.translateToOriginPoint(object.getCenterPoint(), transform.originX, transform.originY);
    const width = object.width * Math.abs(object.scaleX);
    const height = object.height * Math.abs(object.scaleY);
    const uniform = transform.action === "scale" &&
      (object.type === "i-text" || object.type === "text" ||
        Boolean(canvas.uniformScaling) !== Boolean(event.e?.[canvas.uniScaleKey]));
    const snappedSize = (size) => Math.max(GRID_SIZE, Math.round(size / GRID_SIZE) * GRID_SIZE);
    if (uniform && scaleX && scaleY) {
      const size = Math.max(width, height);
      if (size > 0) {
        const ratio = snappedSize(size) / size;
        object.set({scaleX: object.scaleX * ratio, scaleY: object.scaleY * ratio});
      }
    } else {
      if (scaleX && width > 0) object.set({scaleX: Math.sign(object.scaleX) * snappedSize(width) / object.width});
      if (scaleY && height > 0) object.set({scaleY: Math.sign(object.scaleY) * snappedSize(height) / object.height});
    }
    object.setPositionByOrigin(anchor, transform.originX, transform.originY);
    object.setCoords();
  }

  function renderGrid() {
    if (!snapToGrid) return;
    const context = canvas.getContext();
    const transform = canvas.viewportTransform;
    const step = GRID_SIZE * Math.max(1, Math.ceil(8 / (GRID_SIZE * zoom)));
    const left = Math.max(0, -transform[4] / zoom);
    const top = Math.max(0, -transform[5] / zoom);
    const right = Math.min(planData.plan.width, (canvas.getWidth() - transform[4]) / zoom);
    const bottom = Math.min(planData.plan.height, (canvas.getHeight() - transform[5]) / zoom);
    context.save();
    context.fillStyle = "rgba(39, 52, 58, 0.3)";
    for (let x = Math.ceil(left / step) * step; x <= right; x += step) {
      for (let y = Math.ceil(top / step) * step; y <= bottom; y += step) {
        context.fillRect(x * zoom + transform[4] - 1, y * zoom + transform[5] - 1, 2, 2);
      }
    }
    context.restore();
  }

  function getCsrfToken() {
    const input = document.querySelector("#save-form [name=csrfmiddlewaretoken]");
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
    if (!response.ok) throw new Error(interpolate(gettext("Plan request failed (%s)"), [response.status]));
    throw new Error(text || gettext("Plan request returned an invalid response"));
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
      strokeUniform: true,
      opacity: style.opacity === undefined ? 1 : Number(style.opacity),
      angle: Number(style.angle || 0),
      scaleX: Number(style.scale_x || 1),
      scaleY: Number(style.scale_y || 1),
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
      object = new fabric.IText(geometry.text || element.label || gettext("Label"), {
        ...common,
        left: geometry.x || 0,
        top: geometry.y || 0,
        fill: style.fill || "#27343a",
        fontSize: Number(style.font_size || 18),
        fontFamily: "Avenir Next, Trebuchet MS, sans-serif",
      });
    }
    if (style.position_x !== undefined && style.position_y !== undefined) {
      object.set({left: Number(style.position_x), top: Number(style.position_y)});
      object.setCoords();
    }
    const target = targetFromElement(element);
    object.elementType = element.element_type;
    object.itemOpacity = common.opacity;
    prepareObject(object);
    SolomonPlanLabels.attach(object, element.label, style.label_visible !== false, style.font_size || 18, style.label_angle || 0);
    object.targetKind = target.kind;
    object.targetId = target.id ? String(target.id) : "";
    object.locked = Boolean(element.locked);
    return object;
  }

  function prepareObject(object) {
    object.set({strokeUniform: true, opacity: SolomonPlanLabels.displayOpacity(object, seeThrough)});
    if (object.type === "i-text" || object.type === "text") {
      SolomonPlanLabels.normalizeTextScale(object);
      // Only corner handles, so text grows proportionally and is never stretched.
      object.setControlsVisibility({mt: false, mb: false, ml: false, mr: false});
      object.lockScalingFlip = true;
    }
  }

  function applySeeThrough() {
    const button = document.getElementById("toggle-see-through");
    button.classList.toggle("active", seeThrough);
    button.setAttribute("aria-pressed", seeThrough ? "true" : "false");
    canvas.forEachObject((object) => object.set({opacity: SolomonPlanLabels.displayOpacity(object, seeThrough)}));
    canvas.requestRenderAll();
  }

  function serializeObject(object, index) {
    let geometry;
    if (object.type === "line") {
      geometry = {
        type: "line",
        x1: object.x1,
        y1: object.y1,
        x2: object.x2,
        y2: object.y2,
      };
    } else if (object.type === "circle") {
      geometry = {
        type: "point",
        x: object.left + object.radius,
        y: object.top + object.radius,
      };
    } else if (object.type === "i-text" || object.type === "text") {
      geometry = {type: "text", x: object.left, y: object.top, text: object.text};
    } else if (object.type === "polygon" || object.type === "polyline") {
      geometry = {
        type: object.type,
        points: object.points.map((point) => ({x: point.x, y: point.y})),
      };
    } else {
      geometry = {
        type: "rect",
        x: object.left,
        y: object.top,
        width: object.width,
        height: object.height,
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
        opacity: object.itemOpacity === undefined ? object.opacity : object.itemOpacity,
        angle: object.angle || 0,
        scale_x: object.scaleX || 1,
        scale_y: object.scaleY || 1,
        position_x: object.left,
        position_y: object.top,
        radius: object.radius || undefined,
        font_size: object.fontSize || object.labelFontSize,
        label_angle: object.labelAngle,
        label_visible: object.labelVisible,
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
        opacity: TRANSPARENT_OPACITY,
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
      object = new fabric.IText(gettext("Label"), {
        left: center.x,
        top: center.y,
        fill: "#27343a",
        fontSize: 18,
        fontFamily: "Avenir Next, Trebuchet MS, sans-serif",
      });
    }
    object.elementType = elementType;
    object.itemOpacity = elementType === "space" ? TRANSPARENT_OPACITY : 1;
    prepareObject(object);
    SolomonPlanLabels.attach(object, elementType === "text" ? gettext("Label") : "");
    object.targetKind = "";
    object.targetId = "";
    object.locked = false;
    snapPosition(object);
    canvas.discardActiveObject();
    canvas.add(object);
    canvas.setActiveObject(object);
    canvas.bringToFront(object);
    canvas.requestRenderAll();
    updateInspector(object);
    markChanged();
  }

  function duplicateSelectedObject() {
    const source = canvas.getActiveObject();
    if (!source) return;
    source.clone((duplicate) => {
      const offset = 32 / zoom;
      duplicate.set({
        left: Number(source.left || 0) + offset,
        top: Number(source.top || 0) + offset,
      });
      duplicate.elementType = source.elementType;
      duplicate.itemOpacity = source.itemOpacity;
      prepareObject(duplicate);
      SolomonPlanLabels.attach(duplicate, source.elementLabel, source.labelVisible, source.labelFontSize, source.labelAngle);
      duplicate.targetKind = "";
      duplicate.targetId = "";
      duplicate.locked = Boolean(source.locked);
      snapPosition(duplicate);
      canvas.discardActiveObject();
      canvas.add(duplicate);
      canvas.setActiveObject(duplicate);
      canvas.bringToFront(duplicate);
      canvas.requestRenderAll();
      updateInspector(duplicate);
      markChanged();
    });
  }

  function markChanged() {
    dirty = true;
    saveState.textContent = gettext("Changed");
  }

  function objectDimensionBases(object) {
    const strokeWidth = Number(object.strokeWidth || 0);
    return {
      width: Number(object.width || (object.type === "line" ? strokeWidth : 0)),
      height: Number(object.height || (object.type === "line" ? strokeWidth : 0)),
    };
  }

  function deleteSelectedObject() {
    const object = canvas.getActiveObject();
    if (!object) return;
    canvas.remove(object);
    updateInspector();
    markChanged();
  }

  function reorderSelectedObject(direction) {
    const object = canvas.getActiveObject();
    if (!object) return;
    const objects = canvas.getObjects();
    const index = objects.indexOf(object);
    if (direction === "front") canvas.bringToFront(object);
    if (direction === "back") canvas.sendToBack(object);
    if (direction === "forward") canvas.bringForward(object);
    if (direction === "backward") canvas.sendBackwards(object);
    if (canvas.getObjects().indexOf(object) === index) return;
    canvas.requestRenderAll();
    markChanged();
  }

  function populateTargetOptions() {
    const selectedValue = fields.target.value;
    fields.target.replaceChildren();
    const empty = document.createElement("option");
    empty.value = "";
    empty.textContent = gettext("No linked object");
    fields.target.appendChild(empty);
    const collections = [
      ["space", gettext("Spaces"), planData.targets.spaces],
      ["door", gettext("Doors"), planData.targets.doors],
      ["technical_asset", gettext("Technical assets"), planData.targets.technical_assets],
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
      ? interpolate(gettext("Select linked object (%s available)"), [total])
      : gettext("No linkable objects exist on this floor");
    fields.target.disabled = !canvas.getActiveObject() || total === 0;
    fields.target.value = selectedValue;
    targetHelp.textContent = total
      ? gettext("Optional. Any painted element can link to a facility record on this floor.")
      : gettext("Create a space, door, or technical asset for this floor, then select Refresh.");
    targetActions.classList.toggle("is-empty", total === 0);
  }

  function updateInspector(selectedObject) {
    const object = selectedObject || canvas.getActiveObject();
    const disabled = !object;
    document.getElementById("duplicate-element").disabled = disabled;
    document.querySelectorAll("[data-order]").forEach((button) => { button.disabled = disabled; });
    Object.values(fields).forEach((field) => { field.disabled = disabled; });
    if (!object) return;
    fields.type.value = object.elementType || "line";
    fields.label.value = object.elementLabel || (object.type === "i-text" ? object.text : "");
    fields.labelVisible.checked = object.labelVisible;
    const isText = object.type === "i-text" || object.type === "text";
    fields.fontSize.value = isText ? object.fontSize : object.labelFontSize;
    const labelAngle = isText ? object.angle : object.labelAngle;
    fields.labelAngle.value = String(((Math.round(labelAngle / 90) * 90) % 360 + 360) % 360);
    populateTargetOptions();
    fields.target.value = object.targetKind && object.targetId ? `${object.targetKind}:${object.targetId}` : "";
    fields.x.value = Number(object.left || 0).toFixed(1);
    fields.y.value = Number(object.top || 0).toFixed(1);
    const dimensionBases = objectDimensionBases(object);
    fields.width.value = Number(dimensionBases.width * object.scaleX || 0).toFixed(1);
    fields.height.value = Number(dimensionBases.height * object.scaleY || 0).toFixed(1);
    fields.stroke.value = /^#[0-9a-f]{6}$/i.test(object.stroke) ? object.stroke : "#27343a";
    fields.fill.value = /^#[0-9a-f]{6}$/i.test(object.fill) ? object.fill : "#dce9e4";
    fields.locked.checked = Boolean(object.locked);
    fields.transparent.checked = Number(object.itemOpacity === undefined ? 1 : object.itemOpacity) < 1;
  }

  function updateLabel() {
    const object = canvas.getActiveObject();
    if (!object) return;
    object.elementLabel = fields.label.value;
    object.labelVisible = fields.labelVisible.checked;
    if (object.type === "i-text") object.set({text: fields.label.value || "Label"});
    object.setCoords();
    canvas.requestRenderAll();
    markChanged();
  }

  function updateLabelStyle(event) {
    const object = canvas.getActiveObject();
    if (!object) return;
    const field = event.currentTarget;
    if (!field.reportValidity()) return;
    const isText = object.type === "i-text" || object.type === "text";
    if (field === fields.fontSize) {
      const fontSize = Number(field.value);
      if (isText) object.set({fontSize});
      else object.labelFontSize = fontSize;
    } else {
      const angle = Number(field.value);
      if (isText) object.rotate(angle);
      else object.labelAngle = angle;
    }
    object.setCoords();
    canvas.requestRenderAll();
    updateInspector(object);
    markChanged();
  }

  function updateObject() {
    const object = canvas.getActiveObject();
    if (!object) return;
    object.elementType = fields.type.value;
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
    const dimensionBases = objectDimensionBases(object);
    if (dimensionBases.width && Number(fields.width.value) > 0) object.scaleX = Number(fields.width.value) / dimensionBases.width;
    if (dimensionBases.height && Number(fields.height.value) > 0) object.scaleY = Number(fields.height.value) / dimensionBases.height;
    SolomonPlanLabels.normalizeTextScale(object);
    object.locked = fields.locked.checked;
    const currentOpacity = object.itemOpacity === undefined ? 1 : Number(object.itemOpacity);
    if (fields.transparent.checked !== currentOpacity < 1) {
      object.itemOpacity = fields.transparent.checked ? TRANSPARENT_OPACITY : 1;
    }
    object.set({opacity: SolomonPlanLabels.displayOpacity(object, seeThrough)});
    object.setCoords();
    canvas.requestRenderAll();
    markChanged();
  }

  async function savePlan() {
    saveState.textContent = gettext("Saving...");
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
    dirty = false;
    saveState.textContent = gettext("Saved");
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
    if (!window.fabric) throw new Error(gettext("Fabric.js did not load"));
    const response = await fetch(app.dataset.url, {headers: {Accept: "application/json"}});
    if (!response.ok) throw new Error(interpolate(gettext("Plan request failed (%s)"), [response.status]));
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
    canvas.on("selection:created", () => updateInspector());
    canvas.on("selection:updated", () => updateInspector());
    canvas.on("selection:cleared", () => updateInspector());
    canvas.on("after:render", renderGrid);
    canvas.on("object:moving", (event) => {
      snapPosition(event.target);
      updateInspector(event.target);
    });
    canvas.on("object:scaling", (event) => {
      snapResize(event);
      updateInspector(event.target);
    });
    canvas.on("object:rotating", (event) => {
      const object = event.target;
      if (snapToGrid && !panMode && !object.locked && !object.lockRotation) {
        object.rotate(Math.round(object.angle / ROTATION_STEP) * ROTATION_STEP);
        object.setCoords();
      }
      updateInspector(object);
    });
    canvas.on("object:modified", (event) => {
      if (event.target) SolomonPlanLabels.normalizeTextScale(event.target);
      updateInspector();
      markChanged();
    });
    canvas.on("text:changed", (event) => {
      event.target.elementLabel = event.target.text;
      updateInspector(event.target);
      markChanged();
    });
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
      if (!["type", "label", "labelVisible", "fontSize", "labelAngle"].includes(name)) field.addEventListener("change", updateObject);
    });
    fields.fontSize.addEventListener("change", updateLabelStyle);
    fields.labelAngle.addEventListener("change", updateLabelStyle);
    fields.label.addEventListener("input", updateLabel);
    fields.label.addEventListener("change", updateLabel);
    fields.labelVisible.addEventListener("change", updateLabel);
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
    document.getElementById("duplicate-element").addEventListener("click", duplicateSelectedObject);
    document.getElementById("delete-element").addEventListener("click", deleteSelectedObject);
    document.querySelectorAll("[data-order]").forEach((button) => button.addEventListener("click", () => {
      reorderSelectedObject(button.dataset.order);
    }));
    const seeThroughButton = document.getElementById("toggle-see-through");
    seeThroughButton.classList.toggle("active", seeThrough);
    seeThroughButton.setAttribute("aria-pressed", seeThrough ? "true" : "false");
    seeThroughButton.addEventListener("click", () => {
      seeThrough = !seeThrough;
      SolomonPlanLabels.storeSeeThrough(seeThrough);
      applySeeThrough();
    });
    const snapButton = document.getElementById("toggle-snap-grid");
    snapButton.classList.toggle("active", snapToGrid);
    snapButton.setAttribute("aria-pressed", snapToGrid ? "true" : "false");
    snapButton.addEventListener("click", () => {
      snapToGrid = !snapToGrid;
      snapButton.classList.toggle("active", snapToGrid);
      snapButton.setAttribute("aria-pressed", snapToGrid ? "true" : "false");
      canvas.requestRenderAll();
    });
    document.getElementById("zoom-in").addEventListener("click", () => { zoom = Math.min(3, zoom * 1.2); applyZoom(); });
    document.getElementById("zoom-out").addEventListener("click", () => { zoom = Math.max(0.1, zoom / 1.2); applyZoom(); });
    document.getElementById("zoom-fit").addEventListener("click", fitCanvas);
    const saveForm = document.getElementById("save-form");
    saveForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      try {
        await savePlan();
        leavingEditor = true;
        HTMLFormElement.prototype.submit.call(saveForm);
      } catch (error) {
        saveState.textContent = error.message;
      }
    });
    document.getElementById("cancel-edit").addEventListener("click", () => {
      leavingEditor = true;
      dirty = false;
    });
    document.addEventListener("keydown", (event) => {
      if ((event.key === "Delete" || event.key === "Backspace") && !["INPUT", "SELECT", "TEXTAREA"].includes(event.target.tagName)) {
        deleteSelectedObject();
      }
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
        event.preventDefault();
        saveForm.requestSubmit();
      }
      if (event.shiftKey && !event.ctrlKey && !event.metaKey && !event.altKey && event.key.toLowerCase() === "d" && !["INPUT", "SELECT", "TEXTAREA"].includes(event.target.tagName) && !canvas.getActiveObject()?.isEditing) {
        event.preventDefault();
        duplicateSelectedObject();
      }
      const typing = ["INPUT", "SELECT", "TEXTAREA"].includes(event.target.tagName) || canvas.getActiveObject()?.isEditing;
      const orderKeys = {"]": "forward", "[": "backward", "}": "front", "{": "back"};
      if (!typing && !event.ctrlKey && !event.metaKey && !event.altKey && orderKeys[event.key]) {
        event.preventDefault();
        reorderSelectedObject(orderKeys[event.key]);
      }
    });
    window.addEventListener("beforeunload", (event) => {
      if (!dirty || leavingEditor) return;
      event.preventDefault();
      event.returnValue = "";
    });
    window.addEventListener("resize", fitCanvas);
  }

  initialize().catch((error) => {
    loading.textContent = error.message;
    loading.classList.remove("is-hidden");
  });
})();