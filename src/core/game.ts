/** 独立于页面的确定性回合与棋盘规则核心；第 #4 期加入地产买卖、收租、破产与胜负规则。 */
export const SCHEMA_VERSION = 2 as const;
export const UPGRADE_RULES_VERSION = 1 as const;
export type CardKind = 'reward' | 'stride';
export const DEFAULT_CARD_RULES = { tileIds:[6,12,18], rewardCash:80, moveBonus:2, maxHand:3 } as const;
export const DEFAULT_EVENT_RULES = { tileIds:[3,9,15,21], bonus:120, fee:60 } as const;
export const DEFAULT_UPGRADES = { costRates: [0.5, 0.8], rentRates: [1, 2, 4] } as const;
export type PlayerId = string;
export type TileKind = 'start' | 'property' | 'neutral';
export type Phase = 'setup' | 'await_roll' | 'await_decision' | 'await_end_turn' | 'finished';
export type PlayerKind = 'human' | 'computer';

export interface PlayerConfig { readonly id: PlayerId; readonly name: string; }
export interface TileConfig {
  readonly id: number;
  readonly kind: TileKind;
  readonly title: string;
  readonly price?: number;
  readonly rent?: number;
}
export interface GameConfig {
  readonly players: readonly [PlayerConfig, PlayerConfig];
  readonly tiles: readonly TileConfig[];
  readonly initialCash: number;
  readonly maxRounds: number;
  readonly upgrades?: { readonly costRates: readonly [number,number]; readonly rentRates: readonly [number,number,number] };
  readonly eventRules?: {readonly tileIds:readonly number[];readonly bonus:number;readonly fee:number};
  readonly cardRules?: {readonly tileIds:readonly number[];readonly rewardCash:number;readonly moveBonus:number;readonly maxHand:number};
}
export interface Player {
  readonly id: PlayerId;
  readonly name: string;
  readonly kind: PlayerKind;
  readonly position: number;
  readonly cash: number;
  readonly bankrupt: boolean;
  readonly cards?:Readonly<Record<CardKind,number>>;
}
export interface Tile extends TileConfig {
  readonly ownerId: PlayerId | null;
  readonly level?: number;
  readonly upgradeCosts?: readonly [number,number];
  readonly levelRents?: readonly [number,number,number];
  readonly eventBonus?:number;
  readonly eventFee?:number;
  readonly cardStation?:boolean;
}
export interface GameEvent {
  readonly type: 'game_started' | 'die_rolled' | 'player_moved' | 'turn_ended' | 'tile_landed' | 'property_declined' | 'property_bought' | 'property_upgraded' | 'event_bonus' | 'event_fee' | 'card_received' | 'card_used' | 'rent_paid' | 'player_bankrupt' | 'game_finished';
  readonly actorId?: PlayerId;
  readonly details?: Readonly<Record<string, string | number>>;
}
export interface GameState {
  readonly schemaVersion: typeof SCHEMA_VERSION;
  readonly upgradeRulesVersion: typeof UPGRADE_RULES_VERSION;
  readonly cardRules?: {readonly rewardCash:number;readonly moveBonus:number;readonly maxHand:number};
  readonly pendingMoveBonus?:number;
  readonly status: 'setup' | 'playing' | 'finished';
  readonly phase: Phase;
  readonly revision: number;
  readonly round: number;
  readonly currentPlayerIndex: number;
  readonly randomState: number;
  readonly maxRounds: number;
  readonly players: readonly Player[];
  readonly tiles: readonly Tile[];
  readonly winnerId: PlayerId | null;
  readonly events: readonly GameEvent[];
}
export type GameAction =
  | { readonly type: 'start_game'; readonly actorId: PlayerId }
  | { readonly type: 'roll'; readonly actorId: PlayerId }
  | { readonly type: 'buy_property'; readonly actorId: PlayerId }
  | { readonly type: 'decline_property'; readonly actorId: PlayerId }
  | { readonly type: 'end_turn'; readonly actorId: PlayerId }
  | { readonly type: 'upgrade_property'; readonly actorId: PlayerId; readonly tileId: number }
  | { readonly type: 'use_card'; readonly actorId:PlayerId; readonly cardType:CardKind; readonly targetId?:PlayerId };
export type RejectReason = 'INVALID_PHASE' | 'INVALID_ACTOR' | 'INSUFFICIENT_FUNDS';
export type ActionResult =
  | { readonly ok: true; readonly state: GameState; readonly events: readonly GameEvent[] }
  | { readonly ok: false; readonly state: GameState; readonly events: readonly []; readonly reason: RejectReason };

