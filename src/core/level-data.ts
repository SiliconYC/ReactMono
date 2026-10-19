/** Exchange-format levels. No React, filesystem, random numbers or executable map recipes. */
import catalog from '../data/levels.json' with { type: 'json' };
import type { GameConfig, GameMap, TileConfig, FacilityConfig } from './types.js';

export interface LevelDefinition {
  readonly name: string;
  readonly description: string;
  readonly playable: boolean;
  readonly map: GameMap;
  readonly tiles: readonly TileConfig[];
  readonly initialCash: number;
  readonly maxRounds: number;
  readonly eventRules: NonNullable<GameConfig['eventRules']>;
  readonly cardRules: NonNullable<GameConfig['cardRules']>;
  readonly facilityConfig: FacilityConfig | null;
}
const record = (x: unknown): x is Record<string, unknown> => x !== null && typeof x === 'object' && !Array.isArray(x);
const text = (x: unknown): x is string => typeof x === 'string' && x.trim().length > 0;
const integer = (x: unknown, min: number, max = 1_000_000): x is number => typeof x === 'number' && Number.isSafeInteger(x) && x >= min && x <= max;
const keys = (x: Record<string, unknown>, required: string[], optional: string[] = []): boolean =>
  required.every(k => Object.hasOwn(x, k)) && Object.keys(x).every(k => required.includes(k) || optional.includes(k));
function invalid(where: string): never { throw new Error(`关卡数据无效：${where}`); }

