/** Local versioned save contract; migrates historic two-player v1/v2 records. */
import { SCHEMA_VERSION, UPGRADE_RULES_VERSION, makePropertyTile } from './game.js';
import { inferMap, validateMap } from './maps.js';
export const SAVE_FORMAT_VERSION = 1;
export const MAX_SAVE_CHARS = 4_000_000;
export class SaveError extends Error {
    code;
    constructor(code, message) {
        super(message);
        this.code = code;
        this.name = 'SaveError';
    }
}
const record = (x) => x !== null && typeof x === 'object' && !Array.isArray(x);
const finite = (x, min = 0, max = Number.MAX_SAFE_INTEGER) => typeof x === 'number' && Number.isSafeInteger(x) && x >= min && x <= max;
const string = (x, max = 100) => typeof x === 'string' && x.length > 0 && x.length <= max && x.trim().length > 0;
function keys(x, required, optional = []) {
    if (required.some(k => !Object.hasOwn(x, k)) || Object.keys(x).some(k => !required.includes(k) && !optional.includes(k)))
        throw new SaveError('INVALID_STATE', '存档数据无效：字段缺失或出现未知字段');
}
function iso(x) {
    return typeof x === 'string' && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/.test(x) &&
        Number.isFinite(Date.parse(x)) && new Date(x).toISOString() === x;
}
const EVENT_TYPES = new Set([
    'game_started', 'die_rolled', 'player_moved', 'turn_ended', 'tile_landed', 'property_declined',
    'property_bought', 'property_upgraded', 'property_sold', 'property_liquidated', 'rent_paid', 'event_bonus', 'event_fee', 'card_received', 'card_used', 'player_bankrupt', 'game_finished'
]);
/** Validate current and migrated legacy states against the same strict bounds. */
export function validateGameState(value, expectedVersion = SCHEMA_VERSION) {
    if (!record(value))
        throw new SaveError('INVALID_STATE', '存档数据无效：游戏状态必须为对象');
    keys(value, ['schemaVersion', 'status', 'phase', 'revision', 'round', 'currentPlayerIndex', 'randomState',
        'maxRounds', 'players', 'tiles', 'winnerId', 'events', 'upgradeRulesVersion',
        ...(expectedVersion >= 4 ? ['map'] : [])], ['cardRules', 'pendingMoveBonus', ...(expectedVersion >= 4 ? ['automaticLiquidation', 'resaleRules'] : [])]);
    if (value.resaleRules !== undefined) {
        if (!record(value.resaleRules))
            throw new SaveError('INVALID_STATE', '地产出售比例非法');
        keys(value.resaleRules, ['landPercent', 'upgradePercent']);
        if (![value.resaleRules.landPercent, value.resaleRules.upgradePercent].every(v => typeof v === 'number' && Number.isFinite(v) && v >= 0 && v <= 1))
            throw new SaveError('INVALID_STATE', '地产出售比例非法');
    }
    if (value.automaticLiquidation !== undefined && value.automaticLiquidation !== true)
        throw new SaveError('INVALID_STATE', '地产救济规则标识非法');
    if (value.cardRules !== undefined) {
        if (!record(value.cardRules))
            throw new SaveError('INVALID_STATE', '卡片参数无效');
        keys(value.cardRules, ['rewardCash', 'moveBonus', 'maxHand']);
        if (![value.cardRules.rewardCash, value.cardRules.moveBonus, value.cardRules.maxHand].every(v => finite(v, 1, 100000)))
            throw new SaveError('INVALID_STATE', '卡片规则参数无效');
    }
    if (value.pendingMoveBonus !== undefined && !(value.pendingMoveBonus === 0 || value.pendingMoveBonus === (record(value.cardRules) ? value.cardRules.moveBonus : 2)))
        throw new SaveError('INVALID_STATE', '移动修正无效');
    if (value.upgradeRulesVersion !== UPGRADE_RULES_VERSION)
        throw new SaveError('INCOMPATIBLE_VERSION', '地产升级规则版本不兼容');
    if (value.schemaVersion !== expectedVersion)
        throw new SaveError('INCOMPATIBLE_VERSION', '游戏规则版本不兼容');
    if (!['setup', 'playing', 'finished'].includes(String(value.status)) ||
        !['setup', 'await_roll', 'await_decision', 'await_end_turn', 'finished'].includes(String(value.phase)))
        throw new SaveError('INVALID_STATE', '存档数据无效：阶段不合法');
    if ((value.status === 'setup') !== (value.phase === 'setup') ||
        (value.status === 'finished') !== (value.phase === 'finished'))
        throw new SaveError('INVALID_STATE', '存档数据无效：状态与阶段不匹配');
    if (!finite(value.revision, 0, 100000) || !finite(value.maxRounds, 1, 100000) ||
        !finite(value.round, 1, value.maxRounds) || !finite(value.currentPlayerIndex, 0, 3) ||
        !finite(value.randomState, 1, 0xffffffff))
        throw new SaveError('INVALID_STATE', '存档数据无效：回合、修订或随机数状态非法');
    if (!Array.isArray(value.players) || value.players.length < 2 || value.players.length > 4 ||
        (expectedVersion === 2 && value.players.length !== 2) ||
        value.currentPlayerIndex >= value.players.length)
        throw new SaveError('INVALID_STATE', '存档数据无效：玩家数量或行动索引非法');
    const ids = [];
    for (let i = 0; i < value.players.length; i++) {
        const p = value.players[i];
        if (!record(p))
            throw new SaveError('INVALID_STATE', '存档数据无效：玩家字段非法');
        keys(p, ['id', 'name', 'kind', 'position', 'cash', 'bankrupt'], ['cards']);
        if (p.cards !== undefined) {
            if (!record(p.cards))
                throw new SaveError('INVALID_STATE', '卡片库存无效');
            keys(p.cards, ['reward', 'stride']);
            if (!finite(p.cards.reward, 0, 1000) || !finite(p.cards.stride, 0, 1000) ||
                p.cards.reward + p.cards.stride > (record(value.cardRules) ? value.cardRules.maxHand : 3))
                throw new SaveError('INVALID_STATE', '卡片库存超过上限');
        }
        if (!string(p.id, 64) || !string(p.name, 80) || ids.includes(p.id) ||
            (p.kind !== 'human' && p.kind !== 'computer') ||
            (expectedVersion === 2 && p.kind !== (i === 0 ? 'human' : 'computer')) || typeof p.bankrupt !== 'boolean' ||
            !finite(p.cash, 0, 1_000_000_000_000))
            throw new SaveError('INVALID_STATE', '存档数据无效：玩家身份、现金或状态非法');
        ids.push(p.id);
    }
    if (!Array.isArray(value.tiles) || value.tiles.length < 2 || value.tiles.length > 512)
        throw new SaveError('INVALID_STATE', '存档数据无效：地图长度非法');
    if (expectedVersion >= 4) {
        try {
            validateMap(value.map, value.tiles.length);
        }
        catch {
            throw new SaveError('INVALID_STATE', '存档地图标识、版本或路径非法');
        }
    }
    let startCount = 0;
    for (let i = 0; i < value.tiles.length; i++) {
        const t = value.tiles[i];
        if (!record(t))
            throw new SaveError('INVALID_STATE', '存档数据无效：地图格字段非法');
        if (t.kind === 'property') {
            keys(t, ['id', 'kind', 'title', 'price', 'rent', 'ownerId', 'level', 'upgradeCosts', 'levelRents']);
            if (!finite(t.level, 0, 2) || !Array.isArray(t.upgradeCosts) || t.upgradeCosts.length !== 2 ||
                !t.upgradeCosts.every(v => finite(v, 0, 1_000_000_000_000)) ||
                !Array.isArray(t.levelRents) || t.levelRents.length !== 3 ||
                !t.levelRents.every(v => finite(v, 0, 1_000_000_000_000)) || t.levelRents[0] !== t.rent)
                throw new SaveError('INVALID_STATE', '存档数据无效：升级等级与分级费用不合法');
            if (!finite(t.price, 0, 1_000_000_000_000) || !finite(t.rent, 0, 1_000_000_000_000) ||
                (t.ownerId !== null && !ids.includes(String(t.ownerId))))
                throw new SaveError('INVALID_STATE', '存档数据无效：地产价格、租金或产权非法');
        }
        else {
            keys(t, ['id', 'kind', 'title', 'ownerId'], ['eventBonus', 'eventFee', 'cardStation']);
            if (t.cardStation !== undefined && (t.kind !== 'neutral' || t.cardStation !== true))
                throw new SaveError('INVALID_STATE', '卡片格状态非法');
            if (t.eventBonus !== undefined || t.eventFee !== undefined) {
                if (t.kind !== 'neutral' || !finite(t.eventBonus, 0, 1_000_000_000_000) || !finite(t.eventFee, 0, 1_000_000_000_000))
                    throw new SaveError('INVALID_STATE', '存档数据无效：随机事件配置错误');
            }
            if ((t.kind !== 'start' && t.kind !== 'neutral') || t.ownerId !== null)
                throw new SaveError('INVALID_STATE', '存档数据无效：普通格或起点数据非法');
        }
        if (t.kind === 'start')
            startCount++;
        if (t.id !== i || !string(t.title, 100))
            throw new SaveError('INVALID_STATE', '存档数据无效：地图位置或名称非法');
    }
    if (startCount !== 1 || value.tiles[0].kind !== 'start')
        throw new SaveError('INVALID_STATE', '存档数据无效：起点配置非法');
    for (const p of value.players) {
        if (!finite(p.position, 0, value.tiles.length - 1))
            throw new SaveError('INVALID_STATE', '存档数据无效：玩家位置越界');
    }
    if (value.winnerId !== null && !ids.includes(String(value.winnerId)))
        throw new SaveError('INVALID_STATE', '存档数据无效：胜利者身份非法');
    if (value.status !== 'finished' && value.winnerId !== null)
        throw new SaveError('INVALID_STATE', '存档数据无效：未结束对局不能提前有胜利者');
    if (value.phase === 'await_decision') {
        const p = value.players[value.currentPlayerIndex];
        const tile = value.tiles[p.position];
        if (tile.kind !== 'property' || tile.ownerId !== null)
            throw new SaveError('INVALID_STATE', '存档数据无效：购地阶段未落在无主地产');
    }
    const live = value.players.filter((p) => p.bankrupt !== true);
    if (live.length < 1 || (value.status !== 'finished' && (live.length < 2 || value.players[value.currentPlayerIndex].bankrupt)) ||
        (expectedVersion === 2 && value.status !== 'finished' && live.length !== value.players.length))
        throw new SaveError('INVALID_STATE', '存档数据无效：存活玩家或行动顺序非法');
    const checkedPlayers = value.players;
    if (value.tiles.some((t) => t.ownerId !== null && checkedPlayers.some((p) => p.id === t.ownerId && p.bankrupt)))
        throw new SaveError('INVALID_STATE', '破产玩家不能持有地产');
    if (!Array.isArray(value.events))
        throw new SaveError('INVALID_STATE', '存档数据无效：事件列表缺失');
    if (value.status === 'setup' && (value.revision !== 0 || value.round !== 1 ||
        value.currentPlayerIndex !== 0 || value.events.length !== 0))
        throw new SaveError('INVALID_STATE', '存档数据无效：未开始对局已有行动');
    if (!Array.isArray(value.events) || value.events.length > 10000 ||
        value.revision > value.events.length)
        throw new SaveError('INVALID_STATE', '存档数据无效：事件数量或修订状态非法');
    for (const e of value.events) {
        if (!record(e))
            throw new SaveError('INVALID_STATE', '存档数据无效：事件字段非法');
        keys(e, ['type'], ['actorId', 'details']);
        if (!EVENT_TYPES.has(String(e.type)) ||
            (e.actorId !== undefined && !ids.includes(String(e.actorId))))
            throw new SaveError('INVALID_STATE', '存档数据无效：事件类型或行动者非法');
        if (e.details !== undefined) {
            if (!record(e.details) || Object.keys(e.details).length > 32)
                throw new SaveError('INVALID_STATE', '存档数据无效：事件详情非法');
            for (const [k, v] of Object.entries(e.details)) {
                if (!string(k, 80) || ['__proto__', 'constructor', 'prototype'].includes(k) ||
                    !(typeof v === 'string' && v.length <= 300 || typeof v === 'number' && Number.isFinite(v)))
                    throw new SaveError('INVALID_STATE', '存档数据无效：事件详情值非法');
            }
        }
    }
    if (value.status === 'finished' && value.events.at(-1)?.type !== 'game_finished')
        throw new SaveError('INVALID_STATE', '存档数据无效：结束标记缺失');
}
/** FNV-1a 用于检测意外编辑或位损坏；本地公开文件无法提供抗恶意伪造的签名。 */
function checksum(data) {
    let hash = 0x811c9dc5;
    for (let i = 0; i < data.length; i++) {
        hash ^= data.charCodeAt(i);
        hash = Math.imul(hash, 0x01000193);
    }
    return (hash >>> 0).toString(16).padStart(8, '0');
}
export function serializeGame(game, options = {}) {
    validateGameState(game);
    const now = options.now ?? new Date().toISOString();
    const createdAt = options.createdAt ?? now;
    if (!iso(now) || !iso(createdAt) || createdAt > now)
        throw new SaveError('INVALID_STATE', '存档数据无效：时间格式或先后顺序非法');
    const payload = { format: 'reactmono-save', formatVersion: SAVE_FORMAT_VERSION,
        rulesVersion: SCHEMA_VERSION, createdAt, updatedAt: now, game };
    const raw = JSON.stringify(payload);
    if (raw.length > MAX_SAVE_CHARS)
        throw new SaveError('TOO_LARGE', '存档过大，无法保存');
    return JSON.stringify({ ...payload, checksum: checksum(raw) });
}
export function deserializeGame(raw) {
    if (typeof raw !== 'string')
        throw new SaveError('INVALID_JSON', '存档必须是 JSON 文本');
    if (raw.length > MAX_SAVE_CHARS)
        throw new SaveError('TOO_LARGE', '存档过大，已拒绝读取');
    let value;
    try {
        value = JSON.parse(raw);
    }
    catch {
        throw new SaveError('INVALID_JSON', '存档不是有效的 JSON 文件');
    }
    if (!record(value))
        throw new SaveError('INVALID_FORMAT', '存档格式错误');
    if (value.format !== 'reactmono-save')
        throw new SaveError('INVALID_FORMAT', '不是大富翁存档文件');
    if (value.formatVersion !== SAVE_FORMAT_VERSION || ![1, 2, 3, SCHEMA_VERSION].includes(value.rulesVersion))
        throw new SaveError('INCOMPATIBLE_VERSION', '存档版本不兼容');
    keys(value, ['format', 'formatVersion', 'rulesVersion', 'createdAt', 'updatedAt', 'game', 'checksum']);
    if (!iso(value.createdAt) || !iso(value.updatedAt) || value.createdAt > value.updatedAt)
        throw new SaveError('INVALID_STATE', '存档数据无效：时间戳无效');
    if (typeof value.checksum !== 'string' || !/^[0-9a-f]{8}$/.test(value.checksum))
        throw new SaveError('INVALID_CHECKSUM', '存档校验码缺失或损坏');
    const payload = { format: value.format, formatVersion: value.formatVersion, rulesVersion: value.rulesVersion,
        createdAt: value.createdAt, updatedAt: value.updatedAt, game: value.game };
    if (checksum(JSON.stringify(payload)) !== value.checksum)
        throw new SaveError('INVALID_CHECKSUM', '存档内容被修改或已损坏，不能读取');
    if (value.rulesVersion === 1) {
        const old = value.game;
        if (!record(old) || old.schemaVersion !== 1 || !Array.isArray(old.tiles))
            throw new SaveError('INVALID_STATE', '旧版存档结构错误');
        // 校验旧版字段，避免以迁移名义接受未知结构；校验码已按旧载荷完成验证。
        keys(old, ['schemaVersion', 'status', 'phase', 'revision', 'round', 'currentPlayerIndex', 'randomState', 'maxRounds', 'players', 'tiles', 'winnerId', 'events']);
        const tiles = old.tiles.map((tile) => {
            if (!record(tile))
                throw new SaveError('INVALID_STATE', '旧版地块无效');
            if (tile.kind !== 'property')
                return tile;
            keys(tile, ['id', 'kind', 'title', 'price', 'rent', 'ownerId']);
            return { ...makePropertyTile(tile), ownerId: tile.ownerId };
        });
        const upgraded = { ...old, schemaVersion: SCHEMA_VERSION, upgradeRulesVersion: UPGRADE_RULES_VERSION, tiles, map: inferMap(tiles.length) };
        validateGameState(upgraded);
        return JSON.parse(serializeGame(upgraded, { createdAt: value.createdAt, now: value.updatedAt }));
    }
    if (value.rulesVersion === 2 || value.rulesVersion === 3) {
        validateGameState(value.game, value.rulesVersion);
        const upgraded = { ...value.game, schemaVersion: SCHEMA_VERSION, map: inferMap(value.game.tiles.length) };
        validateGameState(upgraded);
        return JSON.parse(serializeGame(upgraded, { createdAt: value.createdAt, now: value.updatedAt }));
    }
    validateGameState(value.game);
    return value;
}