const defaultTiles: readonly TileConfig[] = Array.from({ length: 24 }, (_, index): TileConfig => {
  if (index === 0) return { id: index, kind: 'start', title: '起点' };
  if (index % 3 === 0) return { id: index, kind: 'neutral', title: `休息站 ${index}` };
  return { id: index, kind: 'property', title: `地产 ${index}`, price: 100 + index * 10, rent: 20 + index * 2 };
});

export const DEFAULT_CONFIG: GameConfig = {
  players: [{ id: 'p1', name: '玩家' }, { id: 'p2', name: '电脑' }],
  tiles: defaultTiles,
  initialCash: 1500,
  maxRounds: 60
};

/** 固定 32 位种子，避免 Math.random 导致的回放不一致。 */
export function normalizeSeed(seed: number): number {
  if (!Number.isFinite(seed)) throw new Error('随机种子必须是有限数字');
  return (Math.trunc(seed) >>> 0) || 0x6d2b79f5;
}

/** 返回新随机状态；绝不修改传入状态。 */
export function nextDie(randomState: number): { readonly value: number; readonly nextState: number } {
  let x = normalizeSeed(randomState);
  x ^= x << 13;
  x ^= x >>> 17;
  x ^= x << 5;
  const nextState = x >>> 0;
  return { value: 1 + (nextState % 6), nextState };
}

function validateConfig(config: GameConfig): void {
  if (config.players.length !== 2 || new Set(config.players.map(p => p.id)).size !== 2 ||
      config.players.some(p => !p.id.trim() || !p.name.trim())) throw new Error('玩家配置必须包含两名不同玩家');
  if (config.tiles.length < 2 || config.tiles[0]?.kind !== 'start' ||
      config.tiles.filter(t => t.kind === 'start').length !== 1 ||
      config.tiles.some((t, i) => t.id !== i || !t.title.trim())) throw new Error('地图配置无效');
  if (!Number.isFinite(config.initialCash) || config.initialCash < 0 ||
      !Number.isInteger(config.maxRounds) || config.maxRounds < 1) throw new Error('游戏经济配置无效');
  const cards=config.cardRules??DEFAULT_CARD_RULES;
  if(![cards.rewardCash,cards.moveBonus,cards.maxHand].every(x=>Number.isSafeInteger(x)&&x>0)||
    new Set(cards.tileIds).size!==cards.tileIds.length||
    cards.tileIds.some(i=>!Number.isInteger(i)||i<0||(i<config.tiles.length&&config.tiles[i].kind!=='neutral')))
    throw new Error('卡片配置无效');
  const ev=config.eventRules??DEFAULT_EVENT_RULES;
  if(![ev.bonus,ev.fee].every(v=>Number.isSafeInteger(v)&&v>=0)||
    new Set(ev.tileIds).size!==ev.tileIds.length||
    ev.tileIds.some(i=>!Number.isInteger(i)||i<0||(i<config.tiles.length&&config.tiles[i].kind!=='neutral')))
    throw new Error('随机事件配置无效');
  const up=config.upgrades ?? DEFAULT_UPGRADES;
  if(up.costRates.length!==2 || up.rentRates.length!==3 ||
    ![...up.costRates,...up.rentRates].every(x=>Number.isFinite(x)&&x>=0) ||
    up.rentRates[0]!==1) throw new Error('地产升级倍率配置无效');
  if (config.tiles.some(t => t.kind === 'property' &&
      (!Number.isFinite(t.price) || (t.price ?? 0) < 0 || !Number.isFinite(t.rent) || (t.rent ?? 0) < 0))) {
    throw new Error('地产价格或租金无效');
  }
}

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

export function makePropertyTile(t: TileConfig, upgrades: GameConfig['upgrades']=DEFAULT_UPGRADES): Tile {
  if(t.kind!=='property')throw new Error('只能升级地产');
  const up=upgrades??DEFAULT_UPGRADES;
  return {...t, ownerId:null,level:0,
    upgradeCosts:up.costRates.map(r=>Math.round((t.price??0)*r)) as unknown as [number,number],
    levelRents:up.rentRates.map(r=>Math.round((t.rent??0)*r)) as unknown as [number,number,number]};
}

/** 净资产按购地原价与已付升级费用计价，不计未实现收益。 */
export function netWorth(state: GameState, playerId: PlayerId): number {
  const player = state.players.find(p => p.id === playerId);
  if (!player) throw new Error('玩家不存在');
  return player.cash + state.tiles.reduce((sum, tile) =>
    sum + (tile.ownerId === playerId && tile.kind === 'property'
      ? (tile.price??0)+(tile.upgradeCosts??[]).slice(0,tile.level??0).reduce((a,b)=>a+b,0) : 0), 0);
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
