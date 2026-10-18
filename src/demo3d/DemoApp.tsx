import { useCallback, useEffect, useRef, useState } from 'react';
import { netWorth, propertyVisitAvailable, type GameAction, type GameEvent, type GameState, type StockMarket } from '../core/game.js';
import { createDemoGame, dispatchDemoAction, demoSeedFromSearch, demoRoundsFromSearch } from './session.js';
import { propertyStage, rowHouses, streetForTile } from './properties.js';
import { rentCueFor, type RentCue } from './presentation.js';
import { outcomeSequence, type OutcomeCue } from './outcomes.js';
import { OutcomeOverlay } from './OutcomeOverlay.js';
import { FinancePanel, type FinanceTab } from './FinancePanel.js';
import { WorldCanvas } from './world/WorldCanvas.js';
import type { MotionCue } from './world/Mascot.js';

function describeEvents(events: readonly GameEvent[], game: GameState): string {
  if (events.some(event => event.type === 'game_finished')) return game.winnerId ? `${game.players.find(p => p.id === game.winnerId)?.name}获胜！` : '双方势均力敌，本局平局。';
  const upgraded = events.find(event => event.type === 'property_upgraded');
  if (upgraded) return `${game.tiles[Number(upgraded.details?.tileId)]?.title}：${upgraded.details?.level === 1 ? '住宅落成' : '房屋升级完成'}！本次停留的地产操作已完成。`;
  const bought = events.find(event => event.type === 'property_bought');
  if (bought) return `已买下${game.tiles[Number(bought.details?.tileId)]?.title}。下次停留这里时可以建房。`;
  const feedback: Partial<Record<GameEvent['type'], string>> = {
    bank_deposited: '已存入银行', bank_withdrawn: '已取出现金',
    loan_borrowed: '贷款已到账', loan_repaid: '已偿还贷款',
    property_mortgaged: '地产已抵押，暂停收租与建设', property_released: '已解除抵押，可以恢复收租与建设',
    stock_bought: '股票买入成功，成交款与手续费已从存款扣除', stock_sold: '股票卖出成功，净收入已存入银行'
  };
  for (const event of events) {
    const text = feedback[event.type];
    if (text) return `${text}${typeof event.details?.amount === 'number' ? ` · ¥${event.details.amount}` : ''}`;
  }
  if (events.some(event => event.type === 'property_declined')) return '保留现金，继续今天的旅程。';
  if (events.some(event => event.type === 'turn_ended')) return `轮到${game.players[game.currentPlayerIndex]?.name}了。`;
  const rent = rentCueFor(events);
  if (rent) return `支付租金 ${rent.amount} 金币`;
  const player = game.players[game.currentPlayerIndex];
  return `抵达 ${game.tiles[player.position]?.title}`;
}

type Arrival = Readonly<{ rent: RentCue | null; message: string; outcomes: readonly OutcomeCue[] }>;

