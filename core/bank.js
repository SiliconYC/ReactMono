import { accept, reject } from './transitions.js';
export const DEFAULT_INTEREST_BPS = 100; // 1% each completed round
export const MAX_BANK_BALANCE = 1_000_000_000_000;
export function createBank(interestBps = DEFAULT_INTEREST_BPS) {
    if (!Number.isSafeInteger(interestBps) || interestBps < 0 || interestBps > 1000)
        throw new Error('银行利率无效');
    return { version: 1, interestBps, lastInterestRound: 1 };
}
export function transferBank(state, actor, action) {
    const amount = action.amount, balance = actor.bankBalance;
    if (!state.bank || state.phase !== 'await_end_turn' || !Number.isSafeInteger(amount) || amount < 1 ||
        amount > MAX_BANK_BALANCE || balance === undefined)
        return reject(state, 'INVALID_PHASE');
    if (action.type === 'deposit_bank' ? actor.cash < amount : balance < amount)
        return reject(state, 'INSUFFICIENT_FUNDS');
    const nextCash = actor.cash + (action.type === 'deposit_bank' ? -amount : amount);
    const nextBalance = balance + (action.type === 'deposit_bank' ? amount : -amount);
    if (!Number.isSafeInteger(nextCash) || nextCash < 0 || nextCash > MAX_BANK_BALANCE ||
        !Number.isSafeInteger(nextBalance) || nextBalance < 0 || nextBalance > MAX_BANK_BALANCE)
        return reject(state, 'INVALID_PHASE');
    const type = action.type === 'deposit_bank' ? 'bank_deposited' : 'bank_withdrawn';
    return accept(state, [{ type, actorId: actor.id, details: { amount } }], {
        players: state.players.map(p => p.id === actor.id ? { ...p, cash: nextCash, bankBalance: nextBalance } : p)
    });
}
/** Cash-first debt settlement, then automatic withdrawal, before #35 land liquidation. */
export function coverRentFromBank(state, actor, due) {
    const bankBalance = actor.bankBalance ?? 0;
    const amount = state.bank ? Math.min(bankBalance, Math.max(0, due - actor.cash)) : 0;
    return { cash: actor.cash + amount, bankBalance: bankBalance - amount, amount };
}
export function settleBankRound(state, players, round) {
    const previous = state.bank;
    if (!previous || !Number.isSafeInteger(round) || round !== previous.lastInterestRound + 1)
        throw new Error('银行重复结息或轮次跳跃');
    const events = [];
    const settled = players.map(p => {
        const balance = p.bankBalance ?? 0;
        if (p.bankrupt || balance === 0)
            return p;
        const interest = Math.floor(balance * previous.interestBps / 10000);
        if (!Number.isSafeInteger(balance + interest) || balance + interest > MAX_BANK_BALANCE)
            throw new Error('银行余额超过安全范围');
        if (interest === 0)
            return p;
        events.push({ type: 'bank_interest', actorId: p.id, details: { round, amount: interest } });
        return { ...p, bankBalance: balance + interest };
    });
    return { bank: { ...previous, lastInterestRound: round }, players: settled, events };
}
