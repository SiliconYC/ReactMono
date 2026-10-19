export type WorldPoint = Readonly<{ x: number; z: number }>;
import { INTERNAL_TEST_MAP } from '../../core/maps.js';
import type { GameMap } from '../../core/types.js';

/** Shared scene heights keep board pieces grounded on the miniature terrain. */
export const GROUND_TOP = -0.29;
export const ROAD_TILE_THICKNESS = 0.06;
export const ROAD_TILE_TOP = GROUND_TOP + ROAD_TILE_THICKNESS;
export const ROAD_TILE_CENTER_Y = GROUND_TOP + ROAD_TILE_THICKNESS / 2;
export const ROAD_CONNECTOR_THICKNESS = 0.04;
export const ROAD_CONNECTOR_CENTER_Y = GROUND_TOP + ROAD_CONNECTOR_THICKNESS / 2;
export const ACTOR_ANCHOR_Y = ROAD_TILE_TOP - 0.1;
export const ISLAND_BOTTOM = -1.18;

const LOT_OFFSET = 1.35;

export type MapAnchors = Readonly<{
  tiles: readonly WorldPoint[];
  lots: readonly WorldPoint[];
  bounds: Readonly<{ width: number; depth: number }>;
}>;
const anchorsByMap = new WeakMap<GameMap, MapAnchors>();

/** Derive world positions from rules-map cells; tile IDs and cyclic order stay untouched. */
export function anchorsForMap(map: GameMap): MapAnchors {
  const cached = anchorsByMap.get(map);
  if (cached) return cached;
  const tiles = map.cells.map(cell => ({
    x: (cell.column - (map.columns + 1) / 2) * 2,
    z: (cell.row - (map.rows + 1) / 2) * 2
  }));
  const lots = map.cells.map((cell, tileId) => {
    const road = tiles[tileId];
    const outwardX = cell.column === 1 ? -1 : cell.column === map.columns ? 1 : 0;
    const outwardZ = cell.row === 1 ? -1 : cell.row === map.rows ? 1 : 0;
    const length = Math.hypot(outwardX, outwardZ) || 1;
    return { x: road.x + outwardX / length * LOT_OFFSET, z: road.z + outwardZ / length * LOT_OFFSET };
  });
  const result = { tiles, lots, bounds: { width: map.columns * 2, depth: map.rows * 2 } };
  anchorsByMap.set(map, result);
  return result;
}

export const TILE_ANCHORS = anchorsForMap(INTERNAL_TEST_MAP).tiles;
export const LOT_ANCHORS = anchorsForMap(INTERNAL_TEST_MAP).lots;

export function positionForTile(tileId: number, map: GameMap = INTERNAL_TEST_MAP): WorldPoint {
  const point = anchorsForMap(map).tiles[tileId];
  if (point === undefined) throw new Error(`3D 场景不存在格子 ${tileId}`);
  return point;
}

export function lotForTile(tileId: number, map: GameMap = INTERNAL_TEST_MAP): WorldPoint {
  const point = anchorsForMap(map).lots[tileId];
  if (point === undefined) throw new Error(`3D 场景不存在地产 ${tileId}`);
  return point;
}

/** Face every landmark back toward the shared town center. */
export function inwardAngleForTile(tileId: number, map: GameMap = INTERNAL_TEST_MAP): number {
  const { tiles } = anchorsForMap(map);
  const point = tiles[tileId];
  if (point === undefined) throw new Error(`3D 场景不存在格子 ${tileId}`);
  if (Math.abs(point.z) >= Math.abs(point.x)) return point.z < 0 ? 0 : Math.PI;
  return point.x > 0 ? -Math.PI / 2 : Math.PI / 2;
}

