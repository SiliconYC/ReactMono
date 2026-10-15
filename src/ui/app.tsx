import { applyAction, createGame, type GameAction, type GameEvent, type GameState, type Tile } from '../core/game.js';

interface UiState { readonly game: GameState; readonly message: string; }

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
    this.state = { game: createGame(20261015), message: '按「开始测试对局」，然后掷骰沿着 24 格棋盘前进。' };
  }

  reset = (): void => this.setState({ game: createGame(20261015), message: '棋盘已重置，准备开始新一轮测试。' });

  dispatch = (type: GameAction['type']): void => {
    const { game } = this.state;
    const actor = game.players[game.currentPlayerIndex];
    const result = applyAction(game, { type, actorId: actor.id });
    if (!result.ok) {
      const reason = result.reason === 'NOT_IMPLEMENTED' ? '购买地产将在下一项任务开放。' : '当前阶段不能执行这个操作。';
      this.setState({ message: reason });
      return;
    }
    this.setState({ game: result.state, message: this.describe(result.events, result.state, actor.name) });
  };

  describe = (events: readonly GameEvent[], state: GameState, actorName: string): string => {
    if (events.some(e => e.type === 'game_started')) return '对局已开始！轮到玩家掷骰。';
    if (events.some(e => e.type === 'game_finished')) return '60 轮测试结束！地产经济与正式胜负将在后续版本加入。';
    const dice = events.find(e => e.type === 'die_rolled');
    if (dice) {
      const tile = state.tiles[state.players[state.currentPlayerIndex].position];
      return `${actorName}掷出 ${dice.details?.value} 点，走到了「${tile.title}」。${state.phase === 'await_decision' ? '购买功能尚未开放，请跳过购买。' : '可以结束本回合。'}`;
    }
    if (events.some(e => e.type === 'property_declined')) return '本次跳过购买，没有扣除任何游戏币。现在可以结束回合。';
    if (events.some(e => e.type === 'turn_ended')) return `轮到${state.players[state.currentPlayerIndex].name}行动，点击掷骰继续。`;
    return '操作完成。';
  };

  renderTile = (tile: Tile): unknown => {
    const { game } = this.state;
    const residents = game.players.filter(p => p.position === tile.id);
    return (
      <div key={tile.id} className={`tile tile-${tile.kind} ${residents.length ? 'tile-occupied' : ''}`} style={cellPosition(tile.id)} data-tile-id={tile.id} aria-label={`${tile.id} 号地块，${tile.title}`}>
        <span className="tile-index">{String(tile.id).padStart(2, '0')}</span>
        <span className="tile-icon" aria-hidden="true">{tile.kind === 'start' ? '★' : tile.kind === 'property' ? '⌂' : '☕'}</span>
        <span className="tile-name">{kindLabel[tile.kind]}{tile.kind === 'property' ? ` ${tile.id}` : ''}</span>
        <div className="pieces">{residents.map(p => <span key={p.id} className={`piece ${p.kind}`} title={p.name}>{p.kind === 'human' ? '人' : '机'}</span>)}</div>
      </div>
    );
  };

  render(): unknown {
    const { game, message } = this.state;
    const current = game.players[game.currentPlayerIndex];
    const previousRoll = [...game.events].reverse().find(e => e.type === 'die_rolled');
    const phaseDescription = game.status === 'setup' ? '准备开局'
      : game.status === 'finished' ? '测试对局已结束'
      : game.phase === 'await_roll' ? '等待掷骰'
      : game.phase === 'await_decision' ? '等待处理地产'
      : '等待结束回合';
    return (
      <main className="app-shell">
        <header className="topbar">
          <div className="brand"><span className="brand-mark">富</span><span>大富翁 <small>ReactMono</small></span></div>
          <span className="version-tag">P1 · #3 棋盘回合体验版</span>
        </header>
        <section className="headline"><div><span className="section-eyebrow">24 格 · 两人轮流 · 确定性规则</span><h1>棋盘已经开始转动。</h1><p>掷骰、移动、换人，现在都是真实规则。地产交易与电脑自动行动正在下一阶段路上。</p></div><button type="button" className="reset-btn" onClick={this.reset}>↻ 重新开局</button></section>
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
            <div className="board-legend"><span><i className="legend-property"/>可购地产（暂不可买）</span><span><i className="legend-neutral"/>普通格</span><span><i className="legend-start"/>起点</span></div>
          </section>
          <aside className="sidebar">
            <div className="turn-card">
              <div className="card-label">当前行动</div>
              <div className="turn-person"><span className={`portrait ${current.kind}`}>{current.kind === 'human' ? '人' : '机'}</span><div><strong>{current.name}</strong><small>{phaseDescription}</small></div></div>
              <div className="turn-position">位置：<b>{current.position} 号格</b><span>·</span>资金：<b>{current.cash.toLocaleString('zh-CN')}</b></div>
              {game.status === 'setup' && <button type="button" className="primary-btn" onClick={() => this.dispatch('start_game')}>开始测试对局 <span>→</span></button>}
              {game.phase === 'await_roll' && <button type="button" className="primary-btn" onClick={() => this.dispatch('roll')}>{current.kind === 'computer' ? '代电脑掷骰' : '掷骰前进'} <span>🎲</span></button>}
              {game.phase === 'await_decision' && <button type="button" className="primary-btn" onClick={() => this.dispatch('decline_property')}>跳过购买（功能开发中） <span>→</span></button>}
              {game.phase === 'await_end_turn' && <button type="button" className="primary-btn" onClick={() => this.dispatch('end_turn')}>结束当前回合 <span>→</span></button>}
              {game.phase === 'finished' && <button type="button" className="primary-btn" onClick={this.reset}>重新测试 <span>↻</span></button>}
              <p className="turn-tip" role="status">{message}</p>
            </div>
            <div className="players-card"><div className="card-label">玩家状态</div>{game.players.map(p => <div key={p.id} className={`player-line ${current.id === p.id && game.status === 'playing' ? 'is-current' : ''}`}><span className={`player-dot ${p.kind}`}>{p.kind === 'human' ? '人' : '机'}</span><div><strong>{p.name}</strong><small>{p.position} 号格 · {p.cash.toLocaleString('zh-CN')} 游戏币</small></div><span className="player-kind">{p.kind === 'human' ? '真人' : '电脑'}</span></div>)}</div>
            <div className="info-card"><strong>当前版本说明</strong><p>现在可以反复掷骰、移动与轮流操作。电脑玩家需要手动代掷，地产购买、收租和真正的胜负规则尚未实现。</p><p>待完成：<b>#4 地产经济 → #5 电脑玩家 → #6 完整对局</b></p></div>
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
