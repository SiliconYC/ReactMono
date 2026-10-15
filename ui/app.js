import { applyAction, createGame } from '../core/game.js';
class App extends React.Component {
    constructor(props) {
        super(props);
        this.state = { game: createGame(20261015), message: '工程骨架已就绪，尚未实现完整玩法。' };
    }
    startGame = () => {
        const result = applyAction(this.state.game, { type: 'start_game', actorId: 'p1' });
        if (result.ok) {
            this.setState({ game: result.state, message: '已创建游戏状态。掷骰与移动将在 Issue #3 实现。' });
        }
        else {
            this.setState({ message: `无法开始：${result.reason}` });
        }
    };
    render() {
        const { game, message } = this.state;
        return (React.createElement("main", { className: "container" },
            React.createElement("header", { className: "masthead" },
                React.createElement("span", { className: "eyebrow" }, "\u5927\u5BCC\u7FC1\u4ED3\u5E93 \u00B7 ReactMono"),
                React.createElement("span", { className: "phase-badge" }, "P1 / \u5DE5\u7A0B\u9A8C\u8BC1\u7248")),
            React.createElement("section", { className: "intro" },
                React.createElement("p", { className: "kicker" }, "\u4E00\u6B3E\u6B63\u5728\u6210\u957F\u7684\u56DE\u5408\u5236\u7ECF\u8425\u6E38\u620F"),
                React.createElement("h1", null,
                    "\u5927\u5BCC\u7FC1\uFF0C",
                    React.createElement("span", null, "\u4ECE\u7B2C\u4E00\u6B65\u5F00\u59CB\u3002")),
                React.createElement("p", { className: "lede" }, "\u5F53\u524D\u9875\u9762\u7528\u4E8E\u9A8C\u8BC1 React\u3001TypeScript \u4E0E\u72EC\u7ACB\u6E38\u620F\u89C4\u5219\u6838\u5FC3\u7684\u6D4F\u89C8\u5668\u8FD0\u884C\u80FD\u529B\u3002\u5B8C\u6574\u73A9\u6CD5\u4F1A\u968F\u7740\u540E\u7EED\u4EFB\u52A1\u9010\u6B65\u4E0A\u7EBF\u3002"),
                React.createElement("div", { className: "actions" },
                    React.createElement("button", { type: "button", onClick: this.startGame, disabled: game.status !== 'setup' }, game.status === 'setup' ? '创建测试对局' : '测试对局已创建'),
                    React.createElement("span", { className: "small-hint" }, "\u65E0\u9700\u8D26\u53F7 \u00B7 \u7B80\u4F53\u4E2D\u6587 \u00B7 \u9759\u6001\u7F51\u9875"))),
            React.createElement("section", { className: "panel", "aria-label": "\u6E38\u620F\u72B6\u6001\u9A8C\u8BC1" },
                React.createElement("div", { className: "panel-heading" },
                    React.createElement("h2", null, "\u89C4\u5219\u5F15\u64CE\u72B6\u6001"),
                    React.createElement("span", { className: "status-dot" }, game.status === 'setup' ? '等待开始' : '等待掷骰')),
                React.createElement("div", { className: "metrics" },
                    React.createElement("div", null,
                        React.createElement("span", null, "\u5730\u56FE"),
                        React.createElement("strong", null,
                            game.tiles.length,
                            " \u683C")),
                    React.createElement("div", null,
                        React.createElement("span", null, "\u73A9\u5BB6"),
                        React.createElement("strong", null,
                            game.players.length,
                            " \u4EBA")),
                    React.createElement("div", null,
                        React.createElement("span", null, "\u521D\u59CB\u8D44\u91D1"),
                        React.createElement("strong", null, game.players[0].cash.toLocaleString('zh-CN'))),
                    React.createElement("div", null,
                        React.createElement("span", null, "\u72B6\u6001\u7248\u672C"),
                        React.createElement("strong", null,
                            "v",
                            game.schemaVersion))),
                React.createElement("div", { className: "players" }, game.players.map(player => React.createElement("div", { key: player.id, className: "player" },
                    React.createElement("span", { className: player.kind === 'human' ? 'avatar human' : 'avatar computer' }, player.kind === 'human' ? '人' : '机'),
                    React.createElement("div", null,
                        React.createElement("b", null, player.name),
                        React.createElement("small", null,
                            "\u8D77\u70B9 \u00B7 ",
                            player.cash.toLocaleString('zh-CN'),
                            " \u6E38\u620F\u5E01"))))),
                React.createElement("p", { className: "notice", role: "status" }, message)),
            React.createElement("footer", null, "\u5F53\u524D\u7248\u672C\u53EA\u9A8C\u8BC1\u5DE5\u7A0B\u4E0E\u72B6\u6001\u5951\u7EA6\uFF0C\u4E0D\u4EE3\u8868\u6E38\u620F\u5DF2\u5B8C\u6210\u3002\u4E0B\u4E00\u6B65\uFF1A\u68CB\u76D8\u3001\u63B7\u9AB0\u3001\u56DE\u5408\u63A8\u8FDB\u3002")));
    }
}
const root = document.getElementById('root');
if (!root)
    throw new Error('找不到游戏页面根节点');
ReactDOM.render(React.createElement(App, {}), root);
