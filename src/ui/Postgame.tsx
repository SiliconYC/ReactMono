import type { GameState } from '../core/types.js';
import { netWorth } from '../core/property.js';
import { SeatAvatar } from './game-ui.js';
import './postgame.css';

function resultTitle(game:GameState):string {
  return game.winnerId===null?'净资产并列，平局！':`${game.players.find(p=>p.id===game.winnerId)!.name}获胜！`;
}
function resultReason(game:GameState):string {
  const reason=[...game.events].reverse().find(e=>e.type==='game_finished')?.details?.reason;
  return reason==='bankruptcy'?'其他玩家已破产，最后一位经营者获胜':`达到 ${game.maxRounds} 轮上限，按最终净资产结算`;
}

/** 终局默认留在普通HUD中；详细结算只在主动打开后显示，棋盘继续提供只读浏览。 */
export function PostgameSummary({game,onDetails,onSave,onRestart}:{game:GameState;onDetails:()=>void;onSave:()=>void;onRestart:()=>void}):React.JSX.Element {
  return <section className="result-box postgame-summary" aria-label="对局结果" role="status">
    <div className="postgame-copy"><span>对局已结束 · 自由浏览棋盘</span><h2>{resultTitle(game)}</h2><p>{resultReason(game)}</p></div>
    <div className="postgame-actions">
      <button className="primary-btn" onClick={onDetails}>查看结算</button>
      <button onClick={onSave}>保存或导出</button>
      <button onClick={onRestart}>再来一局</button>
    </div>
  </section>;
}

export function PostgameRanking({game}:{game:GameState}):React.JSX.Element {
  return <section className="postgame-details" aria-label="最终资产排名">
    <h2>{resultTitle(game)}</h2><p>{resultReason(game)}</p>
    <ol className="postgame-ranking">{[...game.players].sort((a,b)=>netWorth(game,b.id)-netWorth(game,a.id)).map((p,i)=><li key={p.id}>
      <span>{i+1}</span><SeatAvatar seat={game.players.indexOf(p)} small/>
      <div><strong>{p.name}</strong><small>{p.bankrupt?'已破产':'最终净资产'}</small></div><b>{netWorth(game,p.id).toLocaleString('zh-CN')}</b>
    </li>)}</ol>
    <p>关闭后可继续浏览最终棋盘、地产与玩家资产。</p>
  </section>;
}
