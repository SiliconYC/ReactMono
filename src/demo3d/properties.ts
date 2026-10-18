import type { GameState, Tile } from '../core/game.js';

/** Demo map metadata; street boundaries do not change the shared save contract. */
export const STREET_BLOCKS = [
  { id: 'north', title: '银杏街区', tileIds: [1, 2, 3] },
  { id: 'east', title: '风铃街区', tileIds: [5, 6, 7] },
  { id: 'south', title: '蜜糖街区', tileIds: [9, 10, 11] },
  { id: 'west', title: '月桂街区', tileIds: [13, 14] }
] as const;

export function propertyStage(tile: Tile): string {
  return ['空地', '住宅', '高级住宅'][tile.level ?? 0] ?? '空地';
}

export function streetForTile(tileId: number) {
  return STREET_BLOCKS.find(block => (block.tileIds as readonly number[]).includes(tileId));
}

export type RowHouse = Readonly<{ blockId: string; ownerId: string; tileIds: readonly number[] }>;

function sideForTile(game: GameState, tileId: number): 'north'|'east'|'south'|'west' {
  const cell = game.map.cells[tileId];
  if (cell.row === 1) return 'north';
  if (cell.column === game.map.columns) return 'east';
  if (cell.row === game.map.rows) return 'south';
  return 'west';
}

/** Built properties share a frontage only while route neighbours stay on one straight map edge. */
export function rowHouses(game: GameState): readonly RowHouse[] {
  const rows: RowHouse[] = [];
  let run: number[] = [];
  let owner: string | null = null;
  let side: ReturnType<typeof sideForTile> | null = null;
  const flush = () => {
    if (run.length > 1 && owner !== null && side !== null) rows.push({ blockId: side, ownerId: owner, tileIds: run });
    run = [];
    owner = null;
  };
  for (const id of game.map.route) {
    const tile = game.tiles[id];
    const tileSide = sideForTile(game, id);
    const nextOwner = tile?.kind === 'property' && (tile.level ?? 0) > 0 ? tile.ownerId : null;
    if (nextOwner === null || nextOwner !== owner || tileSide !== side) flush();
    if (nextOwner !== null) {
      owner = nextOwner;
      side = tileSide;
      run.push(id);
    }
  }
  flush();
  return rows;
}
