const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

class Element {
  constructor() {
    this.childNodes = [];
    this.textContent = "";
    this.dataset = {};
    this.classList = {add() {}, remove() {}, toggle() {}};
  }

  setAttribute() {}

  append(...nodes) {
    this.childNodes.push(...nodes);
  }

  appendChild(node) {
    this.append(node);
  }

  replaceChildren(...nodes) {
    this.childNodes = nodes;
  }

  cloneNode() {
    const clone = new Element();
    clone.textContent = this.textContent;
    clone.childNodes = this.childNodes.map((node) => node.cloneNode(true));
    return clone;
  }

  addEventListener() {}
}

async function loadViewer(highlight = "", translations = {}, planElements) {
  const inspector = new Element();
  const defaultHeading = new Element();
  defaultHeading.textContent = "Floor plan";
  inspector.append(defaultHeading);
  const app = new Element();
  app.dataset = {url: "/plan-data/", highlight};
  const elements = {
    "schematic-app": app,
    "schematic-inspector": inspector,
    "schematic-stage": {clientWidth: 1036},
    "schematic-loading": new Element(),
  };
  let canvas;

  class Canvas {
    constructor() {
      canvas = this;
      this.objects = [];
      this.handlers = {};
    }

    add(object) { this.objects.push(object); }
    on(name, handler) { this.handlers[name] = handler; }
    setDimensions() {}
    setViewportTransform() {}
    requestRenderAll() {}
  }

  class Shape {
    constructor(options) { Object.assign(this, options); }
    set(options) { Object.assign(this, options); }
  }

  const planData = {
    plan: {width: 1000, height: 800},
    revision: {},
    targets: {
      spaces: {
        "1": {url: "/spaces/1/", label: "Linked space", kind_label: "Room", area_m2: 12},
        "2": {url: "/spaces/2/", label: "Second space", kind_label: "Cellar"},
      },
    },
    elements: planElements || [
      {element_type: "space", space_id: 1, geometry: {type: "rect"}, style: {}},
      {element_type: "space", geometry: {type: "rect"}, style: {}},
      {element_type: "space", space_id: 2, geometry: {type: "rect"}, style: {}},
    ],
  };
  const source = fs.readFileSync(
    path.join(__dirname, "../static/solomon_facilities/viewer.js"), "utf8"
  );
  class Text extends Shape {
    constructor(text, options) {
      super({...options, text, type: "text", scaleX: 1, scaleY: 1});
    }
    setCoords() {}
  }
  const fabric = {Canvas, Rect: Shape, Shadow: Shape, Text};
  const labelsWindow = {};
  vm.runInNewContext(
    fs.readFileSync(path.join(__dirname, "../static/solomon_facilities/labels.js"), "utf8"),
    {window: labelsWindow, fabric}
  );
  vm.runInNewContext(source, {
    document: {
      getElementById: (id) => elements[id] || new Element(),
      createElement: () => new Element(),
      querySelectorAll: () => [],
    },
    window: {fabric, addEventListener() {}},
    fabric,
    SolomonPlanLabels: labelsWindow.SolomonPlanLabels,
    gettext: (message) => translations[message] || message,
    fetch: async () => ({ok: true, json: async () => planData}),
  });
  await new Promise((resolve) => setImmediate(resolve));
  assert.ok(canvas, elements["schematic-loading"].textContent);
  assert.ok(canvas.handlers["mouse:down"], "Viewer initialized successfully");
  return {canvas, inspector};
}

function heading(inspector) {
  return inspector.childNodes[0].childNodes[0].textContent;
}

