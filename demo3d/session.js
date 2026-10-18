import { INTERNAL_TEST_MAP, applyAction, createGame } from '../core/game.js';
import { routeSteps } from './route.js';
const TILE_NAMES = [
    '晨曦车站', '银杏小路', '甜橙街', '河畔公园',
    '红砖巷', '钟楼广场', '风铃街', '云朵花园',
    '晴湾银行', '蜜糖路', '书店街', '星光露台',
    '松果公园', '琥珀大道', '月桂巷', '归家广场'
];
const DEMO_TILES = TILE_NAMES.map((title, id) => {
    if (id === 0)
        return { id, kind: 'start', title };
    if (id % 4 === 0 || id === 15)
        return { id, kind: 'neutral', title };
    return {
        id,
        kind: 'property',
        title,
        price: 100 + id * 12,
        rent: 18 + id * 3
    };
});
export const DEMO_CONFIG = {
    map: INTERNAL_TEST_MAP,
    players: [
        { id: 'p1', name: '桃桃', kind: 'human' },
        { id: 'p2', name: '阿团', kind: 'human' }
    ],
    tiles: DEMO_TILES,
    initialCash: 1800,
    bankEnabled: true,
    loanEnabled: true,
    marketEnabled: true,
    propertyVisitOnly: true,
    stockAccount: 'bank',
    maxRounds: 12,
    eventRules: { tileIds: [], bonus: 0, fee: 0 },
    cardRules: { tileIds: [], rewardCash: 80, moveBonus: 2, maxHand: 3 }
};
export function createDemoGame(seed, maxRounds = DEMO_CONFIG.maxRounds) {
    const setup = createGame(seed, { ...DEMO_CONFIG, maxRounds });
    const funded = { ...setup, players: setup.players.map(player => ({ ...player, cash: 1200, bankBalance: 600 })) };
    const started = applyAction(funded, { type: 'start_game', actorId: setup.players[0].id });
    if (!started.ok)
        throw new Error('3D 演示对局启动失败');
    return started.state;
}
function dieValueOf(result) {
    if (!result.ok)
        return null;
    const value = result.events.find(event => event.type === 'die_rolled')?.details?.value;
    return typeof value === 'number' ? value : null;
}
export function dispatchDemoAction(state, action) {
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
export function demoSeedFromSearch(search) {
    const raw = new URLSearchParams(search).get('seed');
    if (raw === null || !/^\d{1,10}$/.test(raw))
        return 20261017;
    const seed = Number(raw);
    return Number.isSafeInteger(seed) && seed <= 0xffffffff ? seed : 20261017;
}
/** Optional normal game length, kept bounded for shareable demo sessions. */
export function demoRoundsFromSearch(search) {
    const raw = new URLSearchParams(search).get('rounds');
    if (raw === null || !/^\d{1,2}$/.test(raw))
        return 12;
    const rounds = Number(raw);
    return rounds >= 1 && rounds <= 60 ? rounds : 12;
}
