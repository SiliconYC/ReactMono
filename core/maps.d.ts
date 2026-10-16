/** Pure, versioned map topology and screen coordinates. Every node has one cyclic successor. */
import type { GameMap } from './types.js';
/** A map declaration may be shared but its game-state copy is isolated. */
export declare function makeRingMap(id: string, version: number, columns: number, rows: number): GameMap;
export declare const DEFAULT_MAP: GameMap;
export declare const INTERNAL_TEST_MAP: GameMap;
/** Original nautical-themed 20-tile board; playable preset supplied by config.ts. */
export declare const HARBOR_MAP: GameMap;
/** Supports tiny custom boards in legacy rules tests and old saved 2-tile fixtures. */
export declare function inferMap(count: number): GameMap;
export declare function cloneMap(map: GameMap): GameMap;
export declare function advancePosition(map: GameMap, from: number, steps: number): number;
/** Reject forged paths, unknown IDs/versions, duplicate/out-of-grid cells and stale geometry. */
export declare function validateMap(map: unknown, tileCount: number): void;
