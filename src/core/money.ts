import type { GameState } from './types.js';
import { quoteMarket } from './market.js';

export const MAX_BANK_BALANCE = 1_000_000_000_000;

export function checkedMoneyAdd(left: number, right: number): number {
  const result = left + right;
  if (!Number.isSafeInteger(left) || !Number.isSafeInteger(right) || !Number.isSafeInteger(result))
    throw new Error('金额运算超出安全整数范围');
  return result;
}

/** 现金允许玩家钱包合流；限制总毛资产可同时保证个人与全局净资产的精度。 */
export function assertMoneyState(state: Pick<GameState, 'players' | 'tiles' | 'market'>): void {
  let assets = 0;
  let debts = 0;
  const owners = new Set(state.players.map(p => p.id));
  const addAsset = (amount: number): void => {
    if (!Number.isSafeInteger(amount) || amount < 0) throw new Error('资产金额超出安全整数范围');
    assets = checkedMoneyAdd(assets, amount);
  };
  for (const player of state.players) {
    addAsset(player.cash);
    const balance = player.bankBalance ?? 0;
    const debt = player.loanBalance ?? 0;
    if (!Number.isSafeInteger(balance) || balance < 0 || balance > MAX_BANK_BALANCE ||
        !Number.isSafeInteger(debt) || debt < 0 || debt > MAX_BANK_BALANCE)
      throw new Error('银行存款或贷款超出安全范围');
    addAsset(balance);
    debts = checkedMoneyAdd(debts, debt);
    if (state.market) for (const [id, lot] of Object.entries(player.holdings ?? {}))
      addAsset(lot.quantity * quoteMarket(state.market, id));
  }
  for (const tile of state.tiles) {
    if (tile.kind !== 'property' || tile.ownerId === null || !owners.has(tile.ownerId)) continue;
    addAsset(tile.price ?? 0);
    for (const cost of (tile.upgradeCosts ?? []).slice(0, tile.level ?? 0)) addAsset(cost);
  }
  checkedMoneyAdd(assets, -debts);
}
