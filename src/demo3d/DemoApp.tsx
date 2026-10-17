import { useCallback, useEffect, useRef, useState } from 'react';
import type { GameAction, GameEvent, GameState } from '../core/game.js';
import { createDemoGame, dispatchDemoAction } from './session.js';
import { propertyStage, rowHouses, streetForTile } from './properties.js';
import { rentCueFor, type RentCue } from './presentation.js';
import { WorldCanvas } from './world/WorldCanvas.js';
import type { MotionCue } from './world/Mascot.js';

function describeEvents(events: readonly GameEvent[], game: GameState): string {
  const upgraded = events.find(event => event.type === 'property_upgraded');
  if (upgraded) return `${game.tiles[Number(upgraded.details?.tileId)]?.title}：${upgraded.details?.level === 1 ? '住宅落成' : '房屋升级完成'}！`;
  const bought = events.find(event => event.type === 'property_bought');
  if (bought) return `已买下${game.tiles[Number(bought.details?.tileId)]?.title}，空地可以稍后建房。`;
  if (events.some(event => event.type === 'property_declined')) return '保留现金，继续今天的旅程。';
  if (events.some(event => event.type === 'turn_ended')) return `轮到${game.players[game.currentPlayerIndex]?.name}了。`;
  const rent = rentCueFor(events);
  if (rent) return `支付租金 ${rent.amount} 金币`;
  const player = game.players[game.currentPlayerIndex];
  return `抵达 ${game.tiles[player.position]?.title}`;
}

