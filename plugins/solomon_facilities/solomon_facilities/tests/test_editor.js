const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

class Field {
  constructor() {
    this.value = "";
    this.dataset = {};
    this.handlers = {};
    this.childNodes = [];
    this.attributes = {};
    this.classes = new Set();
    this.classList = {
      add: (name) => this.classes.add(name),
      remove: (name) => this.classes.delete(name),
      toggle: (name, enabled) => enabled ? this.classes.add(name) : this.classes.delete(name),
    };
  }
  addEventListener(name, handler) { this.handlers[name] = handler; }
  replaceChildren() { this.childNodes = []; }
  appendChild(node) { this.childNodes.push(node); }
  setAttribute(name, value) { this.attributes[name] = value; }
  reportValidity() { return this.value !== "" && Number(this.value) >= 1; }
  change(value) {
    this.value = String(value);
    this.handlers.change({currentTarget: this});
  }
}

class Shape {
  constructor(options) {
    Object.assign(this, {type: "rect", scaleX: 1, scaleY: 1, angle: 0, width: 100, height: 50, objectCaching: true}, options);
  }
  set(options) { Object.assign(this, options); }
  setCoords() {}
  getCenterPoint() { return {x: this.left, y: this.top}; }
  translateToOriginPoint(point) { return point; }
  setPositionByOrigin(point, originX, originY) { this.anchor = {point, originX, originY}; }
  setControlsVisibility() {}
  rotate(angle) { this.angle = angle; }
  clone(callback) { callback(new Shape({...this})); }
  _render() {}
  _toSVG() { return ["<rect/>"]; }
}

class Text extends Shape {
  constructor(text, options) { super({...options, text, type: "i-text"}); }
  render(context) {
    context.captionCaching = this.objectCaching;
    context.labels.push({text: this.text, fontSize: this.fontSize, angle: this.angle});
  }
  toSVG() { return `<text font-size="${this.fontSize}" transform="rotate(${this.angle})">${this.text}</text>`; }
}

function source(name) {
  return fs.readFileSync(path.join(__dirname, "../static/solomon_facilities", name), "utf8");
}

