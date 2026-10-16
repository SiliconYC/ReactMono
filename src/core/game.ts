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
import { makePropertyTile, netWorth } from './property.js';
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
  const reject = (reason: RejectReason): ActionResult => ({ ok: false, reason, state, events: [] });
  if (!actor || actor.id !== action.actorId) return reject('INVALID_ACTOR');
  if (action.type === 'start_game') {
    if (state.phase !== 'setup') return reject('INVALID_PHASE');
    return accept(state, [{ type: 'game_started', actorId: action.actorId }], {
      status: 'playing', phase: 'await_roll'
    });
  }
  if (state.phase === 'setup' || state.phase === 'finished') return reject('INVALID_PHASE');

  switch (action.type) {
    case 'roll': {
      if (state.phase !== 'await_roll') return reject('INVALID_PHASE');
      const { value, nextState } = nextDie(state.randomState);
      const bonus=state.pendingMoveBonus??0;
      const position = (actor.position + value + bonus) % state.tiles.length;
      const landed = state.tiles[position];
      const events: GameEvent[] = [
        { type: 'die_rolled', actorId: actor.id, details: { value, bonus } },
        { type: 'player_moved', actorId: actor.id, details: { from: actor.position, to: position } },
        { type: 'tile_landed', actorId: actor.id, details: { tileId: landed.id, title: landed.title } }
      ];
      let movingPlayers = state.players.map(p => p.id === actor.id ? { ...p, position } : p);
      let finalRandomState=nextState;
      if (landed.kind === 'property' && landed.ownerId && landed.ownerId !== actor.id) {
        const landlord = state.players.find(p => p.id === landed.ownerId);
        if (!landlord) return reject('INVALID_PHASE');
        const due = (landed.level??0)===0 ? (landed.rent??0) : (landed.levelRents?.[landed.level??0]??0);
        const paid = Math.min(actor.cash, due);
        const insolvent = paid < due;
        const players = movingPlayers.map(p => p.id === actor.id
          ? { ...p, cash: p.cash - paid, bankrupt: insolvent }
          : p.id === landlord.id ? { ...p, cash: p.cash + paid } : p);
        events.push({ type: 'rent_paid', actorId: actor.id, details: {
          tileId: landed.id, fromId: actor.id, toId: landlord.id, due, amount: paid
        } });
        if (insolvent) {
          events.push({ type: 'player_bankrupt', actorId: actor.id, details: { creditorId: landlord.id } });
          events.push({ type: 'game_finished', details: { reason: 'bankruptcy', winnerId: landlord.id } });
        }
        return accept(state, events, {
          randomState: nextState, players, pendingMoveBonus:0,
          // 结束比赛后被淘汰者的土地回到无主状态；本阶段不实现清算/拍卖。
          tiles: insolvent ? state.tiles.map(t => t.ownerId === actor.id ? { ...t, ownerId: null, level:0 } : t) : state.tiles,
          status: insolvent ? 'finished' : 'playing',
          winnerId: insolvent ? landlord.id : state.winnerId,
          phase: insolvent ? 'finished' : 'await_end_turn'
        });
      }
      if(landed.kind==='neutral'&&landed.eventBonus!==undefined&&landed.eventFee!==undefined){
        const draw=nextDie(finalRandomState);
        finalRandomState=draw.nextState;
        if(draw.value%2===1){
          movingPlayers=movingPlayers.map(p=>p.id===actor.id?{...p,cash:p.cash+landed.eventBonus!}:p);
          events.push({type:'event_bonus',actorId:actor.id,details:{tileId:landed.id,amount:landed.eventBonus,draw:draw.value}});
        }else{
          const paid=Math.min(actor.cash,landed.eventFee);
          movingPlayers=movingPlayers.map(p=>p.id===actor.id?{...p,cash:p.cash-paid}:p);
          events.push({type:'event_fee',actorId:actor.id,details:{tileId:landed.id,due:landed.eventFee,amount:paid,draw:draw.value}});
        }
      }
      if(landed.cardStation){
        const owner=movingPlayers.find(p=>p.id===actor.id)!;
        const held=owner.cards??{reward:0,stride:0};
        if(held.reward+held.stride<(state.cardRules?.maxHand??DEFAULT_CARD_RULES.maxHand)){
          const draw=nextDie(finalRandomState);finalRandomState=draw.nextState;
          const kind:CardKind=draw.value%2===1?'reward':'stride';
          movingPlayers=movingPlayers.map(p=>p.id===actor.id?{...p,cards:{...held,[kind]:held[kind]+1}}:p);
          events.push({type:'card_received',actorId:actor.id,details:{tileId:landed.id,cardType:kind}});
        }
      }
      const phase: Phase = landed.kind === 'property' && landed.ownerId === null
        ? 'await_decision' : 'await_end_turn';
      return accept(state, events, {
        randomState: finalRandomState,
        players: movingPlayers,
        pendingMoveBonus:0,
        phase
      });
    }
    case 'decline_property': {
      if (state.phase !== 'await_decision') return reject('INVALID_PHASE');
      const tile = state.tiles[actor.position];
      if (tile.kind !== 'property' || tile.ownerId !== null) return reject('INVALID_PHASE');
      return accept(state, [{ type: 'property_declined', actorId: actor.id, details: { tileId: tile.id } }], {
        phase: 'await_end_turn'
      });
    }
    case 'end_turn': {
      if (state.phase !== 'await_end_turn') return reject('INVALID_PHASE');
      const lastPlayer = state.currentPlayerIndex === state.players.length - 1;
      const finished = lastPlayer && state.round >= state.maxRounds;
      const assets = state.players.map(p => netWorth(state, p.id));
      const winnerId = finished && assets[0] !== assets[1]
        ? state.players[assets[0] > assets[1] ? 0 : 1].id : null;
      const events: GameEvent[] = [{ type: 'turn_ended', actorId: actor.id }];
      if (finished) events.push({ type: 'game_finished', details: {
        reason: 'round_limit', draw: winnerId === null ? 1 : 0,
        firstNetWorth: assets[0], secondNetWorth: assets[1],
        ...(winnerId ? { winnerId } : {})
      } });
      return accept(state, events, {
        status: finished ? 'finished' : 'playing',
        phase: finished ? 'finished' : 'await_roll',
        currentPlayerIndex: (state.currentPlayerIndex + 1) % state.players.length,
        round: !finished && lastPlayer ? state.round + 1 : state.round,
        winnerId
      });
    }
    case 'use_card': {
      if(state.phase!=='await_roll'||(action.targetId!==undefined&&action.targetId!==actor.id)||
        !['reward','stride'].includes(action.cardType))return reject('INVALID_PHASE');
      const held=actor.cards??{reward:0,stride:0};
      if((held[action.cardType]??0)<1||(action.cardType==='stride'&&(state.pendingMoveBonus??0)>0))return reject('INVALID_PHASE');
      const rules=state.cardRules??DEFAULT_CARD_RULES;
      const reward=action.cardType==='reward'?rules.rewardCash:0;
      return accept(state,[{type:'card_used',actorId:actor.id,details:{cardType:action.cardType,amount:reward,moveBonus:action.cardType==='stride'?rules.moveBonus:0}}],{
        players:state.players.map(p=>p.id===actor.id?{...p,cash:p.cash+reward,cards:{...held,[action.cardType]:held[action.cardType]-1}}:p),
        pendingMoveBonus:action.cardType==='stride'?rules.moveBonus:(state.pendingMoveBonus??0)
      });
    }
    case 'upgrade_property': {
      if (state.phase !== 'await_end_turn' || !Number.isInteger(action.tileId))return reject('INVALID_PHASE');
      const tile=state.tiles[action.tileId];
      if (!tile || tile.kind!=='property' || tile.ownerId!==actor.id || (tile.level??0)>=2)return reject('INVALID_PHASE');
      const level=tile.level??0;
      const cost=tile.upgradeCosts?.[level];
      if(cost===undefined)return reject('INVALID_PHASE');
      if(actor.cash<cost)return reject('INSUFFICIENT_FUNDS');
      return accept(state,[{type:'property_upgraded',actorId:actor.id,details:{tileId:tile.id,level:level+1,amount:cost}}],{
        tiles:state.tiles.map(t=>t.id===tile.id?{...t,level:level+1}:t),
        players:state.players.map(p=>p.id===actor.id?{...p,cash:p.cash-cost}:p)
      });
    }
    case 'buy_property': {
      if (state.phase !== 'await_decision') return reject('INVALID_PHASE');
      const tile = state.tiles[actor.position];
      if (tile.kind !== 'property' || tile.ownerId !== null) return reject('INVALID_PHASE');
      const price = tile.price ?? 0;
      if (actor.cash < price) return reject('INSUFFICIENT_FUNDS');
      return accept(state, [{ type: 'property_bought', actorId: actor.id, details: {
        tileId: tile.id, amount: price, ownerId: actor.id
      } }], {
        players: state.players.map(p => p.id === actor.id ? { ...p, cash: p.cash - price } : p),
        tiles: state.tiles.map(t => t.id === tile.id ? { ...t, ownerId: actor.id } : t),
        phase: 'await_end_turn'
      });
    }
  }
}

function accept(state: GameState, events: readonly GameEvent[], changes: Partial<GameState>): ActionResult {
  return {
    ok: true,
    events,
    state: { ...state, ...changes, revision: state.revision + 1, events: [...state.events, ...events] }
  };
}
