/** 独立于页面的确定性回合与棋盘规则核心；第 #4 期加入地产买卖、收租、破产与胜负规则。 */
export const SCHEMA_VERSION = 2;
export const UPGRADE_RULES_VERSION = 1;
export const DEFAULT_UPGRADES = { costRates: [0.5, 0.8], rentRates: [1, 2, 4] };
const defaultTiles = Array.from({ length: 24 }, (_, index) => {
    if (index === 0)
        return { id: index, kind: 'start', title: '起点' };
    if (index % 3 === 0)
        return { id: index, kind: 'neutral', title: `休息站 ${index}` };
    return { id: index, kind: 'property', title: `地产 ${index}`, price: 100 + index * 10, rent: 20 + index * 2 };
});
export const DEFAULT_CONFIG = {
    players: [{ id: 'p1', name: '玩家' }, { id: 'p2', name: '电脑' }],
    tiles: defaultTiles,
    initialCash: 1500,
    maxRounds: 60
};
/** 固定 32 位种子，避免 Math.random 导致的回放不一致。 */
export function normalizeSeed(seed) {
    if (!Number.isFinite(seed))
        throw new Error('随机种子必须是有限数字');
    return (Math.trunc(seed) >>> 0) || 0x6d2b79f5;
}
/** 返回新随机状态；绝不修改传入状态。 */
export function nextDie(randomState) {
    let x = normalizeSeed(randomState);
    x ^= x << 13;
    x ^= x >>> 17;
    x ^= x << 5;
    const nextState = x >>> 0;
    return { value: 1 + (nextState % 6), nextState };
}
function validateConfig(config) {
    if (config.players.length !== 2 || new Set(config.players.map(p => p.id)).size !== 2 ||
        config.players.some(p => !p.id.trim() || !p.name.trim()))
        throw new Error('玩家配置必须包含两名不同玩家');
    if (config.tiles.length < 2 || config.tiles[0]?.kind !== 'start' ||
        config.tiles.filter(t => t.kind === 'start').length !== 1 ||
        config.tiles.some((t, i) => t.id !== i || !t.title.trim()))
        throw new Error('地图配置无效');
    if (!Number.isFinite(config.initialCash) || config.initialCash < 0 ||
        !Number.isInteger(config.maxRounds) || config.maxRounds < 1)
        throw new Error('游戏经济配置无效');
    const up = config.upgrades ?? DEFAULT_UPGRADES;
    if (up.costRates.length !== 2 || up.rentRates.length !== 3 ||
        ![...up.costRates, ...up.rentRates].every(x => Number.isFinite(x) && x >= 0) ||
        up.rentRates[0] !== 1)
        throw new Error('地产升级倍率配置无效');
    if (config.tiles.some(t => t.kind === 'property' &&
        (!Number.isFinite(t.price) || (t.price ?? 0) < 0 || !Number.isFinite(t.rent) || (t.rent ?? 0) < 0))) {
        throw new Error('地产价格或租金无效');
    }
}
/** 新建纯数据状态。每次调用都会创建隔离的玩家、棋盘数组。 */
export function createGame(seed, config = DEFAULT_CONFIG) {
    validateConfig(config);
    return {
        schemaVersion: SCHEMA_VERSION,
        upgradeRulesVersion: UPGRADE_RULES_VERSION,
        status: 'setup',
        phase: 'setup',
        revision: 0,
        round: 1,
        currentPlayerIndex: 0,
        randomState: normalizeSeed(seed),
        maxRounds: config.maxRounds,
        players: config.players.map((p, index) => ({
            id: p.id, name: p.name, kind: index === 0 ? 'human' : 'computer',
            position: 0, cash: config.initialCash, bankrupt: false
        })),
        tiles: config.tiles.map(t => t.kind === 'property' ? makePropertyTile(t, config.upgrades ?? DEFAULT_UPGRADES) : ({ ...t, ownerId: null })),
        winnerId: null,
        events: []
    };
}
export function makePropertyTile(t, upgrades = DEFAULT_UPGRADES) {
    if (t.kind !== 'property')
        throw new Error('只能升级地产');
    const up = upgrades ?? DEFAULT_UPGRADES;
    return { ...t, ownerId: null, level: 0,
        upgradeCosts: up.costRates.map(r => Math.round((t.price ?? 0) * r)),
        levelRents: up.rentRates.map(r => Math.round((t.rent ?? 0) * r)) };
}
/** 净资产按购地原价与已付升级费用计价，不计未实现收益。 */
export function netWorth(state, playerId) {
    const player = state.players.find(p => p.id === playerId);
    if (!player)
        throw new Error('玩家不存在');
    return player.cash + state.tiles.reduce((sum, tile) => sum + (tile.ownerId === playerId && tile.kind === 'property'
        ? (tile.price ?? 0) + (tile.upgradeCosts ?? []).slice(0, tile.level ?? 0).reduce((a, b) => a + b, 0) : 0), 0);
}
/** 单一命令入口：始终返回新状态或明确拒绝，不修改传入对象。 */
export function applyAction(state, action) {
    const actor = state.players[state.currentPlayerIndex];
    const reject = (reason) => ({ ok: false, reason, state, events: [] });
    if (!actor || actor.id !== action.actorId)
        return reject('INVALID_ACTOR');
    if (action.type === 'start_game') {
        if (state.phase !== 'setup')
            return reject('INVALID_PHASE');
        return accept(state, [{ type: 'game_started', actorId: action.actorId }], {
            status: 'playing', phase: 'await_roll'
        });
    }
    if (state.phase === 'setup' || state.phase === 'finished')
        return reject('INVALID_PHASE');
    switch (action.type) {
        case 'roll': {
            if (state.phase !== 'await_roll')
                return reject('INVALID_PHASE');
            const { value, nextState } = nextDie(state.randomState);
            const position = (actor.position + value) % state.tiles.length;
            const landed = state.tiles[position];
            const events = [
                { type: 'die_rolled', actorId: actor.id, details: { value } },
                { type: 'player_moved', actorId: actor.id, details: { from: actor.position, to: position } },
                { type: 'tile_landed', actorId: actor.id, details: { tileId: landed.id, title: landed.title } }
            ];
            const movingPlayers = state.players.map(p => p.id === actor.id ? { ...p, position } : p);
            if (landed.kind === 'property' && landed.ownerId && landed.ownerId !== actor.id) {
                const landlord = state.players.find(p => p.id === landed.ownerId);
                if (!landlord)
                    return reject('INVALID_PHASE');
                const due = (landed.level ?? 0) === 0 ? (landed.rent ?? 0) : (landed.levelRents?.[landed.level ?? 0] ?? 0);
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
                    randomState: nextState, players,
                    // 结束比赛后被淘汰者的土地回到无主状态；本阶段不实现清算/拍卖。
                    tiles: insolvent ? state.tiles.map(t => t.ownerId === actor.id ? { ...t, ownerId: null, level: 0 } : t) : state.tiles,
                    status: insolvent ? 'finished' : 'playing',
                    winnerId: insolvent ? landlord.id : state.winnerId,
                    phase: insolvent ? 'finished' : 'await_end_turn'
                });
            }
            const phase = landed.kind === 'property' && landed.ownerId === null
                ? 'await_decision' : 'await_end_turn';
            return accept(state, events, {
                randomState: nextState,
                players: movingPlayers,
                phase
            });
        }
        case 'decline_property': {
            if (state.phase !== 'await_decision')
                return reject('INVALID_PHASE');
            const tile = state.tiles[actor.position];
            if (tile.kind !== 'property' || tile.ownerId !== null)
                return reject('INVALID_PHASE');
            return accept(state, [{ type: 'property_declined', actorId: actor.id, details: { tileId: tile.id } }], {
                phase: 'await_end_turn'
            });
        }
        case 'end_turn': {
            if (state.phase !== 'await_end_turn')
                return reject('INVALID_PHASE');
            const lastPlayer = state.currentPlayerIndex === state.players.length - 1;
            const finished = lastPlayer && state.round >= state.maxRounds;
            const assets = state.players.map(p => netWorth(state, p.id));
            const winnerId = finished && assets[0] !== assets[1]
                ? state.players[assets[0] > assets[1] ? 0 : 1].id : null;
            const events = [{ type: 'turn_ended', actorId: actor.id }];
            if (finished)
                events.push({ type: 'game_finished', details: {
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
        case 'upgrade_property': {
            if (state.phase !== 'await_end_turn' || !Number.isInteger(action.tileId))
                return reject('INVALID_PHASE');
            const tile = state.tiles[action.tileId];
            if (!tile || tile.kind !== 'property' || tile.ownerId !== actor.id || (tile.level ?? 0) >= 2)
                return reject('INVALID_PHASE');
            const level = tile.level ?? 0;
            const cost = tile.upgradeCosts?.[level];
            if (cost === undefined)
                return reject('INVALID_PHASE');
            if (actor.cash < cost)
                return reject('INSUFFICIENT_FUNDS');
            return accept(state, [{ type: 'property_upgraded', actorId: actor.id, details: { tileId: tile.id, level: level + 1, amount: cost } }], {
                tiles: state.tiles.map(t => t.id === tile.id ? { ...t, level: level + 1 } : t),
                players: state.players.map(p => p.id === actor.id ? { ...p, cash: p.cash - cost } : p)
            });
        }
        case 'buy_property': {
            if (state.phase !== 'await_decision')
                return reject('INVALID_PHASE');
            const tile = state.tiles[actor.position];
            if (tile.kind !== 'property' || tile.ownerId !== null)
                return reject('INVALID_PHASE');
            const price = tile.price ?? 0;
            if (actor.cash < price)
                return reject('INSUFFICIENT_FUNDS');
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
function accept(state, events, changes) {
    return {
        ok: true,
        events,
        state: { ...state, ...changes, revision: state.revision + 1, events: [...state.events, ...events] }
    };
}
