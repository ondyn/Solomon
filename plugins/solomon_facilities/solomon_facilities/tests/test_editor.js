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
    this.classList = {add() {}, remove() {}, toggle() {}};
  }
  addEventListener(name, handler) { this.handlers[name] = handler; }
  replaceChildren() { this.childNodes = []; }
  appendChild(node) { this.childNodes.push(node); }
  setAttribute() {}
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

async function loadEditor(elements, translations = {}, targets = {spaces: {}, doors: {}, technical_assets: {}}) {
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
    setViewportTransform(transform) { this.viewportTransform = transform; }
    requestRenderAll() {}
  }
  const fabric = {Canvas, Rect: Shape, IText: Text, Text};
  const window = {fabric, addEventListener() {}};
  vm.runInNewContext(source("labels.js"), {window, fabric});
  vm.runInNewContext(source("editor.js"), {
    window, fabric, SolomonPlanLabels: window.SolomonPlanLabels,
    document: {
      getElementById: field,
      querySelectorAll: () => [],
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
  return {
    canvas, field,
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