async function loadEditor(elements, translations = {}, targets = {spaces: {}, doors: {}, technical_assets: {}}, snapEnabled = false) {
  const fields = {};
  const field = (id) => fields[id] ||= new Field();
  field("schematic-editor").dataset = {url: "/data/", saveUrl: "/data/", revisionId: "1"};
  field("schematic-stage").clientWidth = 1036;
  field("element-label-angle").reportValidity = () => true;
  let canvas;
  let saved;
  class Canvas {
    constructor() {
      canvas = this;
      this.objects = [];
      this.handlers = {};
      this.viewportTransform = [1, 0, 0, 1, 0, 0];
      this.uniformScaling = true;
      this.uniScaleKey = "shiftKey";
    }
    add(object) { this.objects.push(object); }
    on(name, handler) { this.handlers[name] = handler; }
    getActiveObject() { return this.active; }
    setActiveObject(object) { this.active = object; }
    discardActiveObject() { this.active = null; }
    getObjects() { return this.objects; }
    forEachObject(callback) { this.objects.forEach(callback); }
    bringToFront() {}
    setDimensions() {}
    getWidth() { return 1000 * this.viewportTransform[0]; }
    getHeight() { return 800 * this.viewportTransform[3]; }
    getContext() { return this.context; }
    setViewportTransform(transform) { this.viewportTransform = transform; }
    requestRenderAll() {}
  }
  const fabric = {
    Canvas, Rect: Shape, IText: Text, Text,
    Point: class { constructor(x, y) { this.x = x; this.y = y; } },
    util: {
      invertTransform: ([a, , , d, x, y]) => [1 / a, 0, 0, 1 / d, -x / a, -y / d],
      transformPoint: (point, [a, , , d, x, y]) => ({x: point.x * a + x, y: point.y * d + y}),
    },
  };
  const buttons = {add: new Field(), pan: new Field(), select: new Field()};
  buttons.add.dataset.add = "space";
  buttons.pan.dataset.tool = "pan";
  buttons.select.dataset.tool = "select";
  const window = {fabric, addEventListener() {}};
  vm.runInNewContext(source("labels.js"), {window, fabric});
  vm.runInNewContext(source("editor.js"), {
    window, fabric, SolomonPlanLabels: window.SolomonPlanLabels,
    document: {
      getElementById: field,
      querySelectorAll: (selector) => {
        if (selector === "[data-add]") return [buttons.add];
        if (selector === "[data-tool]") return [buttons.pan, buttons.select];
        return [];
      },
      querySelector: () => ({value: "csrf-token"}),
      createElement: () => new Field(),
      addEventListener() {},
    },
    gettext: (message) => translations[message] || message,
    interpolate: (format, values) => format.replace(/%s/g, () => values.shift()),
    HTMLFormElement: {prototype: {submit() {}}},
    fetch: async (url, options) => {
      if (options.method === "PUT") saved = JSON.parse(options.body);
      return {
        ok: true,
        headers: {get: () => "application/json"},
        json: async () => options.method === "PUT" ? {} : {
          plan: {width: 1000, height: 800}, revision: {}, elements,
          targets,
        },
      };
    },
  });
  await new Promise((resolve) => setImmediate(resolve));
  assert.ok(canvas?.handlers["selection:created"], field("schematic-loading").textContent);
  if (!snapEnabled) field("toggle-snap-grid").handlers.click();
  return {
    canvas, field, buttons,
    select(object) {
      canvas.setActiveObject(object);
      canvas.handlers["selection:created"]();
    },
    async save() {
      await field("save-form").handlers.submit({preventDefault() {}});
      assert.ok(saved, field("save-state").textContent);
      return saved;
    },
  };
}

const rectangle = {
  element_type: "space", label: "Room",
  geometry: {type: "rect", x: 20, y: 40, width: 100, height: 50},
  style: {angle: 25, scale_x: 2, scale_y: 3},
};
const textElement = {
  element_type: "text", label: "Note",
  geometry: {type: "text", x: 200, y: 100, text: "Note"},
  style: {font_size: 24},
};

test("snapping starts enabled without changing existing objects or marking the plan changed", async () => {
  const editor = await loadEditor([{...rectangle, geometry: {...rectangle.geometry, x: 23, y: 42}}], {}, undefined, true);
  const button = editor.field("toggle-snap-grid");
  const object = editor.canvas.objects[0];
  assert.equal(button.attributes["aria-pressed"], "true");
  assert.ok(button.classes.has("active"));
  assert.equal(object.left, 23);
  assert.equal(object.top, 42);
  assert.notEqual(editor.field("save-state").textContent, "Changed");
  editor.select(object);
  editor.canvas.handlers["object:moving"]({target: object});
  assert.equal(object.left, 25);
  assert.equal(object.top, 40);
  button.handlers.click();
  assert.equal(button.attributes["aria-pressed"], "false");
  assert.ok(!button.classes.has("active"));
});

