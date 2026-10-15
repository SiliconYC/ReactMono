import { applyAction, createGame, type GameAction, type GameEvent, type GameState, type Tile, netWorth } from '../core/game.js';
import { chooseComputerAction } from '../core/agent.js';

interface UiState { readonly game: GameState; readonly message: string; readonly seedInput: string; readonly fastMode: boolean; readonly activeSeed: number | null; }

/** 环形棋盘固定 8 列 × 6 行：8 + 4 + 8 + 4 = 24 格。 */
function cellPosition(index: number): { gridColumn: number; gridRow: number } {
  if (index < 8) return { gridColumn: index + 1, gridRow: 1 };
  if (index < 12) return { gridColumn: 8, gridRow: index - 6 };
  if (index < 20) return { gridColumn: 20 - index, gridRow: 6 };
  return { gridColumn: 1, gridRow: 25 - index };
}

const kindLabel: Record<Tile['kind'], string> = { start: '起点', property: '地产', neutral: '休息' };

class App extends React.Component<object, UiState> {
  constructor(props: object) {
    super(props);
    this.state = { game: createGame(20261015), seedInput: '20261015', fastMode: false, activeSeed: null, message: '设置对局种子并点击「开始游戏」，然后掷骰沿着 24 格棋盘前进。' };
  }

  private computerTimer: number | null = null;
  reset = (): void => {
    if (this.computerTimer !== null) { window.clearTimeout(this.computerTimer); this.computerTimer = null; }
    this.setState({ game: createGame(20261015), activeSeed: null, message: '已返回新游戏页面。可调整种子后重新开始。' });
  };
  startGame = (): void => {
    const seed = Number(this.state.seedInput.trim());
    if (!/^\d{1,10}$/.test(this.state.seedInput.trim()) || !Number.isSafeInteger(seed) || seed > 4294967295) {
      this.setState({ message: '对局种子请输入 0 至 4294967295 之间的整数。' });
      return;
    }
    const fresh = createGame(seed);
    const result = applyAction(fresh, { type: 'start_game', actorId: fresh.players[0].id });
    if (!result.ok) { this.setState({ message: '无法开始对局，请重新开局。' }); return; }
    this.setState({ game: result.state, activeSeed: seed, message: '游戏已开始！轮到玩家掷骰。' });
  };
  componentWillUnmount(): void {
    if (this.computerTimer !== null) window.clearTimeout(this.computerTimer);
  }

  /** 每次状态变化只安排电脑的一步；重开后旧回调不会碰新对局。 */
  componentDidUpdate(): void {
    const snapshot = this.state.game;
    if (snapshot.status !== 'playing' || snapshot.players[snapshot.currentPlayerIndex].kind !== 'computer' || this.computerTimer !== null) return;
    this.computerTimer = window.setTimeout(() => {
      this.computerTimer = null;
      if (this.state.game !== snapshot) return;
      const action = chooseComputerAction(snapshot, { reserveCash: 200 });
      if (!action) return;
      const result = applyAction(snapshot, action);
      if (!result.ok) {
        this.setState({ message: '电脑操作失败（' + result.reason + '），请重新开局或报告缺陷。' });
        return;
      }
      const actor = snapshot.players[snapshot.currentPlayerIndex];
      this.setState({ game: result.state, message: this.describe(result.events, result.state, actor.name) });
    }, this.state.fastMode ? 8 : 220);
  }

  dispatch = (type: GameAction['type']): void => {
    const { game } = this.state;
    const actor = game.players[game.currentPlayerIndex];
    if (actor.kind === 'computer') return;
    const result = applyAction(game, { type, actorId: actor.id });
    if (!result.ok) {
      const reason = result.reason === 'INSUFFICIENT_FUNDS' ? '资金不足，无法购买这块地产。请放弃购买。' : '当前阶段不能执行这个操作。';
      this.setState({ message: reason });
      return;
    }
    this.setState({ game: result.state, message: this.describe(result.events, result.state, actor.name) });
  };

