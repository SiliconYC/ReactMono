export type WorldPoint = Readonly<{ x: number; z: number }>;

export const TILE_ANCHORS: readonly WorldPoint[] = [
  { x: -4, z: -4 }, { x: -2, z: -4 }, { x: 0, z: -4 }, { x: 2, z: -4 }, { x: 4, z: -4 },
  { x: 4, z: -2 }, { x: 4, z: 0 }, { x: 4, z: 2 }, { x: 4, z: 4 },
  { x: 2, z: 4 }, { x: 0, z: 4 }, { x: -2, z: 4 }, { x: -4, z: 4 },
  { x: -4, z: 2 }, { x: -4, z: 0 }, { x: -4, z: -2 }
];

const LOT_OFFSET = 1.35;

export const LOT_ANCHORS: readonly WorldPoint[] = TILE_ANCHORS.map(point => {
  const length = Math.hypot(point.x, point.z);
  return {
    x: point.x + (point.x / length) * LOT_OFFSET,
    z: point.z + (point.z / length) * LOT_OFFSET
  };
});

export function positionForTile(tileId: number): WorldPoint {
  const point = TILE_ANCHORS[tileId];
  if (point === undefined) throw new Error(`3D 场景不存在格子 ${tileId}`);
  return point;
}

