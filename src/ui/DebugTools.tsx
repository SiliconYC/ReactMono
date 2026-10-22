import * as React from 'react';
import type { GameState } from '../core/types.js';
import { MAX_DEBUG_CASH, MAX_DEBUG_ROUNDS, type DebugSimulationSetup } from '../core/debug-tools.js';
import { syncDebugCashInputs } from './debug-cash-inputs.js';
import './debug-tools.css';

interface DebugToolsProps {
  readonly game: GameState;
  readonly busy: boolean;
  readonly message: string;
  readonly onCash: (playerId: string, cash: number) => void;
  readonly onSimulate: (rounds: number, setup: DebugSimulationSetup) => void;
  readonly onCancel: () => void;
}
export function DebugTools({ game, busy, message, onCash, onSimulate, onCancel }: DebugToolsProps): React.JSX.Element {
  const [cash, setCash] = React.useState<Record<string, string>>({});
  const [rounds, setRounds] = React.useState('10');
  const [error, setError] = React.useState('');
  const [endCondition,setEndCondition] = React.useState<'bankruptcy'|'round_limit'>(game.endCondition??'round_limit');
  const previousPlayers = React.useRef<GameState['players'] | null>(null);
  React.useEffect(() => {
    const previous = previousPlayers.current;
    previousPlayers.current = game.players;
    setCash(drafts => syncDebugCashInputs(drafts, previous, game.players));
  }, [game]);
  React.useEffect(()=>setEndCondition(game.endCondition??'round_limit'),[game.endCondition]);
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
      <p className="debug-note">只改现金，不改银行存款。可逐人设置；一键模拟也会一起应用当前输入，取消或失败则不应用。破产玩家不会复活。</p>
      <div className="debug-cash-list">{game.players.map(player => <div className="debug-cash-row" key={player.id}>
        <label htmlFor={`debug-cash-${player.id}`}>{player.name}<small>{player.bankrupt ? '已破产' : player.kind === 'computer' ? '电脑' : '真人'} · 已生效现金 {player.cash.toLocaleString('zh-CN')} · 存款 {(player.bankBalance ?? 0).toLocaleString('zh-CN')}</small></label>
        <input id={`debug-cash-${player.id}`} type="text" inputMode="numeric" value={cash[player.id] ?? String(player.cash)} disabled={busy || !playing} onChange={event => setCash({ ...cash, [player.id]: event.target.value })} />
        <button disabled={busy || !playing} onClick={() => perform(() => onCash(player.id, parseInteger(cash[player.id] ?? String(player.cash), MAX_DEBUG_CASH)))}>设置</button>
      </div>)}</div>
    </section>
    <section aria-labelledby="debug-rounds-title">
      <h3 id="debug-rounds-title">后台批量推进</h3>
      <p className="debug-note">从当前阶段推进指定轮数，分出胜负时提前停止。默认统一采用平衡策略，已选电脑风格保留，玩家身份不变，完成后直接显示结果。</p>
      <label>模拟结束方式<select aria-label="模拟结束方式" value={endCondition} disabled={busy||!playing} onChange={event=>setEndCondition(event.target.value as 'bankruptcy'|'round_limit')}>
        <option value="bankruptcy">破产决胜 · 不限轮数</option>
        <option value="round_limit" disabled={game.round>game.maxRounds}>限轮结算 · {game.maxRounds} 轮上限</option>
      </select></label>
      {endCondition==='round_limit' && <p className="debug-note">本局最多到第 {game.maxRounds} 轮。要观察更长对局，请选择破产决胜。</p>}
      <p className="debug-note">相同局面重复模拟会得到相同结果。比较多局时，请在新局准备中使用不同的对局种子。</p>
      <form className="debug-rounds-form" onSubmit={event => { event.preventDefault(); if (!busy && playing) perform(() => {
        const count=parseInteger(rounds,MAX_DEBUG_ROUNDS,1);
        const cashById=Object.fromEntries(game.players.flatMap(player=>{
          const draft=cash[player.id]??String(player.cash);
          return draft===String(player.cash)?[]:[[player.id,parseInteger(draft,MAX_DEBUG_CASH)]];
        }));
        onSimulate(count,{cashById,endCondition});
      }); }}>
        <label htmlFor="debug-rounds">推进轮数</label>
        <input id="debug-rounds" type="text" inputMode="numeric" value={rounds} disabled={busy || !playing} onChange={event => setRounds(event.target.value)} />
        <button type="submit" className="primary-btn" disabled={busy || !playing}>{busy ? '正在后台模拟…' : '一键模拟'}</button>
      </form>
      {busy && <p className="debug-note">完成后一次性更新画面。关闭弹窗或取消会保留模拟前的对局。<button onClick={onCancel}>取消模拟</button></p>}
    </section>
    <p className="debug-result" role="status" aria-live="polite">{error || message}</p>
  </div>;
}
