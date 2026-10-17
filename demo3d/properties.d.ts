import type { GameState, Tile } from '../core/game.js';
/** Demo map metadata; street boundaries do not change the shared save contract. */
export declare const STREET_BLOCKS: readonly [{
    readonly id: "north";
    readonly title: "银杏街区";
    readonly tileIds: readonly [1, 2, 3];
}, {
    readonly id: "east";
    readonly title: "风铃街区";
    readonly tileIds: readonly [5, 6, 7];
}, {
    readonly id: "south";
    readonly title: "蜜糖街区";
    readonly tileIds: readonly [9, 10, 11];
}, {
    readonly id: "west";
    readonly title: "月桂街区";
    readonly tileIds: readonly [13, 14];
}];
export declare function propertyStage(tile: Tile): string;
export declare function streetForTile(tileId: number): {
    readonly id: "north";
    readonly title: "银杏街区";
    readonly tileIds: readonly [1, 2, 3];
} | {
    readonly id: "east";
    readonly title: "风铃街区";
    readonly tileIds: readonly [5, 6, 7];
} | {
    readonly id: "south";
    readonly title: "蜜糖街区";
    readonly tileIds: readonly [9, 10, 11];
} | {
    readonly id: "west";
    readonly title: "月桂街区";
    readonly tileIds: readonly [13, 14];
} | undefined;
export type RowHouse = Readonly<{
    blockId: string;
    ownerId: string;
    tileIds: readonly number[];
}>;
/** Only built, consecutive lots within an explicit street can share a frontage. */
export declare function rowHouses(game: GameState): readonly RowHouse[];