/** Authored boards use a simple adjacent cyclic route; old inferred fixture boards are separate. */
export function validateLevelMap(value: unknown): asserts value is GameMap {
  if (!record(value) || !keys(value, ['id','version','columns','rows','cells','route']) ||
      !text(value.id) || !/^[a-z][a-z0-9-]*$/.test(value.id) ||
      !integer(value.version, 1) || !integer(value.columns, 1, 10000) || !integer(value.rows, 1, 10000) ||
      !Array.isArray(value.cells) || !Array.isArray(value.route) || value.cells.length < 4 || value.cells.length > 512 ||
      value.route.length !== value.cells.length || value.route[0] !== 0) invalid('地图结构');
  const cells = value.cells as unknown[];
  const seen = new Set<string>();
  for (const cell of cells) {
    if (!record(cell) || !keys(cell, ['column','row']) || !integer(cell.column, 1, value.columns) || !integer(cell.row, 1, value.rows)) invalid('地图坐标');
    const key = `${cell.column},${cell.row}`;
    if (seen.has(key)) invalid('地图坐标重复');
    seen.add(key);
  }
  const route = value.route as unknown[];
  if (new Set(route).size !== cells.length || !route.every(i => integer(i, 0, cells.length - 1))) invalid('地图路径排列');
  const map = value as unknown as GameMap;
  for (let i = 0; i < route.length; i++) {
    const a = map.cells[map.route[i]], b = map.cells[map.route[(i + 1) % route.length]];
    if (Math.abs(a.column - b.column) + Math.abs(a.row - b.row) !== 1) invalid('地图路径断开');
  }
}
function freeze<T>(value: T): T {
  if (value !== null && typeof value === 'object') {
    for (const child of Object.values(value)) freeze(child);
    Object.freeze(value);
  }
  return value;
}
/** Parse a whole catalog so duplicate IDs and stale references fail before any game starts. */
export function loadLevelCatalog(value: unknown): readonly LevelDefinition[] {
  if (!record(value) || !keys(value, ['schemaVersion','levels']) || value.schemaVersion !== 1 ||
      !Array.isArray(value.levels) || !value.levels.length) invalid('目录版本或内容');
  const ids = new Set<string>();
  for (const level of value.levels) {
    if (!record(level) || !keys(level, ['name','description','playable','map','tiles','initialCash','maxRounds','eventRules','cardRules','facilityConfig']) ||
        !text(level.name) || !text(level.description) || typeof level.playable !== 'boolean' ||
        !integer(level.initialCash, 0) || !integer(level.maxRounds, 1, 10000)) invalid('关卡说明或开局参数');
    validateLevelMap(level.map);
    if (ids.has(level.map.id) || /^custom-\d+$/.test(level.map.id)) invalid('地图标识重复或使用保留标识');
    ids.add(level.map.id);
    if (!Array.isArray(level.tiles) || level.tiles.length !== level.map.cells.length) invalid('地块数量');
    const tiles = level.tiles as unknown[];
    tiles.forEach((tile, i) => {
      if (!record(tile) || !keys(tile, ['id','kind','title'], ['price','rent']) || tile.id !== i || !text(tile.title) || tile.title.length > 100 ||
          (i === 0 ? tile.kind !== 'start' : !['property','neutral'].includes(String(tile.kind)))) invalid('地块标识或种类');
      if (tile.kind === 'property' ? !integer(tile.price, 0) || !integer(tile.rent, 0) : 'price' in tile || 'rent' in tile) invalid('地产价格或租金');
    });
    for (const [kind, fields] of [['eventRules',['bonus','fee']], ['cardRules',['rewardCash','moveBonus','maxHand']]] as const) {
      const rule = level[kind];
      if (!record(rule) || !keys(rule, ['tileIds', ...fields]) || !Array.isArray(rule.tileIds) ||
          new Set(rule.tileIds).size !== rule.tileIds.length ||
          !rule.tileIds.every(i => integer(i, 1, tiles.length - 1) && (tiles[i] as TileConfig).kind === 'neutral') ||
          !fields.every(k => integer(rule[k], kind === 'eventRules' ? 0 : 1, kind === 'eventRules' ? 1_000_000 : k === 'maxHand' ? 1_000 : 100_000))) invalid('事件或卡片站点/参数');
    }
    const eventIds = (level.eventRules as unknown as LevelDefinition['eventRules']).tileIds;
    const cardIds = (level.cardRules as unknown as LevelDefinition['cardRules']).tileIds;
    if (eventIds.some(i => cardIds.includes(i))) invalid('事件与卡片站点重叠');
    const facility = level.facilityConfig;
    if (facility !== null) {
      if (!record(facility) || !keys(facility, ['hospitalTiles','prisonTiles','shopTiles','hospitalTurns','prisonTurns','hospitalFee','prisonFee','prices','stock'])) invalid('特殊设施结构');
      const occupied = new Set<number>();
      for (const key of ['hospitalTiles','prisonTiles','shopTiles']) {
        const list = facility[key];
        if (!Array.isArray(list) || !list.length) invalid('特殊设施位置');
        for (const id of list) {
          if (!integer(id, 1, tiles.length - 1) || (tiles[id] as TileConfig).kind !== 'neutral' || occupied.has(id)) invalid('特殊设施位置');
          occupied.add(id);
        }
      }
      if (!['hospitalTurns','prisonTurns'].every(k => integer(facility[k], 1, 20)) ||
          !['hospitalFee','prisonFee'].every(k => integer(facility[k], 0))) invalid('特殊设施费用或停留回合');
      const cards = ['reward','stride','remote','roadblock','rent_free'];
      for (const key of ['prices','stock']) {
        const values = facility[key];
        if (!record(values) || !keys(values, cards) || !cards.every(k => integer(values[k], key === 'prices' ? 1 : 0, key === 'prices' ? 1_000_000 : 100))) invalid('特殊设施价格或库存');
      }
    }
  }
  // Clone first: callers can continue editing their input without mutating the registry.
  return freeze(structuredClone(value.levels)) as unknown as readonly LevelDefinition[];
}

export const LEVELS = loadLevelCatalog(catalog);
export const PLAYABLE_LEVELS = Object.freeze(LEVELS.filter(level => level.playable));
export function levelConfig(id: string): GameConfig {
  const level = LEVELS.find(level => level.map.id === id);
  if (!level) return invalid(`未知关卡 ${id}`);
  return {
    players: [{id:'p1',name:'玩家'}, {id:'p2',name:'电脑'}],
    map: level.map, tiles: level.tiles, initialCash: level.initialCash, maxRounds: level.maxRounds,
    eventRules: level.eventRules, cardRules: level.cardRules,
    ...(level.facilityConfig ? {facilityConfig:level.facilityConfig} : {})
  };
}
