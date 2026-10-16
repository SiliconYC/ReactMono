import { DEFAULT_CARD_RULES } from './config.js';
import { accept, reject } from './transitions.js';
const CLASSIC = ['reward', 'stride'];
const STRATEGY = ['remote', 'roadblock', 'rent_free'];
export const CARD_NAMES = {
    reward: '奖励卡', stride: '步数卡', remote: '遥控骰子', roadblock: '路障', rent_free: '免租卡'
};
/** The hand limit counts all existing and newly acquired cards. */
export function handSize(cards) {
    return (cards?.reward ?? 0) + (cards?.stride ?? 0) + (cards?.remote ?? 0) + (cards?.roadblock ?? 0) + (cards?.rent_free ?? 0);
}
export function useCard(state, actor, action) {
    if (state.phase !== 'await_roll' || (action.targetId !== undefined && action.targetId !== actor.id) ||
        ![...CLASSIC, ...(state.strategyEnabled === true ? STRATEGY : [])].includes(action.cardType))
        return reject(state, 'INVALID_PHASE');
    const held = actor.cards ?? { reward: 0, stride: 0 };
    if ((held[action.cardType] ?? 0) < 1)
        return reject(state, 'INVALID_PHASE');
    const rules = state.cardRules ?? DEFAULT_CARD_RULES;
    let extra = {};
    if (action.cardType === 'stride') {
        if ((state.pendingMoveBonus ?? 0) > 0 || action.tileId !== undefined || action.dieValue !== undefined)
            return reject(state, 'INVALID_PHASE');
        extra = { pendingMoveBonus: rules.moveBonus };
    }
    else if (action.cardType === 'remote') {
        if ((state.pendingDie ?? 0) !== 0 || !Number.isInteger(action.dieValue) || action.dieValue < 1 ||
            action.dieValue > 6 || action.tileId !== undefined)
            return reject(state, 'INVALID_PHASE');
        extra = { pendingDie: action.dieValue };
    }
    else if (action.cardType === 'roadblock') {
        const tileId = action.tileId;
        if (!Number.isInteger(tileId) || tileId === 0 || tileId === actor.position ||
            !state.map.route.includes(tileId) || state.players.some(p => !p.bankrupt && p.position === tileId) ||
            state.roadblocks?.some(b => b.tileId === tileId) || action.dieValue !== undefined)
            return reject(state, 'INVALID_PHASE');
        extra = { roadblocks: [...(state.roadblocks ?? []), { tileId: tileId, ownerId: actor.id, expiresRound: state.round + 2 }] };
    }
    else if (action.cardType === 'rent_free') {
        if (state.pendingRentWaiver === true || action.tileId !== undefined || action.dieValue !== undefined)
            return reject(state, 'INVALID_PHASE');
        extra = { pendingRentWaiver: true };
    }
    else if (action.tileId !== undefined || action.dieValue !== undefined)
        return reject(state, 'INVALID_PHASE');
    const reward = action.cardType === 'reward' ? rules.rewardCash : 0;
    return accept(state, [{ type: 'card_used', actorId: actor.id, details: {
                cardType: action.cardType, amount: reward, moveBonus: action.cardType === 'stride' ? rules.moveBonus : 0,
                ...(action.cardType === 'remote' ? { dieValue: action.dieValue } : {}),
                ...(action.cardType === 'roadblock' ? { tileId: action.tileId } : {})
            } }], {
        players: state.players.map(p => p.id === actor.id ? { ...p, cash: p.cash + reward,
            cards: { ...held, [action.cardType]: (held[action.cardType] ?? 0) - 1 } } : p),
        ...extra
    });
}