test("grid toggle snaps movement to 5 plan units and saves positions without changing geometry", async () => {
  const editor = await loadEditor([rectangle, textElement]);
  const object = editor.canvas.objects[0];
  editor.select(object);
  const move = (x, y) => {
    object.set({left: x, top: y});
    editor.canvas.handlers["object:moving"]({target: object});
  };
  move(31, 49);
  assert.equal(object.left, 31, "Disabled snapping leaves movement exact");
  assert.equal(object.top, 49);
  const button = editor.field("toggle-snap-grid");
  button.handlers.click();
  assert.equal(button.attributes["aria-pressed"], "true");
  assert.ok(button.classes.has("active"));
  assert.equal(object.left, 31, "Enabling does not move existing elements");
  assert.notEqual(editor.field("save-state").textContent, "Changed");
  for (const [x, y, expectedX, expectedY] of [[31, 49, 30, 50], [32.4, 52.6, 30, 55], [-31, -49, -30, -50], [40, 60, 40, 60]]) {
    move(x, y);
    assert.equal(object.left, expectedX);
    assert.equal(object.top, expectedY);
    assert.ok(Math.abs(object.left - x) <= 2.5);
    assert.ok(Math.abs(object.top - y) <= 2.5);
  }
  assert.equal(editor.field("element-x").value, "40.0");
  assert.equal(editor.field("element-y").value, "60.0");
  assert.equal(object.angle, 25);
  assert.equal(object.scaleX, 2);
  assert.equal(object.scaleY, 3);
  editor.canvas.handlers["object:modified"]({target: object});
  const saved = await editor.save();
  assert.equal(saved.elements[0].style.position_x, 40);
  assert.equal(saved.elements[0].style.position_y, 60);
  assert.equal(saved.elements.length, 2, "The grid is not a saved object");
  const reloaded = await loadEditor(saved.elements);
  assert.equal(reloaded.canvas.objects[0].left, 40);
  assert.equal(reloaded.canvas.objects[0].top, 60);
  button.handlers.click();
  assert.equal(button.attributes["aria-pressed"], "false");
  assert.ok(!button.classes.has("active"));
  move(31, 49);
  assert.equal(object.left, 31);
  assert.equal(object.top, 49);
});

test("snapping respects movement locks, pan mode, zoom, and exact inspector input", async () => {
  const editor = await loadEditor([rectangle, {...rectangle, locked: true}]);
  const object = editor.canvas.objects[0];
  editor.select(object);
  editor.field("toggle-snap-grid").handlers.click();
  object.set({left: 31, top: 49, lockMovementX: true});
  editor.canvas.handlers["object:moving"]({target: object});
  assert.equal(object.left, 31);
  assert.equal(object.top, 50);
  const locked = editor.canvas.objects[1];
  locked.set({left: 31, top: 49});
  editor.canvas.handlers["object:moving"]({target: locked});
  assert.equal(locked.left, 31);
  assert.equal(locked.top, 49);
  editor.buttons.pan.handlers.click();
  object.set({left: 31, top: 49, lockMovementX: false});
  editor.canvas.handlers["object:moving"]({target: object});
  assert.equal(object.top, 49);
  editor.buttons.select.handlers.click();
  editor.select(object);
  editor.field("zoom-out").handlers.click();
  editor.canvas.viewportTransform[4] = 127;
  editor.canvas.viewportTransform[5] = -59;
  editor.canvas.handlers["object:moving"]({target: object});
  assert.equal(object.left, 30);
  assert.equal(object.top, 50);
  editor.field("element-x").change(33);
  assert.equal(object.left, 33, "Inspector input stays exact");
});

test("new and duplicated objects snap only when enabled", async () => {
  const editor = await loadEditor([rectangle]);
  editor.select(editor.canvas.objects[0]);
  editor.field("duplicate-element").handlers.click();
  assert.equal(editor.canvas.objects[1].left, 52);
  editor.field("toggle-snap-grid").handlers.click();
  editor.select(editor.canvas.objects[0]);
  editor.field("duplicate-element").handlers.click();
  assert.equal(editor.canvas.objects[2].left, 50);
  assert.equal(editor.canvas.objects[2].top, 70);
  editor.buttons.add.handlers.click({currentTarget: editor.buttons.add});
  assert.equal(editor.canvas.active.left, 430);
  assert.equal(editor.canvas.active.top, 350);
});

