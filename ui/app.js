import { applyAction, createGame, netWorth } from '../core/game.js';
import { chooseComputerAction } from '../core/agent.js';
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
    componentDidUpdate() {
        const snapshot = this.state.game;
        if (snapshot.status !== 'playing' || snapshot.players[snapshot.currentPlayerIndex].kind !== 'computer')
            return;
        window.setTimeout(() => {
            if (this.state.game !== snapshot)
                return;
            const action = chooseComputerAction(snapshot, { reserveCash: 200 });
            if (!action)
                return;
            const result = applyAction(snapshot, action);
            if (!result.ok) {
                this.setState({ message: '电脑操作失败（' + result.reason + '），请重新开局或报告缺陷。' });
                return;
            }
            const actor = snapshot.players[snapshot.currentPlayerIndex];
            this.setState({ game: result.state, message: this.describe(result.events, result.state, actor.name) });
        }, 380);
    }
    dispatch = (type) => {
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
    describe = (events, state, actorName) => {
        const finished = events.find(e => e.type === 'game_finished');
        if (finished) {
            const winner = state.players.find(p => p.id === state.winnerId);
            const reason = finished.details?.reason === 'bankruptcy' ? '租金不足，发生破产。' : '达到 60 轮上限。';
            return `${reason}${winner ? `赢家是${winner.name}！` : '双方净资产相同，平局！'}`;
        }
        if (events.some(e => e.type === 'game_started'))
            return '对局已开始！轮到玩家掷骰。';
        const bought = events.find(e => e.type === 'property_bought');
        if (bought)
            return `${actorName}花费 ${bought.details?.amount} 游戏币购买了 ${bought.details?.tileId} 号地产。现在可以结束回合。`;
        const rent = events.find(e => e.type === 'rent_paid');
        if (rent)
            return `${actorName}落在对手地产，支付 ${rent.details?.amount} 游戏币租金。现在可以结束回合。`;
        const dice = events.find(e => e.type === 'die_rolled');
        if (dice) {
            const tile = state.tiles[state.players[state.currentPlayerIndex].position];
            return `${actorName}掷出 ${dice.details?.value} 点，走到了「${tile.title}」。${state.phase === 'await_decision' ? `可支付 ${tile.price} 游戏币买地，或选择放弃。` : '可以结束本回合。'}`;
        }
        if (events.some(e => e.type === 'property_declined'))
            return '本次放弃购买，没有扣除游戏币。可以结束回合。';
        if (events.some(e => e.type === 'turn_ended'))
            return `轮到${state.players[state.currentPlayerIndex].name}行动，点击掷骰继续。`;
        return '操作完成。';
    };
    describeEvent = (event) => {
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
    renderTile = (tile) => {
        const { game } = this.state;
        const residents = game.players.filter(p => p.position === tile.id);
        return (React.createElement("div", { key: tile.id, className: `tile tile-${tile.kind} ${tile.ownerId ? `tile-owned-${tile.ownerId}` : ''} ${residents.length ? 'tile-occupied' : ''}`, style: cellPosition(tile.id), "data-tile-id": tile.id, "aria-label": `${tile.id} 号地块，${tile.title}` },
            React.createElement("span", { className: "tile-index" }, String(tile.id).padStart(2, '0')),
            React.createElement("span", { className: "tile-icon", "aria-hidden": "true" }, tile.kind === 'start' ? '★' : tile.kind === 'property' ? '⌂' : '☕'),
            React.createElement("span", { className: "tile-name" },
                kindLabel[tile.kind],
                tile.kind === 'property' ? ` ${tile.id}` : ''),
            tile.kind === 'property' && React.createElement("span", { className: "tile-value" }, tile.ownerId ? (tile.ownerId === 'p1' ? '玩家所有' : '电脑所有') : `售价 ${tile.price}`),
            React.createElement("div", { className: "pieces" }, residents.map(p => React.createElement("span", { key: p.id, className: `piece ${p.kind}`, title: p.name }, p.kind === 'human' ? '人' : '机')))));
    };
    render() {
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
        return (React.createElement("main", { className: "app-shell" },
            React.createElement("header", { className: "topbar" },
                React.createElement("div", { className: "brand" },
                    React.createElement("span", { className: "brand-mark" }, "\u5BCC"),
                    React.createElement("span", null,
                        "\u5927\u5BCC\u7FC1 ",
                        React.createElement("small", null, "ReactMono"))),
                React.createElement("span", { className: "version-tag" }, "P1 \u00B7 #5 \u4EBA\u673A\u5BF9\u5C40\u4F53\u9A8C\u7248")),
            React.createElement("section", { className: "headline" },
                React.createElement("div", null,
                    React.createElement("span", { className: "section-eyebrow" }, "24 \u683C \u00B7 \u4E70\u5730\u6536\u79DF \u00B7 60 \u8F6E\u5B9A\u80DC\u8D1F"),
                    React.createElement("h1", null, "\u6BCF\u4E00\u6B65\uFF0C\u90FD\u662F\u4E00\u7B14\u751F\u610F\u3002"),
                    React.createElement("p", null, "\u4E70\u5730\u3001\u6536\u79DF\u548C\u7834\u4EA7\u5DF2\u7ECF\u751F\u6548\u3002\u8F6E\u5230\u7535\u8111\u65F6\u4F1A\u81EA\u52A8\u63B7\u9AB0\u3001\u51B3\u5B9A\u662F\u5426\u4E70\u5730\u5E76\u7ED3\u675F\u56DE\u5408\uFF1B\u7B2C 60 \u8F6E\u6309\u51C0\u8D44\u4EA7\u51B3\u80DC\u3002")),
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
                            "\u65E0\u4E3B\u5730\u4EA7"),
                        React.createElement("span", null,
                            React.createElement("i", { className: "legend-owned-human" }),
                            "\u73A9\u5BB6\u5730\u4EA7"),
                        React.createElement("span", null,
                            React.createElement("i", { className: "legend-owned-computer" }),
                            "\u7535\u8111\u5730\u4EA7"),
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
                        current.kind === 'computer' && game.status === 'playing' && React.createElement("p", { className: "computer-thinking", role: "status" }, "电脑正在自动操作，保留至少 200 游戏币现金…"),
                        current.kind === 'human' && game.phase === 'await_roll' && React.createElement("button", { type: "button", className: "primary-btn", onClick: () => this.dispatch('roll') },
                            '掷骰前进',
                            " ",
                            React.createElement("span", null, "\uD83C\uDFB2")),
                        current.kind === 'human' && game.phase === 'await_decision' && React.createElement("div", { className: "purchase-actions" },
                            React.createElement("p", { className: "purchase-info" },
                                targetTile.title,
                                "\u3000\u552E\u4EF7 ",
                                React.createElement("b", null, targetTile.price),
                                "\u3000\u8FC7\u8DEF\u8D39 ",
                                React.createElement("b", null, targetTile.rent)),
                            React.createElement("button", { type: "button", className: "primary-btn", onClick: () => this.dispatch('buy_property'), disabled: !hasMoneyForLand },
                                "\u8D2D\u4E70\u5730\u4EA7 ",
                                React.createElement("span", null, "\u2302")),
                            !hasMoneyForLand && React.createElement("p", { className: "insufficient-msg" }, "\u8D44\u91D1\u4E0D\u8DB3\uFF0C\u4E0D\u80FD\u8D2D\u4E70\u6B64\u5730\u3002"),
                            React.createElement("button", { type: "button", className: "secondary-btn", onClick: () => this.dispatch('decline_property') }, "\u653E\u5F03\u8D2D\u4E70\uFF0C\u7EE7\u7EED\u56DE\u5408 \u2192")),
                        current.kind === 'human' && game.phase === 'await_end_turn' && React.createElement("button", { type: "button", className: "primary-btn", onClick: () => this.dispatch('end_turn') },
                            "\u7ED3\u675F\u5F53\u524D\u56DE\u5408 ",
                            React.createElement("span", null, "\u2192")),
                        game.phase === 'finished' && React.createElement("div", { className: "result-box", role: "status" },
                            React.createElement("strong", null, game.winnerId ? `${game.players.find(p => p.id === game.winnerId)?.name}获胜！` : '双方平局！'),
                            React.createElement("p", null,
                                "\u6700\u7EC8\u51C0\u8D44\u4EA7\uFF1A\u73A9\u5BB6 ",
                                netWorth(game, 'p1'),
                                " \u00B7 \u7535\u8111 ",
                                netWorth(game, 'p2')),
                            React.createElement("button", { type: "button", className: "primary-btn", onClick: this.reset },
                                "\u518D\u6765\u4E00\u5C40 ",
                                React.createElement("span", null, "\u21BB"))),
                        React.createElement("p", { className: "turn-tip", role: "status" }, message)),
                    React.createElement("div", { className: "players-card" },
                        React.createElement("div", { className: "card-label" }, "\u73A9\u5BB6\u72B6\u6001"),
                        game.players.map(p => React.createElement("div", { key: p.id, className: `player-line ${current.id === p.id && game.status === 'playing' ? 'is-current' : ''}` },
                            React.createElement("span", { className: `player-dot ${p.kind}` }, p.kind === 'human' ? '人' : '机'),
                            React.createElement("div", null,
                                React.createElement("strong", null, p.name),
                                React.createElement("small", null,
                                    p.position,
                                    " \u53F7\u683C \u00B7 \u73B0\u91D1 ",
                                    p.cash.toLocaleString('zh-CN'),
                                    " \u00B7 \u8D44\u4EA7 ",
                                    netWorth(game, p.id).toLocaleString('zh-CN'),
                                    p.bankrupt ? ' · 已破产' : '')),
                            React.createElement("span", { className: "player-kind" }, p.kind === 'human' ? '真人' : '电脑')))),
                    React.createElement("div", { className: "activity-card" },
                        React.createElement("div", { className: "card-label" }, "\u6700\u8FD1\u4E8B\u4EF6"),
                        React.createElement("ol", null, lastEvents.map((e, i) => React.createElement("li", { key: `${game.events.length}-${i}` }, this.describeEvent(e))))),
                    React.createElement("div", { className: "info-card" },
                        React.createElement("strong", null, "\u5F53\u524D\u7248\u672C\u8BF4\u660E"),
                        React.createElement("p", null, "\u4E70\u5730\u3001\u6536\u79DF\u3001\u7834\u4EA7\u4E0E\u6309\u51C0\u8D44\u4EA7\u7ED3\u7B97\u5DF2\u5B9E\u73B0\u3002\u4E70\u5730\u6B3E\u4ECE\u7CFB\u7EDF\u6263\u9664\uFF1B\u79DF\u91D1\u8FDB\u5165\u5730\u4E3B\u8D26\u6237\u3002\u6BCF\u4EBA\u6700\u591A\u884C\u52A8 60 \u6B21\uFF1B\u5C1A\u65E0\u5EFA\u623F\u6216\u590D\u6742\u6E05\u7B97\u3002"),
                        React.createElement("p", null,
                            "\u63A5\u4E0B\u6765\uFF1A",
                            React.createElement("b", null, "#5 \u7535\u8111\u81EA\u52A8\u884C\u52A8 \u2192 #6 \u5B8C\u6574\u754C\u9762\u9A8C\u6536"),
                            "\u3002\u5F53\u524D\u4ECD\u9700\u8981\u624B\u52A8\u64CD\u4F5C\u7535\u8111\u73A9\u5BB6\u3002")))),
            React.createElement("footer", { className: "footer" }, "\u7EAF\u524D\u7AEF \u00B7 \u7B80\u4F53\u4E2D\u6587 \u00B7 \u4E0D\u9700\u8981\u8D26\u53F7\u3000\uFF5C\u3000\u5F53\u524D\u5C1A\u65E0\u5B58\u8BFB\u6863\u4E0E\u65AD\u7F51\u80FD\u529B\uFF08P2 \u5B9E\u73B0\uFF09")));
    }
}
const root = document.getElementById('root');
if (!root)
    throw new Error('找不到游戏页面根节点');
ReactDOM.render(React.createElement(App, {}), root);