  describe = (events: readonly GameEvent[], state: GameState, actorName: string): string => {
    const finished = events.find(e => e.type === 'game_finished');
    if (finished) {
      const winner = state.players.find(p => p.id === state.winnerId);
      const reason = finished.details?.reason === 'bankruptcy' ? '租金不足，发生破产。' : '达到 60 轮上限。';
      return `${reason}${winner ? `赢家是${winner.name}！` : '双方净资产相同，平局！'}`;
    }
    if (events.some(e => e.type === 'game_started')) return '对局已开始！轮到玩家掷骰。';
    const bought = events.find(e => e.type === 'property_bought');
    if (bought) return `${actorName}花费 ${bought.details?.amount} 游戏币购买了 ${bought.details?.tileId} 号地产。现在可以结束回合。`;
    const rent = events.find(e => e.type === 'rent_paid');
    if (rent) return `${actorName}落在对手地产，支付 ${rent.details?.amount} 游戏币租金。现在可以结束回合。`;
    const dice = events.find(e => e.type === 'die_rolled');
    if (dice) {
      const tile = state.tiles[state.players[state.currentPlayerIndex].position];
      return `${actorName}掷出 ${dice.details?.value} 点，走到了「${tile.title}」。${state.phase === 'await_decision' ? `可支付 ${tile.price} 游戏币买地，或选择放弃。` : '可以结束本回合。'}`;
    }
    if (events.some(e => e.type === 'property_declined')) return '本次放弃购买，没有扣除游戏币。可以结束回合。';
    if (events.some(e => e.type === 'turn_ended')) return `轮到${state.players[state.currentPlayerIndex].name}行动，点击掷骰继续。`;
    return '操作完成。';
  };

  describeEvent = (event: GameEvent): string => {
    const person = this.state.game.players.find(p => p.id === event.actorId)?.name ?? '系统';
    switch (event.type) {
      case 'game_started': return '对局开始';
      case 'die_rolled': return `${person}掷出 ${event.details?.value} 点`;
      case 'tile_landed': return `${person}到达「${event.details?.title}」`;
      case 'property_bought': return `${person}买下 ${event.details?.tileId} 号地产（${event.details?.amount}）`;
      case 'rent_paid': return `${person}支付租金 ${event.details?.amount}`;
      case 'player_bankrupt': return `${person}破产`;
      case 'game_finished': return '对局结束';
      case 'property_declined': return `${person}放弃购买`;
      case 'turn_ended': return `${person}结束回合`;
      case 'player_moved': return `${person}移动到 ${event.details?.to} 号格`;
    }
  };

  renderTile = (tile: Tile): unknown => {
    const { game } = this.state;
    const residents = game.players.filter(p => p.position === tile.id);
    return (
      <div key={tile.id} className={`tile tile-${tile.kind} ${tile.ownerId ? `tile-owned-${tile.ownerId}` : ''} ${residents.length ? 'tile-occupied' : ''}`} style={cellPosition(tile.id)} data-tile-id={tile.id} aria-label={`${tile.id} 号地块，${tile.title}`}>
        <span className="tile-index">{String(tile.id).padStart(2, '0')}</span>
        <span className="tile-icon" aria-hidden="true">{tile.kind === 'start' ? '★' : tile.kind === 'property' ? '⌂' : '☕'}</span>
        <span className="tile-name">{kindLabel[tile.kind]}{tile.kind === 'property' ? ` ${tile.id}` : ''}</span>
        {tile.kind === 'property' && <span className="tile-value">{tile.ownerId ? (tile.ownerId === 'p1' ? '玩家所有' : '电脑所有') : `售价 ${tile.price}`}</span>}
        <div className="pieces">{residents.map(p => <span key={p.id} className={`piece ${p.kind}`} title={p.name}>{p.kind === 'human' ? '人' : '机'}</span>)}</div>
      </div>
    );
  };

