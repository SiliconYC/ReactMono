import { useEffect, useId, useRef, useState } from 'react';
import {
  STOCKS, MAX_SHARES, STOCK_FEE_BPS, stockFee, loanLimit, netWorth,
  type GameState, type GameAction, type StockMarket, type StockId,
} from '../core/game.js';
import { MAX_BANK_BALANCE } from '../core/bank.js';
import './finance.css';

export type FinanceTab = 'bank' | 'market';

interface FinancePanelProps {
  game: GameState;
  actorId: string;
  tab: FinanceTab;
  onTabChange: (tab: FinanceTab) => void;
  onClose: () => void;
  onAction: (action: GameAction) => void;
  history?: readonly StockMarket[];
  disabled?: boolean;
  message?: string;
}

const money = (value: number) => value.toLocaleString('zh-CN');
const signed = (value: number) => `${value > 0 ? '+' : ''}${money(value)}`;
function positiveInteger(value: string): number | null {
  if (!/^\d+$/.test(value)) return null;
  const amount = Number(value);
  return Number.isSafeInteger(amount) && amount > 0 ? amount : null;
}

function AmountInput({ id, label, value, onChange, max, unit = '元' }: {
  id: string; label: string; value: string; onChange: (value: string) => void;
  max: number; unit?: string;
}) {
  const amount = positiveInteger(value);
  const invalid = value !== '' && (amount === null || amount > max);
  return <div className="finance-amount">
    <label htmlFor={id}>{label}</label>
    <div className="finance-input-wrap">
      <input id={id} type="text" inputMode="numeric" pattern="[0-9]*" autoComplete="off"
        value={value} onChange={event => onChange(event.target.value)}
        aria-invalid={invalid} aria-describedby={`${id}-hint`} />
      <span>{unit}</span>
    </div>
    <small id={`${id}-hint`}>{invalid ? '请输入可用范围内的正整数。' : `最多 ${money(max)} ${unit}，仅限正整数。`}</small>
  </div>;
}

function PriceChart({ stockId, snapshots, name }: {
  stockId: StockId; snapshots: readonly StockMarket[]; name: string;
}) {
  if (snapshots.length < 2) return <p className="finance-chart-empty">完成一轮后显示价格走势</p>;
  const values = snapshots.map(snapshot => snapshot.prices[stockId]);
  const low = Math.min(...values), high = Math.max(...values);
  const points = values.map((value, index) =>
    `${8 + index / (values.length - 1) * 304},${62 - (value - low) / Math.max(1, high - low) * 46}`
  ).join(' ');
  return <figure className="finance-chart">
    <svg viewBox="0 0 320 76" role="img" aria-label={`${name}第${snapshots[0].round}至${snapshots.at(-1)!.round}轮价格走势，最低${low}元，最高${high}元`}>
      <path d="M8 64H312" stroke="currentColor" opacity="0.15" />
      <polyline points={points} fill="none" stroke="currentColor" strokeWidth="3" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
    <figcaption><span>第 {snapshots[0].round} 轮</span><span>第 {snapshots.at(-1)!.round} 轮</span></figcaption>
  </figure>;
}

