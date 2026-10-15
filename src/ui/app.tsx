import { applyAction, createGame, type GameState } from '../core/game.js';

interface UiState { game: GameState; message: string }

class App extends React.Component<object, UiState> {
  constructor(props: object) {
    super(props);
    this.state = { game: createGame(20261015), message: '工程骨架已就绪，尚未实现完整玩法。' };
  }

  startGame = (): void => {
    const result = applyAction(this.state.game, { type: 'start_game', actorId: 'p1' });
    if (result.ok) {
      this.setState({ game: result.state, message: '已创建游戏状态。掷骰与移动将在 Issue #3 实现。' });
    } else {
      this.setState({ message: `无法开始：${result.reason}` });
    }
  };

  render(): unknown {
    const { game, message } = this.state;
    return (
      <main className="container">
        <header className="masthead"><span className="eyebrow">大富翁仓库 · ReactMono</span><span className="phase-badge">P1 / 工程验证版</span></header>
        <section className="intro">
          <p className="kicker">一款正在成长的回合制经营游戏</p>
          <h1>大富翁，<span>从第一步开始。</span></h1>
          <p className="lede">当前页面用于验证 React、TypeScript 与独立游戏规则核心的浏览器运行能力。完整玩法会随着后续任务逐步上线。</p>
          <div className="actions"><button type="button" onClick={this.startGame} disabled={game.status !== 'setup'}>{game.status === 'setup' ? '创建测试对局' : '测试对局已创建'}</button><span className="small-hint">无需账号 · 简体中文 · 静态网页</span></div>
        </section>
        <section className="panel" aria-label="游戏状态验证">
          <div className="panel-heading"><h2>规则引擎状态</h2><span className="status-dot">{game.status === 'setup' ? '等待开始' : '等待掷骰'}</span></div>
          <div className="metrics"><div><span>地图</span><strong>{game.tiles.length} 格</strong></div><div><span>玩家</span><strong>{game.players.length} 人</strong></div><div><span>初始资金</span><strong>{game.players[0].cash.toLocaleString('zh-CN')}</strong></div><div><span>状态版本</span><strong>v{game.schemaVersion}</strong></div></div>
          <div className="players">{game.players.map(player => <div key={player.id} className="player"><span className={player.kind === 'human' ? 'avatar human' : 'avatar computer'}>{player.kind === 'human' ? '人' : '机'}</span><div><b>{player.name}</b><small>起点 · {player.cash.toLocaleString('zh-CN')} 游戏币</small></div></div>)}</div>
          <p className="notice" role="status">{message}</p>
        </section>
        <footer>当前版本只验证工程与状态契约，不代表游戏已完成。下一步：棋盘、掷骰、回合推进。</footer>
      </main>
    );
  }
}
const root = document.getElementById('root');
if (!root) throw new Error('找不到游戏页面根节点');
ReactDOM.render(React.createElement(App, {}), root);