test("grid dots follow the viewport and are omitted when snapping is disabled", async () => {
  const editor = await loadEditor([]);
  const dots = [];
  editor.canvas.context = {
    save() {}, restore() {},
    fillRect: (...args) => dots.push(args),
  };
  editor.canvas.handlers["after:render"]();
  assert.equal(dots.length, 0);
  editor.field("toggle-snap-grid").handlers.click();
  editor.canvas.handlers["after:render"]();
  assert.deepEqual(dots[0], [-1, -1, 2, 2]);
  assert.deepEqual(dots[1], [-1, 9, 2, 2]);
  editor.field("zoom-out").handlers.click();
  editor.canvas.viewportTransform[4] = -10;
  editor.canvas.viewportTransform[5] = -10;
  dots.length = 0;
  editor.canvas.handlers["after:render"]();
  assert.ok(Math.abs(dots[0][0] - (20 / 1.2 - 11)) < 1e-9);
  assert.ok(Math.abs(dots[0][1] - (20 / 1.2 - 11)) < 1e-9);
  editor.field("toggle-snap-grid").handlers.click();
  dots.length = 0;
  editor.canvas.handlers["after:render"]();
  assert.equal(dots.length, 0);
});

test("resizing snaps dimensions, keeps the fixed anchor, and saves scales", async () => {
  const editor = await loadEditor([rectangle]);
  const object = editor.canvas.objects[0];
  editor.select(object);
  const resize = (action, scaleX, scaleY, shiftKey = false) => {
    object.set({scaleX, scaleY});
    editor.canvas.handlers["object:scaling"]({
      target: object, transform: {action, originX: "right", originY: "bottom"}, e: {shiftKey},
    });
  };
  resize("scaleX", 1.23, 1.17);
  assert.equal(object.scaleX, 1.23, "Disabled snapping leaves resizing exact");
  editor.field("toggle-snap-grid").handlers.click();
  resize("scaleX", 1.23, 1.17);
  assert.equal(object.width * object.scaleX, 125);
  assert.equal(object.scaleY, 1.17, "Horizontal handles leave height unchanged");
  assert.equal(object.anchor.originX, "right");
  assert.equal(object.anchor.originY, "bottom");
  assert.equal(object.anchor.point.x, 20);
  assert.equal(object.anchor.point.y, 40);
  resize("scaleY", 1.23, 1.17);
  assert.equal(object.scaleX, 1.23);
  assert.equal(object.height * object.scaleY, 60);
  resize("scale", 1.23, 1.17, true);
  assert.equal(object.width * object.scaleX, 125);
  assert.equal(object.height * object.scaleY, 60);
  assert.equal(object.angle, 25);
  assert.equal(editor.field("element-width").value, "125.0");
  assert.equal(editor.field("element-height").value, "60.0");
  editor.canvas.handlers["object:modified"]({target: object});
  const saved = await editor.save();
  assert.equal(saved.elements[0].style.scale_x, 1.25);
  assert.equal(saved.elements[0].style.scale_y, 1.2);
  editor.field("element-width").change(123);
  assert.equal(object.width * object.scaleX, 123, "Inspector dimensions remain exact");
});

test("proportional resizing snaps the larger dimension without stretching shapes or text", async () => {
  const editor = await loadEditor([rectangle, textElement]);
  editor.field("toggle-snap-grid").handlers.click();
  for (const object of editor.canvas.objects) {
    editor.select(object);
    object.set({scaleX: 1.23, scaleY: 2.46});
    editor.canvas.handlers["object:scaling"]({
      target: object, transform: {action: "scale", originX: "left", originY: "top"}, e: {},
    });
    assert.equal(object.width * object.scaleX, 125);
    assert.equal(object.scaleY / object.scaleX, 2);
  }
  const text = editor.canvas.objects[1];
  text.set({scaleX: 1.23, scaleY: 1.23});
  editor.canvas.handlers["object:scaling"]({
    target: text, transform: {action: "scale", originX: "left", originY: "top"}, e: {shiftKey: true},
  });
  assert.equal(text.scaleX, text.scaleY, "Text stays proportional even with Shift");
  editor.canvas.handlers["object:modified"]({target: text});
  assert.equal(text.scaleX, 1);
  assert.equal(text.scaleY, 1);
  assert.equal(text.fontSize, 30);
});

