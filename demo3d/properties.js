/** Demo map metadata; street boundaries do not change the shared save contract. */
export const STREET_BLOCKS = [
    { id: 'north', title: '银杏街区', tileIds: [1, 2, 3] },
    { id: 'east', title: '风铃街区', tileIds: [5, 6, 7] },
    { id: 'south', title: '蜜糖街区', tileIds: [9, 10, 11] },
    { id: 'west', title: '月桂街区', tileIds: [13, 14] }
];
export function propertyStage(tile) {
    return ['空地', '住宅', '高级住宅'][tile.level ?? 0] ?? '空地';
}
export function streetForTile(tileId) {
    return STREET_BLOCKS.find(block => block.tileIds.includes(tileId));
}
/** Only built, consecutive lots within an explicit street can share a frontage. */
export function rowHouses(game) {
    const rows = [];
    for (const block of STREET_BLOCKS) {
        let run = [];
        let owner = null;
        const flush = () => {
            if (run.length > 1 && owner !== null)
                rows.push({ blockId: block.id, ownerId: owner, tileIds: run });
            run = [];
        };
        for (const id of block.tileIds) {
            const tile = game.tiles[id];
            const nextOwner = tile?.kind === 'property' && (tile.level ?? 0) > 0 ? tile.ownerId : null;
            if (nextOwner === null || nextOwner !== owner)
                flush();
            owner = nextOwner;
            if (owner !== null)
                run.push(id);
        }
        flush();
    }
    return rows;
}
