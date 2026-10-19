/** Pure orthographic composition; no DOM, Three renderer or saved-game dependencies. */
export type ViewportInsets = Readonly<{
  top: number;
  right: number;
  bottom: number;
  left: number;
}>;
export function cameraFrame(
  viewport: Readonly<{ width: number; height: number }>,
  insets: ViewportInsets = { top: 0, right: 0, bottom: 0, left: 0 },
  bounds: Readonly<{ width: number; depth: number }>,
): Readonly<{
  zoom: number;
  offsetX: number;
  offsetY: number;
  projectedWidth: number;
  projectedHeight: number;
}> {
  const width = Math.max(1, viewport.width - insets.left - insets.right);
  const height = Math.max(1, viewport.height - insets.top - insets.bottom);
  const elevation = Math.atan2(12.2, Math.hypot(10.2, 10.2));
  const projectedWidth = (bounds.width + bounds.depth) / Math.SQRT2;
  // Include roofs and the die over the actor above the continuous ground.
  const projectedHeight =
    projectedWidth * Math.sin(elevation) + 3.6 * Math.cos(elevation);
  return {
    zoom: Math.min(width / projectedWidth, height / projectedHeight),
    offsetX: (insets.left - insets.right) / 2,
    offsetY: (insets.bottom - insets.top) / 2,
    projectedWidth,
    projectedHeight,
  };
}
