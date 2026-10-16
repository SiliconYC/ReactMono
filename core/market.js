/** Five wholly fictitious companies; no external prices, account or network dependency. */
import { normalizeSeed } from './random.js';
export const STOCKS = [
    { id: 'SEA', name: '海岚科技', initialPrice: 80 },
    { id: 'RIVER', name: '碧波航运', initialPrice: 130 },
    { id: 'FARM', name: '青禾农业', initialPrice: 55 },
    { id: 'STAR', name: '星河能源', initialPrice: 105 },
    { id: 'TOWER', name: '远山工业', initialPrice: 160 }
];
const MAX_PRICE = 100000;
const ids = STOCKS.map(s => s.id);
const isRecord = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);
function nextRandom(value) {
    let x = value >>> 0;
    x ^= x << 13;
    x ^= x >>> 17;
    x ^= x << 5;
    return (x >>> 0) || 0x6d2b79f5;
}
export function validateMarket(value) {
    if (!isRecord(value) || Object.keys(value).sort().join(',') !== 'prices,rngState,round,version' ||
        value.version !== 1 || !Number.isSafeInteger(value.round) || Number(value.round) < 1 ||
        !Number.isSafeInteger(value.rngState) || Number(value.rngState) < 1 || Number(value.rngState) > 0xffffffff ||
        !isRecord(value.prices) || Object.keys(value.prices).sort().join(',') !== [...ids].sort().join(',') ||
        ids.some(id => !Number.isSafeInteger(value.prices[id]) ||
            Number(value.prices[id]) < 1 ||
            Number(value.prices[id]) > MAX_PRICE))
        throw new Error('行情状态无效');
}
export function createMarket(seed) {
    const rngState = normalizeSeed((normalizeSeed(seed) ^ 0x9e3779b9) >>> 0);
    return { version: 1, round: 1, rngState, prices: Object.fromEntries(STOCKS.map(s => [s.id, s.initialPrice])) };
}
export function quoteMarket(market, id) {
    if (!ids.some(s => s === id))
        throw new Error('股票代码不存在');
    return market.prices[id];
}
/** One fixed settlement per new game round; integer ±6% move per company. */
export function advanceMarket(state, round) {
    validateMarket(state);
    if (!Number.isSafeInteger(round) || round !== state.round + 1)
        throw new Error('行情轮次无效');
    let rngState = state.rngState;
    const prices = {};
    for (const stock of STOCKS) {
        rngState = nextRandom(rngState);
        const pct = (rngState % 13) - 6;
        prices[stock.id] = Math.max(1, Math.min(MAX_PRICE, Math.round(state.prices[stock.id] * (100 + pct) / 100)));
    }
    return { version: 1, round, rngState, prices };
}