export function DemoApp(): React.JSX.Element {
  const [seed] = useState(() => demoSeedFromSearch(window.location.search));
  const [roundLimit] = useState(() => demoRoundsFromSearch(window.location.search));
  const [game, setGame] = useState(() => createDemoGame(seed, roundLimit));
  const [motion, setMotion] = useState<MotionCue | null>(null);
  const [beforeTravel, setBeforeTravel] = useState<GameState | null>(null);
  const [rent, setRent] = useState<RentCue | null>(null);
  const [outcomes, setOutcomes] = useState<readonly OutcomeCue[]>([]);
  const [financeTab, setFinanceTab] = useState<FinanceTab | null>(null);
  const [marketHistory, setMarketHistory] = useState<readonly StockMarket[]>(() => game.market ? [game.market] : []);
  const pendingArrival = useRef<Arrival | null>(null);
  const [lastDie, setLastDie] = useState<number | null>(null);
  const [dieNonce, setDieNonce] = useState(0);
  const [visualTile, setVisualTile] = useState(0);
  const [followCurrent, setFollowCurrent] = useState(true);
  const [message, setMessage] = useState('现金买地盖楼，存款投资股票。每次停留只能进行一次地产操作。');
  const [reducedMotion, setReducedMotion] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    const changed = () => setReducedMotion(media.matches);
    changed();
    media.addEventListener('change', changed);
    return () => media.removeEventListener('change', changed);
  }, []);
  const outcome = motion || rent ? null : outcomes[0] ?? null;
  const busy = motion !== null || rent !== null || outcomes.length > 0;
  const shownGame = beforeTravel ?? game;
  const current = game.players[game.currentPlayerIndex];
  const currentTile = game.tiles[current.position];
  const displayTile = game.tiles[motion ? visualTile : current.position] ?? currentTile;
  const ownCurrent = currentTile.kind === 'property' && currentTile.ownerId === current.id;
  const nextCost = ownCurrent ? currentTile.upgradeCosts?.[currentTile.level ?? 0] : undefined;
  const visitAvailable = propertyVisitAvailable(game, current, current.position);
  const street = streetForTile(current.position);
  const terrace = rowHouses(game).find(row => row.tileIds.includes(current.position));
  const canFinance = !busy && game.status === 'playing' && game.phase === 'await_end_turn';

  const finishMotion = useCallback(() => {
    setMotion(null);
    setBeforeTravel(null);
    const arrival = pendingArrival.current;
    pendingArrival.current = null;
    if (arrival) {
      setRent(arrival.rent);
      setOutcomes(arrival.outcomes);
      setMessage(arrival.message);
    }
  }, []);
  const finishOutcome = useCallback(() => setOutcomes(queue => queue.slice(1)), []);

  useEffect(() => {
    if (!rent) return;
    const timer = window.setTimeout(() => setRent(null), reducedMotion ? 600 : 1900);
    return () => window.clearTimeout(timer);
  }, [rent, reducedMotion]);
  useEffect(() => {
    if (!outcome) return;
    const timer = window.setTimeout(finishOutcome, reducedMotion ? 250 : outcome.stage === 'bankrupt' ? 1800 : 2200);
    return () => window.clearTimeout(timer);
  }, [outcome, reducedMotion, finishOutcome]);

  const execute = useCallback((action: GameAction) => {
    if (busy) return;
    const actor = game.players[game.currentPlayerIndex];
    const result = dispatchDemoAction(game, action);
    if (!result.ok) {
      setMessage(result.reason === 'INSUFFICIENT_FUNDS' ? '可用余额或抵押额度不足，请检查现金、存款与持仓。' : '当前无法执行这项操作；每次停留只能对当前地块建设一次。');
      return;
    }
    setGame(result.after);
    if (result.after.market && result.after.market.round !== game.market?.round) {
      const market = result.after.market;
      setMarketHistory(history => [...history, market]);
    }
    if (action.type === 'end_turn' || action.type === 'roll') {
      setFinanceTab(null);
      if (action.type === 'end_turn') setLastDie(null);
    }
    const arrival = { rent: rentCueFor(result.events), message: describeEvents(result.events, result.after), outcomes: outcomeSequence(result.events, result.after) };
    if (action.type === 'roll' && result.dieValue !== null && result.route.length > 0) {
      const nonce = dieNonce + 1;
      setDieNonce(nonce);
      setLastDie(result.dieValue);
      setBeforeTravel(game);
      setVisualTile(actor.position);
      pendingArrival.current = arrival;
      setMessage(`${actor.name}掷出 ${result.dieValue} 点，正在前进…`);
      setMotion({ actorId: actor.id, fromTileId: actor.position, path: result.route, nonce });
    } else {
      setMessage(arrival.message);
      setOutcomes(arrival.outcomes);
    }
  }, [busy, dieNonce, game]);
  const perform = (type: 'roll' | 'buy_property' | 'decline_property' | 'end_turn' | 'upgrade_property') => execute(
    type === 'upgrade_property' ? { type, actorId: current.id, tileId: current.position } : { type, actorId: current.id }
  );
  const reset = useCallback(() => {
    const next = createDemoGame(seed, roundLimit);
    setGame(next);
    setMarketHistory(next.market ? [next.market] : []);
    setMotion(null);
    setBeforeTravel(null);
    setRent(null);
    setOutcomes([]);
    setFinanceTab(null);
    pendingArrival.current = null;
    setLastDie(null);
    setVisualTile(0);
    setMessage('新的一天开始了。现金和存款各有用途，桃桃先投骰。');
  }, [seed, roundLimit]);
  const winner = game.players.find(player => player.id === game.winnerId);

  return (
    <main className="demo-shell" data-phase={game.phase} data-busy={String(busy)} data-visual-tile={visualTile} data-outcome={outcome?.stage ?? ''}>
      <header className="top-rail">
        <div className="brand-block"><span className="brand-mark" aria-hidden="true">富</span><div><p>大富翁 · 迁移参考</p><h1>晴湾小镇 <small className="retirement-flag">待删除</small></h1></div></div>
        <div className="round-chip"><span>当前回合</span><strong>{shownGame.round} / {game.maxRounds}</strong></div>
        <button type="button" className="view-toggle" aria-pressed={!followCurrent} onClick={() => setFollowCurrent(value => !value)}>{followCurrent ? '全景视角' : '跟随角色'}</button>
      </header>
      <p className="retirement-notice" role="note">独立 demo 已标记待删除；3D 场景与金融、地产玩法正在并入主程序。正式版完成双地图、电脑、存档、离线和移动端验收后，再移除本页源码。</p>
      <nav className="finance-tools" aria-label="金融服务">
        <button type="button" disabled={!canFinance} onClick={() => setFinanceTab('bank')}>银行</button>
        <button type="button" disabled={!canFinance} onClick={() => setFinanceTab('market')}>股市</button>
        <small>{canFinance ? '落地后办理 · 股票使用存款' : '处理完停留地块后可办理'}</small>
      </nav>

      <section className="world-stage" aria-label="3D 游戏地图">
        <WorldCanvas game={shownGame} motion={motion} dieValue={lastDie} dieNonce={dieNonce}
          reducedMotion={reducedMotion} followCurrent={followCurrent} rent={rent} outcome={outcome}
          paused={financeTab !== null}
          pendingBankruptIds={outcomes.filter(cue => cue.stage === 'bankrupt' && cue.actorId).map(cue => cue.actorId!)}
          onMotionComplete={finishMotion} onActorStep={setVisualTile} />
        <div className="location-card" aria-live="polite"><span>{motion ? '正在前进' : '当前位置'}</span><strong>{displayTile.title}</strong><small>{lastDie === null ? '等待投骰' : `最近掷出 ${lastDie} 点`}</small></div>
        <div className="event-toast" role="status"><span aria-hidden="true">✦</span>{message}</div>
        {rent && <div className="rent-receipt" role="status" aria-label="租金结算"><span>租金结算 · {game.tiles[rent.tileId].title}</span><strong>{game.players.find(p => p.id === rent.fromId)?.name} <b>−¥{rent.amount}</b></strong><i aria-hidden="true">● → ● → ●</i><strong>{game.players.find(p => p.id === rent.toId)?.name} <em>+¥{rent.amount}</em></strong></div>}
        {outcome && <OutcomeOverlay game={game} cue={outcome} reducedMotion={reducedMotion} onSkip={finishOutcome} />}
      </section>

      <aside className="player-stack" aria-label="玩家资产">
        {shownGame.players.map((player, index) => (
          <article className="player-card" data-active={index === shownGame.currentPlayerIndex} data-player-id={player.id} key={player.id}>
            <span className={`avatar avatar-${index + 1}`} aria-hidden="true">{index === 0 ? '桃' : '团'}</span>
            <div><strong>{player.name}</strong><span>{player.bankrupt ? '已破产' : index === shownGame.currentPlayerIndex ? '行动中' : '等待中'}</span></div>
            <b className="player-cash"><small>现金</small>¥ {player.cash.toLocaleString('zh-CN')}</b>
            <div className="balance-row"><span className="player-deposit">存款 ¥ {(player.bankBalance ?? 0).toLocaleString('zh-CN')}</span><span className="player-loan">贷款 ¥ {(player.loanBalance ?? 0).toLocaleString('zh-CN')}</span></div>
            {rent && (player.id === rent.fromId || player.id === rent.toId) && <span className={`cash-delta ${player.id === rent.fromId ? 'debit' : 'credit'}`}>{player.id === rent.fromId ? '−' : '+'}¥{rent.amount}</span>}
          </article>
        ))}
      </aside>

      {!busy && game.status === 'playing' && game.phase === 'await_end_turn' && ownCurrent && <aside className="property-panel" aria-label="地产管理">
        <span className="property-caption">当前停留地产 · {street?.title}</span><h2>{currentTile.title}</h2>
        <div className="property-stage"><strong>{propertyStage(currentTile)}</strong><span>{currentTile.mortgaged ? '已抵押' : terrace ? `联排 ${terrace.tileIds.length} 户` : '独立地块'}</span></div>
        <p>租金 ¥{currentTile.mortgaged ? 0 : currentTile.levelRents?.[currentTile.level ?? 0]} · 同街区连续住宅可组成联排</p>
        {nextCost === undefined ? <strong className="max-level">已达最高等级</strong> : currentTile.mortgaged ? <strong className="visit-hint">请先到银行解除抵押</strong> : !visitAvailable ? <strong className="visit-hint">本次已操作，下次停留时再建设</strong> : <>
          <button type="button" className="primary-action" disabled={current.cash < nextCost} onClick={() => perform('upgrade_property')}>{(currentTile.level ?? 0) === 0 ? '建房' : '升级房屋'} · ¥{nextCost}</button>
          <small>{current.cash < nextCost ? `现金不足，需要 ¥${nextCost}` : '本次停留最多建设一次'}</small>
        </>}
      </aside>}

      {game.status === 'finished' && !busy && <section className="match-result" aria-label="对局结果">
        <span>晴湾小镇 · 本局结算</span><h2>{winner ? `${winner.name}获胜！` : '势均力敌，平局！'}</h2>
        <p>{game.events.some(event => event.type === 'player_bankrupt') ? '对手破产，最后留在小镇的玩家获胜。' : '本局轮次结束，按包含现金、存款、股票和地产并扣除贷款的净资产结算。'}</p>
        {game.players.map(player => <article key={player.id}><strong>{player.name}{player.bankrupt ? ' · 已破产' : player.id === game.winnerId ? ' · 获胜' : ''}</strong><span>现金 ¥{player.cash} · 存款 ¥{player.bankBalance ?? 0} · 贷款 ¥{player.loanBalance ?? 0}</span><b>净资产 ¥{netWorth(game, player.id).toLocaleString('zh-CN')}</b></article>)}
      </section>}

      <footer className="action-dock" aria-label="回合操作"><div className="turn-copy"><span>{current.name}的回合</span><strong>{busy ? outcome ? '正在揭晓本局结果' : rent ? '正在结算租金' : '看，角色正在穿过街区' : game.status === 'finished' ? winner ? `${winner.name}获胜！` : '本局平局' : '下一步做什么？'}</strong></div><div className="action-buttons">
        {game.phase === 'await_roll' && <button type="button" className="primary-action" disabled={busy} onClick={() => perform('roll')}><span className="dice-icon" aria-hidden="true">⚄</span>投骰前进</button>}
        {game.phase === 'await_decision' && !busy && <><button type="button" className="primary-action" disabled={current.cash < (currentTile.price ?? 0)} onClick={() => perform('buy_property')}>买下此地 · ¥{currentTile.price}</button><button type="button" className="secondary-action" onClick={() => perform('decline_property')}>暂不购买</button></>}
        {game.phase === 'await_end_turn' && !busy && <button type="button" className="primary-action" onClick={() => perform('end_turn')}>结束回合 <span aria-hidden="true">→</span></button>}
        {game.status === 'finished' && !busy && <button type="button" className="primary-action" onClick={reset}>再逛一次晴湾</button>}
      </div></footer>
      {financeTab && canFinance && <FinancePanel game={game} actorId={current.id} tab={financeTab} onTabChange={setFinanceTab} onClose={() => setFinanceTab(null)} onAction={execute} history={marketHistory} message={message} />}
    </main>
  );
}
