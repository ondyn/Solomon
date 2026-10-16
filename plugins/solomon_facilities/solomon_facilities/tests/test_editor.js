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
  setCoords() {
    this.controlPositions = {};
    for (const [key, control] of Object.entries(this.controls || {})) {
      this.controlPositions[key] = control.positionHandler(null, null, this);
    }
  }
  getViewportTransform() { return this.canvas?.viewportTransform || [1, 0, 0, 1, 0, 0]; }
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

class Line extends Shape {
  constructor([x1, y1, x2, y2], options) {
    super({...options, type: "line", x1, y1, x2, y2,
      left: Math.min(x1, x2), top: Math.min(y1, y2),
      width: Math.abs(x2 - x1), height: Math.abs(y2 - y1)});
  }
  set(options) {
    super.set(options);
    if (["x1", "x2", "y1", "y2"].some((key) => key in options)) {
      this.left = Math.min(this.x1, this.x2);
      this.top = Math.min(this.y1, this.y2);
      this.width = Math.abs(this.x2 - this.x1);
      this.height = Math.abs(this.y2 - this.y1);
    }
  }
  clone(callback) {
    const duplicate = new Line([this.x1, this.y1, this.x2, this.y2], {...this});
    duplicate.set({left: this.left, top: this.top});
    callback(duplicate);
  }
}

function source(name) {
  return fs.readFileSync(path.join(__dirname, "../static/solomon_facilities", name), "utf8");
}