export function FinancePanel({ game, actorId, tab, onTabChange, onClose, onAction, history = [], disabled = false, message }: FinancePanelProps) {
  const id = useId();
  const dialogRef = useRef<HTMLDivElement>(null);
  const closeRef = useRef(onClose);
  closeRef.current = onClose;
  const [depositText, setDepositText] = useState('100');
  const [withdrawText, setWithdrawText] = useState('100');
  const [borrowText, setBorrowText] = useState('100');
  const [repayText, setRepayText] = useState('100');
  const [selectedTileId, setSelectedTileId] = useState<number | null>(null);
  const [stockId, setStockId] = useState<StockId>(STOCKS[0].id);
  const [quantityText, setQuantityText] = useState('1');
  const player = game.players.find(candidate => candidate.id === actorId);
  const locked = disabled || game.status !== 'playing' || game.phase !== 'await_end_turn'
    || game.players[game.currentPlayerIndex]?.id !== actorId || !player || player.bankrupt;

  useEffect(() => {
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const dialog = dialogRef.current;
    if (!dialog) return;
    const focusable = () => Array.from(dialog.querySelectorAll<HTMLElement>(
      'button:not(:disabled), input:not(:disabled), select:not(:disabled), [tabindex="0"]'
    )).filter(element => !element.closest('fieldset:disabled') && element.getClientRects().length > 0);
    dialog.focus();
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        event.stopPropagation();
        closeRef.current();
      }
      if (event.key !== 'Tab') return;
      const items = focusable(), first = items[0], last = items.at(-1);
      if (!first) { event.preventDefault(); dialog.focus(); return; }
      if (event.shiftKey && (document.activeElement === first || document.activeElement === dialog)) {
        event.preventDefault(); last?.focus();
      } else if (!event.shiftKey && (document.activeElement === last || document.activeElement === dialog)) {
        event.preventDefault(); first.focus();
      }
    };
    const onFocus = (event: FocusEvent) => {
      if (event.target instanceof Node && !dialog.contains(event.target)) dialog.focus();
    };
    document.addEventListener('keydown', onKeyDown, true);
    document.addEventListener('focusin', onFocus);
    return () => {
      document.removeEventListener('keydown', onKeyDown, true);
      document.removeEventListener('focusin', onFocus);
      if (previous?.isConnected) previous.focus();
    };
  }, []);

  const dispatch = (action: GameAction) => {
    if (!locked && action.actorId === actorId) onAction(action);
  };
  const cash = player?.cash ?? 0, balance = player?.bankBalance ?? 0, debt = player?.loanBalance ?? 0;
  const creditLimit = loanLimit(game, actorId), availableCredit = Math.max(0, creditLimit - debt);
  const owned = game.tiles.filter(tile => tile.kind === 'property' && tile.ownerId === actorId);
  const selectedTile = owned.find(tile => tile.id === selectedTileId) ?? owned[0];
  const pledgedLimit = selectedTile ? loanLimit({ ...game, tiles: game.tiles.map(tile => tile.id === selectedTile.id ? { ...tile, mortgaged: true } : tile) }, actorId) : creditLimit;
  const canMortgage = !!selectedTile && !selectedTile.mortgaged && pledgedLimit <= MAX_BANK_BALANCE;
  const canRelease = !!selectedTile?.mortgaged && debt <= loanLimit(game, actorId, selectedTile.id);
  const depositMax = Math.max(0, Math.min(cash, MAX_BANK_BALANCE - balance));
  const withdrawMax = Math.max(0, Math.min(balance, MAX_BANK_BALANCE - cash));
  const borrowMax = Math.max(0, Math.min(availableCredit, MAX_BANK_BALANCE - cash));
  const repayMax = Math.max(0, Math.min(cash, debt));
  const deposit = positiveInteger(depositText), withdrawal = positiveInteger(withdrawText);
  const borrowing = positiveInteger(borrowText), repayment = positiveInteger(repayText);
  const validAmount = (value: number | null, max: number): value is number => value !== null && value <= max;
  const stock = STOCKS.find(candidate => candidate.id === stockId)!;
  const quote = game.market?.prices[stockId] ?? 0;
  const lot = player?.holdings?.[stockId];
  const quantity = positiveInteger(quantityText);
  const gross = quantity === null ? 0 : quantity * quote;
  const validTrade = quantity !== null && quantity <= MAX_SHARES && quote > 0
    && Number.isSafeInteger(gross) && gross > 0 && gross <= MAX_BANK_BALANCE;
  const fee = validTrade ? stockFee(gross) : 0;
  const buyCost = gross + fee, sellProceeds = gross - fee;
  const bankMarket = !!game.market && !!game.bank && game.stockAccount === 'bank';
  const canBuy = bankMarket && validTrade && buyCost <= balance
    && (lot?.quantity ?? 0) + (quantity ?? 0) <= MAX_SHARES
    && (lot?.costBasis ?? 0) + buyCost <= MAX_BANK_BALANCE;
  const canSell = bankMarket && validTrade && (quantity ?? 0) <= (lot?.quantity ?? 0)
    && balance + sellProceeds <= MAX_BANK_BALANCE;
  // One snapshot per round, ending at the live quotation; never invent missing prices.
  const snapshots = Array.from(new Map([...history.filter(snapshot => snapshot.round <= (game.market?.round ?? 0)),
    ...(game.market ? [game.market] : [])].map(snapshot => [snapshot.round, snapshot])).values())
    .sort((left, right) => left.round - right.round).slice(-20);
  const previousQuote = snapshots.filter(snapshot => snapshot.round < (game.market?.round ?? 0)).at(-1);
  const quoteChange = (symbol: typeof STOCKS[number]) => {
    const current = game.market?.prices[symbol.id] ?? symbol.initialPrice;
    const previous = previousQuote?.prices[symbol.id] ?? (game.market?.round === 1 ? symbol.initialPrice : null);
    return previous === null ? null : { amount: current - previous, percent: (current - previous) / previous * 100 };
  };
  const holdingsValue = STOCKS.reduce((sum, item) => sum + (player?.holdings?.[item.id]?.quantity ?? 0) * (game.market?.prices[item.id] ?? 0), 0);

  return <div className="finance-overlay" onClick={event => { if (event.target === event.currentTarget) onClose(); }}>
    <div className="finance-dialog" ref={dialogRef} role="dialog" aria-label="银行与股市" aria-modal="true" aria-describedby={`${id}-intro`} tabIndex={-1}>
      <header className="finance-header">
        <div><p>晴湾小镇 · 第 {game.round} 轮</p><h2>银行与股市</h2></div>
        <button type="button" className="finance-close" onClick={onClose} aria-label="关闭银行与股市">×</button>
      </header>
      <p className="finance-intro" id={`${id}-intro`}>{player?.name ?? '当前玩家'}的资金管理 · 所有金额均为游戏币</p>
      <div className="finance-tabs" role="tablist" aria-label="资金管理">
        {(['bank', 'market'] as const).map(value => <button key={value} id={`${id}-${value}-tab`} type="button" role="tab"
          aria-selected={tab === value} aria-controls={`${id}-${value}-panel`} tabIndex={tab === value ? 0 : -1}
          onClick={() => onTabChange(value)} onKeyDown={event => {
            if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
            event.preventDefault();
            const next = event.key === 'Home' ? 'bank' : event.key === 'End' ? 'market' : value === 'bank' ? 'market' : 'bank';
            onTabChange(next);
            document.getElementById(`${id}-${next}-tab`)?.focus();
          }}>{value === 'bank' ? '银行' : '股市'}</button>)}
      </div>
      <div className="finance-scroll">
        {message && <p className="finance-feedback" role="status" aria-live="polite">{message}</p>}
        {locked && <p className="finance-warning" role="status">当前无法交易，请在你的回合行动结束后操作。</p>}
        <dl className="finance-balances" aria-live="polite">
          <div><dt>随身现金</dt><dd>{money(cash)}<small>元</small></dd></div>
          <div><dt>银行存款</dt><dd>{money(balance)}<small>元</small></dd></div>
          <div><dt>贷款欠款</dt><dd className={debt > 0 ? 'finance-negative' : ''}>{money(debt)}<small>元</small></dd></div>
          <div><dt>净资产</dt><dd>{money(player ? netWorth(game, actorId) : 0)}<small>元</small></dd></div>
        </dl>
        {tab === 'bank' ? <section role="tabpanel" id={`${id}-bank-panel`} aria-labelledby={`${id}-bank-tab`}>
          <div className="finance-section-heading"><h3>现金与存款</h3><span>每轮存款利息 {(game.bank?.interestBps ?? 100) / 100}%</span></div>
          <p className="finance-note">现金用于买地、建设与还款；买股使用银行存款。租金不足时会自动提取存款。</p>
          {!game.bank && <p className="finance-warning">本局未启用银行。</p>}
          <fieldset className="finance-grid" disabled={locked || !game.bank}>
            <form className="finance-card" onSubmit={event => { event.preventDefault(); if (validAmount(deposit, depositMax)) dispatch({ type: 'deposit_bank', actorId, amount: deposit }); }}>
              <AmountInput id={`${id}-deposit`} label="存入银行" value={depositText} onChange={setDepositText} max={depositMax} />
              <button className="finance-primary" disabled={!validAmount(deposit, depositMax)}>存款</button>
            </form>
            <form className="finance-card" onSubmit={event => { event.preventDefault(); if (validAmount(withdrawal, withdrawMax)) dispatch({ type: 'withdraw_bank', actorId, amount: withdrawal }); }}>
              <AmountInput id={`${id}-withdraw`} label="取出现金" value={withdrawText} onChange={setWithdrawText} max={withdrawMax} />
              <button className="finance-secondary" disabled={!validAmount(withdrawal, withdrawMax)}>取款</button>
            </form>
          </fieldset>
          <div className="finance-section-heading"><h3>地产抵押贷款</h3><span>每轮贷款利息 {(game.loan?.interestBps ?? 200) / 100}%</span></div>
          <p className="finance-note">抵押仅增加额度，申请贷款后现金到账。抵押地产不收租、不可建设；解押后恢复。利息每轮先扣现金，再扣存款；不足部分计入欠款，超出额度将收回抵押地产。</p>
          {!game.loan && <p className="finance-warning">本局未启用抵押贷款。</p>}
          <fieldset className="finance-loan" disabled={locked || !game.loan}>
            <div className="finance-card finance-collateral">
              <label htmlFor={`${id}-collateral`}>选择自有地产</label>
              <select id={`${id}-collateral`} value={selectedTile?.id ?? ''} disabled={owned.length === 0}
                onChange={event => setSelectedTileId(Number(event.target.value))}>
                {owned.length === 0 && <option value="">暂无自有地产</option>}
                {owned.map(tile => <option key={tile.id} value={tile.id}>{tile.title} · {tile.mortgaged ? '已抵押' : '未抵押'}</option>)}
              </select>
              <p>{selectedTile ? selectedTile.mortgaged ? `解押后总额度 ${money(loanLimit(game, actorId, selectedTile.id))} 元` : `抵押可增加 ${money(pledgedLimit - creditLimit)} 元额度` : '购买地产后即可在此申请抵押。'}</p>
              <div className="finance-button-row">
                <button type="button" className="finance-secondary" disabled={!canMortgage} onClick={() => { if (selectedTile && canMortgage) dispatch({ type: 'mortgage_property', actorId, tileId: selectedTile.id }); }}>抵押地产</button>
                <button type="button" className="finance-secondary" disabled={!canRelease} onClick={() => { if (selectedTile && canRelease) dispatch({ type: 'release_mortgage', actorId, tileId: selectedTile.id }); }}>解除抵押</button>
              </div>
              {selectedTile?.mortgaged && !canRelease && <small className="finance-negative">欠款超过解押后的额度，请先还款。</small>}
            </div>
            <p className="finance-credit">抵押总额度 <b>{money(creditLimit)}</b> 元 <span>·</span> 还可贷款 <b>{money(availableCredit)}</b> 元</p>
            <div className="finance-grid">
              <form className="finance-card" onSubmit={event => { event.preventDefault(); if (validAmount(borrowing, borrowMax)) dispatch({ type: 'borrow_loan', actorId, amount: borrowing }); }}>
                <AmountInput id={`${id}-borrow`} label="申请贷款，转入现金" value={borrowText} onChange={setBorrowText} max={borrowMax} />
                <button className="finance-primary" disabled={!validAmount(borrowing, borrowMax)}>申请贷款</button>
              </form>
              <form className="finance-card" onSubmit={event => { event.preventDefault(); if (validAmount(repayment, repayMax)) dispatch({ type: 'repay_loan', actorId, amount: repayment }); }}>
                <AmountInput id={`${id}-repay`} label="使用现金还款" value={repayText} onChange={setRepayText} max={repayMax} />
                <button className="finance-secondary" disabled={!validAmount(repayment, repayMax)}>偿还贷款</button>
              </form>
            </div>
          </fieldset>
        </section> : <section role="tabpanel" id={`${id}-market-panel`} aria-labelledby={`${id}-market-tab`}>
          <div className="finance-section-heading"><h3>街区证券交易所</h3><span>持仓市值 {money(holdingsValue)} 元</span></div>
          <p className="finance-note">五家虚构公司，每轮更新行情。买股扣存款，卖股回存款；每笔手续费 {STOCK_FEE_BPS / 100}%，向上取整且至少 1 元。盈亏随行情变化。</p>
          {!bankMarket && <p className="finance-warning">本局未启用存款证券交易。</p>}
          <div className="finance-stock-list" aria-label="选择股票">
            {STOCKS.map(company => {
              const change = quoteChange(company), holding = player?.holdings?.[company.id];
              return <button key={company.id} type="button" className="finance-stock" aria-pressed={stockId === company.id} onClick={() => setStockId(company.id)}>
                <strong>{company.name}</strong>
                <b>{game.market ? money(game.market.prices[company.id]) : '—'}<small> 元</small></b>
                <span className={change && change.amount < 0 ? 'finance-negative' : 'finance-positive'}>{change ? `${signed(change.amount)}（${change.percent > 0 ? '+' : ''}${change.percent.toFixed(1)}%）` : '暂无上轮行情'}</span>
                <small>持有 {money(holding?.quantity ?? 0)} 股</small>
              </button>;
            })}
          </div>
          <div className="finance-stock-detail">
            <div className="finance-section-heading"><h3>{stock.name}</h3><span>第 {game.market?.round ?? game.round} 轮现价 {money(quote)} 元</span></div>
            <PriceChart stockId={stockId} snapshots={snapshots} name={stock.name} />
            <dl className="finance-position">
              <div><dt>持仓</dt><dd>{money(lot?.quantity ?? 0)} 股</dd></div>
              <div><dt>成本（含买入费）</dt><dd>{money(lot?.costBasis ?? 0)} 元</dd></div>
              <div><dt>当前市值</dt><dd>{money((lot?.quantity ?? 0) * quote)} 元</dd></div>
              <div><dt>浮动盈亏（未扣卖出费）</dt><dd className={(lot?.quantity ?? 0) * quote - (lot?.costBasis ?? 0) < 0 ? 'finance-negative' : 'finance-positive'}>{signed((lot?.quantity ?? 0) * quote - (lot?.costBasis ?? 0))} 元</dd></div>
            </dl>
            <fieldset className="finance-order" disabled={locked || !bankMarket}>
              <AmountInput id={`${id}-shares`} label={`${stock.name}交易数量`} value={quantityText} onChange={setQuantityText} max={MAX_SHARES} unit="股" />
              <dl className="finance-order-summary" aria-live="polite">
                <div><dt>交易金额</dt><dd>{validTrade ? money(gross) : '—'} 元</dd></div>
                <div><dt>本笔手续费</dt><dd>{validTrade ? money(fee) : '—'} 元</dd></div>
                <div><dt>买入需存款</dt><dd>{validTrade ? money(buyCost) : '—'} 元</dd></div>
                <div><dt>卖出回存款</dt><dd>{validTrade ? money(sellProceeds) : '—'} 元</dd></div>
              </dl>
              <div className="finance-button-row">
                <button type="button" className="finance-primary" disabled={!canBuy} onClick={() => { if (canBuy && quantity !== null) dispatch({ type: 'buy_stock', actorId, stockId, quantity }); }}>买入{stock.name}</button>
                <button type="button" className="finance-secondary" disabled={!canSell} onClick={() => { if (canSell && quantity !== null) dispatch({ type: 'sell_stock', actorId, stockId, quantity }); }}>卖出{stock.name}</button>
              </div>
              {validTrade && buyCost > balance && <p className="finance-note">买入所需存款不足，可到银行先存款。</p>}
              {validTrade && (quantity ?? 0) > (lot?.quantity ?? 0) && <p className="finance-note">卖出数量不能超过当前持仓。</p>}
            </fieldset>
          </div>
        </section>}
      </div>
      <footer className="finance-footer">交易不会结束回合，完成后关闭面板继续游戏。</footer>
    </div>
  </div>;
}
