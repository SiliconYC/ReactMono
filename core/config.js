export const DEFAULT_CARD_RULES = { tileIds: [6, 12, 18], rewardCash: 80, moveBonus: 2, maxHand: 3 };
export const DEFAULT_EVENT_RULES = { tileIds: [3, 9, 15, 21], bonus: 120, fee: 60 };
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
export function validateConfig(config) {
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
    const cards = config.cardRules ?? DEFAULT_CARD_RULES;
    if (![cards.rewardCash, cards.moveBonus, cards.maxHand].every(x => Number.isSafeInteger(x) && x > 0) ||
        new Set(cards.tileIds).size !== cards.tileIds.length ||
        cards.tileIds.some(i => !Number.isInteger(i) || i < 0 || (i < config.tiles.length && config.tiles[i].kind !== 'neutral')))
        throw new Error('卡片配置无效');
    const ev = config.eventRules ?? DEFAULT_EVENT_RULES;
    if (![ev.bonus, ev.fee].every(v => Number.isSafeInteger(v) && v >= 0) ||
        new Set(ev.tileIds).size !== ev.tileIds.length ||
        ev.tileIds.some(i => !Number.isInteger(i) || i < 0 || (i < config.tiles.length && config.tiles[i].kind !== 'neutral')))
        throw new Error('随机事件配置无效');
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
