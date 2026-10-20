import {
  applyAction,
  createGame,
  type ActionResult,
  type GameAction,
  type GameConfig,
  type GameEvent,
  type GameState,
  type RejectReason
} from '../core/game.js';
import { levelConfig } from '../core/level-data.js';
import { routeSteps } from './route.js';

export const DEMO_CONFIG: GameConfig = {
  ...levelConfig('internal-square-16'),
  players: [
    { id: 'p1', name: '桃桃', kind: 'human' },
    { id: 'p2', name: '阿团', kind: 'human' }
  ],
  bankEnabled: true,
  loanEnabled: true,
  marketEnabled: true,
  propertyVisitOnly: true,
  stockAccount: 'bank'
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

export function createDemoGame(seed: number, maxRounds: number = DEMO_CONFIG.maxRounds): GameState {
  const setup = createGame(seed, { ...DEMO_CONFIG, maxRounds });
  const funded = { ...setup, players: setup.players.map(player => ({ ...player, cash: 1200, bankBalance: 600 })) };
  const started = applyAction(funded, { type: 'start_game', actorId: setup.players[0].id });
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


/** Share a reproducible real game without embedding snapshots or synthetic outcomes. */
export function demoSeedFromSearch(search: string): number {
  const raw = new URLSearchParams(search).get('seed');
  if (raw === null || !/^\d{1,10}$/.test(raw)) return 20261017;
  const seed = Number(raw);
  return Number.isSafeInteger(seed) && seed <= 0xffffffff ? seed : 20261017;
}

/** Optional normal game length, kept bounded for shareable demo sessions. */
export function demoRoundsFromSearch(search: string): number {
  const raw = new URLSearchParams(search).get('rounds');
  if (raw === null || !/^\d{1,2}$/.test(raw)) return 12;
  const rounds = Number(raw);
  return rounds >= 1 && rounds <= 60 ? rounds : 12;
}
