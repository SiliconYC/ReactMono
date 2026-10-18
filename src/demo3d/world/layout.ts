export type WorldPoint = Readonly<{ x: number; z: number }>;

/** Shared scene heights keep board pieces grounded on the miniature terrain. */
export const GROUND_TOP = -0.29;
export const ROAD_TILE_THICKNESS = 0.06;
export const ROAD_TILE_TOP = GROUND_TOP + ROAD_TILE_THICKNESS;
export const ROAD_TILE_CENTER_Y = GROUND_TOP + ROAD_TILE_THICKNESS / 2;
export const ROAD_CONNECTOR_THICKNESS = 0.04;
export const ROAD_CONNECTOR_CENTER_Y = GROUND_TOP + ROAD_CONNECTOR_THICKNESS / 2;
export const ACTOR_ANCHOR_Y = ROAD_TILE_TOP - 0.1;
export const ISLAND_BOTTOM = -1.18;

export const TILE_ANCHORS: readonly WorldPoint[] = [
  { x: -4, z: -4 }, { x: -2, z: -4 }, { x: 0, z: -4 }, { x: 2, z: -4 }, { x: 4, z: -4 },
  { x: 4, z: -2 }, { x: 4, z: 0 }, { x: 4, z: 2 }, { x: 4, z: 4 },
  { x: 2, z: 4 }, { x: 0, z: 4 }, { x: -2, z: 4 }, { x: -4, z: 4 },
  { x: -4, z: 2 }, { x: -4, z: 0 }, { x: -4, z: -2 }
];

const LOT_OFFSET = 1.35;

export const LOT_ANCHORS: readonly WorldPoint[] = TILE_ANCHORS.map(point => {
  // Straight street frontages keep adjacent homes aligned for terraced buildings.
  return {
    x: point.x + (Math.abs(point.x) === 4 ? Math.sign(point.x) * LOT_OFFSET : 0),
    z: point.z + (Math.abs(point.z) === 4 ? Math.sign(point.z) * LOT_OFFSET : 0)
  };
});

export function positionForTile(tileId: number): WorldPoint {
  const point = TILE_ANCHORS[tileId];
  if (point === undefined) throw new Error(`3D 场景不存在格子 ${tileId}`);
  return point;
}

