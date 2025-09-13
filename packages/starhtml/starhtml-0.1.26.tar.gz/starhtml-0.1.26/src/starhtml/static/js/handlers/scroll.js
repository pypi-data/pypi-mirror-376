import { SmoothScroll } from "./smooth-scroll.js";
import { createRAFThrottle, createTimerThrottle } from "./throttle.js";
const DEFAULT_THROTTLE = 100;
const DIRECTION_THRESHOLD = 5;
const SCROLL_ARG_NAMES = [
  "scrollX",
  "scrollY",
  "direction",
  "velocity",
  "delta",
  "visible",
  "visiblePercent",
  "progress",
  "pageProgress",
  "elementTop",
  "elementBottom",
  "isTop",
  "isBottom"
];
function calculateVisiblePercent(rect, viewportHeight) {
  if (rect.bottom < 0 || rect.top > viewportHeight) return 0;
  const visibleTop = Math.max(0, rect.top);
  const visibleBottom = Math.min(viewportHeight, rect.bottom);
  const visibleHeight = visibleBottom - visibleTop;
  return Math.round(visibleHeight / rect.height * 100);
}
function getScrollData(el, lastScrollY) {
  const currentY = window.scrollY;
  const currentX = window.scrollX;
  const delta = currentY - lastScrollY;
  const direction = Math.abs(delta) > DIRECTION_THRESHOLD ? delta > 0 ? "down" : "up" : "none";
  const velocity = Math.abs(delta);
  const rect = el.getBoundingClientRect();
  const elementTop = rect.top + window.scrollY;
  const elementBottom = elementTop + rect.height;
  const viewportHeight = window.innerHeight;
  const docHeight = document.documentElement.scrollHeight - window.innerHeight;
  const pageProgress = docHeight > 0 ? Math.round(window.scrollY / docHeight * 100) : 0;
  let elProgress = pageProgress;
  if (el.scrollHeight > el.clientHeight + 1) {
    elProgress = Math.round(el.scrollTop / (el.scrollHeight - el.clientHeight) * 100);
  }
  const visiblePercent = calculateVisiblePercent(rect, viewportHeight);
  const isInViewport = rect.top < viewportHeight && rect.bottom > 0;
  const isTop = currentY <= 0;
  const isBottom = currentY >= docHeight;
  return {
    scrollX: currentX,
    scrollY: currentY,
    direction,
    velocity,
    delta,
    visible: isInViewport,
    visiblePercent,
    progress: elProgress,
    pageProgress,
    elementTop,
    elementBottom,
    isTop,
    isBottom
  };
}
function getThrottleMs(mods) {
  const throttleValue = mods.get("throttle");
  if (throttleValue !== void 0) {
    if (throttleValue instanceof Set) {
      return Number.parseInt(String(Array.from(throttleValue)[0])) || DEFAULT_THROTTLE;
    }
    return Number.parseInt(String(throttleValue)) || DEFAULT_THROTTLE;
  }
  return DEFAULT_THROTTLE;
}
const scrollAttributePlugin = {
  type: "attribute",
  name: "onScroll",
  keyReq: "starts",
  argNames: [...SCROLL_ARG_NAMES],
  onLoad(ctx) {
    const { el, value, mods, rx, mergePatch, startBatch, endBatch } = ctx;
    if (!value?.trim()) {
      return;
    }
    const throttleMs = getThrottleMs(mods);
    let lastScrollY = window.scrollY;
    let isUpdating = false;
    let smoothScroll = null;
    if (mods.has("smooth")) {
      smoothScroll = new SmoothScroll(el, () => {
        if (!isUpdating) {
          updateScroll();
        }
      });
      smoothScroll.start();
    }
    const updateScroll = () => {
      if (isUpdating) {
        return;
      }
      isUpdating = true;
      const rawScrollData = getScrollData(el, lastScrollY);
      let scrollData = rawScrollData;
      if (smoothScroll) {
        const smoothedValues = smoothScroll.getSmoothData({
          scrollY: rawScrollData.scrollY,
          velocity: rawScrollData.velocity,
          progress: rawScrollData.progress,
          pageProgress: rawScrollData.pageProgress,
          visiblePercent: rawScrollData.visiblePercent
        });
        scrollData = {
          ...rawScrollData,
          scrollY: smoothedValues.scrollY,
          velocity: smoothedValues.velocity,
          progress: smoothedValues.progress,
          pageProgress: smoothedValues.pageProgress,
          visiblePercent: smoothedValues.visiblePercent
        };
      }
      startBatch();
      try {
        mergePatch({
          scrollX: scrollData.scrollX,
          scrollY: scrollData.scrollY,
          direction: scrollData.direction,
          velocity: scrollData.velocity,
          delta: scrollData.delta,
          visible: scrollData.visible,
          visiblePercent: scrollData.visiblePercent,
          progress: scrollData.progress,
          pageProgress: scrollData.pageProgress,
          elementTop: scrollData.elementTop,
          elementBottom: scrollData.elementBottom,
          isTop: scrollData.isTop,
          isBottom: scrollData.isBottom
        });
        rx(
          scrollData.scrollX,
          scrollData.scrollY,
          scrollData.direction,
          scrollData.velocity,
          scrollData.delta,
          scrollData.visible,
          scrollData.visiblePercent,
          scrollData.progress,
          scrollData.pageProgress,
          scrollData.elementTop,
          scrollData.elementBottom,
          scrollData.isTop,
          scrollData.isBottom
        );
      } catch (error) {
        console.error("Error executing scroll handler:", error);
      } finally {
        endBatch();
        lastScrollY = rawScrollData.scrollY;
        isUpdating = false;
      }
    };
    const throttledUpdate = throttleMs <= 16 ? createRAFThrottle(updateScroll) : createTimerThrottle(updateScroll, throttleMs);
    updateScroll();
    const handleScroll = () => {
      throttledUpdate();
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    let elementScrollCleanup = null;
    if (el.scrollHeight > el.clientHeight) {
      const handleElementScroll = () => throttledUpdate();
      el.addEventListener("scroll", handleElementScroll, { passive: true });
      elementScrollCleanup = () => el.removeEventListener("scroll", handleElementScroll);
    }
    return () => {
      window.removeEventListener("scroll", handleScroll);
      elementScrollCleanup?.();
      smoothScroll?.cleanup();
    };
  }
};
var scroll_default = scrollAttributePlugin;
export {
  scroll_default as default
};
