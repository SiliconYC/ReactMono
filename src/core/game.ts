/** Stable public API; the implementation remains deterministic and React-independent. */
export { SCHEMA_VERSION, UPGRADE_RULES_VERSION } from './types.js';
export type { CardKind, PlayerId, TileKind, Phase, PlayerKind, PlayerConfig, TileConfig, GameConfig, Player, Tile, GameEvent, GameState, GameAction, RejectReason, ActionResult } from './types.js';
export { DEFAULT_CARD_RULES, DEFAULT_EVENT_RULES, DEFAULT_UPGRADES, DEFAULT_CONFIG } from './config.js';
export { normalizeSeed, nextDie } from './random.js';
export { makePropertyTile, netWorth } from './property.js';
import { SCHEMA_VERSION, UPGRADE_RULES_VERSION } from './types.js';
import type { CardKind, PlayerId, Phase, PlayerConfig, TileConfig, GameConfig, Player, Tile, GameEvent, GameState, GameAction, RejectReason, ActionResult } from './types.js';
import { DEFAULT_CARD_RULES, DEFAULT_EVENT_RULES, DEFAULT_UPGRADES, DEFAULT_CONFIG, validateConfig } from './config.js';
import { normalizeSeed, nextDie } from './random.js';
import { makePropertyTile, declineProperty, upgradeProperty, buyProperty } from './property.js';
import { accept, reject } from './transitions.js';
import { rollTurn, endTurn } from './turns.js';
import { useCard } from './cards.js';
/** 新建纯数据状态。每次调用都会创建隔离的玩家、棋盘数组。 */
export function createGame(seed: number, config: GameConfig = DEFAULT_CONFIG): GameState {
  validateConfig(config);
  return {
    schemaVersion: SCHEMA_VERSION,
    upgradeRulesVersion: UPGRADE_RULES_VERSION,
    cardRules: {rewardCash:(config.cardRules??DEFAULT_CARD_RULES).rewardCash,
      moveBonus:(config.cardRules??DEFAULT_CARD_RULES).moveBonus,
      maxHand:(config.cardRules??DEFAULT_CARD_RULES).maxHand},
    pendingMoveBonus:0,
    status: 'setup',
    phase: 'setup',
    revision: 0,
    round: 1,
    currentPlayerIndex: 0,
    randomState: normalizeSeed(seed),
    maxRounds: config.maxRounds,
    players: config.players.map((p, index): Player => ({
      id: p.id, name: p.name, kind: index === 0 ? 'human' : 'computer',
      position: 0, cash: config.initialCash, bankrupt: false, cards:{reward:0,stride:0}
    })),
    tiles: config.tiles.map(t => {
      if(t.kind==='property')return makePropertyTile(t,config.upgrades??DEFAULT_UPGRADES);
      const tile:Tile={...t,ownerId:null};
      if(t.kind==='neutral'&&(config.eventRules??DEFAULT_EVENT_RULES).tileIds.includes(t.id)){
        Object.assign(tile,{eventBonus:(config.eventRules??DEFAULT_EVENT_RULES).bonus,eventFee:(config.eventRules??DEFAULT_EVENT_RULES).fee});
      }
      if(t.kind==='neutral'&&(config.cardRules??DEFAULT_CARD_RULES).tileIds.includes(t.id))Object.assign(tile,{cardStation:true});
      return tile;
    }),
    winnerId: null,
    events: []
  };
}

/** 单一命令入口：始终返回新状态或明确拒绝，不修改传入对象。 */
export function applyAction(state: GameState, action: GameAction): ActionResult {
  const actor = state.players[state.currentPlayerIndex];
  if (!actor || actor.id !== action.actorId) return reject(state,'INVALID_ACTOR');
  if (action.type === 'start_game') {
    if (state.phase !== 'setup') return reject(state,'INVALID_PHASE');
    return accept(state, [{ type: 'game_started', actorId: action.actorId }], {
      status: 'playing', phase: 'await_roll'
    });
  }
  if (state.phase === 'setup' || state.phase === 'finished') return reject(state,'INVALID_PHASE');

  switch (action.type) {
    case 'roll': return rollTurn(state,actor);
    case 'decline_property': return declineProperty(state,actor);
    case 'end_turn': return endTurn(state,actor);
    case 'use_card': return useCard(state,actor,action);
    case 'upgrade_property': return upgradeProperty(state,actor,action);
    case 'buy_property': return buyProperty(state,actor);
  }
}
