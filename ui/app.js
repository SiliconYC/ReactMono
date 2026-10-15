import { applyAction, createGame, netWorth } from '../core/game.js';
import { chooseComputerAction } from '../core/agent.js';
import { listSlots, readSlot, writeSlot, deleteSlot } from '../storage/indexeddb.js';
import { deserializeGame, MAX_SAVE_CHARS } from '../core/save.js';
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
        this.state = { game: createGame(20261015), seedInput: '20261015', fastMode: false, activeSeed: null, saveSlots: [], saveStatus: '正在读取本地存档…', storageBusy: false, importPreview: null, importName: '', message: '设置对局种子并点击「开始游戏」，然后掷骰沿着 24 格棋盘前进。' };
    }
    computerTimer = null;
    saveEpoch = 0;
    saveQueue = Promise.resolve();
    componentDidMount() { void this.refreshSlots(); }
    stopTimer() {
        if (this.computerTimer !== null) {
            window.clearTimeout(this.computerTimer);
            this.computerTimer = null;
        }
    }
    refreshSlots = async () => {
        try {
            const saveSlots = await listSlots();
            this.setState({ saveSlots, saveStatus: this.state.saveStatus === '正在读取本地存档…' ? '本地存档已就绪' : this.state.saveStatus });
        }
        catch (e) {
            this.setState({ saveStatus: '本地存储不可用：' + (e instanceof Error ? e.message : String(e)) + '。请检查无痕模式或磁盘空间。' });
        }
    };
    scheduleAutosave(game) {
        const epoch = this.saveEpoch;
        this.saveQueue = this.saveQueue.then(async () => {
            if (epoch !== this.saveEpoch)
                return;
            await writeSlot('auto', '自动存档', 'auto', game);
            if (epoch !== this.saveEpoch)
                return;
            this.setState({ saveStatus: '自动保存成功 · 第 ' + game.round + ' 轮' });
            await this.refreshSlots();
        }).catch(e => {
            if (epoch === this.saveEpoch)
                this.setState({ saveStatus: '自动保存失败：' + (e instanceof Error ? e.message : String(e)) + '。请手动导出备份。' });
        });
    }
    exportSlot = async (slot) => {
        try {
            const backup = await readSlot(slot.id);
            const content = JSON.stringify(backup, null, 2);
            const blob = new Blob([content], { type: 'application/json;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            const filename = slot.name.replace(/[\\/:*?"<>|]/g, '_');
            link.href = url;
            link.download = '存档-' + filename + '-' + backup.updatedAt.slice(0, 10).replaceAll('-', '') + '.json';
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.setTimeout(() => URL.revokeObjectURL(url), 1000);
            this.setState({ saveStatus: '已生成「' + slot.name + '」备份文件，请自行保管。' });
        }
        catch (e) {
            this.setState({ saveStatus: '导出失败：' + (e instanceof Error ? e.message : String(e)) });
        }
    };
    selectImport = async (event) => {
        const file = event.target.files?.[0];
        event.target.value = '';
        if (!file)
            return;
        this.setState({ importPreview: null });
        if (file.size > MAX_SAVE_CHARS) {
            this.setState({ saveStatus: '导入失败：文件过大，最多 4 MB' });
            return;
        }
        try {
            const raw = await file.text();
            const preview = deserializeGame(raw);
            const filename = file.name.replace(/^存档-(.*)-[0-9]{8}\.json$/i, '$1').replace(/\.json$/i, '');
            const name = (filename.trim() || '导入存档').slice(0, 60);
            this.setState({ importPreview: preview, importName: name, saveStatus: '文件校验通过，请预览并选择导入方式。' });
        }
        catch (e) {
            this.setState({ saveStatus: '导入失败：' + (e instanceof Error ? e.message : String(e)) + '。原存档未改动。' });
        }
    };
    applyImport = async (mode) => {
        const { importPreview, saveSlots } = this.state;
        if (!importPreview || this.state.storageBusy)
            return;
        const name = this.state.importName.trim();
        if (!name || name.length > 60) {
            this.setState({ saveStatus: '请输入 1 至 60 个字符的存档名称' });
            return;
        }
        const duplicate = saveSlots.find(s => s.name === name);
        if (mode === 'overwrite' && !duplicate)
            return;
        const id = mode === 'overwrite' && duplicate ? duplicate.id : 'manual-' + crypto.randomUUID();
        const newName = mode === 'new' && duplicate ? name + '（副本）' : name;
        if (newName.length > 60) {
            this.setState({ saveStatus: '副本名称过长，请先缩短名称' });
            return;
        }
        try {
            await writeSlot(id, newName, 'manual', importPreview.game);
            this.setState({ importPreview: null, importName: '', saveStatus: '「' + newName + '」已安全导入，可点击读取继续对局。' });
            await this.refreshSlots();
        }
        catch (e) {
            this.setState({ saveStatus: '写入失败：' + (e instanceof Error ? e.message : String(e)) + '。原存档未被修改。' });
        }
    };
    newManualSlot = async () => {
        if (this.state.game.status === 'setup' || this.state.storageBusy)
            return;
        const name = window.prompt('输入新存档名称', '存档 ' + new Date().toLocaleString('zh-CN'))?.trim();
        if (!name)
            return;
        if (name.length > 60) {
            this.setState({ saveStatus: '名称最多 60 个字符' });
            return;
        }
        try {
            await writeSlot('manual-' + crypto.randomUUID(), name, 'manual', this.state.game);
            this.setState({ saveStatus: '手动存档「' + name + '」保存成功' });
            await this.refreshSlots();
        }
        catch (e) {
            this.setState({ saveStatus: '手动保存失败：' + (e instanceof Error ? e.message : String(e)) });
        }
    };
    overwriteSlot = async (slot) => {
        if (this.state.game.status === 'setup' || slot.kind !== 'manual' || this.state.storageBusy)
            return;
        if (!window.confirm('确定用当前对局覆盖「' + slot.name + '」吗？'))
            return;
        try {
            await writeSlot(slot.id, slot.name, 'manual', this.state.game);
            this.setState({ saveStatus: '已覆盖「' + slot.name + '」' });
            await this.refreshSlots();
        }
        catch (e) {
            this.setState({ saveStatus: '覆盖失败：' + (e instanceof Error ? e.message : String(e)) });
        }
    };
    restoreSlot = async (slot) => {
        if (this.state.storageBusy)
            return;
        if (!window.confirm('读取「' + slot.name + '」将替换屏幕上的当前游戏，是否继续？'))
            return;
        this.saveEpoch++;
        this.stopTimer();
        this.setState({ storageBusy: true, saveStatus: '正在读取「' + slot.name + '」…' });
        try {
            await this.saveQueue;
            const saved = await readSlot(slot.id);
            this.setState({ game: saved.game, activeSeed: null, storageBusy: false,
                saveStatus: '已读取「' + slot.name + '」', message: '已恢复第 ' + saved.game.round + ' 轮，可从当前阶段继续。' });
        }
        catch (e) {
            this.setState({ storageBusy: false, saveStatus: '读档失败：' + (e instanceof Error ? e.message : String(e)) + '。原对局未被修改。' });
        }
    };
    removeSlot = async (slot) => {
        if (this.state.storageBusy || !window.confirm('确定永久删除「' + slot.name + '」吗？'))
            return;
        try {
            await deleteSlot(slot.id);
            this.setState({ saveStatus: '已删除「' + slot.name + '」' });
            await this.refreshSlots();
        }
        catch (e) {
            this.setState({ saveStatus: '删除失败：' + (e instanceof Error ? e.message : String(e)) });
        }
    };
    reset = () => {
        this.saveEpoch++;
        this.stopTimer();
        this.setState({ game: createGame(20261015), activeSeed: null, message: '已返回新游戏页面。可调整种子后重新开始。' });
    };
    startGame = () => {
        const seed = Number(this.state.seedInput.trim());
        if (!/^\d{1,10}$/.test(this.state.seedInput.trim()) || !Number.isSafeInteger(seed) || seed > 4294967295) {
            this.setState({ message: '对局种子请输入 0 至 4294967295 之间的整数。' });
            return;
        }
        this.saveEpoch++;
        this.stopTimer();
        const fresh = createGame(seed);
        const result = applyAction(fresh, { type: 'start_game', actorId: fresh.players[0].id });
        if (!result.ok) {
            this.setState({ message: '无法开始对局，请重新开局。' });
            return;
        }
        this.setState({ game: result.state, activeSeed: seed, message: '游戏已开始！轮到玩家掷骰。' });
    };
    componentWillUnmount() {
        this.stopTimer();
    }
    /** 每次状态变化只安排电脑的一步；重开后旧回调不会碰新对局。 */
    componentDidUpdate(_prevProps, prevState) {
        if (this.state.game !== prevState.game && this.state.game.status !== 'setup')
            this.scheduleAutosave(this.state.game);
        if (this.state.storageBusy)
            return;
        const snapshot = this.state.game;
        if (snapshot.status !== 'playing' || snapshot.players[snapshot.currentPlayerIndex].kind !== 'computer' || this.computerTimer !== null)
            return;
        this.computerTimer = window.setTimeout(() => {
            this.computerTimer = null;
            if (this.state.game !== snapshot || this.state.storageBusy)
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
        }, this.state.fastMode ? 8 : 220);
    }
    dispatch = (type) => {
        if (this.state.storageBusy)
            return;
        const { game } = this.state;
        const actor = game.players[game.currentPlayerIndex];
        if (actor.kind === 'computer')
            return;
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
        return (React.createElement("main", { className: "app-shell", "data-game-status": game.status, "data-game-phase": game.phase, "data-game-revision": game.revision },
            React.createElement("header", { className: "topbar" },
                React.createElement("div", { className: "brand" },
                    React.createElement("span", { className: "brand-mark" }, "\u5BCC"),
                    React.createElement("span", null,
                        "\u5927\u5BCC\u7FC1 ",
                        React.createElement("small", null, "ReactMono"))),
                React.createElement("span", { className: "version-tag" }, "P2 \u00B7 \u672C\u5730\u591A\u5B58\u6863")),
            React.createElement("section", { className: "headline" },
                React.createElement("div", null,
                    React.createElement("span", { className: "section-eyebrow" }, "24 \u683C \u00B7 \u4E70\u5730\u6536\u79DF \u00B7 60 \u8F6E\u5B9A\u80DC\u8D1F"),
                    React.createElement("h1", null, "\u6BCF\u4E00\u6B65\uFF0C\u90FD\u662F\u4E00\u7B14\u751F\u610F\u3002"),
                    React.createElement("p", null, "\u4E00\u4E2A\u4EBA\u5C31\u80FD\u5B8C\u6210\u6574\u5C40\uFF1A\u63B7\u9AB0\u3001\u4E70\u5730\u3001\u6536\u79DF\uFF0C\u4E0E\u81EA\u52A8\u884C\u52A8\u7684\u7535\u8111\u5BF9\u6297\uFF1B\u6709\u4EBA\u7834\u4EA7\u5373\u51B3\u51FA\u80DC\u8D1F\uFF0C\u5426\u5219\u7B2C 60 \u8F6E\u6309\u51C0\u8D44\u4EA7\u51B3\u80DC\u3002")),
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
                        game.status === 'setup' && React.createElement("div", { className: "start-form" },
                            React.createElement("label", { className: "field-label", htmlFor: "game-seed" },
                                "\u5BF9\u5C40\u79CD\u5B50 ",
                                React.createElement("small", null, "\u76F8\u540C\u79CD\u5B50\u53EF\u91CD\u73B0\u9AB0\u5B50\u7ED3\u679C")),
                            React.createElement("input", { id: "game-seed", "aria-label": "\u5BF9\u5C40\u79CD\u5B50", inputMode: "numeric", type: "text", maxLength: 10, value: this.state.seedInput, onChange: (event) => this.setState({ seedInput: event.target.value }) }),
                            React.createElement("label", { className: "fast-setting" },
                                React.createElement("input", { type: "checkbox", "aria-label": "\u5FEB\u901F\u6A21\u5F0F", checked: this.state.fastMode, onChange: (event) => this.setState({ fastMode: event.target.checked }) }),
                                "\u5FEB\u901F\u6A21\u5F0F\uFF08\u7F29\u77ED\u7535\u8111\u64CD\u4F5C\u95F4\u9694\uFF09"),
                            React.createElement("button", { type: "button", className: "primary-btn", onClick: this.startGame },
                                "\u5F00\u59CB\u6E38\u620F ",
                                React.createElement("span", null, "\u2192"))),
                        current.kind === 'computer' && game.status === 'playing' && React.createElement("p", { className: "computer-thinking", role: "status" }, "\u7535\u8111\u6B63\u5728\u81EA\u52A8\u64CD\u4F5C\uFF0C\u4FDD\u7559\u81F3\u5C11 200 \u6E38\u620F\u5E01\u73B0\u91D1\u2026"),
                        current.kind === 'human' && game.phase === 'await_roll' && React.createElement("button", { type: "button", className: "primary-btn", onClick: () => this.dispatch('roll') },
                            "\u63B7\u9AB0\u524D\u8FDB ",
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
                            React.createElement("p", null, [...game.events].reverse().find(e => e.type === 'game_finished')?.details?.reason === 'bankruptcy' ? '结束原因：一方无法付清租金' : '结束原因：达到回合上限'),
                            React.createElement("p", null,
                                "\u6700\u7EC8\u51C0\u8D44\u4EA7\uFF1A\u73A9\u5BB6 ",
                                netWorth(game, 'p1'),
                                " \u00B7 \u7535\u8111 ",
                                netWorth(game, 'p2')),
                            React.createElement("p", null,
                                "\u672C\u5C40\u79CD\u5B50\uFF1A",
                                this.state.activeSeed),
                            React.createElement("button", { type: "button", className: "primary-btn", onClick: this.reset },
                                "\u518D\u6765\u4E00\u5C40 ",
                                React.createElement("span", null, "\u21BB"))),
                        React.createElement("p", { className: "turn-tip", role: "status" }, message)),
                    React.createElement("div", { className: "saves-card" },
                        React.createElement("div", { className: "card-label" }, "\u672C\u5730\u5B58\u6863"),
                        React.createElement("p", { className: "save-message", role: "status" }, this.state.saveStatus),
                        React.createElement("button", { type: "button", className: "secondary-btn", disabled: game.status === 'setup' || this.state.storageBusy, onClick: () => void this.newManualSlot() }, "\u521B\u5EFA\u624B\u52A8\u5B58\u6863"),
                        React.createElement("ul", { className: "save-list" }, this.state.saveSlots.map(slot => React.createElement("li", { key: slot.id },
                            React.createElement("div", null,
                                React.createElement("strong", null, slot.name),
                                React.createElement("small", null,
                                    slot.kind === 'auto' ? '自动' : '手动',
                                    " \u00B7 ",
                                    new Date(slot.updatedAt).toLocaleString('zh-CN'))),
                            React.createElement("div", { className: "save-actions" },
                                React.createElement("button", { type: "button", disabled: this.state.storageBusy, onClick: () => void this.restoreSlot(slot) }, "\u8BFB\u53D6"),
                                React.createElement("button", { type: "button", disabled: this.state.storageBusy, onClick: () => void this.exportSlot(slot) }, "\u5BFC\u51FA"),
                                slot.kind === 'manual' && React.createElement("button", { type: "button", disabled: this.state.storageBusy || game.status === 'setup', onClick: () => void this.overwriteSlot(slot) }, "\u8986\u76D6"),
                                React.createElement("button", { type: "button", disabled: this.state.storageBusy, onClick: () => void this.removeSlot(slot) }, "\u5220\u9664"))))),
                        React.createElement("label", { className: "import-label" },
                            "\u4ECE\u672C\u673A\u6587\u4EF6\u5BFC\u5165\uFF08\u53EA\u8BFB\u53D6 JSON\uFF0C\u4E0D\u4E0A\u4F20\u4E91\u7AEF\uFF09",
                            React.createElement("input", { type: "file", accept: ".json,application/json", "aria-label": "\u5BFC\u5165 JSON \u5B58\u6863\u6587\u4EF6", onChange: (event) => void this.selectImport(event) })),
                        this.state.importPreview && React.createElement("div", { className: "import-preview", role: "region", "aria-label": "\u5B58\u6863\u5BFC\u5165\u9884\u89C8" },
                            React.createElement("strong", null,
                                "\u5BFC\u5165\u9884\u89C8\uFF1A\u7B2C ",
                                this.state.importPreview.game.round,
                                " \u8F6E"),
                            React.createElement("p", null,
                                "\u73A9\u5BB6\u73B0\u91D1 ",
                                this.state.importPreview.game.players[0].cash,
                                "\uFF0C\u7535\u8111\u73B0\u91D1 ",
                                this.state.importPreview.game.players[1].cash,
                                "\uFF1B \u5DF2\u6709\u5730\u4EA7 ",
                                this.state.importPreview.game.tiles.filter(t => t.ownerId !== null).length,
                                " \u5757\uFF1B \u5F53\u524D\u9636\u6BB5 ",
                                this.state.importPreview.game.phase),
                            React.createElement("label", null,
                                "\u5B58\u6863\u540D\u79F0 ",
                                React.createElement("input", { "aria-label": "\u5BFC\u5165\u5B58\u6863\u540D\u79F0", type: "text", maxLength: 60, value: this.state.importName, onChange: (e) => this.setState({ importName: e.target.value }) })),
                            this.state.saveSlots.some(s => s.name === this.state.importName.trim()) ? React.createElement("div", { className: "save-actions" },
                                React.createElement("button", { type: "button", onClick: () => void this.applyImport('overwrite') }, "\u8986\u76D6\u540C\u540D\u5B58\u6863"),
                                React.createElement("button", { type: "button", onClick: () => void this.applyImport('new') }, "\u53E6\u5B58\u4E3A\u526F\u672C")) : React.createElement("button", { type: "button", className: "secondary-btn", onClick: () => void this.applyImport('new') }, "\u786E\u8BA4\u5BFC\u5165\u5B58\u6863"),
                            React.createElement("button", { type: "button", className: "secondary-btn", onClick: () => this.setState({ importPreview: null, importName: '', saveStatus: '已取消导入' }) }, "\u53D6\u6D88\u5BFC\u5165"))),
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
                        React.createElement("strong", null, "\u73A9\u6CD5\u8BF4\u660E"),
                        React.createElement("p", null, "\u2460 \u70B9\u51FB\u300C\u5F00\u59CB\u6E38\u620F\u300D\uFF0C\u8F6E\u5230\u73A9\u5BB6\u65F6\u63B7\u9AB0\u524D\u8FDB\u3002\u2461 \u5230\u65E0\u4E3B\u5730\u4EA7\u53EF\u4E70\u5165\u6216\u653E\u5F03\uFF1B\u7ECF\u8FC7\u5BF9\u624B\u5730\u4EA7\u4F1A\u81EA\u52A8\u4ED8\u79DF\u3002\u2462 \u5904\u7406\u5B8C\u5730\u5757\u540E\u7ED3\u675F\u56DE\u5408\uFF0C\u7535\u8111\u4F1A\u81EA\u52A8\u884C\u52A8\u3002"),
                        React.createElement("p", null, "\u4ED8\u4E0D\u8D77\u79DF\u91D1\u7ACB\u5373\u7834\u4EA7\uFF1B\u5426\u5219\u6700\u591A\u73A9 60 \u8F6E\uFF0C\u6700\u7EC8\u6309\u73B0\u91D1\u52A0\u571F\u5730\u539F\u4EF7\u8BA1\u7B97\u51C0\u8D44\u4EA7\u3002\u7535\u8111\u8D2D\u5730\u540E\u81F3\u5C11\u4FDD\u7559 200 \u6E38\u620F\u5E01\u3002"),
                        React.createElement("p", null, "\u8FD9\u662F P1 \u7B80\u5316\u53EF\u73A9\u7248\uFF1A\u5C1A\u4E0D\u5305\u542B\u5347\u7EA7\u3001\u80A1\u7968\u3001\u5361\u7247\u3001\u5B58\u6863\u6216\u79BB\u7EBF\u529F\u80FD\uFF0C\u540E\u7EED\u9636\u6BB5\u9010\u6B65\u52A0\u5165\u3002")))),
            React.createElement("footer", { className: "footer" }, "\u7EAF\u524D\u7AEF \u00B7 \u7B80\u4F53\u4E2D\u6587 \u00B7 \u4E0D\u9700\u8981\u8D26\u53F7\u3000\uFF5C\u3000IndexedDB \u672C\u673A\u5B58\u6863 \u00B7 \u4E0D\u4E0A\u4F20\u4E91\u7AEF")));
    }
}
const root = document.getElementById('root');
if (!root)
    throw new Error('找不到游戏页面根节点');
ReactDOM.render(React.createElement(App, {}), root);