async function loadEditor(elements, translations = {}, targets = {spaces: {}, doors: {}, technical_assets: {}}, snapEnabled = false, revision = {}) {
  const fields = {};
  const field = (id) => fields[id] ||= new Field();
  field("schematic-editor").dataset = {url: "/data/", saveUrl: "/data/", revisionId: "1"};
  field("schematic-stage").clientWidth = 1036;
  field("element-label-angle").reportValidity = () => true;
  field("toggle-background").disabled = true;
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
    add(object) {
      object.canvas = this;
      this.objects.push(object);
      object.setCoords();
    }
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
    setBackgroundImage(image, done) { this.backgroundImage = image; done(); }
  }
  const fabric = {
    Canvas, Rect: Shape, Line, IText: Text, Text,
    Image: {fromURL: (url, done) => done(new Shape({url, width: 500, height: 400}))},
    Point: class { constructor(x, y) { this.x = x; this.y = y; } },
    Control: class { constructor(options) { Object.assign(this, options); } },
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
          plan: {width: 1000, height: 800}, revision, elements,
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

// The drawn top-left corner of a left/top-origin shape: its stroke centerline, rotated with the shape.
function corner(object) {
  const half = Number(object.strokeWidth || 0) / 2;
  const radians = object.angle * Math.PI / 180;
  return {
    x: object.left + half * Math.cos(radians) - half * Math.sin(radians),
    y: object.top + half * Math.sin(radians) + half * Math.cos(radians),
  };
}

function assertCorner(object, x, y) {
  const point = corner(object);
  assert.ok(Math.abs(point.x - x) < 1e-9 && Math.abs(point.y - y) < 1e-9, `corner ${point.x},${point.y} is not ${x},${y}`);
}

test("editor source visibility changes neither selection, dirty state, nor saved elements", async () => {
  const editor = await loadEditor([rectangle], {}, undefined, false, {background_url: "/source.svg"});
  const button = editor.field("toggle-background");
  const image = editor.canvas.backgroundImage;
  const object = editor.canvas.objects[0];
  editor.select(object);
  const before = await editor.save();
  const saveState = editor.field("save-state").textContent;
  assert.equal(button.disabled, false);
  assert.equal(image.visible, true);
  assert.equal(button.attributes["aria-pressed"], "true");
  button.handlers.click();
  assert.equal(image.visible, false);
  assert.equal(button.attributes["aria-pressed"], "false");
  assert.equal(button.classes.has("active"), false);
  assert.equal(editor.canvas.getActiveObject(), object);
  assert.equal(editor.field("save-state").textContent, saveState);
  assert.deepEqual(await editor.save(), before);
  button.handlers.click();
  assert.equal(image.visible, true);
  assert.equal(image.opacity, 0.7);
  assert.equal(button.attributes["aria-pressed"], "true");
  assert.equal(button.classes.has("active"), true);
});

test("editor leaves source toggle disabled without a background", async () => {
  const editor = await loadEditor([]);
  assert.equal(editor.field("toggle-background").disabled, true);
  assert.equal(editor.field("toggle-background").handlers.click, undefined);
});

test("all line tools calculate endpoint controls before and after canvas attachment", async () => {
  for (const snapEnabled of [false, true]) {
    const editor = await loadEditor([], {}, undefined, snapEnabled);
    editor.canvas.viewportTransform = [2, 0, 0, 2, 17, -11];
    for (const type of ["wall", "door", "window", "line", "dimension"]) {
      editor.buttons.add.dataset.add = type;
      editor.buttons.add.handlers.click({currentTarget: editor.buttons.add});
      const object = editor.canvas.getActiveObject();
      assert.equal(object.elementType, type);
      assert.equal(object.canvas, editor.canvas);
      assert.equal(object.width, 120);
      const detached = new Line([object.x1, object.y1, object.x2, object.y2], {});
      detached.set({left: object.left, top: object.top, strokeWidth: object.strokeWidth});
      detached.controls = object.controls;
      detached.setCoords();
      assert.equal(detached.controlPositions.p1.x, object.x1);
      assert.equal(detached.controlPositions.p2.y, object.y2);
      object.setCoords();
      assert.equal(object.controlPositions.p1.x, object.x1 * 2 + 17);
      assert.equal(object.controlPositions.p2.y, object.y2 * 2 - 11);
    }
    assert.equal(editor.canvas.getObjects().length, 5);
    assert.equal(editor.field("save-state").textContent, "Changed");
    const saved = await editor.save();
    assert.equal(saved.elements.length, 5);
  }
});

test("new wall thickness is thin, editable independently of length, and persists", async () => {
  const editor = await loadEditor([]);
  editor.buttons.add.dataset.add = "wall";
  editor.buttons.add.handlers.click({currentTarget: editor.buttons.add});
  const wall = editor.canvas.objects[0];
  assert.equal(wall.strokeWidth, 3);
  assert.equal(editor.field("element-height").value, "3.0");
  editor.field("element-height").change(1.5);
  assert.equal(wall.strokeWidth, 1.5);
  assert.equal(wall.scaleY, 1);
  assert.equal(wall.x2 - wall.x1, 120);
  editor.field("element-width").change(240);
  assert.equal(wall.x2 - wall.x1, 240);
  assert.equal(wall.strokeWidth, 1.5);
  wall.controls.p2.actionHandler({}, {target: wall}, wall.x1, wall.y1 + 100);
  assert.equal(wall.angle, 0, "Walls become vertical by moving an endpoint, not by rotating");
  assert.equal(editor.field("element-width").value, "1.5");
  editor.field("element-width").change(2);
  assert.equal(wall.strokeWidth, 2);
  assert.equal(wall.y2 - wall.y1, 100);
  const saved = await editor.save();
  const reloaded = await loadEditor(saved.elements);
  reloaded.select(reloaded.canvas.objects[0]);
  assert.equal(reloaded.field("element-width").value, "2.0");
  assert.equal(reloaded.field("element-height").value, "100.0");
  assert.equal(saved.elements[0].style.stroke_width, 2);
  assert.equal(saved.elements[0].style.angle, 0);
  assert.equal(saved.elements[0].style.scale_y, 1);
});

test("legacy rotated and scaled lines are baked into the same rendered endpoints", async () => {
  const editor = await loadEditor([{
    element_type: "door", label: "A",
    geometry: {type: "line", x1: 0, x2: 120, y1: 0, y2: 1e-14},
    style: {scale_x: 1 / 6, scale_y: 9014775342729034, stroke_width: 3,
      position_x: 125, position_y: 370, angle: 90},
  }]);
  const door = editor.canvas.objects[0];
  editor.select(door);
  assert.deepEqual([door.x1, door.y1, door.x2, door.y2], [123.5, 371.5, 123.5, 391.5]);
  assert.equal(door.angle, 0);
  assert.equal(door.scaleX, 1);
  assert.equal(door.scaleY, 1);
  assert.equal(door.left, 122);
  assert.equal(door.top, 370);
  assert.equal(editor.field("element-x").value, "123.5");
  assert.equal(editor.field("element-width").value, "3.0");
  assert.equal(editor.field("element-height").value, "20.0");
  assert.notEqual(editor.field("save-state").textContent, "Changed");
  const saved = await editor.save();
  assert.deepEqual(saved.elements[0].geometry, {type: "line", x1: 123.5, y1: 371.5, x2: 123.5, y2: 391.5});
  assert.equal(saved.elements[0].style.position_x, 122);
  assert.equal(saved.elements[0].style.position_y, 370);
  assert.equal(saved.elements[0].style.angle, 0);
  assert.equal(saved.elements[0].style.scale_y, 1);
});

test("line endpoints survive modification, save, duplicate, and reload", async () => {
  const editor = await loadEditor([{
    element_type: "door", label: "B",
    geometry: {type: "line", x1: -60, x2: 60, y1: 0, y2: 0},
    style: {scale_x: 1 / 6, scale_y: 1, stroke_width: 3,
      position_x: 160, position_y: 370, angle: 90},
  }]);
  const door = editor.canvas.objects[0];
  const endpoints = (line) => [line.x1, line.y1, line.x2, line.y2];
  editor.select(door);
  assert.deepEqual(endpoints(door), [158.5, 371.5, 158.5, 391.5]);
  editor.canvas.handlers["object:modified"]({target: door});
  assert.deepEqual(endpoints(door), [158.5, 371.5, 158.5, 391.5]);
  editor.field("duplicate-element").handlers.click();
  const duplicate = editor.canvas.objects[1];
  assert.deepEqual(endpoints(duplicate), [190.5, 403.5, 190.5, 423.5]);
  const saved = await editor.save();
  assert.equal(saved.elements[0].geometry.x1, 158.5);
  assert.equal(saved.elements[1].geometry.y1, 403.5);
  const reloaded = await loadEditor(saved.elements);
  assert.deepEqual(endpoints(reloaded.canvas.objects[0]), [158.5, 371.5, 158.5, 391.5]);
  assert.deepEqual(endpoints(reloaded.canvas.objects[1]), [190.5, 403.5, 190.5, 423.5]);
});

test("line endpoints drag, snap to other elements before the grid, and lock with Shift", async () => {
  const editor = await loadEditor([
    {element_type: "wall", geometry: {type: "line", x1: 100, y1: 100, x2: 200, y2: 100}, style: {stroke_width: 3, position_x: 98.5, position_y: 98.5}},
    {element_type: "space", geometry: {type: "rect", x: 249, y: 149, width: 50, height: 50}, style: {stroke_width: 2}},
  ], {}, undefined, true);
  const wall = editor.canvas.objects[0];
  const drag = (x, y, shiftKey = false) => wall.controls.p2.actionHandler({shiftKey}, {target: wall}, x, y);
  editor.select(wall);
  assert.equal(drag(247.5, 152.5), true);
  assert.deepEqual([wall.x2, wall.y2], [250, 150], "Room corner wins over the grid");
  assert.equal(wall.angle, 0);
  assert.equal(wall.left, 98.5);
  drag(222.4, 131);
  assert.deepEqual([wall.x2, wall.y2], [220, 130], "Free endpoints snap to the grid");
  drag(222.4, 107, true);
  assert.deepEqual([wall.x2, wall.y2], [220, 100], "Shift keeps the wall horizontal");
  assert.equal(editor.field("element-width").value, "120.0");
  assert.equal(editor.field("element-height").value, "3.0");
  editor.field("toggle-snap-grid").handlers.click();
  drag(222.4, 131);
  assert.deepEqual([wall.x2, wall.y2], [222.4, 131]);
  wall.locked = true;
  assert.equal(drag(0, 0), false);
  assert.deepEqual([wall.x2, wall.y2], [222.4, 131]);
});

test("moving a line snaps an endpoint to a nearby wall endpoint", async () => {
  const editor = await loadEditor([
    {element_type: "wall", geometry: {type: "line", x1: 100, y1: 100, x2: 200, y2: 100}, style: {stroke_width: 3, position_x: 98.5, position_y: 98.5}},
    {element_type: "wall", geometry: {type: "line", x1: 202, y1: 103, x2: 202, y2: 203}, style: {stroke_width: 3, position_x: 200.5, position_y: 101.5}},
  ], {}, undefined, true);
  const vertical = editor.canvas.objects[1];
  editor.select(vertical);
  editor.canvas.handlers["object:moving"]({target: vertical});
  editor.canvas.handlers["object:modified"]({target: vertical});
  assert.deepEqual([vertical.x1, vertical.y1, vertical.x2, vertical.y2], [200, 100, 200, 200]);
});

test("align to grid joins legacy walls and rooms on shared grid points", async () => {
  const editor = await loadEditor([
    {element_type: "wall", geometry: {type: "line", x1: 0, y1: 0, x2: 100, y2: 0}, style: {stroke_width: 2, position_x: 480, position_y: 320}},
    {element_type: "wall", geometry: {type: "line", x1: 0, y1: 0, x2: 100, y2: 0}, style: {stroke_width: 2, position_x: 481, position_y: 320, angle: 90}},
    {element_type: "space", geometry: {type: "rect", x: 480, y: 320, width: 100.4, height: 59.8}, style: {stroke_width: 2}},
    {element_type: "space", locked: true, geometry: {type: "rect", x: 13, y: 13, width: 10, height: 10}, style: {stroke_width: 2}},
    textElement,
  ]);
  const [horizontal, vertical, room, locked, text] = editor.canvas.objects;
  assert.deepEqual([horizontal.x1, horizontal.y1], [481, 321]);
  assert.deepEqual([vertical.x1, vertical.y1], [480, 321], "Rotated legacy walls render 2 units off");
  editor.field("align-grid").handlers.click();
  assert.deepEqual([horizontal.x1, horizontal.y1, horizontal.x2, horizontal.y2], [480, 320, 580, 320]);
  assert.deepEqual([vertical.x1, vertical.y1, vertical.x2, vertical.y2], [480, 320, 480, 420]);
  assert.equal(room.left + room.strokeWidth / 2, 480);
  assert.equal(room.top + room.strokeWidth / 2, 320);
  assert.equal(room.width * room.scaleX, 100);
  assert.equal(room.height * room.scaleY, 60);
  assert.equal(locked.left, 13);
  assert.equal(text.left, 200);
  assert.equal(editor.field("save-state").textContent, "Changed");
});

test("vertical line Width changes stroke thickness and Height changes length", async () => {
  const editor = await loadEditor([{
    element_type: "wall", geometry: {type: "line", x1: 10, x2: 10, y1: 20, y2: 120},
    style: {stroke_width: 7, scale_x: 1000},
  }]);
  const wall = editor.canvas.objects[0];
  editor.select(wall);
  editor.field("element-width").change(2);
  editor.field("element-height").change(200);
  assert.equal(wall.strokeWidth, 2);
  assert.equal(wall.scaleX, 1);
  assert.equal(wall.height * wall.scaleY, 200);
});

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
  assertCorner(object, 25, 45);
  assert.equal(editor.field("element-x").value, "25.0");
  assert.equal(editor.field("element-y").value, "45.0");
  button.handlers.click();
  assert.equal(button.attributes["aria-pressed"], "false");
  assert.ok(!button.classes.has("active"));
});

