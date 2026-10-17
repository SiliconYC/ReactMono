export type WorldPoint = Readonly<{
    x: number;
    z: number;
}>;
export declare const TILE_ANCHORS: readonly WorldPoint[];
export declare const LOT_ANCHORS: readonly WorldPoint[];
export declare function positionForTile(tileId: number): WorldPoint;