test("unlinked selection clears details, preserves focus, and allows linked reselection", async () => {
  const {canvas, inspector} = await loadViewer();
  const [linked, unlinked, second] = canvas.objects;
  const click = (target) => canvas.handlers["mouse:down"]({target});

  click(linked);
  assert.equal(heading(inspector), "Linked space");
  assert.ok(inspector.childNodes[1].childNodes.length > 0);

  click(unlinked);
  assert.equal(inspector.childNodes.length, 0);
  assert.equal(unlinked.stroke, "#efb419");
  assert.equal(linked.stroke, linked.viewerBaseStyle.stroke);

  click(unlinked);
  assert.equal(inspector.childNodes.length, 0);
  assert.equal(unlinked.stroke, "#efb419");

  click(second);
  assert.equal(heading(inspector), "Second space");
  assert.equal(unlinked.stroke, unlinked.viewerBaseStyle.stroke);

  click(unlinked);
  click(null);
  assert.equal(inspector.childNodes.length, 1);
  assert.equal(inspector.childNodes[0].textContent, "Floor plan");
  assert.equal(unlinked.stroke, unlinked.viewerBaseStyle.stroke);
});

test("unlinked selection clears details from an initially highlighted space", async () => {
  const {canvas, inspector} = await loadViewer("1");
  assert.equal(heading(inspector), "Linked space");
  canvas.handlers["mouse:down"]({target: canvas.objects[1]});
  assert.equal(inspector.childNodes.length, 0);
  assert.equal(canvas.objects[1].stroke, "#efb419");
});

test("viewer uses translated inspector labels without changing record data", async () => {
  const {canvas, inspector} = await loadViewer("", {Type: "Typ", Area: "Plocha"});
  canvas.handlers["mouse:down"]({target: canvas.objects[0]});
  assert.equal(heading(inspector), "Linked space");
  assert.deepEqual(
    inspector.childNodes[1].childNodes.map((node) => node.textContent),
    ["Typ", "Room", "Plocha", "12 m²"]
  );
});

test("viewer loads saved caption and standalone text styling with legacy defaults", async () => {
  const {canvas} = await loadViewer("", {}, [
    {element_type: "space", label: "Room", geometry: {type: "rect"}, style: {font_size: 36, label_angle: 270, angle: 25}},
    {element_type: "text", geometry: {type: "text", text: "Note"}, style: {font_size: 48, angle: 90}},
    {element_type: "space", label: "Legacy", geometry: {type: "rect"}, style: {}},
  ]);
  assert.equal(canvas.objects[0].labelFontSize, 36);
  assert.equal(canvas.objects[0].labelAngle, 270);
  assert.equal(canvas.objects[0].angle, 25);
  assert.equal(canvas.objects[1].fontSize, 48);
  assert.equal(canvas.objects[1].angle, 90);
  assert.equal(canvas.objects[2].labelFontSize, 18);
  assert.equal(canvas.objects[2].labelAngle, 0);
});

function loadLabels() {
  const sandbox = {window: {}, fabric: {}};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../static/solomon_facilities/labels.js"), "utf8"), sandbox);
  return sandbox.window.SolomonPlanLabels;
}

test("text scaling is baked into font size instead of stretching", () => {
  const labels = loadLabels();
  const text = {type: "i-text", fontSize: 18, scaleX: 3, scaleY: 2, set(values) { Object.assign(this, values); }, setCoords() {}};
  assert.equal(labels.normalizeTextScale(text), true);
  assert.equal(text.fontSize, 36);
  assert.equal(text.scaleX, 1);
  assert.equal(text.scaleY, 1);
  assert.equal(labels.normalizeTextScale({type: "rect", scaleX: 2, scaleY: 2}), false);
});

test("see-through mode caps shape opacity but keeps per-item opacity and text", () => {
  const labels = loadLabels();
  assert.equal(labels.displayOpacity({type: "rect", itemOpacity: 1}, false), 1);
  assert.equal(labels.displayOpacity({type: "rect", itemOpacity: 0.62}, false), 0.62);
  assert.ok(labels.displayOpacity({type: "rect", itemOpacity: 1}, true) < 1);
  assert.equal(labels.displayOpacity({type: "text", itemOpacity: 1}, true), 1);
});