test("grid toggle snaps the drawn corner to 5 plan units and saves positions without changing geometry", async () => {
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
  for (const [x, y, expectedX, expectedY] of [[31, 49, 30, 50], [32.4, 52.6, 35, 55], [-31, -49, -30, -50], [40, 60, 40, 60]]) {
    move(x, y);
    assertCorner(object, expectedX, expectedY);
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
  assert.equal(saved.elements[0].style.position_x, object.left);
  assert.equal(saved.elements[0].style.position_y, object.top);
  assert.equal(saved.elements.length, 2, "The grid is not a saved object");
  const reloaded = await loadEditor(saved.elements);
  assertCorner(reloaded.canvas.objects[0], 40, 60);
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
  assert.ok(Math.abs(corner(object).y - 50) < 1e-9);
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
  assertCorner(object, 30, 50);
  editor.field("element-x").change(33);
  assert.ok(Math.abs(corner(object).x - 33) < 1e-9, "Inspector input stays exact");
});

test("new and duplicated objects snap only when enabled", async () => {
  const editor = await loadEditor([rectangle]);
  editor.select(editor.canvas.objects[0]);
  editor.field("duplicate-element").handlers.click();
  assert.equal(editor.canvas.objects[1].left, 52);
  editor.field("toggle-snap-grid").handlers.click();
  editor.select(editor.canvas.objects[0]);
  editor.field("duplicate-element").handlers.click();
  assertCorner(editor.canvas.objects[2], 50, 75);
  editor.buttons.add.handlers.click({currentTarget: editor.buttons.add});
  assertCorner(editor.canvas.active, 430, 350);
  editor.buttons.add.dataset.add = "wall";
  editor.buttons.add.handlers.click({currentTarget: editor.buttons.add});
  const wall = editor.canvas.active;
  assert.deepEqual([wall.x1 % 5, wall.y1 % 5, wall.x2 % 5, wall.y2 % 5], [0, 0, 0, 0]);
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
