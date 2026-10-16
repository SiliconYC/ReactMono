import { applyAction, createGame, DEFAULT_CONFIG, HARBOR_CONFIG, netWorth, resaleValue, loanLimit, STOCKS, quoteMarket } from '../core/game.js';
import { chooseComputerAction } from '../core/agent.js';
import { COMPUTER_STYLES, COMPUTER_STYLE_NAMES } from '../core/strategic-agent.js';
import { listSlots, readSlot, writeSlot, deleteSlot } from '../storage/indexeddb.js';
import { deserializeGame, MAX_SAVE_CHARS } from '../core/save.js';
/** Read screen positions from map data, never infer them from the tile ID. */
function cellPosition(map, index) {
    const point = map.cells[index];
    return { gridColumn: point.column, gridRow: point.row };
}
const kindLabel = { start: '起点', property: '地产', neutral: '休息' };
class App extends React.Component {
    constructor(props) {
        super(props);
        this.state = { game: createGame(20261015), seedInput: '20261015', bankAmountInput: '100', stockAmountInput: '1', strategyDieInput: '1', roadblockTileInput: '1', playerSetup: [{ id: 'p1', name: '玩家', kind: 'human' }, { id: 'p2', name: '电脑', kind: 'computer', computerStyle: 'balanced' }], roundsInput: '60', selectedMapId: 'classic-24', awaitingHandoff: false, fastMode: false, specialEnabled: false, activeSeed: null, saveSlots: [], saveStatus: '正在读取本地存档…', storageBusy: false, importPreview: null, importName: '', offline: typeof navigator === 'undefined' ? false : !navigator.onLine, pwaUpdate: false, pwaMessage: '', message: '设置对局种子并点击「开始游戏」，然后掷骰沿着 24 格棋盘前进。' };
    }
    computerTimer = null;
    saveEpoch = 0;
    saveQueue = Promise.resolve();
    pwaRegistration = null;
    shouldReload = false;
    updateOnline = () => { this.setState({ offline: !navigator.onLine }); };
    controllerChanged = () => { if (this.shouldReload)
        window.location.reload(); };
    checkUpdate = (reg) => {
        if (reg.waiting && navigator.serviceWorker.controller)
            this.setState({ pwaUpdate: true });
    };
    initPwa = async () => {
        if (!('serviceWorker' in navigator)) {
            this.setState({ pwaMessage: '本浏览器不支持应用安装，仍可在线游玩。' });
            return;
        }
        try {
            navigator.serviceWorker.addEventListener('controllerchange', this.controllerChanged);
            const reg = await navigator.serviceWorker.register('./sw.js', { scope: './' });
            this.pwaRegistration = reg;
            reg.addEventListener('updatefound', () => {
                const worker = reg.installing;
                worker?.addEventListener('statechange', () => {
                    if (worker.state === 'installed')
                        this.checkUpdate(reg);
                });
            });
            this.checkUpdate(reg);
        }
        catch (e) {
            this.setState({ pwaMessage: '离线缓存安装失败，在线游戏仍可使用：' + (e instanceof Error ? e.message : String(e)) });
        }
    };
    applyPwaUpdate = async () => {
        const worker = this.pwaRegistration?.waiting;
        if (!worker)
            return;
        await this.saveQueue;
        this.shouldReload = true;
        worker.postMessage('SKIP_WAITING');
    };
    componentDidMount() {
        void this.refreshSlots();
        window.addEventListener('online', this.updateOnline);
        window.addEventListener('offline', this.updateOnline);
        void this.initPwa();
    }
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
            // 后台自动保存不可盖掉文件损坏、导入冲突等用户必须看见的提示。
            if (this.state.saveStatus === '本地存档已就绪' || this.state.saveStatus.startsWith('自动保存成功'))
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
            this.setState({ game: saved.game, activeSeed: null, storageBusy: false, awaitingHandoff: false,
                roundsInput: String(saved.game.maxRounds), selectedMapId: saved.game.map.id,
                playerSetup: saved.game.players.map(p => ({ id: p.id, name: p.name, kind: p.kind, ...(p.computerStyle ? { computerStyle: p.computerStyle } : {}) })),
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
        const base = this.state.selectedMapId === 'harbor-20' ? HARBOR_CONFIG : DEFAULT_CONFIG;
        this.setState({ game: createGame(20261015, base), activeSeed: null, awaitingHandoff: false, message: '已返回新游戏页面。可调整种子及地图后重新开始。' });
    };
    /** Keep stable IDs when the local seating plan changes. */
    setPlayerCount = (count) => {
        if (!Number.isInteger(count) || count < 2 || count > 4)
            return;
        const roster = Array.from({ length: count }, (_, i) => this.state.playerSetup[i] ?? {
            id: 'p' + (i + 1), name: '玩家' + (i + 1), kind: 'human'
        });
        this.setState({ playerSetup: roster });
    };
    updatePlayer = (index, field, value) => {
        const roster = this.state.playerSetup.map((p, i) => {
            if (i !== index)
                return p;
            const { computerStyle: _previous, ...rest } = p;
            return field === 'kind' ? { ...rest, kind: value, ...(value === 'computer' ? { computerStyle: p.computerStyle ?? 'balanced' } : {}) }
                : { ...p, name: value };
        });
        this.setState({ playerSetup: roster });
    };
    selectMap = (id) => {
        if (id !== 'classic-24' && id !== 'harbor-20')
            return;
        const base = id === 'harbor-20' ? HARBOR_CONFIG : DEFAULT_CONFIG;
        this.setState({ selectedMapId: id, game: createGame(20261015, { ...base, players: this.state.playerSetup }),
            message: id === 'harbor-20' ? '已选择海港环线：20 格，独立价格及海港主题地产。' : '已选择经典环线：24 格，原有规则完整保留。' });
    };
    acknowledgeHandoff = () => {
        this.setState({ awaitingHandoff: false, message: '已轮到' + this.state.game.players[this.state.game.currentPlayerIndex].name + '操作。' });
    };
    startGame = () => {
        const seed = Number(this.state.seedInput.trim());
        if (!/^\d{1,10}$/.test(this.state.seedInput.trim()) || !Number.isSafeInteger(seed) || seed > 4294967295) {
            this.setState({ message: '对局种子请输入 0 至 4294967295 之间的整数。' });
            return;
        }
        const rawRounds = this.state.roundsInput.trim();
        const rounds = Number(rawRounds);
        if (!/^[0-9]{1,3}$/.test(rawRounds) || !Number.isSafeInteger(rounds) || rounds < 1 || rounds > 200) {
            this.setState({ message: '最大轮数必须是 1 至 200 的整数。' });
            return;
        }
        const roster = this.state.playerSetup.map(p => ({ ...p, name: p.name.trim(),
            ...(p.kind === 'computer' ? { computerStyle: p.computerStyle ?? 'balanced' } : {}) }));
        if (roster.some(p => !p.name || p.name.length > 24) || new Set(roster.map(p => p.name)).size !== roster.length) {
            this.setState({ message: '所有玩家都必须填写不同的姓名（最多 24 字）。' });
            return;
        }
        let fresh;
        try {
            fresh = createGame(seed, { ...(this.state.selectedMapId === 'harbor-20' ? HARBOR_CONFIG : DEFAULT_CONFIG), players: roster, maxRounds: rounds, automaticLiquidation: true, bankEnabled: true, loanEnabled: true, marketEnabled: true, strategyEnabled: true, specialEnabled: this.state.specialEnabled });
        }
        catch (e) {
            this.setState({ message: '开局配置无效：' + (e instanceof Error ? e.message : String(e)) });
            return;
        }
        this.saveEpoch++;
        this.stopTimer();
        const result = applyAction(fresh, { type: 'start_game', actorId: fresh.players[0].id });
        if (!result.ok) {
            this.setState({ message: '无法开始对局，请重新开局。' });
            return;
        }
        this.setState({ game: result.state, activeSeed: seed, awaitingHandoff: false, message: '游戏已开始！轮到' + fresh.players[0].name + '掷骰。' });
    };
    componentWillUnmount() {
        window.removeEventListener('online', this.updateOnline);
        window.removeEventListener('offline', this.updateOnline);
        navigator.serviceWorker?.removeEventListener('controllerchange', this.controllerChanged);
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
    dispatch = (type, tileId, cardType, stockId) => {
        if (this.state.storageBusy || this.state.awaitingHandoff)
            return;
        const { game } = this.state;
        const actor = game.players[game.currentPlayerIndex];
        if (actor.kind === 'computer')
            return;
        const bankAmount = /^[1-9][0-9]{0,12}$/.test(this.state.bankAmountInput.trim()) ? Number(this.state.bankAmountInput.trim()) : NaN;
        const stockAmount = /^[1-9][0-9]{0,6}$/.test(this.state.stockAmountInput.trim()) ? Number(this.state.stockAmountInput.trim()) : NaN;
        const action = (type === 'buy_stock' || type === 'sell_stock') ? { type, actorId: actor.id, stockId: stockId ?? 'SEA', quantity: stockAmount }
            : (type === 'upgrade_property' || type === 'sell_property' || type === 'mortgage_property' || type === 'release_mortgage') ? { type, actorId: actor.id, tileId: tileId ?? -1 }
                : type === 'deposit_bank' || type === 'withdraw_bank' || type === 'borrow_loan' || type === 'repay_loan' ? { type, actorId: actor.id, amount: bankAmount }
                    : type === 'buy_shop_card' ? { type, actorId: actor.id, cardType: cardType ?? 'reward' }
                        : type === 'use_card' ? { type, actorId: actor.id, cardType: cardType ?? 'reward',
                            ...(cardType === 'remote' ? { dieValue: Number(this.state.strategyDieInput) } : {}),
                            ...(cardType === 'roadblock' ? { tileId: Number(game.tiles.some(t => t.id === Number(this.state.roadblockTileInput) && t.id !== 0 && t.id !== actor.position && !game.players.some(p => !p.bankrupt && p.position === t.id) && !game.roadblocks?.some(b => b.tileId === t.id)) ? this.state.roadblockTileInput : game.tiles.find(t => t.id !== 0 && t.id !== actor.position && !game.players.some(p => !p.bankrupt && p.position === t.id) && !game.roadblocks?.some(b => b.tileId === t.id))?.id ?? -1) } : {}) } : { type, actorId: actor.id };
        const highRisk = type === 'mortgage_property' || type === 'borrow_loan' ||
            ((type === 'buy_stock' || type === 'sell_stock') && Number.isFinite(stockAmount) && stockAmount >= 50);
        if (highRisk) {
            const detail = type === 'mortgage_property' ? '确认抵押地产？抵押后该地产暂不收租，贷款违约可能被银行收回。'
                : type === 'borrow_loan' ? '确认借入 ' + bankAmount + ' 游戏币？贷款计息且可能触发抵押物清算。'
                    : '确认' + (type === 'buy_stock' ? '买入' : '卖出') + ' ' + stockAmount + ' 股？股票成交后价格会波动，且需支付手续费。';
            if (!window.confirm(detail)) {
                this.setState({ message: '已取消操作，本局资产没有变化。' });
                return;
            }
        }
        const result = applyAction(game, action);
        if (!result.ok) {
            const bankAction = type === 'deposit_bank' || type === 'withdraw_bank' || type === 'borrow_loan' || type === 'repay_loan';
            const stockAction = type === 'buy_stock' || type === 'sell_stock';
            const reason = result.reason === 'INVALID_ACTOR' ? '当前操作玩家已变更，请查看上方高亮玩家。'
                : stockAction ? (result.reason === 'INSUFFICIENT_FUNDS' ? '股票交易未执行：现金不足或持仓数量不够。' : '股票交易未执行：请输入有效股数，交易仅限当前玩家的结算阶段。')
                    : bankAction ? (result.reason === 'INSUFFICIENT_FUNDS' ? '银行或借贷操作未执行：现金、存款或可借额度不足。' : '银行或借贷操作未执行：金额必须是有效正整数，且只能在本人结算阶段操作。')
                        : result.reason === 'INSUFFICIENT_FUNDS' ? '操作未执行：现金不足。' : '操作未执行：当前阶段或目标不合法，请检查所选地产、卡片目标和行动玩家。';
            this.setState({ message: reason });
            return;
        }
        const next = result.state.players[result.state.currentPlayerIndex];
        const handoff = type === 'end_turn' && result.state.status === 'playing'
            && next.kind === 'human' && next.id !== actor.id;
        this.setState({ game: result.state, awaitingHandoff: handoff,
            message: handoff ? '请将设备交给 ' + next.name + '；确认就位后方可继续。' : this.describe(result.events, result.state, actor.name) });
    };
    describe = (events, state, actorName) => {
        const finished = events.find(e => e.type === 'game_finished');
        if (finished) {
            const winner = state.players.find(p => p.id === state.winnerId);
            const reason = finished.details?.reason === 'bankruptcy' ? '租金不足，发生破产。' : '达到 60 轮上限。';
            return `${reason}${winner ? `赢家是${winner.name}！` : '双方净资产相同，平局！'}`;
        }
        if (events.some(e => e.type === 'game_started'))
            return '对局已开始！';
        const stockEvent = events.find(e => e.type === 'stock_bought' || e.type === 'stock_sold' || e.type === 'stock_liquidated');
        if (stockEvent)
            return this.describeEvent(stockEvent);
        const bankEvent = events.find(e => e.type === 'bank_deposited' || e.type === 'bank_withdrawn');
        if (bankEvent)
            return bankEvent.type === 'bank_deposited' ? `${actorName}存入银行 ${bankEvent.details?.amount} 游戏币。` : `${actorName}取出存款 ${bankEvent.details?.amount} 游戏币。`;
        const loanEvent = events.find(e => ['property_mortgaged', 'property_released', 'loan_borrowed', 'loan_repaid', 'loan_default', 'loan_interest'].includes(e.type));
        if (loanEvent)
            return this.describeEvent(loanEvent);
        const interest = events.filter(e => e.type === 'bank_interest');
        if (interest.length)
            return `本轮银行结息 ${interest.length} 笔，总计 ${interest.reduce((sum, e) => sum + Number(e.details?.amount ?? 0), 0)} 游戏币。`;
        const upgraded = events.find(e => e.type === 'property_upgraded');
        if (upgraded)
            return `${actorName}升级了 ${upgraded.details?.tileId} 号地产至 ${upgraded.details?.level} 级，花费 ${upgraded.details?.amount} 游戏币。`;
        const used = events.find(e => e.type === 'card_used');
        if (used)
            return used.details?.cardType === 'reward' ? `${actorName}使用奖励卡，获得 ${used.details?.amount} 游戏币。` :
                used.details?.cardType === 'stride' ? `${actorName}使用步数卡，下次掷骰额外前进 ${used.details?.moveBonus} 格。` :
                    this.describeEvent(used);
        const special = events.find(e => e.type === 'event_bonus' || e.type === 'event_fee');
        if (special)
            return special.type === 'event_bonus' ? `${actorName}触发幸运事件，获得 ${special.details?.amount} 游戏币。` : `${actorName}触发费用事件，支付 ${special.details?.amount} 游戏币（应付 ${special.details?.due}）。`;
        const bought = events.find(e => e.type === 'property_bought');
        if (bought)
            return `${actorName}花费 ${bought.details?.amount} 游戏币购买了 ${bought.details?.tileId} 号地产。现在可以结束回合。`;
        const sold = events.find(e => e.type === 'property_sold');
        if (sold)
            return `${actorName}出售了 ${sold.details?.tileId} 号地产，获得 ${sold.details?.amount} 游戏币。`;
        const rent = events.find(e => e.type === 'rent_paid');
        if (rent)
            return `${actorName}落在对手地产，${events.some(e => e.type === 'property_liquidated') ? '已自动出售地产救急，' : ''}支付 ${rent.details?.amount} 游戏币租金。${state.status === 'playing' ? '现在可以结束回合。' : ''}`;
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
    cardName = (kind) => ({
        reward: '奖励卡', stride: '步数卡', remote: '遥控骰子', roadblock: '路障', rent_free: '免租卡'
    }[String(kind)] ?? '卡片');
    describeEvent = (event) => {
        const person = this.state.game.players.find(p => p.id === event.actorId)?.name ?? '系统';
        switch (event.type) {
            case 'game_started': return '对局开始';
            case 'die_rolled': return `${person}掷出 ${event.details?.value} 点`;
            case 'tile_landed': return `${person}到达「${event.details?.title}」`;
            case 'card_received': return `${person}在卡片站获得${this.cardName(event.details?.cardType)}`;
            case 'card_used': return `${person}使用${this.cardName(event.details?.cardType)}${event.details?.cardType === 'roadblock' ? '，放在 ' + event.details?.tileId + ' 号格' : event.details?.cardType === 'remote' ? '，指定骰点 ' + event.details?.dieValue : ''}`;
            case 'roadblock_triggered': return `${person}碰到 ${event.details?.tileId} 号格路障，提前停下`;
            case 'rent_waived': return `${person}免除 ${event.details?.amount} 游戏币租金`;
            case 'facility_entered': return `${person}来到${event.details?.kind === 'hospital' ? '医院' : event.details?.kind === 'prison' ? '监狱' : '商店'}${event.details?.turns ? '，需跳过 ' + event.details.turns + ' 回合' : '，可以购买道具'}`;
            case 'detention_skipped': return `${person}暂停行动，剩余 ${event.details?.remaining} 回合`;
            case 'detention_released': return `${person}获准离开${event.details?.kind === 'hospital' ? '医院' : '监狱'}`;
            case 'shop_purchased': return `${person}花费 ${event.details?.amount} 游戏币购买${this.cardName(event.details?.cardType)}`;
            case 'shop_left': return `${person}离开商店`;
            case 'card_expired': return event.details?.cardType === 'roadblock' ? `${person}放置在 ${event.details?.tileId} 号格的路障已过期` : `${person}的免租保护已到期`;
            case 'event_bonus': return `${person}在事件格获得 ${event.details?.amount} 游戏币`;
            case 'event_fee': return `${person}在事件格支付 ${event.details?.amount} 游戏币`;
            case 'property_upgraded': return `${person}将 ${event.details?.tileId} 号地产升到 ${event.details?.level} 级（${event.details?.amount}）`;
            case 'property_bought': return `${person}买下 ${event.details?.tileId} 号地产（${event.details?.amount}）`;
            case 'property_sold': return `${person}出售 ${event.details?.tileId} 号地产，回收 ${event.details?.amount} 游戏币`;
            case 'property_liquidated': return `${person}欠费救济，变卖 ${event.details?.tileId} 号地产收回 ${event.details?.amount} 游戏币`;
            case 'property_mortgaged': return `${person}抵押 ${event.details?.tileId} 号地产，额度 ${event.details?.credit}`;
            case 'property_released': return `${person}解除 ${event.details?.tileId} 号地产抵押`;
            case 'loan_borrowed': return `${person}借入 ${event.details?.amount} 游戏币`;
            case 'loan_repaid': return `${person}偿还贷款 ${event.details?.amount} 游戏币`;
            case 'loan_interest': return `${person}贷款利息 ${event.details?.amount}（已付 ${event.details?.paid}）`;
            case 'loan_default': return `${person}违约，抵押地产收回 ${event.details?.collateral} 块`;
            case 'stock_bought': return `${person}以 ${event.details?.price} 游戏币买入 ${event.details?.stockId} ${event.details?.quantity} 股，手续费 ${event.details?.fee}`;
            case 'stock_sold': return `${person}卖出 ${event.details?.stockId} ${event.details?.quantity} 股，手续费 ${event.details?.fee}，已实现盈亏 ${event.details?.realized}`;
            case 'stock_liquidated': return `${person}欠租时变卖 ${event.details?.stockId} ${event.details?.quantity} 股，到账 ${event.details?.amount}`;
            case 'bank_deposited': return `${person}存入银行 ${event.details?.amount} 游戏币`;
            case 'bank_withdrawn': return `${person}${event.details?.reason === 'rent' ? '自动取款支付租金' : '从银行取出'} ${event.details?.amount} 游戏币`;
            case 'bank_interest': return `${person}获得本轮银行利息 ${event.details?.amount} 游戏币`;
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
        const residents = game.players.filter(p => p.position === tile.id && !p.bankrupt);
        return (React.createElement("div", { key: tile.id, className: `tile tile-${tile.kind} ${tile.ownerId ? `tile-owned-${tile.ownerId}` : ''} ${residents.length ? 'tile-occupied' : ''}`, style: cellPosition(game.map, tile.id), "data-tile-id": tile.id, "aria-label": `${tile.id} 号地块，${tile.title}` },
            React.createElement("span", { className: "tile-index" },
                String(tile.id).padStart(2, '0'),
                game.roadblocks?.some(b => b.tileId === tile.id) ? ' 🚧' : ''),
            React.createElement("span", { className: "tile-icon", "aria-hidden": "true" }, tile.facility === 'hospital' ? '✚' : tile.facility === 'prison' ? '▤' : tile.facility === 'shop' ? '▣' : tile.kind === 'start' ? '★' : tile.kind === 'property' ? '⌂' : tile.eventBonus !== undefined ? '✦' : tile.cardStation ? '▣' : '☕'),
            React.createElement("span", { className: "tile-name" }, tile.facility === 'hospital' ? '医院' : tile.facility === 'prison' ? '监狱' : tile.facility === 'shop' ? '商店' : tile.kind === 'property' ? tile.title : tile.eventBonus !== undefined ? '机会' : tile.cardStation ? '卡片' : kindLabel[tile.kind]),
            tile.kind === 'property' && React.createElement("span", { className: "tile-value" }, tile.ownerId ? `${game.players.find(p => p.id === tile.ownerId)?.name ?? '未知'} · ${tile.level ?? 0}级 · 租 ${tile.levelRents?.[tile.level ?? 0] ?? tile.rent}` : `售价 ${tile.price}`),
            React.createElement("div", { className: "pieces" }, residents.map(p => React.createElement("span", { key: p.id, className: `piece ${p.kind}`, title: p.name }, p.kind === 'human' ? '人' : '机')))));
    };
    render() {
        const { game, message } = this.state;
        const current = game.players[game.currentPlayerIndex];
        const previousRoll = [...game.events].reverse().find(e => e.type === 'die_rolled');
        const phaseDescription = game.status === 'setup' ? '准备开局'
            : game.status === 'finished' ? '对局已结束'
                : game.phase === 'await_shop' ? '正在商店购物'
                    : current.detention !== undefined ? '暂停行动 · 剩余 ' + current.detention.remaining + ' 回合'
                        : game.phase === 'await_roll' ? '等待掷骰'
                            : game.phase === 'await_decision' ? '等待处理地产'
                                : '等待结束回合';
        const targetTile = game.tiles[current.position];
        const hasMoneyForLand = targetTile.kind === 'property' && targetTile.ownerId === null && current.cash >= (targetTile.price ?? 0);
        const lastEvents = game.events.filter(e => !['player_moved'].includes(e.type)).slice(-6).reverse();
        const currentShop = game.shops?.find(s => s.tileId === current.position);
        const cardKinds = ['reward', 'stride', 'remote', 'roadblock', 'rent_free'];
        const availableRoadblocks = game.tiles.filter(t => t.id !== 0 && t.id !== current.position &&
            !game.players.some(p => !p.bankrupt && p.position === t.id) && !game.roadblocks?.some(b => b.tileId === t.id));
        return (React.createElement("main", { className: "app-shell", "data-game-status": game.status, "data-game-phase": game.phase, "data-game-revision": game.revision, "data-map-id": game.map.id },
            React.createElement("header", { className: "topbar" },
                React.createElement("div", { className: "brand" },
                    React.createElement("span", { className: "brand-mark" }, "\u5BCC"),
                    React.createElement("span", null,
                        "\u5927\u5BCC\u7FC1 ",
                        React.createElement("small", null, "ReactMono"))),
                React.createElement("span", { className: "version-tag" }, "P3 \u00B7 \u591A\u4EBA\u5BF9\u5C40"),
                React.createElement("span", { className: "network-indicator", role: "status" },
                    this.state.offline ? '已断网 · 可用本地缓存' : '已联网',
                    this.state.pwaMessage ? ' · ' + this.state.pwaMessage : ''),
                this.state.pwaUpdate && React.createElement("button", { className: "secondary-btn", type: "button", onClick: () => void this.applyPwaUpdate() }, "\u68C0\u6D4B\u5230\u65B0\u7248\uFF0C\u4FDD\u5B58\u5E76\u66F4\u65B0")),
            React.createElement("section", { className: "headline" },
                React.createElement("div", null,
                    React.createElement("span", { className: "section-eyebrow" },
                        game.tiles.length,
                        " \u683C \u00B7 \u4E24\u5F20\u5730\u56FE \u00B7 2\uFF5E4 \u4EBA \u00B7 \u672C\u673A\u8F6E\u6D41"),
                    React.createElement("h1", null, "\u6BCF\u4E00\u6B65\uFF0C\u90FD\u662F\u4E00\u7B14\u751F\u610F\u3002"),
                    React.createElement("p", null, "\u9080\u8BF7\u670B\u53CB\u5728\u540C\u4E00\u8BBE\u5907\u8F6E\u6D41\u884C\u52A8\uFF0C\u4E5F\u53EF\u4EE5\u4E0E\u4E00\u540D\u6216\u591A\u540D\u7535\u8111\u73A9\u5BB6\u5BF9\u6297\u3002\u6240\u6709\u5BF9\u5C40\u90FD\u5728\u672C\u5730\u5B8C\u6210\u3002")),
                React.createElement("button", { type: "button", className: "reset-btn", onClick: this.reset }, "\u21BB \u91CD\u65B0\u5F00\u5C40")),
            game.status !== 'setup' && React.createElement("section", { className: "asset-overview", "aria-label": "\u591A\u4EBA\u8D44\u4EA7\u603B\u89C8" },
                React.createElement("div", { className: "asset-heading" },
                    React.createElement("strong", null, "\u591A\u4EBA\u8D44\u4EA7\u603B\u89C8"),
                    React.createElement("span", null,
                        "\u7B2C ",
                        game.round,
                        " / ",
                        game.maxRounds,
                        " \u8F6E \u00B7 \u5F53\u524D\uFF1A",
                        current.name)),
                React.createElement("div", { className: "asset-grid" }, game.players.map(p => {
                    const properties = game.tiles.filter(t => t.kind === 'property' && t.ownerId === p.id);
                    const shares = STOCKS.reduce((total, stock) => total + (p.holdings?.[stock.id]?.quantity ?? 0), 0);
                    const shareValue = game.market ? STOCKS.reduce((total, stock) => total + (p.holdings?.[stock.id]?.quantity ?? 0) * quoteMarket(game.market, stock.id), 0) : 0;
                    return React.createElement("div", { className: `asset-player ${game.status === 'playing' && p.id === current.id ? 'is-active' : ''} ${p.bankrupt ? 'is-bankrupt' : ''}`, key: p.id, "data-player-id": p.id, "data-active-player": String(game.status === 'playing' && p.id === current.id) },
                        React.createElement("div", { className: "asset-identity" },
                            React.createElement("span", { className: `player-dot ${p.kind}` }, p.kind === 'human' ? '人' : '机'),
                            React.createElement("strong", null, p.name),
                            React.createElement("span", { className: "asset-turn-tag" }, p.bankrupt ? '已破产' : p.id === current.id && game.status === 'playing' ? '当前操作' : p.kind === 'computer' ? '电脑' : '真人')),
                        React.createElement("dl", { className: "asset-metrics" },
                            React.createElement("div", null,
                                React.createElement("dt", null, "\u73B0\u91D1"),
                                React.createElement("dd", null, p.cash.toLocaleString('zh-CN'))),
                            React.createElement("div", null,
                                React.createElement("dt", null, "\u94F6\u884C\u5B58\u6B3E"),
                                React.createElement("dd", null, (p.bankBalance ?? 0).toLocaleString('zh-CN'))),
                            React.createElement("div", null,
                                React.createElement("dt", null, "\u5730\u4EA7"),
                                React.createElement("dd", null,
                                    properties.length,
                                    " \u5757",
                                    properties.some(t => t.mortgaged) ? ` · 抵押 ${properties.filter(t => t.mortgaged).length}` : '')),
                            React.createElement("div", null,
                                React.createElement("dt", null, "\u80A1\u7968"),
                                React.createElement("dd", null,
                                    shares,
                                    " \u80A1 \u00B7 ",
                                    shareValue.toLocaleString('zh-CN'),
                                    " \u5E01")),
                            React.createElement("div", null,
                                React.createElement("dt", null, "\u8D37\u6B3E"),
                                React.createElement("dd", null, (p.loanBalance ?? 0).toLocaleString('zh-CN'))),
                            React.createElement("div", { className: "asset-net" },
                                React.createElement("dt", null, "\u51C0\u8D44\u4EA7"),
                                React.createElement("dd", null, netWorth(game, p.id).toLocaleString('zh-CN')))),
                        p.detention && React.createElement("small", { className: "asset-status" },
                            p.detention.kind === 'hospital' ? '医院' : '监狱',
                            " \u00B7 \u8FD8\u9700\u505C\u7559 ",
                            p.detention.remaining,
                            " \u56DE\u5408"));
                }))),
            React.createElement("div", { className: "layout" },
                React.createElement("section", { className: "board-card", "aria-label": `${game.tiles.length} 格游戏棋盘` },
                    React.createElement("div", { className: "board", style: {
                            gridTemplateColumns: `repeat(${game.map.columns},minmax(0,1fr))`,
                            gridTemplateRows: `repeat(${game.map.rows},minmax(0,1fr))`,
                            ...(game.map.id === 'classic-24' ? {} : { aspectRatio: `${game.map.columns}/${game.map.rows}` })
                        } },
                        game.tiles.map(this.renderTile),
                        game.map.columns > 2 && game.map.rows > 2 && game.map.cells.every(p => p.row === 1 || p.row === game.map.rows || p.column === 1 || p.column === game.map.columns) &&
                            React.createElement("div", { className: "board-center", style: { gridColumn: `2/${game.map.columns}`, gridRow: `2/${game.map.rows}` } },
                                React.createElement("div", { className: "board-center-label" },
                                    "\u5F53\u524D\u7B2C ",
                                    React.createElement("b", null, game.round),
                                    " / ",
                                    game.maxRounds,
                                    " \u8F6E"),
                                React.createElement("div", { className: "center-title" },
                                    game.map.id === 'harbor-20' ? '海港环线' : '环游大富翁',
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
                            React.createElement("b", null, current.cash.toLocaleString('zh-CN')),
                            game.bank && React.createElement("span", null,
                                " \u00B7 \u94F6\u884C\u5B58\u6B3E\uFF1A",
                                React.createElement("b", null, (current.bankBalance ?? 0).toLocaleString('zh-CN'))),
                            game.loan && React.createElement("span", null,
                                " \u00B7 \u8D37\u6B3E\uFF1A",
                                React.createElement("b", null, (current.loanBalance ?? 0).toLocaleString('zh-CN')),
                                " \u00B7 \u51C0\u8D44\u4EA7\uFF1A",
                                React.createElement("b", null, netWorth(game, current.id).toLocaleString('zh-CN')))),
                        game.status === 'setup' && React.createElement("div", { className: "start-form" },
                            React.createElement("label", { className: "field-label", htmlFor: "game-map" },
                                "\u6E38\u620F\u5730\u56FE ",
                                React.createElement("small", null, "\u7ECF\u5178\u73AF\u7EBF 24 \u683C\uFF1B\u539F\u521B\u6D77\u6E2F 20 \u683C\uFF08\u4EF7\u683C\u4E0E\u5730\u540D\u4E0D\u540C\uFF09")),
                            React.createElement("select", { id: "game-map", "aria-label": "\u6E38\u620F\u5730\u56FE", value: this.state.selectedMapId, onChange: (event) => this.selectMap(event.target.value) },
                                React.createElement("option", { value: "classic-24" }, "\u7ECF\u5178\u73AF\u7EBF \u00B7 24 \u683C"),
                                React.createElement("option", { value: "harbor-20" }, "\u6D77\u6E2F\u73AF\u7EBF \u00B7 20 \u683C")),
                            React.createElement("label", { className: "field-label", htmlFor: "game-seed" },
                                "\u5BF9\u5C40\u79CD\u5B50 ",
                                React.createElement("small", null, "\u76F8\u540C\u79CD\u5B50\u53EF\u91CD\u73B0\u9AB0\u5B50\u7ED3\u679C")),
                            React.createElement("input", { id: "game-seed", "aria-label": "\u5BF9\u5C40\u79CD\u5B50", inputMode: "numeric", type: "text", maxLength: 10, value: this.state.seedInput, onChange: (event) => this.setState({ seedInput: event.target.value }) }),
                            React.createElement("label", { className: "field-label", htmlFor: "player-count" }, "\u73A9\u5BB6\u4EBA\u6570"),
                            React.createElement("select", { id: "player-count", "aria-label": "\u73A9\u5BB6\u4EBA\u6570", value: this.state.playerSetup.length, onChange: (event) => this.setPlayerCount(Number(event.target.value)) }, [2, 3, 4].map(n => React.createElement("option", { key: n, value: n },
                                n,
                                " \u4EBA"))),
                            React.createElement("div", { className: "setup-roster" }, this.state.playerSetup.map((p, i) => React.createElement("div", { className: "setup-player", key: p.id },
                                React.createElement("label", null,
                                    "\u7B2C ",
                                    i + 1,
                                    " \u4F4D\u73A9\u5BB6\u59D3\u540D",
                                    React.createElement("input", { "aria-label": `第 ${i + 1} 位玩家姓名`, type: "text", maxLength: 24, value: p.name, onChange: (event) => this.updatePlayer(i, 'name', event.target.value) })),
                                React.createElement("label", null,
                                    "\u7C7B\u578B",
                                    React.createElement("select", { "aria-label": `第 ${i + 1} 位玩家类型`, value: p.kind ?? (i === 0 ? 'human' : 'computer'), onChange: (event) => this.updatePlayer(i, 'kind', event.target.value) },
                                        React.createElement("option", { value: "human" }, "\u771F\u4EBA"),
                                        React.createElement("option", { value: "computer" }, "\u7535\u8111"))),
                                p.kind === 'computer' && React.createElement("label", null,
                                    "\u7535\u8111\u7B56\u7565",
                                    React.createElement("select", { "aria-label": `第 ${i + 1} 位电脑策略`, value: p.computerStyle ?? 'balanced', onChange: (event) => this.setState({ playerSetup: this.state.playerSetup.map((item, j) => j === i ? { ...item, computerStyle: event.target.value } : item) }) }, COMPUTER_STYLES.map(style => React.createElement("option", { key: style, value: style }, COMPUTER_STYLE_NAMES[style]))))))),
                            React.createElement("label", { className: "field-label", htmlFor: "max-rounds" }, "\u6700\u591A\u8F6E\u6570"),
                            React.createElement("input", { id: "max-rounds", "aria-label": "\u6700\u591A\u8F6E\u6570", type: "text", inputMode: "numeric", maxLength: 3, value: this.state.roundsInput, onChange: (event) => this.setState({ roundsInput: event.target.value }) }),
                            React.createElement("label", { className: "fast-setting" },
                                React.createElement("input", { type: "checkbox", "aria-label": "\u542F\u7528\u533B\u9662\u3001\u76D1\u72F1\u4E0E\u5546\u5E97", checked: this.state.specialEnabled, onChange: (event) => this.setState({ specialEnabled: event.target.checked }) }),
                                "\u542F\u7528\u533B\u9662\u3001\u76D1\u72F1\u4E0E\u5546\u5E97\uFF08\u7ECF\u5178\u8BBE\u65BD\uFF0C\u53EF\u5173\u95ED\u4FDD\u7559\u65E7\u7248\u5730\u56FE\uFF09"),
                            React.createElement("label", { className: "fast-setting" },
                                React.createElement("input", { type: "checkbox", "aria-label": "\u5FEB\u901F\u6A21\u5F0F", checked: this.state.fastMode, onChange: (event) => this.setState({ fastMode: event.target.checked }) }),
                                "\u5FEB\u901F\u6A21\u5F0F\uFF08\u7F29\u77ED\u7535\u8111\u64CD\u4F5C\u95F4\u9694\uFF09"),
                            React.createElement("button", { type: "button", className: "primary-btn", onClick: this.startGame },
                                "\u5F00\u59CB\u6E38\u620F ",
                                React.createElement("span", null, "\u2192"))),
                        this.state.awaitingHandoff && game.status === 'playing' && React.createElement("div", { className: "handoff-panel", role: "status" },
                            React.createElement("strong", null,
                                "\u8F6E\u5230 ",
                                current.name),
                            React.createElement("p", null, "\u8BF7\u628A\u8BBE\u5907\u4EA4\u7ED9\u8FD9\u540D\u73A9\u5BB6\uFF0C\u51C6\u5907\u597D\u4EE5\u540E\u786E\u8BA4\u3002\u4E0A\u4E00\u4F4D\u73A9\u5BB6\u4E0D\u80FD\u7EE7\u7EED\u64CD\u4F5C\u3002"),
                            React.createElement("button", { type: "button", className: "primary-btn", onClick: this.acknowledgeHandoff }, "\u6211\u5DF2\u5C31\u4F4D\uFF0C\u5F00\u59CB\u64CD\u4F5C")),
                        current.kind === 'computer' && game.status === 'playing' && React.createElement("p", { className: "computer-thinking", role: "status" },
                            "\u7535\u8111\u6B63\u5728\u81EA\u52A8\u64CD\u4F5C\uFF08",
                            current.computerStyle ? COMPUTER_STYLE_NAMES[current.computerStyle] : '经典',
                            "\u7B56\u7565\uFF09\u2026"),
                        current.kind === 'human' && !this.state.awaitingHandoff && game.phase === 'await_roll' && current.detention === undefined && React.createElement("div", { className: "purchase-actions" },
                            React.createElement("p", { className: "purchase-info" },
                                "\u624B\u724C\uFF1A\u5956\u52B1 ",
                                current.cards?.reward ?? 0,
                                " \u00B7 \u6B65\u6570 ",
                                current.cards?.stride ?? 0,
                                game.strategyEnabled ? ' · 遥控 ' + (current.cards?.remote ?? 0) + ' · 路障 ' + (current.cards?.roadblock ?? 0) + ' · 免租 ' + (current.cards?.rent_free ?? 0) : '',
                                (game.pendingMoveBonus ?? 0) > 0 ? ` · 已加步数 ${game.pendingMoveBonus}` : '',
                                (game.pendingDie ?? 0) > 0 ? ` · 已指定骰点 ${game.pendingDie}` : '',
                                game.pendingRentWaiver ? ' · 本次免租' : ''),
                            (current.cards?.reward ?? 0) > 0 && React.createElement("button", { type: "button", className: "secondary-btn", onClick: () => this.dispatch('use_card', undefined, 'reward') },
                                "\u4F7F\u7528\u5956\u52B1\u5361\uFF08+",
                                game.cardRules?.rewardCash ?? 80,
                                " \u6E38\u620F\u5E01\uFF09"),
                            (current.cards?.stride ?? 0) > 0 && (game.pendingMoveBonus ?? 0) === 0 && React.createElement("button", { type: "button", className: "secondary-btn", onClick: () => this.dispatch('use_card', undefined, 'stride') },
                                "\u4F7F\u7528\u6B65\u6570\u5361\uFF08+",
                                game.cardRules?.moveBonus ?? 2,
                                " \u683C\uFF09"),
                            game.strategyEnabled && (current.cards?.remote ?? 0) > 0 && (game.pendingDie ?? 0) === 0 && React.createElement("div", { className: "purchase-info" },
                                React.createElement("label", { htmlFor: "remote-die" }, "\u9065\u63A7\u9AB0\u70B9 "),
                                React.createElement("select", { id: "remote-die", "aria-label": "\u9065\u63A7\u9AB0\u70B9", value: this.state.strategyDieInput, onChange: (e) => this.setState({ strategyDieInput: e.target.value }) }, [1, 2, 3, 4, 5, 6].map(n => React.createElement("option", { key: n, value: n },
                                    n,
                                    " \u70B9"))),
                                React.createElement("button", { type: "button", className: "secondary-btn", onClick: () => this.dispatch('use_card', undefined, 'remote') }, "\u4F7F\u7528\u9065\u63A7\u9AB0\u5B50")),
                            game.strategyEnabled && (current.cards?.roadblock ?? 0) > 0 && React.createElement("div", { className: "purchase-info" },
                                React.createElement("label", { htmlFor: "roadblock-tile" }, "\u653E\u7F6E\u8DEF\u969C "),
                                React.createElement("select", { id: "roadblock-tile", "aria-label": "\u8DEF\u969C\u76EE\u6807\u683C", value: availableRoadblocks.some(t => String(t.id) === this.state.roadblockTileInput) ? this.state.roadblockTileInput : String(availableRoadblocks[0]?.id ?? ''), onChange: (e) => this.setState({ roadblockTileInput: e.target.value }) }, availableRoadblocks.map(t => React.createElement("option", { key: t.id, value: t.id },
                                    t.id,
                                    " \u00B7 ",
                                    t.title))),
                                React.createElement("button", { type: "button", className: "secondary-btn", disabled: availableRoadblocks.length === 0, onClick: () => this.dispatch('use_card', undefined, 'roadblock') }, "\u653E\u7F6E\u8DEF\u969C")),
                            game.strategyEnabled && (current.cards?.rent_free ?? 0) > 0 && !game.pendingRentWaiver && React.createElement("button", { type: "button", className: "secondary-btn", onClick: () => this.dispatch('use_card', undefined, 'rent_free') }, "\u4F7F\u7528\u514D\u79DF\u5361\uFF08\u672C\u6B21\u63B7\u9AB0\u6709\u6548\uFF09"),
                            React.createElement("button", { type: "button", className: "primary-btn", onClick: () => this.dispatch('roll') },
                                "\u63B7\u9AB0\u524D\u8FDB ",
                                React.createElement("span", null, "\uD83C\uDFB2"))),
                        current.kind === 'human' && !this.state.awaitingHandoff && game.phase === 'await_roll' && current.detention !== undefined && React.createElement("div", { className: "purchase-actions" },
                            React.createElement("p", { className: "purchase-info" },
                                "\u6B63\u5728",
                                current.detention.kind === 'hospital' ? '住院' : '服刑',
                                " \u00B7 \u5269\u4F59 ",
                                current.detention.remaining,
                                " \u6B21\u8F6E\u5230\u4F60\u7684\u56DE\u5408"),
                            React.createElement("button", { type: "button", className: "primary-btn", onClick: () => this.dispatch('skip_turn') }, "\u8DF3\u8FC7\u5F53\u524D\u505C\u7559\u56DE\u5408")),
                        current.kind === 'human' && !this.state.awaitingHandoff && game.phase === 'await_shop' && React.createElement("div", { className: "purchase-actions" },
                            React.createElement("p", { className: "purchase-info" },
                                "\u5546\u5E97 \u00B7 \u73B0\u91D1 ",
                                current.cash,
                                " \u00B7 \u624B\u724C\u4E0A\u9650 ",
                                game.cardRules?.maxHand ?? 3),
                            cardKinds.map(k => React.createElement("button", { key: k, type: "button", className: "secondary-btn", disabled: !currentShop || (currentShop.cards[k] ?? 0) < 1 || current.cash < (game.facilityRules?.prices[k] ?? Infinity) ||
                                    cardKinds.reduce((sum, x) => sum + (current.cards?.[x] ?? 0), 0) >= (game.cardRules?.maxHand ?? 3), onClick: () => this.dispatch('buy_shop_card', undefined, k) },
                                "\u8D2D\u4E70",
                                this.cardName(k),
                                " \u00B7 ",
                                game.facilityRules?.prices[k] ?? 0,
                                " \u5E01 \u00B7 \u5269\u4F59 ",
                                currentShop?.cards[k] ?? 0)),
                            React.createElement("button", { type: "button", className: "primary-btn", onClick: () => this.dispatch('leave_shop') }, "\u79BB\u5F00\u5546\u5E97")),
                        current.kind === 'human' && !this.state.awaitingHandoff && game.phase === 'await_decision' && React.createElement("div", { className: "purchase-actions" },
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
                        current.kind === 'human' && !this.state.awaitingHandoff && game.phase === 'await_end_turn' && React.createElement("div", { className: "purchase-actions" },
                            React.createElement("div", { className: "action-navigation", role: "navigation", "aria-label": "\u4EA4\u6613\u64CD\u4F5C\u5FEB\u6377\u5165\u53E3" }, ([{ id: 'property-management', label: '地产管理' }, ...(game.bank ? [{ id: 'bank-actions', label: '银行存取' }] : []), ...(game.loan ? [{ id: 'loan-actions', label: '贷款与抵押入口' }] : []), ...(game.market ? [{ id: 'stock-actions', label: '股票交易' }] : [])]).map(link => React.createElement("button", { key: link.id, type: "button", onClick: () => document.getElementById(link.id)?.scrollIntoView({ behavior: 'smooth', block: 'start' }) },
                                link.label,
                                " \u2193"))),
                            React.createElement("strong", { id: "property-management", className: "management-heading" },
                                "\u5730\u4EA7\u7BA1\u7406 \u00B7 ",
                                current.name),
                            game.tiles.filter(t => t.kind === 'property' && t.ownerId === current.id && t.mortgaged !== true && (t.level ?? 0) < 2).map(tile => React.createElement("button", { type: "button", key: tile.id, className: "secondary-btn", disabled: current.cash < (tile.upgradeCosts?.[tile.level ?? 0] ?? Infinity), onClick: () => this.dispatch('upgrade_property', tile.id) },
                                "\u5347\u7EA7 ",
                                tile.title,
                                " \u2192 ",
                                (tile.level ?? 0) + 1,
                                " \u7EA7 \u00B7 \u8D39\u7528 ",
                                tile.upgradeCosts?.[tile.level ?? 0])),
                            game.tiles.filter(t => t.kind === 'property' && t.ownerId === current.id && t.mortgaged !== true).map(tile => React.createElement("button", { type: "button", key: 'sell-' + tile.id, className: "secondary-btn", onClick: () => {
                                    if (window.confirm('确认出售「' + tile.title + '」？价格 ' + resaleValue(tile, game.resaleRules) + ' 游戏币，建筑升级不返还原价。'))
                                        this.dispatch('sell_property', tile.id);
                                } },
                                "\u51FA\u552E ",
                                tile.title,
                                " \u00B7 \u56DE\u6536 ",
                                resaleValue(tile, game.resaleRules),
                                " \u6E38\u620F\u5E01")),
                            game.bank && React.createElement("div", { id: "bank-actions", className: "bank-actions", role: "group", "aria-label": "\u94F6\u884C\u64CD\u4F5C" },
                                React.createElement("strong", { className: "management-heading" },
                                    "\u94F6\u884C\u5B58\u53D6 \u00B7 ",
                                    current.name),
                                React.createElement("p", { className: "purchase-info" },
                                    "\u94F6\u884C\uFF1A\u6BCF\u5B8C\u6210\u4E00\u8F6E\u6309 ",
                                    game.bank.interestBps / 100,
                                    "% \u7ED3\u606F\uFF0C\u73B0\u91D1\u4E0E\u5B58\u6B3E\u5206\u5F00\u8BA1\u7B97\uFF0C\u6B20\u79DF\u65F6\u4F18\u5148\u81EA\u52A8\u53D6\u6B3E\u3002"),
                                React.createElement("label", { htmlFor: "bank-amount" }, "\u94F6\u884C\u4EA4\u6613\u91D1\u989D\uFF08\u6E38\u620F\u5E01\uFF09"),
                                React.createElement("input", { id: "bank-amount", "aria-label": "\u94F6\u884C\u4EA4\u6613\u91D1\u989D", inputMode: "numeric", type: "text", value: this.state.bankAmountInput, onChange: (e) => this.setState({ bankAmountInput: e.target.value }) }),
                                React.createElement("button", { type: "button", className: "secondary-btn", disabled: !/^[1-9][0-9]*$/.test(this.state.bankAmountInput) || Number(this.state.bankAmountInput) > current.cash, onClick: () => this.dispatch('deposit_bank') }, "\u5B58\u5165\u94F6\u884C"),
                                React.createElement("button", { type: "button", className: "secondary-btn", disabled: !/^[1-9][0-9]*$/.test(this.state.bankAmountInput) || Number(this.state.bankAmountInput) > (current.bankBalance ?? 0), onClick: () => this.dispatch('withdraw_bank') }, "\u4ECE\u94F6\u884C\u53D6\u6B3E")),
                            game.loan && React.createElement("div", { id: "loan-actions", className: "bank-actions loan-actions", role: "group", "aria-label": "\u5730\u4EA7\u62B5\u62BC\u4E0E\u8D37\u6B3E" },
                                React.createElement("strong", { className: "management-heading" },
                                    "\u62B5\u62BC\u501F\u8D37 \u00B7 ",
                                    current.name),
                                React.createElement("p", { className: "purchase-info" },
                                    "\u8D37\u6B3E ",
                                    (current.loanBalance ?? 0).toLocaleString('zh-CN'),
                                    " \u00B7 \u62B5\u62BC\u989D\u5EA6 ",
                                    loanLimit(game, current.id),
                                    " \u00B7 \u6BCF\u8F6E\u5229\u7387 ",
                                    game.loan.interestBps / 100,
                                    "%\u3002\u62B5\u62BC\u5730\u4EA7\u6682\u505C\u79DF\u91D1\u3001\u5347\u7EA7\u548C\u51FA\u552E\uFF1B\u8D85\u989D\u65F6\u94F6\u884C\u6536\u56DE\u62B5\u62BC\u7269\u3002"),
                                game.tiles.filter(t => t.kind === 'property' && t.ownerId === current.id).map(tile => React.createElement("button", { type: "button", key: 'lien-' + tile.id, className: "secondary-btn", disabled: tile.mortgaged === true && (current.loanBalance ?? 0) > loanLimit(game, current.id, tile.id), onClick: () => this.dispatch(tile.mortgaged === true ? 'release_mortgage' : 'mortgage_property', tile.id) },
                                    tile.mortgaged === true ? '解除抵押' : '抵押',
                                    " ",
                                    tile.title)),
                                React.createElement("p", { className: "purchase-info" },
                                    "\u4E0A\u65B9\u94F6\u884C\u4EA4\u6613\u91D1\u989D\u540C\u6837\u7528\u4E8E\u501F\u8D37\u3002\u5F53\u524D\u53EF\u501F ",
                                    Math.max(0, loanLimit(game, current.id) - (current.loanBalance ?? 0)),
                                    " \u6E38\u620F\u5E01\u3002"),
                                React.createElement("button", { type: "button", className: "secondary-btn", disabled: !/^[1-9][0-9]*$/.test(this.state.bankAmountInput) || Number(this.state.bankAmountInput) > loanLimit(game, current.id) - (current.loanBalance ?? 0), onClick: () => this.dispatch('borrow_loan') }, "\u501F\u5165\u8D37\u6B3E"),
                                React.createElement("button", { type: "button", className: "secondary-btn", disabled: !/^[1-9][0-9]*$/.test(this.state.bankAmountInput) || Number(this.state.bankAmountInput) > Math.min(current.cash, current.loanBalance ?? 0), onClick: () => this.dispatch('repay_loan') }, "\u507F\u8FD8\u8D37\u6B3E")),
                            game.market && React.createElement("div", { id: "stock-actions", className: "bank-actions stock-actions", role: "group", "aria-label": "\u80A1\u7968\u4EA4\u6613" },
                                React.createElement("strong", null,
                                    "\u865A\u62DF\u80A1\u7968\u4EA4\u6613\u6240 \u00B7 ",
                                    current.name),
                                React.createElement("p", { className: "purchase-info" }, "\u672C\u8F6E\u62A5\u4EF7 \u00B7 \u6BCF\u7B14\u4EA4\u6613\u624B\u7EED\u8D39 0.5%\uFF0C\u6700\u4F4E 1 \u6E38\u620F\u5E01\u3002\u4EC5\u4F7F\u7528\u624B\u6301\u73B0\u91D1\uFF0C\u6309\u5F53\u524D\u5E02\u573A\u4EF7\u6210\u4EA4\uFF1B\u884C\u60C5\u6BCF\u8F6E\u53D8\u5316\u3002"),
                                React.createElement("label", { htmlFor: "stock-amount" }, "\u80A1\u7968\u4EA4\u6613\u6570\u91CF\uFF08\u80A1\uFF09"),
                                React.createElement("input", { id: "stock-amount", type: "text", "aria-label": "\u80A1\u7968\u4EA4\u6613\u6570\u91CF", inputMode: "numeric", value: this.state.stockAmountInput, onChange: (event) => this.setState({ stockAmountInput: event.target.value }) }),
                                STOCKS.map(stock => {
                                    const quote = quoteMarket(game.market, stock.id);
                                    const lot = current.holdings?.[stock.id];
                                    const held = lot?.quantity ?? 0;
                                    const marketValue = held * quote;
                                    const pnl = marketValue - (lot?.costBasis ?? 0);
                                    return React.createElement("div", { className: "stock-entry", key: stock.id },
                                        React.createElement("div", null,
                                            React.createElement("strong", null, stock.name),
                                            "\uFF08",
                                            stock.id,
                                            "\uFF09 \u00B7 \u62A5\u4EF7 ",
                                            quote,
                                            " \u6E38\u620F\u5E01"),
                                        React.createElement("div", { className: "purchase-info" },
                                            "\u6301\u6709 ",
                                            held,
                                            " \u80A1 \u00B7 \u6210\u672C ",
                                            lot?.costBasis ?? 0,
                                            " \u00B7 \u5E02\u503C ",
                                            marketValue,
                                            " \u00B7 \u6D6E\u52A8\u76C8\u4E8F ",
                                            pnl >= 0 ? '+' : '',
                                            pnl),
                                        React.createElement("button", { type: "button", className: "secondary-btn", disabled: !/^[1-9][0-9]*$/.test(this.state.stockAmountInput) || quote * Number(this.state.stockAmountInput) + Math.max(1, Math.ceil(quote * Number(this.state.stockAmountInput) * 0.005)) > current.cash, onClick: () => this.dispatch('buy_stock', undefined, undefined, stock.id) },
                                            "\u4E70\u5165 ",
                                            stock.name),
                                        React.createElement("button", { type: "button", className: "secondary-btn", disabled: !/^[1-9][0-9]*$/.test(this.state.stockAmountInput) || Number(this.state.stockAmountInput) > held, onClick: () => this.dispatch('sell_stock', undefined, undefined, stock.id) },
                                            "\u5356\u51FA ",
                                            stock.name));
                                }),
                                React.createElement("p", { className: "purchase-info" },
                                    "\u6301\u4ED3\u5E02\u503C\uFF1A",
                                    STOCKS.reduce((sum, stock) => sum + (current.holdings?.[stock.id]?.quantity ?? 0) * quoteMarket(game.market, stock.id), 0).toLocaleString('zh-CN'),
                                    " \u6E38\u620F\u5E01\u3002")),
                            React.createElement("button", { type: "button", className: "primary-btn", onClick: () => this.dispatch('end_turn') },
                                "\u7ED3\u675F\u5F53\u524D\u56DE\u5408 ",
                                React.createElement("span", null, "\u2192"))),
                        game.phase === 'finished' && React.createElement("div", { className: "result-box", role: "status" },
                            React.createElement("strong", null, game.winnerId ? `${game.players.find(p => p.id === game.winnerId)?.name}获胜！` : '净资产并列，平局！'),
                            React.createElement("p", null, [...game.events].reverse().find(e => e.type === 'game_finished')?.details?.reason === 'bankruptcy' ? '结束原因：一方无法付清租金' : '结束原因：达到回合上限'),
                            React.createElement("p", null,
                                "\u6700\u7EC8\u51C0\u8D44\u4EA7\uFF1A",
                                game.players.map(p => `${p.name} ${netWorth(game, p.id)}`).join(' · ')),
                            React.createElement("p", null,
                                "\u672C\u5C40\u79CD\u5B50\uFF1A",
                                this.state.activeSeed),
                            React.createElement("button", { type: "button", className: "primary-btn", onClick: this.reset },
                                "\u518D\u6765\u4E00\u5C40 ",
                                React.createElement("span", null, "\u21BB"))),
                        React.createElement("p", { className: "turn-tip", role: "status" }, message)),
                    React.createElement("div", { className: "saves-card" },
                        React.createElement("div", { className: "card-label" }, "\u672C\u5730\u5B58\u6863"),
                        React.createElement("p", { className: "save-warning" }, "\u6E05\u9664\u6D4F\u89C8\u5668\u7AD9\u70B9\u6570\u636E\u6216\u5378\u8F7D\u5E94\u7528\u53EF\u80FD\u6C38\u4E45\u5220\u9664\u672C\u5730\u5B58\u6863\uFF1B\u8BF7\u5B9A\u671F\u4F7F\u7528\u300C\u5BFC\u51FA\u300D\u4FDD\u5B58 JSON \u5907\u4EFD\u3002"),
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
                                    game.bank ? ` · 存款 ${(p.bankBalance ?? 0).toLocaleString('zh-CN')}` : '',
                                    game.market ? ` · 股票 ${Object.values(p.holdings ?? {}).reduce((sum, lot) => sum + (lot?.quantity ?? 0), 0)} 股` : '',
                                    game.loan ? ` · 贷款 ${(p.loanBalance ?? 0).toLocaleString('zh-CN')}` : '',
                                    " \u00B7 \u51C0\u8D44\u4EA7 ",
                                    netWorth(game, p.id).toLocaleString('zh-CN'),
                                    p.detention ? ` · ${p.detention.kind === 'hospital' ? '住院' : '入狱'}剩余 ${p.detention.remaining} 回合` : '',
                                    p.bankrupt ? ' · 已破产' : '')),
                            React.createElement("span", { className: "player-kind" }, p.kind === 'human' ? '真人' : '电脑')))),
                    React.createElement("div", { className: "activity-card" },
                        React.createElement("div", { className: "card-label" }, "\u6700\u8FD1\u4E8B\u4EF6"),
                        React.createElement("ol", null, lastEvents.map((e, i) => React.createElement("li", { key: `${game.events.length}-${i}` }, this.describeEvent(e))))),
                    React.createElement("div", { className: "info-card" },
                        React.createElement("strong", null, "\u73A9\u6CD5\u8BF4\u660E"),
                        React.createElement("p", null, "\u2460 \u70B9\u51FB\u300C\u5F00\u59CB\u6E38\u620F\u300D\uFF0C\u8F6E\u5230\u73A9\u5BB6\u65F6\u63B7\u9AB0\u524D\u8FDB\u3002\u2461 \u5230\u65E0\u4E3B\u5730\u4EA7\u53EF\u4E70\u5165\u6216\u653E\u5F03\uFF1B\u7ECF\u8FC7\u5BF9\u624B\u5730\u4EA7\u4F1A\u81EA\u52A8\u4ED8\u79DF\u3002\u2462 \u5904\u7406\u5B8C\u5730\u5757\u540E\u7ED3\u675F\u56DE\u5408\uFF0C\u7535\u8111\u4F1A\u81EA\u52A8\u884C\u52A8\u3002"),
                        React.createElement("p", null, "\u4ED8\u4E0D\u8D77\u79DF\u91D1\u53EF\u80FD\u51FA\u552E\u5730\u4EA7\u6216\u7834\u4EA7\uFF1B\u6700\u7EC8\u6309\u73B0\u91D1\u3001\u5B58\u6B3E\u3001\u5730\u4EA7\u6210\u672C\u3001\u80A1\u7968\u5E02\u503C\u51CF\u8D37\u6B3E\u8BA1\u7B97\u51C0\u8D44\u4EA7\u3002\u7535\u8111\u8D2D\u5730\u540E\u81F3\u5C11\u4FDD\u7559 200 \u6E38\u620F\u5E01\u3002"),
                        React.createElement("p", null, "\u5361\u7247\u7AD9\u53EF\u83B7\u5F97\u5956\u52B1\u3001\u6B65\u6570\u3001\u9065\u63A7\u9AB0\u5B50\u3001\u8DEF\u969C\u53CA\u514D\u79DF\u5361\uFF1B\u53EA\u5728\u63B7\u9AB0\u524D\u4F7F\u7528\u3002\u8DEF\u969C\u8BA9\u5BF9\u624B\u63D0\u524D\u505C\u4E0B\uFF0C\u6700\u591A\u6301\u7EED\u4E24\u8F6E\uFF1B\u514D\u79DF\u5361\u4EC5\u4FDD\u62A4\u4E0B\u4E00\u6B21\u843D\u5730\u3002\u5B58\u6863\u4E0E\u79BB\u7EBF\u6E38\u73A9\u5747\u5728\u672C\u673A\u5B8C\u6210\u3002")))),
            React.createElement("footer", { className: "footer" },
                "\u7EAF\u524D\u7AEF \u00B7 \u7B80\u4F53\u4E2D\u6587 \u00B7 \u4E0D\u9700\u8981\u8D26\u53F7\u3000\uFF5C\u3000IndexedDB \u672C\u673A\u5B58\u6863 \u00B7 \u4E0D\u4E0A\u4F20\u4E91\u7AEF\u3000\uFF5C\u3000",
                React.createElement("a", { className: "visual-lab-link", href: "./visual-lab.html" }, "\u539F\u521B\u7F8E\u672F\u6837\u4F8B"))));
    }
}
const root = document.getElementById('root');
if (!root)
    throw new Error('找不到游戏页面根节点');
ReactDOM.render(React.createElement(App, {}), root);
