import {
  INTERNAL_TEST_MAP,
  applyAction,
  createGame,
  type ActionResult,
  type GameAction,
  type GameConfig,
  type GameEvent,
  type GameState,
  type RejectReason,
  type TileConfig
} from '../core/game.js';
import { routeSteps } from './route.js';

const TILE_NAMES = [
  '晨曦车站', '银杏小路', '甜橙街', '河畔公园',
  '红砖巷', '钟楼广场', '风铃街', '云朵花园',
  '晴湾码头', '蜜糖路', '书店街', '星光露台',
  '松果公园', '琥珀大道', '月桂巷', '归家广场'
] as const;

const DEMO_TILES: readonly TileConfig[] = TILE_NAMES.map((title, id): TileConfig => {
  if (id === 0) return { id, kind: 'start', title };
  if (id % 4 === 0 || id === 15) return { id, kind: 'neutral', title };
  return {
    id,
    kind: 'property',
    title,
    price: 100 + id * 12,
    rent: 18 + id * 3
  };
});

export const DEMO_CONFIG: GameConfig = {
  map: INTERNAL_TEST_MAP,
  players: [
    { id: 'p1', name: '桃桃', kind: 'human' },
    { id: 'p2', name: '阿团', kind: 'human' }
  ],
  tiles: DEMO_TILES,
  initialCash: 1200,
  maxRounds: 12,
  eventRules: { tileIds: [], bonus: 0, fee: 0 },
  cardRules: { tileIds: [], rewardCash: 80, moveBonus: 2, maxHand: 3 }
};

export type AcceptedDemoCommand = {
  readonly ok: true;
  readonly before: GameState;
  readonly after: GameState;
  readonly events: readonly GameEvent[];
  readonly dieValue: number | null;
  readonly route: readonly number[];
};

export type RejectedDemoCommand = {
  readonly ok: false;
  readonly before: GameState;
  readonly after: GameState;
  readonly events: readonly [];
  readonly dieValue: null;
  readonly route: readonly [];
  readonly reason: RejectReason;
};

export type DemoCommandResult = AcceptedDemoCommand | RejectedDemoCommand;

export function createDemoGame(seed: number): GameState {
  const setup = createGame(seed, DEMO_CONFIG);
  const started = applyAction(setup, { type: 'start_game', actorId: setup.players[0].id });
  if (!started.ok) throw new Error('3D 演示对局启动失败');
  return started.state;
}

function dieValueOf(result: ActionResult): number | null {
  if (!result.ok) return null;
  const value = result.events.find(event => event.type === 'die_rolled')?.details?.value;
  return typeof value === 'number' ? value : null;
}

export function dispatchDemoAction(state: GameState, action: GameAction): DemoCommandResult {
  const before = state;
  const actor = before.players[before.currentPlayerIndex];
  const result = applyAction(before, action);
  if (!result.ok) {
    return {
      ok: false,
      before,
      after: result.state,
      events: [],
      dieValue: null,
      route: [],
      reason: result.reason
    };
  }

  const dieValue = dieValueOf(result);
  const bonusEvent = result.events.find(event => event.type === 'die_rolled');
  const bonus = typeof bonusEvent?.details?.bonus === 'number' ? bonusEvent.details.bonus : 0;
  const route = dieValue === null || actor === undefined
    ? []
    : routeSteps(before.map.route, actor.position, dieValue + bonus);

  return {
    ok: true,
    before,
    after: result.state,
    events: result.events,
    dieValue,
    route
  };
}