test("resize snapping respects scale locks, minimum size, zero dimensions, flips, and pan mode", async () => {
  const editor = await loadEditor([rectangle]);
  const object = editor.canvas.objects[0];
  editor.select(object);
  editor.field("toggle-snap-grid").handlers.click();
  const resize = () => editor.canvas.handlers["object:scaling"]({
    target: object, transform: {action: "scale", originX: "left", originY: "top"}, e: {shiftKey: true},
  });
  object.set({scaleX: 1.23, scaleY: 1.17, lockScalingX: true});
  resize();
  assert.equal(object.scaleX, 1.23);
  assert.equal(object.scaleY, 1.2);
  object.set({scaleX: 0.001, scaleY: -0.001, lockScalingX: false});
  resize();
  assert.equal(object.width * object.scaleX, 5);
  assert.equal(object.height * object.scaleY, -5);
  object.set({width: 0, scaleX: 1.23, scaleY: 1.17});
  resize();
  assert.equal(object.scaleX, 1.23, "Zero-width lines do not divide by zero");
  assert.equal(object.scaleY, 1.2);
  object.set({locked: true, scaleY: 1.17});
  resize();
  assert.equal(object.scaleY, 1.17);
  object.locked = false;
  editor.buttons.pan.handlers.click();
  resize();
  assert.equal(object.scaleY, 1.17);
});

test("rotation snaps in 15-degree steps only when enabled and persists", async () => {
  const editor = await loadEditor([rectangle]);
  const object = editor.canvas.objects[0];
  editor.select(object);
  const rotate = (angle) => {
    object.angle = angle;
    editor.canvas.handlers["object:rotating"]({target: object});
  };
  rotate(23);
  assert.equal(object.angle, 23);
  editor.field("toggle-snap-grid").handlers.click();
  for (const [angle, expected] of [[22.4, 15], [22.6, 30], [89, 90], [359, 360], [-23, -30]]) {
    rotate(angle);
    assert.equal(object.angle, expected);
    assert.ok(Math.abs(object.angle - angle) <= 7.5);
  }
  object.lockRotation = true;
  rotate(23);
  assert.equal(object.angle, 23);
  object.lockRotation = false;
  object.locked = true;
  rotate(23);
  assert.equal(object.angle, 23);
  object.locked = false;
  rotate(44);
  editor.canvas.handlers["object:modified"]({target: object});
  const saved = await editor.save();
  assert.equal(saved.elements[0].style.angle, 45);
  editor.field("toggle-snap-grid").handlers.click();
  rotate(23);
  assert.equal(object.angle, 23);
});

test("editor translates save states and linked-object options without changing labels", async () => {
  const editor = await loadEditor([rectangle], {
    Changed: "Změněno",
    Saved: "Uloženo",
    Spaces: "Prostory",
    "Select linked object (%s available)": "Vyberte propojený objekt (k dispozici: %s)",
  }, {spaces: {"1": {id: 1, label: "Room"}}, doors: {}, technical_assets: {}});
  editor.select(editor.canvas.objects[0]);
  const options = editor.field("element-target").childNodes;
  assert.equal(options[0].textContent, "Vyberte propojený objekt (k dispozici: 1)");
  assert.equal(options[1].label, "Prostory");
  assert.equal(options[1].childNodes[0].textContent, "Room");
  editor.field("element-font-size").change(32);
  assert.equal(editor.field("save-state").textContent, "Změněno");
  await editor.save();
  assert.equal(editor.field("save-state").textContent, "Uloženo");
});