  render(): unknown {
    const { game, message } = this.state;
    const current = game.players[game.currentPlayerIndex];
    const previousRoll = [...game.events].reverse().find(e => e.type === 'die_rolled');
    const phaseDescription = game.status === 'setup' ? '准备开局'
      : game.status === 'finished' ? '对局已结束'
      : game.phase === 'await_roll' ? '等待掷骰'
      : game.phase === 'await_decision' ? '等待处理地产'
      : '等待结束回合';
    const targetTile = game.tiles[current.position];
    const hasMoneyForLand = targetTile.kind === 'property' && targetTile.ownerId === null && current.cash >= (targetTile.price ?? 0);
    const lastEvents = game.events.filter(e => !['player_moved'].includes(e.type)).slice(-6).reverse();
    return (
      <main className="app-shell" data-game-status={game.status} data-game-phase={game.phase} data-game-revision={game.revision}>
        <header className="topbar">
          <div className="brand"><span className="brand-mark">富</span><span>大富翁 <small>ReactMono</small></span></div>
          <span className="version-tag">P1 · #6 完整对局版</span>
        </header>
        <section className="headline"><div><span className="section-eyebrow">24 格 · 买地收租 · 60 轮定胜负</span><h1>每一步，都是一笔生意。</h1><p>一个人就能完成整局：掷骰、买地、收租，与自动行动的电脑对抗；有人破产即决出胜负，否则第 60 轮按净资产决胜。</p></div><button type="button" className="reset-btn" onClick={this.reset}>↻ 重新开局</button></section>
        <div className="layout">
          <section className="board-card" aria-label="24 格游戏棋盘">
            <div className="board">
              {game.tiles.map(this.renderTile)}
              <div className="board-center">
                <div className="board-center-label">当前第 <b>{game.round}</b> / {game.maxRounds} 轮</div>
                <div className="center-title">环游大富翁<span>体验棋盘</span></div>
                <div className="dice-display" aria-label="上一次骰子点数">{previousRoll ? '⚀⚁⚂⚃⚄⚅'[Number(previousRoll.details?.value) - 1] : '⚄'}</div>
                <div className="center-subtitle">{previousRoll ? `上次掷出 ${previousRoll.details?.value} 点` : '等待第一颗骰子'}</div>
              </div>
            </div>
            <div className="board-legend"><span><i className="legend-property"/>无主地产</span><span><i className="legend-owned-human"/>玩家地产</span><span><i className="legend-owned-computer"/>电脑地产</span><span><i className="legend-neutral"/>普通格</span><span><i className="legend-start"/>起点</span></div>
          </section>
          <aside className="sidebar">
            <div className="turn-card">
              <div className="card-label">当前行动</div>
              <div className="turn-person"><span className={`portrait ${current.kind}`}>{current.kind === 'human' ? '人' : '机'}</span><div><strong>{current.name}</strong><small>{phaseDescription}</small></div></div>
              <div className="turn-position">位置：<b>{current.position} 号格</b><span>·</span>资金：<b>{current.cash.toLocaleString('zh-CN')}</b></div>
              {game.status === 'setup' && <div className="start-form">
                <label className="field-label" htmlFor="game-seed">对局种子 <small>相同种子可重现骰子结果</small></label>
                <input id="game-seed" aria-label="对局种子" inputMode="numeric" type="text" maxLength={10} value={this.state.seedInput} onChange={(event: {target:{value:string}}) => this.setState({ seedInput: event.target.value })} />
                <label className="fast-setting"><input type="checkbox" aria-label="快速模式" checked={this.state.fastMode} onChange={(event: {target:{checked:boolean}}) => this.setState({ fastMode: event.target.checked })} />快速模式（缩短电脑操作间隔）</label>
                <button type="button" className="primary-btn" onClick={this.startGame}>开始游戏 <span>→</span></button>
              </div>}
              {current.kind === 'computer' && game.status === 'playing' && <p className="computer-thinking" role="status">电脑正在自动操作，保留至少 200 游戏币现金…</p>}
              {current.kind === 'human' && game.phase === 'await_roll' && <button type="button" className="primary-btn" onClick={() => this.dispatch('roll')}>掷骰前进 <span>🎲</span></button>}
              {current.kind === 'human' && game.phase === 'await_decision' && <div className="purchase-actions">
                <p className="purchase-info">{targetTile.title}　售价 <b>{targetTile.price}</b>　过路费 <b>{targetTile.rent}</b></p>
                <button type="button" className="primary-btn" onClick={() => this.dispatch('buy_property')} disabled={!hasMoneyForLand}>购买地产 <span>⌂</span></button>
                {!hasMoneyForLand && <p className="insufficient-msg">资金不足，不能购买此地。</p>}
                <button type="button" className="secondary-btn" onClick={() => this.dispatch('decline_property')}>放弃购买，继续回合 →</button>
              </div>}
              {current.kind === 'human' && game.phase === 'await_end_turn' && <button type="button" className="primary-btn" onClick={() => this.dispatch('end_turn')}>结束当前回合 <span>→</span></button>}
              {game.phase === 'finished' && <div className="result-box" role="status"><strong>{game.winnerId ? `${game.players.find(p => p.id === game.winnerId)?.name}获胜！` : '双方平局！'}</strong><p>{[...game.events].reverse().find(e => e.type === 'game_finished')?.details?.reason === 'bankruptcy' ? '结束原因：一方无法付清租金' : '结束原因：达到回合上限'}</p><p>最终净资产：玩家 {netWorth(game,'p1')} · 电脑 {netWorth(game,'p2')}</p><p>本局种子：{this.state.activeSeed}</p><button type="button" className="primary-btn" onClick={this.reset}>再来一局 <span>↻</span></button></div>}
              <p className="turn-tip" role="status">{message}</p>
            </div>
            <div className="players-card"><div className="card-label">玩家状态</div>{game.players.map(p => <div key={p.id} className={`player-line ${current.id === p.id && game.status === 'playing' ? 'is-current' : ''}`}><span className={`player-dot ${p.kind}`}>{p.kind === 'human' ? '人' : '机'}</span><div><strong>{p.name}</strong><small>{p.position} 号格 · 现金 {p.cash.toLocaleString('zh-CN')} · 资产 {netWorth(game,p.id).toLocaleString('zh-CN')}{p.bankrupt ? ' · 已破产' : ''}</small></div><span className="player-kind">{p.kind === 'human' ? '真人' : '电脑'}</span></div>)}</div>
            <div className="activity-card"><div className="card-label">最近事件</div><ol>{lastEvents.map((e,i) => <li key={`${game.events.length}-${i}`}>{this.describeEvent(e)}</li>)}</ol></div>
            <div className="info-card"><strong>玩法说明</strong><p>① 点击「开始游戏」，轮到玩家时掷骰前进。② 到无主地产可买入或放弃；经过对手地产会自动付租。③ 处理完地块后结束回合，电脑会自动行动。</p><p>付不起租金立即破产；否则最多玩 60 轮，最终按现金加土地原价计算净资产。电脑购地后至少保留 200 游戏币。</p><p>这是 P1 简化可玩版：尚不包含升级、股票、卡片、存档或离线功能，后续阶段逐步加入。</p></div>
          </aside>
        </div>
        <footer className="footer">纯前端 · 简体中文 · 不需要账号　｜　当前尚无存读档与断网能力（P2 实现）</footer>
      </main>
    );
  }
}
const root = document.getElementById('root');
if (!root) throw new Error('找不到游戏页面根节点');
ReactDOM.render(React.createElement(App, {}), root);
