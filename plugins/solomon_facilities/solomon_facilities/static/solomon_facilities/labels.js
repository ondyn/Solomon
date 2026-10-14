(function () {
  "use strict";

  function attach(object, label, visible = true) {
    object.elementLabel = label || "";
    object.labelVisible = visible;
    // Labels can extend beyond narrow shapes, so do not clip them to an object cache.
    object.objectCaching = false;
    const isText = object.type === "i-text" || object.type === "text";
    const render = object._render;
    const toSvg = object._toSVG;
    const caption = new fabric.Text("", {
      originX: "center",
      originY: "center",
      fill: "#27343a",
      backgroundColor: "rgba(255, 255, 255, 0.85)",
      fontSize: 18,
      fontFamily: "Avenir Next, Trebuchet MS, sans-serif",
      textAlign: "center",
    });

    function visibleCaption() {
      if (isText || !object.labelVisible || !object.elementLabel) return null;
      caption.set({text: object.elementLabel});
      return caption;
    }

    // Captions are drawn in the object's scaled space; undo the scale so text is never stretched.
    function inverseScale(target) {
      return [1 / (Number(target.scaleX) || 1), 1 / (Number(target.scaleY) || 1)];
    }

    object._render = function (context) {
      if (isText && !this.labelVisible) return;
      render.call(this, context);
      const label = visibleCaption();
      if (!label) return;
      const [scaleX, scaleY] = inverseScale(this);
      context.save();
      context.scale(scaleX, scaleY);
      label.render(context);
      context.restore();
    };

    object._toSVG = function () {
      if (!this.visible || (isText && !this.labelVisible)) return [];
      const markup = toSvg.call(this);
      const label = visibleCaption();
      if (label) {
        const [scaleX, scaleY] = inverseScale(this);
        markup.push(`<g transform="scale(${scaleX} ${scaleY})">\n`, label.toSVG(), "</g>\n");
      }
      return markup;
    };
  }

  // Text elements resize through their font size so glyphs keep their proportions.
  function normalizeTextScale(object) {
    if (object.type !== "i-text" && object.type !== "text") return false;
    const scaleX = Number(object.scaleX) || 1;
    const scaleY = Number(object.scaleY) || 1;
    if (scaleX === 1 && scaleY === 1) return false;
    const fontSize = Math.max(1, Number(object.fontSize || 18) * Math.abs(scaleY));
    object.set({fontSize: Math.round(fontSize * 10) / 10, scaleX: 1, scaleY: 1});
    object.setCoords();
    return true;
  }

  const SEE_THROUGH_OPACITY = 0.4;
  const SEE_THROUGH_KEY = "solomon-plan-see-through";

  function isTextObject(object) {
    return object.type === "i-text" || object.type === "text";
  }

  function displayOpacity(object, seeThrough) {
    const opacity = object.itemOpacity === undefined ? 1 : Number(object.itemOpacity);
    if (!seeThrough || isTextObject(object)) return opacity;
    return Math.min(opacity, SEE_THROUGH_OPACITY);
  }

  function loadSeeThrough() {
    try {
      return window.localStorage.getItem(SEE_THROUGH_KEY) === "1";
    } catch (error) {
      return false;
    }
  }

  function storeSeeThrough(enabled) {
    try {
      window.localStorage.setItem(SEE_THROUGH_KEY, enabled ? "1" : "0");
    } catch (error) {
      // Storage may be unavailable (private mode); the toggle still works for this page.
    }
  }

  window.SolomonPlanLabels = {
    attach,
    normalizeTextScale,
    displayOpacity,
    loadSeeThrough,
    storeSeeThrough,
  };
})();
