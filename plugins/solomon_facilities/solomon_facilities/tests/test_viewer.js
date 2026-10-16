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
    this.handlers = {};
    this.attributes = {};
    this.classes = new Set();
    this.classList = {
      add: (name) => this.classes.add(name),
      remove: (name) => this.classes.delete(name),
      toggle: (name, enabled) => enabled ? this.classes.add(name) : this.classes.delete(name),
    };
  }

  setAttribute(name, value) { this.attributes[name] = value; }

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

  addEventListener(name, handler) { this.handlers[name] = handler; }
  click() {}
}

async function loadViewer(highlight = "", translations = {}, planElements, revision = {}) {
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
    "export-svg": new Element(),
    "toggle-background": new Element(),
  };
  elements["toggle-background"].disabled = true;
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
    setBackgroundImage(image, done) { this.backgroundImage = image; done(); }
    toSVG(options) {
      this.exported = {options, backgroundImage: this.backgroundImage, backgroundColor: this.backgroundColor};
      if (this.exportError) throw this.exportError;
      return "<svg/>";
    }
  }

  class Shape {
    constructor(options) { Object.assign(this, options); }
    set(options) { Object.assign(this, options); }
  }

  const planData = {
    plan: {width: 1000, height: 800},
    revision,
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
  const fabric = {
    Canvas, Rect: Shape, Shadow: Shape, Text,
    Image: {fromURL: (url, done) => done(new Shape({url, width: 500, height: 400}))},
  };
  const labelsWindow = {};
  vm.runInNewContext(
    fs.readFileSync(path.join(__dirname, "../static/solomon_facilities/labels.js"), "utf8"),
    {window: labelsWindow, fabric}
  );
  vm.runInNewContext(source, {
    Blob,
    URL: {createObjectURL: () => "blob:export", revokeObjectURL() {}},
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
  return {
    canvas, inspector, backgroundButton: elements["toggle-background"],
    exportSvg: () => elements["export-svg"].handlers.click(),
  };
}

test("source background toggles independently of vectors and stays hidden after SVG export", async () => {
  const {canvas, backgroundButton, exportSvg} = await loadViewer("", {}, undefined, {
    background_url: "/source.svg", background_rotation: 90,
  });
  const image = canvas.backgroundImage;
  const vectors = [...canvas.objects];
  assert.equal(backgroundButton.disabled, false);
  assert.equal(backgroundButton.attributes["aria-pressed"], "true");
  assert.equal(image.visible, true);
  assert.equal(image.opacity, 0.82);
  assert.equal(image.angle, 90);
  backgroundButton.handlers.click();
  assert.equal(image.visible, false);
  assert.equal(backgroundButton.attributes["aria-pressed"], "false");
  assert.equal(backgroundButton.classes.has("active"), false);
  assert.deepEqual(canvas.objects, vectors);
  exportSvg();
  assert.equal(canvas.exported.backgroundImage, null);
  assert.equal(canvas.backgroundImage, image);
  assert.equal(image.visible, false);
  canvas.exportError = new Error("Export failed");
  assert.throws(exportSvg, /Export failed/);
  assert.equal(image.visible, false);
  backgroundButton.handlers.click();
  assert.equal(image.visible, true);
  assert.equal(image.opacity, 0.82);
  assert.equal(backgroundButton.classes.has("active"), true);
  assert.equal(backgroundButton.attributes["aria-pressed"], "true");
});

test("viewer leaves source background toggle disabled without a source", async () => {
  const {backgroundButton} = await loadViewer();
  assert.equal(backgroundButton.disabled, true);
  assert.equal(backgroundButton.handlers.click, undefined);
});

test("SVG export excludes backgrounds, uses full plan dimensions, and restores the viewer", async () => {
  const viewer = await loadViewer();
  const background = {url: "source.svg"};
  viewer.canvas.backgroundImage = background;
  viewer.canvas.backgroundColor = "#ffffff";
  viewer.exportSvg();
  assert.equal(viewer.canvas.exported.backgroundImage, null);
  assert.equal(viewer.canvas.exported.backgroundColor, "");
  assert.equal(JSON.stringify(viewer.canvas.exported.options), JSON.stringify({
    width: 1000, height: 800, viewBox: {x: 0, y: 0, width: 1000, height: 800},
  }));
  assert.equal(viewer.canvas.backgroundImage, background);
  assert.equal(viewer.canvas.backgroundColor, "#ffffff");
  viewer.canvas.exportError = new Error("Export failed");
  assert.throws(viewer.exportSvg, /Export failed/);
  assert.equal(viewer.canvas.backgroundImage, background);
  assert.equal(viewer.canvas.backgroundColor, "#ffffff");
});

test("line normalization fixes degenerate axes but preserves diagonal geometry and scales", () => {
  const labels = loadLabels();
  const line = {type: "line", x1: 0, x2: 100, y1: 0, y2: 50, scaleX: 2, scaleY: 3,
    set(values) { Object.assign(this, values); }};
  labels.normalizeLineScale(line);
  assert.equal(line.scaleX, 2);
  assert.equal(line.scaleY, 3);
  assert.equal(line.y2, 50);
});

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
