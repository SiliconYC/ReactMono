/** 独立于页面的最小确定性规则契约；#3 起才会实现骰子、地产与完整回合。 */
export const SCHEMA_VERSION = 1;
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
        tiles: config.tiles.map(t => ({ ...t, ownerId: null })),
        winnerId: null,
        events: []
    };
}
/** #2 只实现开始游戏；其余命令等待后续 Issue，以明确拒绝而不是伪造行为。 */
export function applyAction(state, action) {
    if (state.players[state.currentPlayerIndex]?.id !== action.actorId) {
        return { ok: false, reason: 'INVALID_ACTOR', state, events: [] };
    }
    if (action.type === 'start_game') {
        if (state.phase !== 'setup')
            return { ok: false, reason: 'INVALID_PHASE', state, events: [] };
        const event = { type: 'game_started', actorId: action.actorId };
        return {
            ok: true, events: [event],
            state: { ...state, status: 'playing', phase: 'await_roll', revision: state.revision + 1,
                events: [...state.events, event] }
        };
    }
    if (state.phase === 'setup' || state.phase === 'finished') {
        return { ok: false, reason: 'INVALID_PHASE', state, events: [] };
    }
    return { ok: false, reason: 'NOT_IMPLEMENTED', state, events: [] };
}
