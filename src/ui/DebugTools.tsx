import * as React from 'react';
import type { GameState } from '../core/types.js';
import { MAX_DEBUG_CASH, MAX_DEBUG_ROUNDS } from '../core/debug-tools.js';
import { syncDebugCashInputs } from './debug-cash-inputs.js';
import './debug-tools.css';

interface DebugToolsProps {
  readonly game: GameState;
  readonly busy: boolean;
  readonly message: string;
  readonly onCash: (playerId: string, cash: number) => void;
  readonly onSimulate: (rounds: number) => void;
  readonly onCancel: () => void;
}
export function DebugTools({ game, busy, message, onCash, onSimulate, onCancel }: DebugToolsProps): React.JSX.Element {
  const [cash, setCash] = React.useState<Record<string, string>>({});
  const [rounds, setRounds] = React.useState('10');
  const [error, setError] = React.useState('');
  const previousPlayers = React.useRef<GameState['players'] | null>(null);
  React.useEffect(() => {
    const previous = previousPlayers.current;
    previousPlayers.current = game.players;
    setCash(drafts => syncDebugCashInputs(drafts, previous, game.players));
  }, [game]);
  const playing = game.status === 'playing';
  const parseInteger = (input: string, max: number, min = 0): number => {
    const value = Number(input.trim());
    if (!/^\d+$/.test(input.trim()) || !Number.isSafeInteger(value) || value < min || value > max)
      throw new Error(`请输入 ${min} 至 ${max} 的整数`);
    return value;
  };
  const perform = (action: () => void): void => {
    setError('');
    try { action(); } catch (error) { setError(error instanceof Error ? error.message : String(error)); }
  };
  return <div className="debug-tools" aria-busy={busy}>
    <p>直接修改当前对局。仅在本机运行，修改后会自动保存。</p>
    {!playing && <p className="debug-note">对局已结束，调试工具仅供查看。请新开一局以继续调试。</p>}
    <section aria-labelledby="debug-cash-title">
      <h3 id="debug-cash-title">设置玩家现金</h3>
      <p className="debug-note">只改现金，不改银行存款。破产玩家不会因此复活。</p>
      <div className="debug-cash-list">{game.players.map(player => <div className="debug-cash-row" key={player.id}>
        <label htmlFor={`debug-cash-${player.id}`}>{player.name}<small>{player.bankrupt ? '已破产' : player.kind === 'computer' ? '电脑' : '真人'} · 存款 {(player.bankBalance ?? 0).toLocaleString('zh-CN')}</small></label>
        <input id={`debug-cash-${player.id}`} type="text" inputMode="numeric" value={cash[player.id] ?? String(player.cash)} disabled={busy || !playing} onChange={event => setCash({ ...cash, [player.id]: event.target.value })} />
        <button disabled={busy || !playing} onClick={() => perform(() => onCash(player.id, parseInteger(cash[player.id] ?? String(player.cash), MAX_DEBUG_CASH)))}>设置</button>
      </div>)}</div>
    </section>
    <section aria-labelledby="debug-rounds-title">
      <h3 id="debug-rounds-title">后台批量推进</h3>
      <p className="debug-note">从当前阶段继续，真人暂按基础策略操作，玩家身份保持不变。推进到轮次增加指定数值时停止；到达原定 {game.maxRounds} 轮上限或提前分出胜负时结束。期间跳过掷骰、移动和建设演出。</p>
      <form className="debug-rounds-form" onSubmit={event => { event.preventDefault(); if (!busy && playing) perform(() => onSimulate(parseInteger(rounds, MAX_DEBUG_ROUNDS, 1))); }}>
        <label htmlFor="debug-rounds">推进轮数</label>
        <input id="debug-rounds" type="text" inputMode="numeric" value={rounds} disabled={busy || !playing} onChange={event => setRounds(event.target.value)} />
        <button type="submit" className="primary-btn" disabled={busy || !playing}>{busy ? '正在后台模拟…' : '一键模拟'}</button>
      </form>
      {busy && <p className="debug-note">完成后一次性更新画面。关闭弹窗或取消会保留模拟前的对局。<button onClick={onCancel}>取消模拟</button></p>}
    </section>
    <p className="debug-result" role="status" aria-live="polite">{error || message}</p>
  </div>;
}