test("caption size and quarter turns save, duplicate, and reload independently of shape geometry", async () => {
  const editor = await loadEditor([rectangle, textElement]);
  const object = editor.canvas.objects[0];
  editor.select(object);
  assert.equal(editor.field("element-font-size").value, 18);
  assert.equal(editor.field("element-label-angle").value, "0");
  editor.field("element-font-size").change(32.5);
  for (const angle of [90, 180, 270, 0]) {
    editor.field("element-label-angle").change(angle);
    assert.equal(object.labelAngle, angle);
    assert.equal(object.angle, 25);
  }
  editor.field("element-label-angle").change(270);
  assert.equal(object.labelFontSize, 32.5);
  assert.equal(object.scaleX, 2);
  assert.equal(object.scaleY, 3);
  editor.field("duplicate-element").handlers.click();
  const duplicate = editor.canvas.objects[2];
  assert.equal(duplicate.labelFontSize, 32.5);
  assert.equal(duplicate.labelAngle, 270);
  const saved = await editor.save();
  assert.equal(saved.elements[0].style.font_size, 32.5);
  assert.equal(saved.elements[0].style.label_angle, 270);
  assert.equal(saved.elements[0].style.angle, 25);
  assert.equal(saved.elements[2].style.font_size, 32.5);
  assert.equal(saved.elements[2].style.label_angle, 270);
  const reloaded = await loadEditor(saved.elements);
  reloaded.select(reloaded.canvas.objects[0]);
  assert.equal(reloaded.field("element-font-size").value, 32.5);
  assert.equal(reloaded.field("element-label-angle").value, "270");
});

test("standalone text size and orientation persist without stretching", async () => {
  const editor = await loadEditor([textElement]);
  const object = editor.canvas.objects[0];
  editor.select(object);
  editor.field("element-font-size").change(48);
  for (const angle of [0, 90, 180, 270]) {
    editor.field("element-label-angle").change(angle);
    assert.equal(object.angle, angle);
  }
  assert.equal(object.fontSize, 48);
  assert.equal(object.scaleX, 1);
  assert.equal(object.scaleY, 1);
  const saved = await editor.save();
  assert.equal(saved.elements[0].style.font_size, 48);
  assert.equal(saved.elements[0].style.angle, 270);
  const reloaded = await loadEditor(saved.elements);
  reloaded.select(reloaded.canvas.objects[0]);
  assert.equal(reloaded.field("element-font-size").value, 48);
  assert.equal(reloaded.field("element-label-angle").value, "270");
});

test("invalid text sizes do not change the object or mark it changed", async () => {
  const editor = await loadEditor([rectangle]);
  editor.select(editor.canvas.objects[0]);
  for (const value of ["", 0, -10, "invalid"]) editor.field("element-font-size").change(value);
  assert.equal(editor.canvas.objects[0].labelFontSize, 18);
  assert.notEqual(editor.field("save-state").textContent, "Changed");
});

test("uncached captions preserve size and rotation in canvas rendering and SVG", () => {
  const window = {};
  vm.runInNewContext(source("labels.js"), {window, fabric: {Text}});
  const object = new Shape({scaleX: 2, scaleY: 4});
  window.SolomonPlanLabels.attach(object, "Room", true, 36, 270);
  const context = {
    labels: [], scales: [],
    save() {}, restore() {},
    scale(x, y) { this.scales.push([x, y]); },
  };
  object._render(context);
  assert.equal(object.objectCaching, false);
  assert.equal(context.captionCaching, false, "Detached captions must not use low-resolution bitmap caches");
  assert.deepEqual(context.scales, [[0.5, 0.25]]);
  assert.deepEqual(context.labels, [{text: "Room", fontSize: 36, angle: 270}]);
  object.visible = true;
  assert.match(object._toSVG().join(""), /scale\(0.5 0.25\)/);
  assert.match(object._toSVG().join(""), /font-size="36" transform="rotate\(270\)"/);
  object.labelVisible = false;
  context.labels = [];
  object._render(context);
  assert.equal(context.labels.length, 0);
  assert.equal(object._toSVG().join(""), "<rect/>");
});
