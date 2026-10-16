/** P4 #63: React 交互视觉切片，直接驱动正式规则引擎，不伪造棋局或交易。 */
import { createGame, applyAction, DEFAULT_CONFIG, HARBOR_CONFIG, netWorth } from '../core/game.js';
function newGame(map) {
    const config = map === 'harbor-20' ? HARBOR_CONFIG : DEFAULT_CONFIG;
    const setup = createGame(20261017, { ...config,
        players: [{ id: 'p1', name: '小栗', kind: 'human' }, { id: 'p2', name: '阿澜', kind: 'human' }],
        maxRounds: 6, marketEnabled: true, bankEnabled: true, loanEnabled: true,
        strategyEnabled: true, specialEnabled: true, automaticLiquidation: true });
    const start = applyAction(setup, { type: 'start_game', actorId: 'p1' });
    if (!start.ok)
        throw Error('美术样例游戏创建失败');
    return start.state;
}
function tileCaption(tile) {
    if (tile.facility === 'hospital')
        return '医院';
    if (tile.facility === 'prison')
        return '监狱';
    if (tile.facility === 'shop')
        return '商店';
    if (tile.kind === 'start')
        return '起点';
    if (tile.kind === 'neutral')
        return '机会';
    return tile.title;
}
class VisualLab extends React.Component {
    state = { game: newGame('classic-24'), selected: 0, theme: 'paper', message: '轮到小栗掷骰' };
    reset = (map) => this.setState({ game: newGame(map), selected: 0, message: '已换地图，重新开始' });
    act = (type) => {
        const state = this.state.game, actor = state.players[state.currentPlayerIndex];
        // 小切片只公开有限的真实引擎命令；任何拒绝都展示在界面而不绕过规则。
        const action = { type, actorId: actor.id };
        const result = applyAction(state, action);
        if (!result.ok) {
            this.setState({ message: '规则拒绝：' + result.reason });
            return;
        }
        const next = result.state.players[result.state.currentPlayerIndex];
        this.setState({ game: result.state, selected: result.state.players[result.state.currentPlayerIndex].position,
            message: result.state.status === 'finished' ? '本局结束 · 可更换地图重新玩'
                : type === 'roll' ? '走到了 ' + (result.state.tiles.find(t => t.id === result.state.players.find(x => x.id === actor.id)?.position)?.title ?? '新位置')
                    : '轮到 ' + next.name + ' · ' + (result.state.phase === 'await_roll' ? '请掷骰' : '继续选择') });
    };
    render() {
        const { game: g, selected, theme, message } = this.state;
        const p = g.players[g.currentPlayerIndex];
        const tile = g.tiles.find(t => t.id === selected) ?? g.tiles[0];
        const decision = g.tiles.find(t => t.id === p.position) ?? tile;
        const canBuy = g.phase === 'await_decision' && p.cash >= (decision.price ?? Infinity);
        const phase = g.phase;
        return React.createElement("main", { className: 'visual-lab v-theme-' + theme, "data-map-id": g.map.id, "data-lab-phase": g.phase },
            React.createElement("header", { className: "v-header" },
                React.createElement("div", null,
                    React.createElement("a", { className: "v-back", href: "./index.html" }, "\u2190 \u8FD4\u56DE\u6B63\u5F0F\u6E38\u620F"),
                    React.createElement("div", { className: "v-kicker", style: { marginTop: '13px' } }, "REACTMONO \u00B7 P4 VISUAL LAB"),
                    React.createElement("h1", { className: "v-heading" }, "\u5C0F\u9547\u68CB\u76D8"),
                    React.createElement("p", { className: "v-note" }, "\u539F\u521B\u7EB8\u827A\u98CE\u683C \u00B7 \u64CD\u4F5C\u8FDE\u63A5\u6B63\u5F0F\u89C4\u5219\u5F15\u64CE")),
                React.createElement("div", { className: "v-choices", role: "group", "aria-label": "\u8BBE\u8BA1\u65B9\u5411\u5BF9\u6BD4" },
                    React.createElement("button", { className: "v-choice", type: "button", "aria-pressed": theme === 'paper', onClick: () => this.setState({ theme: 'paper' }) }, "\u7EB8\u827A\u5C0F\u9547"),
                    React.createElement("button", { className: "v-choice", type: "button", "aria-pressed": theme === 'candy', onClick: () => this.setState({ theme: 'candy' }) }, "\u7CD6\u679C\u9713\u8679"))),
            React.createElement("div", { className: "v-layout" },
                React.createElement("section", { className: "v-stage", "aria-label": "\u4E92\u52A8\u68CB\u76D8" },
                    React.createElement("div", { className: "v-board", style: { gridTemplateColumns: 'repeat(' + g.map.columns + ',minmax(0,1fr))',
                            gridTemplateRows: 'repeat(' + g.map.rows + ',minmax(0,1fr))', aspectRatio: g.map.columns + '/' + g.map.rows } },
                        g.tiles.map(t => {
                            const cell = g.map.cells[t.id];
                            const occupants = g.players.filter(player => !player.bankrupt && player.position === t.id);
                            return React.createElement("button", { key: t.id, type: "button", className: "v-tile", style: { gridColumn: cell.column, gridRow: cell.row }, "data-kind": t.kind, "data-owner": t.ownerId ?? 'none', "data-selected": selected === t.id, "aria-label": t.title + '，' + (t.ownerId ? '已有主人' : '未持有') + (occupants.length ? '，有棋子' : ''), "aria-pressed": selected === t.id, onClick: () => this.setState({ selected: t.id }) },
                                React.createElement("span", { className: "v-tile-index" }, t.id),
                                t.kind === 'property' ? React.createElement("img", { className: "v-tile-icon", src: "./art/house.svg", alt: "" }) :
                                    t.kind === 'start' ? React.createElement("img", { className: "v-tile-icon", src: "./art/coin.svg", alt: "" }) :
                                        React.createElement("span", { "aria-hidden": "true", style: { fontSize: '20px' } }, "\u25C6"),
                                React.createElement("span", { className: "v-tile-label" }, tileCaption(t)),
                                occupants.length > 0 && React.createElement("span", { className: "v-pawns" }, occupants.map(o => React.createElement("span", { className: "v-pawn", key: o.id, title: o.name }))));
                        }),
                        React.createElement("div", { className: "v-board-center", style: { gridColumn: '2 / ' + g.map.columns, gridRow: '2 / ' + g.map.rows } },
                            React.createElement("div", { className: "v-sun", "aria-hidden": "true" }, g.round),
                            React.createElement("strong", null, phase === 'finished' ? '游戏结束' : p.name + '的回合'),
                            React.createElement("span", null,
                                "\u7B2C ",
                                g.round,
                                " / ",
                                g.maxRounds,
                                " \u8F6E"))),
                    React.createElement("div", { className: "v-actions", role: "group", "aria-label": "\u771F\u6B63\u7684\u89C4\u5219\u64CD\u4F5C" },
                        phase === 'await_roll' && !p.detention && React.createElement("button", { type: "button", className: "v-btn v-btn-main", onClick: () => this.act('roll') }, "\u63B7\u9AB0\u524D\u8FDB \u2192"),
                        phase === 'await_roll' && p.detention && React.createElement("button", { type: "button", className: "v-btn v-btn-main", onClick: () => this.act('skip_turn') }, "\u8DF3\u8FC7\u505C\u7559\u56DE\u5408"),
                        phase === 'await_decision' && React.createElement(React.Fragment, null,
                            React.createElement("button", { type: "button", className: "v-btn v-btn-main", disabled: !canBuy, onClick: () => this.act('buy_property') },
                                "\u8D2D\u4E70\u5730\u4EA7 ",
                                decision.price),
                            React.createElement("button", { type: "button", className: "v-btn", onClick: () => this.act('decline_property') }, "\u653E\u5F03\u8D2D\u4E70")),
                        phase === 'await_shop' && React.createElement("button", { type: "button", className: "v-btn v-btn-main", onClick: () => this.act('leave_shop') }, "\u79BB\u5F00\u5546\u5E97"),
                        phase === 'await_end_turn' && React.createElement(React.Fragment, null,
                            React.createElement("button", { type: "button", className: "v-btn v-btn-main", onClick: () => this.act('end_turn') }, "\u7ED3\u675F\u56DE\u5408 \u2192"),
                            React.createElement("button", { type: "button", className: "v-btn", disabled: p.cash < 50, onClick: () => {
                                    const result = applyAction(g, { type: 'deposit_bank', actorId: p.id, amount: 50 });
                                    if (result.ok)
                                        this.setState({ game: result.state, message: '已存入 50 游戏币' });
                                    else
                                        this.setState({ message: '存款失败：' + result.reason });
                                } }, "\u94F6\u884C\u5B58\u5165 50")),
                        phase === 'finished' && React.createElement("button", { className: "v-btn v-btn-main", type: "button", onClick: () => this.reset(g.map.id) }, "\u518D\u73A9\u4E00\u5C40"))),
                React.createElement("aside", { className: "v-panel" },
                    React.createElement("div", { className: "v-control" },
                        React.createElement("strong", null, "\u5C0F\u9547\u7ECF\u8425"),
                        React.createElement("select", { "aria-label": "\u9884\u89C8\u5730\u56FE", value: g.map.id, onChange: (e) => this.reset(e.target.value) },
                            React.createElement("option", { value: "classic-24" }, "\u7ECF\u5178\u73AF\u7EBF"),
                            React.createElement("option", { value: "harbor-20" }, "\u6D77\u6E2F\u73AF\u7EBF"))),
                    React.createElement("div", { className: "v-player-row" }, g.players.map(player => React.createElement("div", { key: player.id, className: "v-player", "data-active": p.id === player.id },
                        React.createElement("strong", null,
                            React.createElement("i", { "aria-hidden": "true", className: "v-avatar" }),
                            player.name),
                        React.createElement("span", null,
                            "\u73B0\u91D1 ",
                            player.cash),
                        React.createElement("span", null,
                            "\u51C0\u8D44\u4EA7 ",
                            netWorth(g, player.id))))),
                    React.createElement("div", { className: "v-inspector", "aria-live": "polite" },
                        React.createElement("strong", null, tile.title),
                        React.createElement("span", null, tile.kind === 'property'
                            ? '地价 ' + tile.price + ' · 租金 ' + (tile.levelRents?.[tile.level ?? 0] ?? tile.rent) + ' · ' + (tile.ownerId ? (g.players.find(x => x.id === tile.ownerId)?.name ?? '已售') + '持有' : '尚未出售')
                            : tile.kind === 'start' ? '从这里出发，沿棋盘前进。' : tile.facility ? '特殊设施 · ' + tileCaption(tile) : '休息与机会格')),
                    React.createElement("p", { className: "v-status", role: "status" }, message),
                    React.createElement("div", { className: "v-token-strip", "aria-label": "\u89C6\u89C9\u989C\u8272\u6837\u672C" }, ['--rm-primary', '--rm-water', '--rm-land', '--rm-accent', '--rm-player-a', '--rm-player-b'].map(v => React.createElement("span", { key: v, className: "v-token", style: { background: 'var(' + v + ')' }, title: v }))),
                    React.createElement("p", { className: "v-small" }, "\u70B9\u51FB\u5730\u5757\u67E5\u770B\u4FE1\u606F\u3002\u5207\u6362\u914D\u8272\u53EA\u66F4\u6539\u663E\u793A\uFF1B\u6BCF\u6B21\u4EA4\u6613\u548C\u63B7\u9AB0\u5747\u7531\u6B63\u5F0F\u89C4\u5219\u5F15\u64CE\u88C1\u5B9A\u3002\u6B64\u6837\u4F8B\u4E0D\u8BFB\u53D6\u6216\u8986\u76D6\u6B63\u5F0F\u6E38\u620F\u5B58\u6863\u3002"))));
    }
}
const root = document.getElementById('root');
if (root)
    ReactDOM.render(React.createElement(VisualLab, {}), root);
