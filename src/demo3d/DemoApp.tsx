import { useCallback, useMemo, useState } from 'react';
import type { GameAction, GameEvent, GameState } from '../core/game.js';
import { createDemoGame, dispatchDemoAction } from './session.js';
import { WorldCanvas } from './world/WorldCanvas.js';
import type { MotionCue } from './world/Mascot.js';

function describeEvents(events: readonly GameEvent[], game: GameState): string {
  const rent = events.find(event => event.type === 'rent_paid');
  if (rent !== undefined) return `支付租金 ${rent.details?.amount ?? 0} 金币`;
  const landed = events.find(event => event.type === 'tile_landed');
  const player = game.players[game.currentPlayerIndex];
  const tile = game.tiles[player?.position ?? 0];
  return landed === undefined ? '行动完成' : `抵达 ${tile?.title ?? '新地点'}`;
}

export function DemoApp(): React.JSX.Element {
  const [game, setGame] = useState(() => createDemoGame(20261017));
  const [motion, setMotion] = useState<MotionCue | null>(null);
  const [busy, setBusy] = useState(false);
  const [lastDie, setLastDie] = useState<number | null>(null);
  const [dieNonce, setDieNonce] = useState(0);
  const [visualTile, setVisualTile] = useState(0);
  const [followCurrent, setFollowCurrent] = useState(true);
  const [message, setMessage] = useState('沿着环岛街区投骰前进，买下第一栋属于你的房子。');
  const reducedMotion = useMemo(
    () => typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    []
  );
  const current = game.players[game.currentPlayerIndex];
  const currentTile = game.tiles[current.position];

  const finishMotion = useCallback(() => {
    setBusy(false);
    setMotion(null);
  }, []);

  const perform = useCallback((type: GameAction['type']) => {
    if (busy) return;
    const actor = game.players[game.currentPlayerIndex];
    const action = { type, actorId: actor.id } as GameAction;
    const result = dispatchDemoAction(game, action);
    if (!result.ok) {
      setMessage(`规则拒绝了这次操作：${result.reason}`);
      return;
    }

    setGame(result.after);
    setMessage(describeEvents(result.events, result.after));
    if (type === 'roll' && result.dieValue !== null && result.route.length > 0) {
      const nonce = dieNonce + 1;
      setDieNonce(nonce);
      setLastDie(result.dieValue);
      setBusy(true);
      setVisualTile(actor.position);
      setMotion({ actorId: actor.id, fromTileId: actor.position, path: result.route, nonce });
    }
  }, [busy, dieNonce, game]);

  const reset = useCallback(() => {
    const next = createDemoGame(20261017);
    setGame(next);
    setMotion(null);
    setBusy(false);
    setLastDie(null);
    setVisualTile(0);
    setMessage('新的一天开始了。桃桃先投骰。');
  }, []);

  return (
    <main className="demo-shell" data-phase={game.phase} data-busy={String(busy)} data-visual-tile={visualTile}>
      <header className="top-rail">
        <div className="brand-block">
          <span className="brand-mark" aria-hidden="true">M</span>
          <div><p>REACTMONO · 3D VERTICAL SLICE</p><h1>晴湾小镇</h1></div>
        </div>
        <div className="round-chip"><span>当前回合</span><strong>{game.round} / {game.maxRounds}</strong></div>
        <button type="button" className="view-toggle" onClick={() => setFollowCurrent(value => !value)}>
          {followCurrent ? '全景视角' : '跟随角色'}
        </button>
      </header>

      <section className="world-stage" aria-label="3D 游戏地图">
        <WorldCanvas
          game={game}
          motion={motion}
          dieValue={lastDie}
          dieNonce={dieNonce}
          reducedMotion={reducedMotion}
          followCurrent={followCurrent}
          onMotionComplete={finishMotion}
          onActorStep={setVisualTile}
        />
        <div className="location-card" aria-live="polite">
          <span>{busy ? '正在前进' : '当前位置'}</span>
          <strong>{currentTile.title}</strong>
          <small>{lastDie === null ? '等待第一次投骰' : `最近掷出 ${lastDie} 点`}</small>
        </div>
        <div className="event-toast" role="status"><span aria-hidden="true">✦</span>{message}</div>
      </section>

      <aside className="player-stack" aria-label="玩家资产">
        {game.players.map((player, index) => (
          <article className="player-card" data-active={index === game.currentPlayerIndex} key={player.id}>
            <span className={`avatar avatar-${index + 1}`} aria-hidden="true">{index === 0 ? '桃' : '团'}</span>
            <div><strong>{player.name}</strong><span>{index === game.currentPlayerIndex ? '行动中' : '等待中'}</span></div>
            <b>¥ {player.cash.toLocaleString('zh-CN')}</b>
          </article>
        ))}
      </aside>

      <footer className="action-dock" aria-label="回合操作">
        <div className="turn-copy"><span>{current.name}的回合</span><strong>{busy ? '看，角色正在穿过街区' : '下一步做什么？'}</strong></div>
        <div className="action-buttons">
          {game.phase === 'await_roll' && (
            <button type="button" className="primary-action" disabled={busy} onClick={() => perform('roll')}>
              <span className="dice-icon" aria-hidden="true">⚄</span>投骰前进
            </button>
          )}
          {game.phase === 'await_decision' && !busy && (
            <>
              <button type="button" className="primary-action" onClick={() => perform('buy_property')}>买下此地 · ¥{currentTile.price}</button>
              <button type="button" className="secondary-action" onClick={() => perform('decline_property')}>暂不购买</button>
            </>
          )}
          {game.phase === 'await_end_turn' && !busy && (
            <button type="button" className="primary-action" onClick={() => perform('end_turn')}>结束回合 <span aria-hidden="true">→</span></button>
          )}
          {game.status === 'finished' && <button type="button" className="primary-action" onClick={reset}>再逛一次晴湾</button>}
        </div>
      </footer>
    </main>
  );
}