export function DemoApp(): React.JSX.Element {
  const [game, setGame] = useState(() => createDemoGame(20261017));
  const [motion, setMotion] = useState<MotionCue | null>(null);
  const [beforeTravel, setBeforeTravel] = useState<GameState | null>(null);
  const [rent, setRent] = useState<RentCue | null>(null);
  const pendingArrival = useRef<{ rent: RentCue | null; message: string } | null>(null);
  const [lastDie, setLastDie] = useState<number | null>(null);
  const [dieNonce, setDieNonce] = useState(0);
  const [visualTile, setVisualTile] = useState(0);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [followCurrent, setFollowCurrent] = useState(true);
  const [message, setMessage] = useState('投骰探索街区，买地、建房，再把住宅升级。');
  const [reducedMotion, setReducedMotion] = useState(() => window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    const changed = () => setReducedMotion(media.matches);
    changed();
    media.addEventListener('change', changed);
    return () => media.removeEventListener('change', changed);
  }, []);
  const busy = motion !== null || rent !== null;
  const shownGame = beforeTravel ?? game;
  const current = game.players[game.currentPlayerIndex];
  const currentTile = game.tiles[current.position];
  const displayTile = game.tiles[motion ? visualTile : current.position] ?? currentTile;
  const owned = game.tiles.filter(tile => tile.kind === 'property' && tile.ownerId === current.id);
  const selected = owned.find(tile => tile.id === selectedId) ?? owned[0];
  const nextCost = selected?.upgradeCosts?.[selected.level ?? 0];
  const street = selected ? streetForTile(selected.id) : undefined;
  const terrace = selected ? rowHouses(game).find(row => row.tileIds.includes(selected.id)) : undefined;

  const finishMotion = useCallback(() => {
    setMotion(null);
    setBeforeTravel(null);
    const arrival = pendingArrival.current;
    pendingArrival.current = null;
    if (arrival) {
      setRent(arrival.rent);
      setMessage(arrival.message);
    }
  }, []);

  useEffect(() => {
    if (!rent) return;
    const timer = window.setTimeout(() => setRent(null), 1900);
    return () => window.clearTimeout(timer);
  }, [rent]);

  const perform = useCallback((type: GameAction['type'], tileId?: number) => {
    if (busy) return;
    const actor = game.players[game.currentPlayerIndex];
    const result = dispatchDemoAction(game, { type, actorId: actor.id, ...(tileId === undefined ? {} : { tileId }) } as GameAction);
    if (!result.ok) {
      setMessage(result.reason === 'INSUFFICIENT_FUNDS' ? '现金不足，先保留资金吧。' : '当前无法执行这项操作。');
      return;
    }
    setGame(result.after);
    if (type === 'buy_property') setSelectedId(actor.position);
    if (type === 'end_turn') {
      setLastDie(null);
      setSelectedId(null);
    }
    if (type === 'roll' && result.dieValue !== null && result.route.length > 0) {
      const nonce = dieNonce + 1;
      setDieNonce(nonce);
      setLastDie(result.dieValue);
      setBeforeTravel(game);
      setVisualTile(actor.position);
      pendingArrival.current = { rent: rentCueFor(result.events), message: describeEvents(result.events, result.after) };
      setMessage(`${actor.name}掷出 ${result.dieValue} 点，正在前进…`);
      setMotion({ actorId: actor.id, fromTileId: actor.position, path: result.route, nonce });
    } else setMessage(describeEvents(result.events, result.after));
  }, [busy, dieNonce, game]);

  const reset = useCallback(() => {
    setGame(createDemoGame(20261017));
    setMotion(null);
    setBeforeTravel(null);
    setRent(null);
    pendingArrival.current = null;
    setLastDie(null);
    setVisualTile(0);
    setSelectedId(null);
    setMessage('新的一天开始了。桃桃先投骰。');
  }, []);
  const winner = game.players.find(player => player.id === game.winnerId);

  return (
    <main className="demo-shell" data-phase={game.phase} data-busy={String(busy)} data-visual-tile={visualTile}>
      <header className="top-rail">
        <div className="brand-block">
          <span className="brand-mark" aria-hidden="true">富</span>
          <div><p>大富翁 · 3D 体验切片</p><h1>晴湾小镇</h1></div>
        </div>
        <div className="round-chip"><span>当前回合</span><strong>{shownGame.round} / {game.maxRounds}</strong></div>
        <button type="button" className="view-toggle" aria-pressed={!followCurrent} onClick={() => setFollowCurrent(value => !value)}>
          {followCurrent ? '全景视角' : '跟随角色'}
        </button>
      </header>

      <section className="world-stage" aria-label="3D 游戏地图">
        <WorldCanvas game={shownGame} motion={motion} dieValue={lastDie} dieNonce={dieNonce}
          reducedMotion={reducedMotion} followCurrent={followCurrent} rent={rent}
          onMotionComplete={finishMotion} onActorStep={setVisualTile} />
        <div className="location-card" aria-live="polite">
          <span>{motion ? '正在前进' : '当前位置'}</span><strong>{displayTile.title}</strong>
          <small>{lastDie === null ? '等待投骰' : `最近掷出 ${lastDie} 点`}</small>
        </div>
        <div className="event-toast" role="status"><span aria-hidden="true">✦</span>{message}</div>
        {rent && (
          <div className="rent-receipt" role="status" aria-label="租金结算">
            <span>租金结算 · {game.tiles[rent.tileId].title}</span>
            <strong>{game.players.find(p => p.id === rent.fromId)?.name} <b>−¥{rent.amount}</b></strong>
            <i aria-hidden="true">● → ● → ●</i>
            <strong>{game.players.find(p => p.id === rent.toId)?.name} <em>+¥{rent.amount}</em></strong>
          </div>
        )}
      </section>

      <aside className="player-stack" aria-label="玩家资产">
        {shownGame.players.map((player, index) => (
          <article className="player-card" data-active={index === shownGame.currentPlayerIndex} data-player-id={player.id} key={player.id}>
            <span className={`avatar avatar-${index + 1}`} aria-hidden="true">{index === 0 ? '桃' : '团'}</span>
            <div><strong>{player.name}</strong><span>{player.bankrupt ? '已破产' : index === shownGame.currentPlayerIndex ? '行动中' : '等待中'}</span></div>
            <b>¥ {player.cash.toLocaleString('zh-CN')}</b>
            {rent && (player.id === rent.fromId || player.id === rent.toId) && (
              <span className={`cash-delta ${player.id === rent.fromId ? 'debit' : 'credit'}`}>
                {player.id === rent.fromId ? '−' : '+'}¥{rent.amount}
              </span>
            )}
          </article>
        ))}
      </aside>

      {!busy && game.status === 'playing' && game.phase === 'await_end_turn' && selected && (
        <aside className="property-panel" aria-label="地产管理">
          <label htmlFor="owned-lot">我的地产 · {owned.length} 块</label>
          <select id="owned-lot" value={selected.id} onChange={event => setSelectedId(Number(event.target.value))}>
            {owned.map(tile => <option value={tile.id} key={tile.id}>{tile.title} · {propertyStage(tile)}</option>)}
          </select>
          <div className="property-stage"><strong>{propertyStage(selected)}</strong><span>{street?.title}</span></div>
          <p>租金 ¥{selected.levelRents?.[selected.level ?? 0]}{terrace ? ` · 联排 ${terrace.tileIds.length} 户` : ' · 同街区连续住宅可组成联排'}</p>
          {nextCost === undefined ? <strong className="max-level">已达最高等级</strong> : (
            <button type="button" className="primary-action" disabled={current.cash < nextCost} onClick={() => perform('upgrade_property', selected.id)}>
              {(selected.level ?? 0) === 0 ? '建房' : '升级房屋'} · ¥{nextCost}
            </button>
          )}
          {nextCost !== undefined && current.cash < nextCost && <small>现金不足，需要 ¥{nextCost}</small>}
        </aside>
      )}

      <footer className="action-dock" aria-label="回合操作">
        <div className="turn-copy"><span>{current.name}的回合</span><strong>{busy ? rent ? '正在结算租金' : '看，角色正在穿过街区' : game.status === 'finished' ? `${winner?.name ?? '本局'}获胜！` : '下一步做什么？'}</strong></div>
        <div className="action-buttons">
          {game.phase === 'await_roll' && <button type="button" className="primary-action" disabled={busy} onClick={() => perform('roll')}><span className="dice-icon" aria-hidden="true">⚄</span>投骰前进</button>}
          {game.phase === 'await_decision' && !busy && <>
            <button type="button" className="primary-action" disabled={current.cash < (currentTile.price ?? 0)} onClick={() => perform('buy_property')}>买下此地 · ¥{currentTile.price}</button>
            <button type="button" className="secondary-action" onClick={() => perform('decline_property')}>暂不购买</button>
          </>}
          {game.phase === 'await_end_turn' && !busy && <button type="button" className="primary-action" onClick={() => perform('end_turn')}>结束回合 <span aria-hidden="true">→</span></button>}
          {game.status === 'finished' && !busy && <button type="button" className="primary-action" onClick={reset}>再逛一次晴湾</button>}
        </div>
      </footer>
    </main>
  );
}
