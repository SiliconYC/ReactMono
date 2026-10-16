/** Local versioned save contract; migrates historic two-player v1/v2 records. */
import { SCHEMA_VERSION, UPGRADE_RULES_VERSION, makePropertyTile } from './game.js';
import { inferMap, validateMap } from './maps.js';
import { STOCKS } from './market.js';
import { validateMarket } from './market.js';
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
    'property_bought', 'property_upgraded', 'property_sold', 'property_liquidated', 'bank_deposited', 'bank_withdrawn', 'bank_interest', 'property_mortgaged', 'property_released', 'loan_borrowed', 'loan_repaid', 'loan_interest', 'loan_default', 'stock_bought', 'stock_sold', 'stock_liquidated', 'rent_paid', 'event_bonus', 'event_fee', 'card_received', 'card_used', 'roadblock_triggered', 'rent_waived', 'card_expired', 'facility_entered', 'detention_skipped', 'detention_released', 'shop_purchased', 'shop_left', 'player_bankrupt', 'game_finished'
]);
/** Validate current and migrated legacy states against the same strict bounds. */
export function validateGameState(value, expectedVersion = SCHEMA_VERSION) {
    if (!record(value))
        throw new SaveError('INVALID_STATE', '存档数据无效：游戏状态必须为对象');
    keys(value, ['schemaVersion', 'status', 'phase', 'revision', 'round', 'currentPlayerIndex', 'randomState',
        'maxRounds', 'players', 'tiles', 'winnerId', 'events', 'upgradeRulesVersion',
        ...(expectedVersion >= 4 ? ['map'] : [])], ['cardRules', 'pendingMoveBonus', ...(expectedVersion >= 4 ? ['automaticLiquidation', 'resaleRules', 'market', 'bank', 'loan', 'strategyEnabled', 'pendingDie', 'pendingRentWaiver', 'roadblocks', 'specialEnabled', 'facilityRules', 'shops'] : [])]);
    if (value.strategyEnabled !== undefined && value.strategyEnabled !== true)
        throw new SaveError('INVALID_STATE', '策略卡规则标识非法');
    if (value.strategyEnabled === true) {
        if (!finite(value.pendingDie, 0, 6) || typeof value.pendingRentWaiver !== 'boolean' ||
            !Array.isArray(value.roadblocks) || value.roadblocks.length > 24)
            throw new SaveError('INVALID_STATE', '策略卡待执行状态非法');
        if (value.phase !== 'await_roll' && (value.pendingDie !== 0 || value.pendingRentWaiver !== false))
            throw new SaveError('INVALID_STATE', '策略卡存在非法残留效果');
    }
    else if (value.pendingDie !== undefined || value.pendingRentWaiver !== undefined || value.roadblocks !== undefined)
        throw new SaveError('INVALID_STATE', '旧版对局不能携带策略卡状态');
    if (value.specialEnabled !== undefined && value.specialEnabled !== true)
        throw new SaveError('INVALID_STATE', '特殊设施开关非法');
    if (value.specialEnabled === true) {
        if (value.strategyEnabled !== true || !record(value.facilityRules) || !Array.isArray(value.shops))
            throw new SaveError('INVALID_STATE', '特殊设施状态缺失');
        keys(value.facilityRules, ['version', 'hospitalTurns', 'prisonTurns', 'hospitalFee', 'prisonFee', 'prices']);
        const f = value.facilityRules;
        if (f.version !== 1 || !finite(f.hospitalTurns, 1, 20) || !finite(f.prisonTurns, 1, 20) ||
            !finite(f.hospitalFee, 0, 1000000) || !finite(f.prisonFee, 0, 1000000) ||
            !record(f.prices) || value.shops.length > 24)
            throw new SaveError('INVALID_STATE', '医院、监狱配置非法');
        keys(f.prices, ['reward', 'stride', 'remote', 'roadblock', 'rent_free']);
        if (!Object.values(f.prices).every(p => finite(p, 1, 1000000)))
            throw new SaveError('INVALID_STATE', '商店价格非法');
    }
    else if (value.facilityRules !== undefined || value.shops !== undefined)
        throw new SaveError('INVALID_STATE', '旧对局不得持有特殊设施');
    if (value.bank !== undefined) {
        if (!record(value.bank))
            throw new SaveError('INVALID_STATE', '银行状态非法');
        keys(value.bank, ['version', 'interestBps', 'lastInterestRound']);
        if (value.bank.version !== 1 || !finite(value.bank.interestBps, 0, 1000) || value.bank.lastInterestRound !== value.round)
            throw new SaveError('INVALID_STATE', '银行重复结息标记或利率非法');
    }
    if (value.loan !== undefined) {
        if (!record(value.loan))
            throw new SaveError('INVALID_STATE', '贷款状态非法');
        keys(value.loan, ['version', 'interestBps', 'lastInterestRound']);
        if (value.loan.version !== 1 || !finite(value.loan.interestBps, 0, 1000) || value.loan.lastInterestRound !== value.round ||
            value.bank === undefined)
            throw new SaveError('INVALID_STATE', '贷款状态或结息轮次非法');
    }
    if (value.market !== undefined) {
        try {
            validateMarket(value.market);
            if (value.market.round !== value.round)
                throw new Error('round');
        }
        catch {
            throw new SaveError('INVALID_STATE', '存档行情快照无效');
        }
    }
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
        !['setup', 'await_roll', 'await_decision', 'await_end_turn', 'await_shop', 'finished'].includes(String(value.phase)))
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
        keys(p, ['id', 'name', 'kind', 'position', 'cash', 'bankrupt'], ['cards', ...(expectedVersion >= 4 ? ['bankBalance', 'loanBalance', 'holdings', 'detention'] : [])]);
        if (value.bank !== undefined ? !finite(p.bankBalance, 0, 1_000_000_000_000) :
            p.bankBalance !== undefined && p.bankBalance !== 0)
            throw new SaveError('INVALID_STATE', '玩家银行存款非法');
        if (value.loan !== undefined ? !finite(p.loanBalance, 0, 1_000_000_000_000) :
            p.loanBalance !== undefined && p.loanBalance !== 0)
            throw new SaveError('INVALID_STATE', '玩家贷款余额非法');
        if (p.bankrupt === true && typeof p.loanBalance === 'number' && p.loanBalance > 0)
            throw new SaveError('INVALID_STATE', '破产玩家存在未处理债务');
        if (p.bankrupt === true && typeof p.bankBalance === 'number' && p.bankBalance > 0)
            throw new SaveError('INVALID_STATE', '破产玩家存在未清算存款');
        if (p.holdings !== undefined) {
            if (value.market === undefined || !record(p.holdings))
                throw new SaveError('INVALID_STATE', '玩家持仓缺少行情或数据非法');
            for (const [id, lot] of Object.entries(p.holdings)) {
                if (!STOCKS.some(stock => stock.id === id) || !record(lot))
                    throw new SaveError('INVALID_STATE', '非法股票代码或持仓');
                keys(lot, ['quantity', 'costBasis']);
                if (!finite(lot.quantity, 1, 1_000_000) || !finite(lot.costBasis, 1, 1_000_000_000_000))
                    throw new SaveError('INVALID_STATE', '股票数量或成本非法');
                if (p.bankrupt === true)
                    throw new SaveError('INVALID_STATE', '破产玩家不得持有股票');
            }
        }
        if (p.detention !== undefined) {
            if (value.specialEnabled !== true || !record(p.detention) || p.bankrupt === true)
                throw new SaveError('INVALID_STATE', '停留玩家无效');
            keys(p.detention, ['kind', 'remaining']);
            if (!['hospital', 'prison'].includes(String(p.detention.kind)) || !finite(p.detention.remaining, 1, 20) ||
                p.detention.remaining > (p.detention.kind === 'hospital' ?
                    value.facilityRules.hospitalTurns : value.facilityRules.prisonTurns))
                throw new SaveError('INVALID_STATE', '医院或监狱剩余回合非法');
        }
        if (p.cards !== undefined) {
            if (!record(p.cards))
                throw new SaveError('INVALID_STATE', '卡片库存无效');
            keys(p.cards, ['reward', 'stride'], value.strategyEnabled === true ? ['remote', 'roadblock', 'rent_free'] : []);
            if (!finite(p.cards.reward, 0, 1000) || !finite(p.cards.stride, 0, 1000) ||
                !['remote', 'roadblock', 'rent_free'].every(k => p.cards[k] === undefined || (value.strategyEnabled === true && finite(p.cards[k], 0, 1000))) ||
                p.cards.reward + p.cards.stride +
                    Number(p.cards.remote ?? 0) + Number(p.cards.roadblock ?? 0) + Number(p.cards.rent_free ?? 0) >
                    (record(value.cardRules) ? value.cardRules.maxHand : 3))
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
            keys(t, ['id', 'kind', 'title', 'price', 'rent', 'ownerId', 'level', 'upgradeCosts', 'levelRents'], expectedVersion >= 4 ? ['mortgaged'] : []);
            if (t.mortgaged !== undefined && (t.mortgaged !== true || value.loan === undefined || t.ownerId === null))
                throw new SaveError('INVALID_STATE', '地产抵押状态无效');
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
            keys(t, ['id', 'kind', 'title', 'ownerId'], ['eventBonus', 'eventFee', 'cardStation', ...(expectedVersion >= 4 ? ['facility'] : [])]);
            if (t.facility !== undefined) {
                if (value.specialEnabled !== true || t.kind !== 'neutral' ||
                    !['hospital', 'prison', 'shop'].includes(String(t.facility)) ||
                    t.cardStation !== undefined || t.eventBonus !== undefined || t.eventFee !== undefined)
                    throw new SaveError('INVALID_STATE', '特殊地块非法');
            }
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
    if (value.specialEnabled === true) {
        const shops = value.shops, used = new Set();
        for (const stock of shops) {
            if (!record(stock))
                throw new SaveError('INVALID_STATE', '商店存货记录非法');
            keys(stock, ['tileId', 'cards']);
            if (!finite(stock.tileId, 1, value.tiles.length - 1) || used.has(stock.tileId) ||
                value.tiles[stock.tileId].facility !== 'shop' || !record(stock.cards))
                throw new SaveError('INVALID_STATE', '商店地点重复或无效');
            keys(stock.cards, ['reward', 'stride', 'remote', 'roadblock', 'rent_free']);
            if (!Object.values(stock.cards).every(v => finite(v, 0, 100)))
                throw new SaveError('INVALID_STATE', '商店存货非法');
            used.add(stock.tileId);
        }
        if (value.tiles.some((t) => t.facility === 'shop' && !used.has(t.id)) ||
            !value.tiles.some((t) => t.facility === 'hospital') ||
            !value.tiles.some((t) => t.facility === 'prison'))
            throw new SaveError('INVALID_STATE', '设施配置与商店清单不符');
        for (const p of value.players) {
            if (p.detention !== undefined && value.tiles[p.position].facility !== p.detention.kind)
                throw new SaveError('INVALID_STATE', '被拘留玩家不在设施内');
        }
    }
    else if (value.players.some((p) => p.detention !== undefined) ||
        value.tiles.some((t) => t.facility !== undefined))
        throw new SaveError('INVALID_STATE', '普通对局出现特殊设施');
    if (value.strategyEnabled === true) {
        const used = new Set();
        for (const b of value.roadblocks) {
            if (!record(b))
                throw new SaveError('INVALID_STATE', '路障记录非法');
            keys(b, ['tileId', 'ownerId', 'expiresRound']);
            if (!finite(b.tileId, 1, value.tiles.length - 1) || used.has(b.tileId) ||
                !ids.includes(String(b.ownerId)) || value.players.some((p) => p.id === b.ownerId && p.bankrupt === true) ||
                !finite(b.expiresRound, 1, value.maxRounds + 2))
                throw new SaveError('INVALID_STATE', '路障目标、期限或归属非法');
            used.add(b.tileId);
        }
    }
    if (value.loan !== undefined) {
        for (const p of value.players) {
            const limit = value.tiles.reduce((sum, t) => {
                if (t.kind !== 'property' || t.ownerId !== p.id || t.mortgaged !== true)
                    return sum;
                const upgrades = t.upgradeCosts;
                const paid = upgrades.slice(0, t.level).reduce((a, b) => a + b, 0);
                const landPercent = record(value.resaleRules) ? Number(value.resaleRules.landPercent) : 0.75;
                const upgradePercent = record(value.resaleRules) ? Number(value.resaleRules.upgradePercent) : 0.5;
                return sum + Math.floor((Math.floor(Number(t.price) * landPercent) + Math.floor(paid * upgradePercent)) / 2);
            }, 0);
            if (Number(p.loanBalance) > limit)
                throw new SaveError('INVALID_STATE', '贷款余额超过抵押额度');
        }
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
    if (value.phase === 'await_shop') {
        const p = value.players[value.currentPlayerIndex];
        if (value.specialEnabled !== true || value.tiles[p.position].facility !== 'shop' || p.detention !== undefined)
            throw new SaveError('INVALID_STATE', '商店阶段与玩家位置不匹配');
    }
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
        if (!record(old) || old.schemaVersion !== 1 || !Array.isArray(old.tiles) || !Array.isArray(old.players))
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
