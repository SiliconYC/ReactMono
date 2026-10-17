export const TILE_ANCHORS = [
    { x: -4, z: -4 }, { x: -2, z: -4 }, { x: 0, z: -4 }, { x: 2, z: -4 }, { x: 4, z: -4 },
    { x: 4, z: -2 }, { x: 4, z: 0 }, { x: 4, z: 2 }, { x: 4, z: 4 },
    { x: 2, z: 4 }, { x: 0, z: 4 }, { x: -2, z: 4 }, { x: -4, z: 4 },
    { x: -4, z: 2 }, { x: -4, z: 0 }, { x: -4, z: -2 }
];
const LOT_OFFSET = 1.35;
export const LOT_ANCHORS = TILE_ANCHORS.map(point => {
    // Straight street frontages keep adjacent homes aligned for terraced buildings.
    return {
        x: point.x + (Math.abs(point.x) === 4 ? Math.sign(point.x) * LOT_OFFSET : 0),
        z: point.z + (Math.abs(point.z) === 4 ? Math.sign(point.z) * LOT_OFFSET : 0)
    };
});
export function positionForTile(tileId) {
    const point = TILE_ANCHORS[tileId];
    if (point === undefined)
        throw new Error(`3D 场景不存在格子 ${tileId}`);
    return point;
}
