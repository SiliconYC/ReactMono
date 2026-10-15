import { applyAction, createGame } from '../core/game.js';
/** 环形棋盘固定 8 列 × 6 行：8 + 4 + 8 + 4 = 24 格。 */
function cellPosition(index) {
    if (index < 8)
        return { gridColumn: index + 1, gridRow: 1 };
    if (index < 12)
        return { gridColumn: 8, gridRow: index - 6 };
    if (index < 20)
        return { gridColumn: 20 - index, gridRow: 6 };
    return { gridColumn: 1, gridRow: 25 - index };
}
const kindLabel = { start: '起点', property: '地产', neutral: '休息' };
class App extends React.Component {
    constructor(props) {
        super(props);
        this.state = { game: createGame(20261015), message: '按「开始测试对局」，然后掷骰沿着 24 格棋盘前进。' };
    }
    reset = () => this.setState({ game: createGame(20261015), message: '棋盘已重置，准备开始新一轮测试。' });
    dispatch = (type) => {
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
    describe = (events, state, actorName) => {
        if (events.some(e => e.type === 'game_started'))
            return '对局已开始！轮到玩家掷骰。';
        if (events.some(e => e.type === 'game_finished'))
            return '60 轮测试结束！地产经济与正式胜负将在后续版本加入。';
        const dice = events.find(e => e.type === 'die_rolled');
        if (dice) {
            const tile = state.tiles[state.players[state.currentPlayerIndex].position];
            return `${actorName}掷出 ${dice.details?.value} 点，走到了「${tile.title}」。${state.phase === 'await_decision' ? '购买功能尚未开放，请跳过购买。' : '可以结束本回合。'}`;
        }
        if (events.some(e => e.type === 'property_declined'))
            return '本次跳过购买，没有扣除任何游戏币。现在可以结束回合。';
        if (events.some(e => e.type === 'turn_ended'))
            return `轮到${state.players[state.currentPlayerIndex].name}行动，点击掷骰继续。`;
        return '操作完成。';
    };
    renderTile = (tile) => {
        const { game } = this.state;
        const residents = game.players.filter(p => p.position === tile.id);
        return (React.createElement("div", { key: tile.id, className: `tile tile-${tile.kind} ${residents.length ? 'tile-occupied' : ''}`, style: cellPosition(tile.id), "data-tile-id": tile.id, "aria-label": `${tile.id} 号地块，${tile.title}` },
            React.createElement("span", { className: "tile-index" }, String(tile.id).padStart(2, '0')),
            React.createElement("span", { className: "tile-icon", "aria-hidden": "true" }, tile.kind === 'start' ? '★' : tile.kind === 'property' ? '⌂' : '☕'),
            React.createElement("span", { className: "tile-name" },
                kindLabel[tile.kind],
                tile.kind === 'property' ? ` ${tile.id}` : ''),
            React.createElement("div", { className: "pieces" }, residents.map(p => React.createElement("span", { key: p.id, className: `piece ${p.kind}`, title: p.name }, p.kind === 'human' ? '人' : '机')))));
    };
    render() {
        const { game, message } = this.state;
        const current = game.players[game.currentPlayerIndex];
        const previousRoll = [...game.events].reverse().find(e => e.type === 'die_rolled');
        const phaseDescription = game.status === 'setup' ? '准备开局'
            : game.status === 'finished' ? '测试对局已结束'
                : game.phase === 'await_roll' ? '等待掷骰'
                    : game.phase === 'await_decision' ? '等待处理地产'
                        : '等待结束回合';
        return (React.createElement("main", { className: "app-shell" },
            React.createElement("header", { className: "topbar" },
                React.createElement("div", { className: "brand" },
                    React.createElement("span", { className: "brand-mark" }, "\u5BCC"),
                    React.createElement("span", null,
                        "\u5927\u5BCC\u7FC1 ",
                        React.createElement("small", null, "ReactMono"))),
                React.createElement("span", { className: "version-tag" }, "P1 \u00B7 #3 \u68CB\u76D8\u56DE\u5408\u4F53\u9A8C\u7248")),
            React.createElement("section", { className: "headline" },
                React.createElement("div", null,
                    React.createElement("span", { className: "section-eyebrow" }, "24 \u683C \u00B7 \u4E24\u4EBA\u8F6E\u6D41 \u00B7 \u786E\u5B9A\u6027\u89C4\u5219"),
                    React.createElement("h1", null, "\u68CB\u76D8\u5DF2\u7ECF\u5F00\u59CB\u8F6C\u52A8\u3002"),
                    React.createElement("p", null, "\u63B7\u9AB0\u3001\u79FB\u52A8\u3001\u6362\u4EBA\uFF0C\u73B0\u5728\u90FD\u662F\u771F\u5B9E\u89C4\u5219\u3002\u5730\u4EA7\u4EA4\u6613\u4E0E\u7535\u8111\u81EA\u52A8\u884C\u52A8\u6B63\u5728\u4E0B\u4E00\u9636\u6BB5\u8DEF\u4E0A\u3002")),
                React.createElement("button", { type: "button", className: "reset-btn", onClick: this.reset }, "\u21BB \u91CD\u65B0\u5F00\u5C40")),
            React.createElement("div", { className: "layout" },
                React.createElement("section", { className: "board-card", "aria-label": "24 \u683C\u6E38\u620F\u68CB\u76D8" },
                    React.createElement("div", { className: "board" },
                        game.tiles.map(this.renderTile),
                        React.createElement("div", { className: "board-center" },
                            React.createElement("div", { className: "board-center-label" },
                                "\u5F53\u524D\u7B2C ",
                                React.createElement("b", null, game.round),
                                " / ",
                                game.maxRounds,
                                " \u8F6E"),
                            React.createElement("div", { className: "center-title" },
                                "\u73AF\u6E38\u5927\u5BCC\u7FC1",
                                React.createElement("span", null, "\u4F53\u9A8C\u68CB\u76D8")),
                            React.createElement("div", { className: "dice-display", "aria-label": "\u4E0A\u4E00\u6B21\u9AB0\u5B50\u70B9\u6570" }, previousRoll ? '⚀⚁⚂⚃⚄⚅'[Number(previousRoll.details?.value) - 1] : '⚄'),
                            React.createElement("div", { className: "center-subtitle" }, previousRoll ? `上次掷出 ${previousRoll.details?.value} 点` : '等待第一颗骰子'))),
                    React.createElement("div", { className: "board-legend" },
                        React.createElement("span", null,
                            React.createElement("i", { className: "legend-property" }),
                            "\u53EF\u8D2D\u5730\u4EA7\uFF08\u6682\u4E0D\u53EF\u4E70\uFF09"),
                        React.createElement("span", null,
                            React.createElement("i", { className: "legend-neutral" }),
                            "\u666E\u901A\u683C"),
                        React.createElement("span", null,
                            React.createElement("i", { className: "legend-start" }),
                            "\u8D77\u70B9"))),
                React.createElement("aside", { className: "sidebar" },
                    React.createElement("div", { className: "turn-card" },
                        React.createElement("div", { className: "card-label" }, "\u5F53\u524D\u884C\u52A8"),
                        React.createElement("div", { className: "turn-person" },
                            React.createElement("span", { className: `portrait ${current.kind}` }, current.kind === 'human' ? '人' : '机'),
                            React.createElement("div", null,
                                React.createElement("strong", null, current.name),
                                React.createElement("small", null, phaseDescription))),
                        React.createElement("div", { className: "turn-position" },
                            "\u4F4D\u7F6E\uFF1A",
                            React.createElement("b", null,
                                current.position,
                                " \u53F7\u683C"),
                            React.createElement("span", null, "\u00B7"),
                            "\u8D44\u91D1\uFF1A",
                            React.createElement("b", null, current.cash.toLocaleString('zh-CN'))),
                        game.status === 'setup' && React.createElement("button", { type: "button", className: "primary-btn", onClick: () => this.dispatch('start_game') },
                            "\u5F00\u59CB\u6D4B\u8BD5\u5BF9\u5C40 ",
                            React.createElement("span", null, "\u2192")),
                        game.phase === 'await_roll' && React.createElement("button", { type: "button", className: "primary-btn", onClick: () => this.dispatch('roll') },
                            current.kind === 'computer' ? '代电脑掷骰' : '掷骰前进',
                            " ",
                            React.createElement("span", null, "\uD83C\uDFB2")),
                        game.phase === 'await_decision' && React.createElement("button", { type: "button", className: "primary-btn", onClick: () => this.dispatch('decline_property') },
                            "\u8DF3\u8FC7\u8D2D\u4E70\uFF08\u529F\u80FD\u5F00\u53D1\u4E2D\uFF09 ",
                            React.createElement("span", null, "\u2192")),
                        game.phase === 'await_end_turn' && React.createElement("button", { type: "button", className: "primary-btn", onClick: () => this.dispatch('end_turn') },
                            "\u7ED3\u675F\u5F53\u524D\u56DE\u5408 ",
                            React.createElement("span", null, "\u2192")),
                        game.phase === 'finished' && React.createElement("button", { type: "button", className: "primary-btn", onClick: this.reset },
                            "\u91CD\u65B0\u6D4B\u8BD5 ",
                            React.createElement("span", null, "\u21BB")),
                        React.createElement("p", { className: "turn-tip", role: "status" }, message)),
                    React.createElement("div", { className: "players-card" },
                        React.createElement("div", { className: "card-label" }, "\u73A9\u5BB6\u72B6\u6001"),
                        game.players.map(p => React.createElement("div", { key: p.id, className: `player-line ${current.id === p.id && game.status === 'playing' ? 'is-current' : ''}` },
                            React.createElement("span", { className: `player-dot ${p.kind}` }, p.kind === 'human' ? '人' : '机'),
                            React.createElement("div", null,
                                React.createElement("strong", null, p.name),
                                React.createElement("small", null,
                                    p.position,
                                    " \u53F7\u683C \u00B7 ",
                                    p.cash.toLocaleString('zh-CN'),
                                    " \u6E38\u620F\u5E01")),
                            React.createElement("span", { className: "player-kind" }, p.kind === 'human' ? '真人' : '电脑')))),
                    React.createElement("div", { className: "info-card" },
                        React.createElement("strong", null, "\u5F53\u524D\u7248\u672C\u8BF4\u660E"),
                        React.createElement("p", null, "\u73B0\u5728\u53EF\u4EE5\u53CD\u590D\u63B7\u9AB0\u3001\u79FB\u52A8\u4E0E\u8F6E\u6D41\u64CD\u4F5C\u3002\u7535\u8111\u73A9\u5BB6\u9700\u8981\u624B\u52A8\u4EE3\u63B7\uFF0C\u5730\u4EA7\u8D2D\u4E70\u3001\u6536\u79DF\u548C\u771F\u6B63\u7684\u80DC\u8D1F\u89C4\u5219\u5C1A\u672A\u5B9E\u73B0\u3002"),
                        React.createElement("p", null,
                            "\u5F85\u5B8C\u6210\uFF1A",
                            React.createElement("b", null, "#4 \u5730\u4EA7\u7ECF\u6D4E \u2192 #5 \u7535\u8111\u73A9\u5BB6 \u2192 #6 \u5B8C\u6574\u5BF9\u5C40"))))),
            React.createElement("footer", { className: "footer" }, "\u7EAF\u524D\u7AEF \u00B7 \u7B80\u4F53\u4E2D\u6587 \u00B7 \u4E0D\u9700\u8981\u8D26\u53F7\u3000\uFF5C\u3000\u5F53\u524D\u5C1A\u65E0\u5B58\u8BFB\u6863\u4E0E\u65AD\u7F51\u80FD\u529B\uFF08P2 \u5B9E\u73B0\uFF09")));
    }
}
const root = document.getElementById('root');
if (!root)
    throw new Error('找不到游戏页面根节点');
ReactDOM.render(React.createElement(App, {}), root);
