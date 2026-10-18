export type WorldPoint = Readonly<{
    x: number;
    z: number;
}>;
/** Shared scene heights keep board pieces grounded on the miniature terrain. */
export declare const GROUND_TOP = -0.29;
export declare const ROAD_TILE_THICKNESS = 0.06;
export declare const ROAD_TILE_TOP: number;
export declare const ROAD_TILE_CENTER_Y: number;
export declare const ROAD_CONNECTOR_THICKNESS = 0.04;
export declare const ROAD_CONNECTOR_CENTER_Y: number;
export declare const ACTOR_ANCHOR_Y: number;
export declare const ISLAND_BOTTOM = -1.18;
export declare const TILE_ANCHORS: readonly WorldPoint[];
export declare const LOT_ANCHORS: readonly WorldPoint[];
export declare function positionForTile(tileId: number): WorldPoint;
