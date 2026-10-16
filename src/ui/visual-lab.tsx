/** P4 #63: React 交互视觉切片，直接驱动正式规则引擎，不伪造棋局或交易。 */
import {createGame,applyAction,DEFAULT_CONFIG,HARBOR_CONFIG,netWorth} from '../core/game.js';
import type {GameState,GameAction,Tile} from '../core/game.js';

type Theme='paper'|'candy';
interface LabState { readonly game:GameState;readonly selected:number;readonly theme:Theme;readonly message:string; }

function newGame(map:string):GameState {
  const config=map==='harbor-20'?HARBOR_CONFIG:DEFAULT_CONFIG;
  const setup=createGame(20261017,{...config,
    players:[{id:'p1',name:'小栗',kind:'human'},{id:'p2',name:'阿澜',kind:'human'}],
    maxRounds:6,marketEnabled:true,bankEnabled:true,loanEnabled:true,
    strategyEnabled:true,specialEnabled:true,automaticLiquidation:true});
  const start=applyAction(setup,{type:'start_game',actorId:'p1'});
  if(!start.ok)throw Error('美术样例游戏创建失败');
  return start.state;
}
function tileCaption(tile:Tile):string {
  if(tile.facility==='hospital')return '医院';
  if(tile.facility==='prison')return '监狱';
  if(tile.facility==='shop')return '商店';
  if(tile.kind==='start')return '起点';
  if(tile.kind==='neutral')return '机会';
  return tile.title;
}
class VisualLab extends React.Component<object,LabState> {
  state:LabState={game:newGame('classic-24'),selected:0,theme:'paper',message:'轮到小栗掷骰'};
  private reset=(map:string):void=>this.setState({game:newGame(map),selected:0,message:'已换地图，重新开始'});
  private act=(type:GameAction['type']):void=>{
    const state=this.state.game,actor=state.players[state.currentPlayerIndex];
    // 小切片只公开有限的真实引擎命令；任何拒绝都展示在界面而不绕过规则。
    const action={type,actorId:actor.id} as GameAction;
    const result=applyAction(state,action);
    if(!result.ok){this.setState({message:'规则拒绝：'+result.reason});return;}
    const next=result.state.players[result.state.currentPlayerIndex];
    this.setState({game:result.state,selected:result.state.players[result.state.currentPlayerIndex].position,
      message:result.state.status==='finished'?'本局结束 · 可更换地图重新玩'
        :type==='roll'?'走到了 '+(result.state.tiles.find(t=>t.id===result.state.players.find(x=>x.id===actor.id)?.position)?.title??'新位置')
        :'轮到 '+next.name+' · '+(result.state.phase==='await_roll'?'请掷骰':'继续选择')});
  };
  render():unknown {
    const {game:g,selected,theme,message}=this.state;
    const p=g.players[g.currentPlayerIndex];
    const tile=g.tiles.find(t=>t.id===selected)??g.tiles[0];
    const decision=g.tiles.find(t=>t.id===p.position)??tile;
    const canBuy=g.phase==='await_decision' && p.cash>=(decision.price??Infinity);
    const phase=g.phase;
    return <main className={'visual-lab v-theme-'+theme} data-map-id={g.map.id} data-lab-phase={g.phase}>
      <header className="v-header">
        <div><a className="v-back" href="./index.html">← 返回正式游戏</a>
          <div className="v-kicker" style={{marginTop:'13px'}}>REACTMONO · P4 VISUAL LAB</div>
          <h1 className="v-heading">小镇棋盘</h1>
          <p className="v-note">原创纸艺风格 · 操作连接正式规则引擎</p></div>
        <div className="v-choices" role="group" aria-label="设计方向对比">
          <button className="v-choice" type="button" aria-pressed={theme==='paper'} onClick={()=>this.setState({theme:'paper'})}>纸艺小镇</button>
          <button className="v-choice" type="button" aria-pressed={theme==='candy'} onClick={()=>this.setState({theme:'candy'})}>糖果霓虹</button>
        </div>
      </header>
      <div className="v-layout">
        <section className="v-stage" aria-label="互动棋盘">
          <div className="v-board" style={{gridTemplateColumns:'repeat('+g.map.columns+',minmax(0,1fr))',
            gridTemplateRows:'repeat('+g.map.rows+',minmax(0,1fr))',aspectRatio:g.map.columns+'/'+g.map.rows}}>
            {g.tiles.map(t=>{
              const cell=g.map.cells[t.id];
              const occupants=g.players.filter(player=>!player.bankrupt&&player.position===t.id);
              return <button key={t.id} type="button" className="v-tile"
                style={{gridColumn:cell.column,gridRow:cell.row}}
                data-kind={t.kind} data-owner={t.ownerId??'none'} data-selected={selected===t.id}
                aria-label={t.title+'，'+(t.ownerId?'已有主人':'未持有')+(occupants.length?'，有棋子':'')}
                aria-pressed={selected===t.id} onClick={()=>this.setState({selected:t.id})}>
                <span className="v-tile-index">{t.id}</span>
                {t.kind==='property'?<img className="v-tile-icon" src="./art/house.svg" alt=""/>:
                  t.kind==='start'?<img className="v-tile-icon" src="./art/coin.svg" alt=""/>:
                  <span aria-hidden="true" style={{fontSize:'20px'}}>◆</span>}
                <span className="v-tile-label">{tileCaption(t)}</span>
                {occupants.length>0&&<span className="v-pawns">
                  {occupants.map(o=><span className="v-pawn" key={o.id} title={o.name}/>)}
                </span>}
              </button>;
            })}
            <div className="v-board-center" style={{gridColumn:'2 / '+g.map.columns,gridRow:'2 / '+g.map.rows}}>
              <div className="v-sun" aria-hidden="true">{g.round}</div>
              <strong>{phase==='finished'?'游戏结束':p.name+'的回合'}</strong>
              <span>第 {g.round} / {g.maxRounds} 轮</span>
            </div>
          </div>
          <div className="v-actions" role="group" aria-label="真正的规则操作">
            {phase==='await_roll'&&!p.detention&&<button type="button" className="v-btn v-btn-main" onClick={()=>this.act('roll')}>掷骰前进 →</button>}
            {phase==='await_roll'&&p.detention&&<button type="button" className="v-btn v-btn-main" onClick={()=>this.act('skip_turn')}>跳过停留回合</button>}
            {phase==='await_decision'&&<>
              <button type="button" className="v-btn v-btn-main" disabled={!canBuy} onClick={()=>this.act('buy_property')}>购买地产 {decision.price}</button>
              <button type="button" className="v-btn" onClick={()=>this.act('decline_property')}>放弃购买</button>
            </>}
            {phase==='await_shop'&&<button type="button" className="v-btn v-btn-main" onClick={()=>this.act('leave_shop')}>离开商店</button>}
            {phase==='await_end_turn'&&<>
              <button type="button" className="v-btn v-btn-main" onClick={()=>this.act('end_turn')}>结束回合 →</button>
              <button type="button" className="v-btn" disabled={p.cash<50} onClick={()=>{
                const result=applyAction(g,{type:'deposit_bank',actorId:p.id,amount:50});
                if(result.ok)this.setState({game:result.state,message:'已存入 50 游戏币'});
                else this.setState({message:'存款失败：'+result.reason});
              }}>银行存入 50</button>
            </>}
            {phase==='finished'&&<button className="v-btn v-btn-main" type="button" onClick={()=>this.reset(g.map.id)}>再玩一局</button>}
          </div>
        </section>
        <aside className="v-panel">
          <div className="v-control">
            <strong>小镇经营</strong>
            <select aria-label="预览地图" value={g.map.id} onChange={(e:{target:{value:string}})=>this.reset(e.target.value)}>
              <option value="classic-24">经典环线</option><option value="harbor-20">海港环线</option>
            </select>
          </div>
          <div className="v-player-row">
            {g.players.map(player=><div key={player.id} className="v-player" data-active={p.id===player.id}>
              <strong><i aria-hidden="true" className="v-avatar"/>{player.name}</strong>
              <span>现金 {player.cash}</span><span>净资产 {netWorth(g,player.id)}</span>
            </div>)}
          </div>
          <div className="v-inspector" aria-live="polite">
            <strong>{tile.title}</strong>
            <span>{tile.kind==='property'
              ?'地价 '+tile.price+' · 租金 '+(tile.levelRents?.[tile.level??0]??tile.rent)+' · '+(tile.ownerId?(g.players.find(x=>x.id===tile.ownerId)?.name??'已售')+'持有':'尚未出售')
              :tile.kind==='start'?'从这里出发，沿棋盘前进。':tile.facility?'特殊设施 · '+tileCaption(tile):'休息与机会格'}</span>
          </div>
          <p className="v-status" role="status">{message}</p>
          <div className="v-token-strip" aria-label="视觉颜色样本">
            {['--rm-primary','--rm-water','--rm-land','--rm-accent','--rm-player-a','--rm-player-b'].map(v=>
              <span key={v} className="v-token" style={{background:'var('+v+')'}} title={v}/>)}
          </div>
          <p className="v-small">点击地块查看信息。切换配色只更改显示；每次交易和掷骰均由正式规则引擎裁定。此样例不读取或覆盖正式游戏存档。</p>
        </aside>
      </div>
    </main>;
  }
}
const root=document.getElementById('root');
if(root)ReactDOM.render(React.createElement(VisualLab,{}),root);
