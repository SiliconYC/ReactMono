import { applyAction, createGame, type GameAction, type CardKind, type GameEvent, type GameState, type Tile, netWorth } from '../core/game.js';
import { chooseComputerAction } from '../core/agent.js';
import { listSlots, readSlot, writeSlot, deleteSlot, type SlotSummary } from '../storage/indexeddb.js';
import { deserializeGame, MAX_SAVE_CHARS, type SaveEnvelope } from '../core/save.js';

interface UiState { readonly game: GameState; readonly message: string; readonly seedInput: string; readonly fastMode: boolean; readonly activeSeed: number | null; readonly saveSlots: readonly SlotSummary[]; readonly saveStatus: string; readonly storageBusy: boolean; readonly importPreview: SaveEnvelope | null; readonly importName: string; readonly offline: boolean; readonly pwaUpdate: boolean; readonly pwaMessage: string; }

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
    this.state = { game: createGame(20261015), seedInput: '20261015', fastMode: false, activeSeed: null, saveSlots: [], saveStatus: '正在读取本地存档…', storageBusy: false, importPreview: null, importName: '', offline: typeof navigator==='undefined'?false:!navigator.onLine, pwaUpdate:false, pwaMessage:'', message: '设置对局种子并点击「开始游戏」，然后掷骰沿着 24 格棋盘前进。' };
  }

  private computerTimer: number | null = null;

  private saveEpoch = 0;
  private saveQueue: Promise<void> = Promise.resolve();

  private pwaRegistration:ServiceWorkerRegistration|null=null;
  private shouldReload=false;
  private updateOnline=():void=>{this.setState({offline:!navigator.onLine});};
  private controllerChanged=():void=>{if(this.shouldReload)window.location.reload();};
  private checkUpdate = (reg:ServiceWorkerRegistration):void => {
    if(reg.waiting && navigator.serviceWorker.controller)this.setState({pwaUpdate:true});
  };
  private initPwa = async():Promise<void> => {
    if(!('serviceWorker' in navigator)){this.setState({pwaMessage:'本浏览器不支持应用安装，仍可在线游玩。'});return;}
    try{
      navigator.serviceWorker.addEventListener('controllerchange',this.controllerChanged);
      const reg=await navigator.serviceWorker.register('./sw.js',{scope:'./'});
      this.pwaRegistration=reg;
      reg.addEventListener('updatefound',()=>{
        const worker=reg.installing;
        worker?.addEventListener('statechange',()=>{
          if(worker.state==='installed')this.checkUpdate(reg);
        });
      });
      this.checkUpdate(reg);
    }catch(e){this.setState({pwaMessage:'离线缓存安装失败，在线游戏仍可使用：'+(e instanceof Error?e.message:String(e))});}
  };
  private applyPwaUpdate=async():Promise<void>=>{
    const worker=this.pwaRegistration?.waiting;
    if(!worker)return;
    await this.saveQueue;
    this.shouldReload=true;
    worker.postMessage('SKIP_WAITING');
  };
  componentDidMount():void {
    void this.refreshSlots();
    window.addEventListener('online',this.updateOnline);
    window.addEventListener('offline',this.updateOnline);
    void this.initPwa();
  }
  private stopTimer():void {
    if(this.computerTimer!==null){window.clearTimeout(this.computerTimer);this.computerTimer=null;}
  }
  private refreshSlots = async ():Promise<void> => {
    try {
      const saveSlots=await listSlots();
      this.setState({saveSlots,saveStatus:this.state.saveStatus==='正在读取本地存档…'?'本地存档已就绪':this.state.saveStatus});
    }catch(e){this.setState({saveStatus:'本地存储不可用：'+(e instanceof Error?e.message:String(e))+'。请检查无痕模式或磁盘空间。'});}
  };
  private scheduleAutosave(game:GameState):void {
    const epoch=this.saveEpoch;
    this.saveQueue=this.saveQueue.then(async()=>{
      if(epoch!==this.saveEpoch)return;
      await writeSlot('auto','自动存档','auto',game);
      if(epoch!==this.saveEpoch)return;
      // 后台自动保存不可盖掉文件损坏、导入冲突等用户必须看见的提示。
      if(this.state.saveStatus==='本地存档已就绪'||this.state.saveStatus.startsWith('自动保存成功'))
        this.setState({saveStatus:'自动保存成功 · 第 '+game.round+' 轮'});
      await this.refreshSlots();
    }).catch(e=>{
      if(epoch===this.saveEpoch)this.setState({saveStatus:'自动保存失败：'+(e instanceof Error?e.message:String(e))+'。请手动导出备份。'});
    });
  }

  private exportSlot = async (slot:SlotSummary):Promise<void> => {
    try{
      const backup=await readSlot(slot.id);
      const content=JSON.stringify(backup,null,2);
      const blob=new Blob([content],{type:'application/json;charset=utf-8'});
      const url=URL.createObjectURL(blob);
      const link=document.createElement('a');
      const filename=slot.name.replace(/[\\/:*?"<>|]/g,'_');
      link.href=url;
      link.download='存档-'+filename+'-'+backup.updatedAt.slice(0,10).replaceAll('-','')+'.json';
      document.body.appendChild(link);
      link.click();link.remove();
      window.setTimeout(()=>URL.revokeObjectURL(url),1000);
      this.setState({saveStatus:'已生成「'+slot.name+'」备份文件，请自行保管。'});
    }catch(e){this.setState({saveStatus:'导出失败：'+(e instanceof Error?e.message:String(e))});}
  };
  private selectImport = async (event:{target:{files:FileList|null;value:string}}):Promise<void> => {
    const file=event.target.files?.[0];
    event.target.value='';
    if(!file)return;
    this.setState({importPreview:null});
    if(file.size>MAX_SAVE_CHARS){this.setState({saveStatus:'导入失败：文件过大，最多 4 MB'});return;}
    try{
      const raw=await file.text();
      const preview=deserializeGame(raw);
      const filename=file.name.replace(/^存档-(.*)-[0-9]{8}\.json$/i,'$1').replace(/\.json$/i,'');
      const name=(filename.trim()||'导入存档').slice(0,60);
      this.setState({importPreview:preview,importName:name,saveStatus:'文件校验通过，请预览并选择导入方式。'});
    }catch(e){this.setState({saveStatus:'导入失败：'+(e instanceof Error?e.message:String(e))+'。原存档未改动。'});}
  };
  private applyImport = async (mode:'new'|'overwrite'):Promise<void> => {
    const {importPreview,saveSlots}=this.state;
    if(!importPreview||this.state.storageBusy)return;
    const name=this.state.importName.trim();
    if(!name||name.length>60){this.setState({saveStatus:'请输入 1 至 60 个字符的存档名称'});return;}
    const duplicate=saveSlots.find(s=>s.name===name);
    if(mode==='overwrite'&&!duplicate)return;
    const id=mode==='overwrite'&&duplicate?duplicate.id:'manual-'+crypto.randomUUID();
    const newName=mode==='new'&&duplicate?name+'（副本）':name;
    if(newName.length>60){this.setState({saveStatus:'副本名称过长，请先缩短名称'});return;}
    try{
      await writeSlot(id,newName,'manual',importPreview.game);
      this.setState({importPreview:null,importName:'',saveStatus:'「'+newName+'」已安全导入，可点击读取继续对局。'});
      await this.refreshSlots();
    }catch(e){this.setState({saveStatus:'写入失败：'+(e instanceof Error?e.message:String(e))+'。原存档未被修改。'});}
  };

  private newManualSlot = async ():Promise<void> => {
    if(this.state.game.status==='setup' || this.state.storageBusy)return;
    const name=window.prompt('输入新存档名称','存档 '+new Date().toLocaleString('zh-CN'))?.trim();
    if(!name)return;
    if(name.length>60){this.setState({saveStatus:'名称最多 60 个字符'});return;}
    try {
      await writeSlot('manual-'+crypto.randomUUID(),name,'manual',this.state.game);
      this.setState({saveStatus:'手动存档「'+name+'」保存成功'});
      await this.refreshSlots();
    }catch(e){this.setState({saveStatus:'手动保存失败：'+(e instanceof Error?e.message:String(e))});}
  };
  private overwriteSlot = async (slot:SlotSummary):Promise<void> => {
    if(this.state.game.status==='setup'||slot.kind!=='manual'||this.state.storageBusy)return;
    if(!window.confirm('确定用当前对局覆盖「'+slot.name+'」吗？'))return;
    try {
      await writeSlot(slot.id,slot.name,'manual',this.state.game);
      this.setState({saveStatus:'已覆盖「'+slot.name+'」'});
      await this.refreshSlots();
    }catch(e){this.setState({saveStatus:'覆盖失败：'+(e instanceof Error?e.message:String(e))});}
  };
  private restoreSlot = async (slot:SlotSummary):Promise<void> => {
    if(this.state.storageBusy)return;
    if(!window.confirm('读取「'+slot.name+'」将替换屏幕上的当前游戏，是否继续？'))return;
    this.saveEpoch++;
    this.stopTimer();
    this.setState({storageBusy:true,saveStatus:'正在读取「'+slot.name+'」…'});
    try {
      await this.saveQueue;
      const saved=await readSlot(slot.id);
      this.setState({game:saved.game,activeSeed:null,storageBusy:false,
        saveStatus:'已读取「'+slot.name+'」',message:'已恢复第 '+saved.game.round+' 轮，可从当前阶段继续。'});
    }catch(e){this.setState({storageBusy:false,saveStatus:'读档失败：'+(e instanceof Error?e.message:String(e))+'。原对局未被修改。'});}
  };
  private removeSlot = async (slot:SlotSummary):Promise<void> => {
    if(this.state.storageBusy||!window.confirm('确定永久删除「'+slot.name+'」吗？'))return;
    try{await deleteSlot(slot.id);this.setState({saveStatus:'已删除「'+slot.name+'」'});await this.refreshSlots();}
    catch(e){this.setState({saveStatus:'删除失败：'+(e instanceof Error?e.message:String(e))});}
  };

  reset = (): void => {
    this.saveEpoch++;
    this.stopTimer();
    this.setState({ game: createGame(20261015), activeSeed: null, message: '已返回新游戏页面。可调整种子后重新开始。' });
  };
  startGame = (): void => {
    const seed = Number(this.state.seedInput.trim());
    if (!/^\d{1,10}$/.test(this.state.seedInput.trim()) || !Number.isSafeInteger(seed) || seed > 4294967295) {
      this.setState({ message: '对局种子请输入 0 至 4294967295 之间的整数。' });
      return;
    }
    this.saveEpoch++;
    this.stopTimer();
    const fresh = createGame(seed);
    const result = applyAction(fresh, { type: 'start_game', actorId: fresh.players[0].id });
    if (!result.ok) { this.setState({ message: '无法开始对局，请重新开局。' }); return; }
    this.setState({ game: result.state, activeSeed: seed, message: '游戏已开始！轮到玩家掷骰。' });
  };
  componentWillUnmount(): void {
    window.removeEventListener('online',this.updateOnline);
    window.removeEventListener('offline',this.updateOnline);
    navigator.serviceWorker?.removeEventListener('controllerchange',this.controllerChanged);
    this.stopTimer();
  }

  /** 每次状态变化只安排电脑的一步；重开后旧回调不会碰新对局。 */
  componentDidUpdate(_prevProps:object, prevState:UiState): void {
    if(this.state.game!==prevState.game && this.state.game.status!=='setup') this.scheduleAutosave(this.state.game);
    if(this.state.storageBusy)return;
    const snapshot = this.state.game;
    if (snapshot.status !== 'playing' || snapshot.players[snapshot.currentPlayerIndex].kind !== 'computer' || this.computerTimer !== null) return;
    this.computerTimer = window.setTimeout(() => {
      this.computerTimer = null;
      if (this.state.game !== snapshot || this.state.storageBusy) return;
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

  dispatch = (type: GameAction['type'],tileId?:number,cardType?:CardKind): void => {
    if(this.state.storageBusy)return;
    const { game } = this.state;
    const actor = game.players[game.currentPlayerIndex];
    if (actor.kind === 'computer') return;
    const action:GameAction=type==='upgrade_property'?{type,actorId:actor.id,tileId:tileId??-1}
      :type==='use_card'?{type,actorId:actor.id,cardType:cardType??'reward'}:{type,actorId:actor.id};
    const result = applyAction(game,action);
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
    const upgraded=events.find(e=>e.type==='property_upgraded');
    if(upgraded)return `${actorName}升级了 ${upgraded.details?.tileId} 号地产至 ${upgraded.details?.level} 级，花费 ${upgraded.details?.amount} 游戏币。`;
    const used=events.find(e=>e.type==='card_used');
    if(used)return used.details?.cardType==='reward'?`${actorName}使用奖励卡，获得 ${used.details?.amount} 游戏币。`:`${actorName}使用步数卡，下次掷骰额外前进 ${used.details?.moveBonus} 格。`;
    const special=events.find(e=>e.type==='event_bonus'||e.type==='event_fee');
    if(special)return special.type==='event_bonus' ? `${actorName}触发幸运事件，获得 ${special.details?.amount} 游戏币。` : `${actorName}触发费用事件，支付 ${special.details?.amount} 游戏币（应付 ${special.details?.due}）。`;
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
      case 'card_received': return `${person}在卡片站获得${event.details?.cardType==='reward'?'奖励卡':'步数卡'}`;
      case 'card_used': return `${person}使用${event.details?.cardType==='reward'?'奖励卡':'步数卡'}`;
      case 'event_bonus': return `${person}在事件格获得 ${event.details?.amount} 游戏币`;
      case 'event_fee': return `${person}在事件格支付 ${event.details?.amount} 游戏币`;
      case 'property_upgraded': return `${person}将 ${event.details?.tileId} 号地产升到 ${event.details?.level} 级（${event.details?.amount}）`;
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
        <span className="tile-icon" aria-hidden="true">{tile.kind === 'start' ? '★' : tile.kind === 'property' ? '⌂' : tile.eventBonus!==undefined ? '✦' : tile.cardStation ? '▣' : '☕'}</span>
        <span className="tile-name">{tile.eventBonus!==undefined?'机会':tile.cardStation?'卡片':kindLabel[tile.kind]}{tile.kind === 'property' ? ` ${tile.id}` : ''}</span>
        {tile.kind === 'property' && <span className="tile-value">{tile.ownerId ? `${tile.ownerId === 'p1' ? '玩家' : '电脑'} · ${tile.level??0}级 · 租 ${tile.levelRents?.[tile.level??0]??tile.rent}` : `售价 ${tile.price}`}</span>}
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
          <span className="version-tag">P2 · 可离线</span>
          <span className="network-indicator" role="status">{this.state.offline?'已断网 · 可用本地缓存':'已联网'}{this.state.pwaMessage?' · '+this.state.pwaMessage:''}</span>
          {this.state.pwaUpdate&&<button className="secondary-btn" type="button" onClick={()=>void this.applyPwaUpdate()}>检测到新版，保存并更新</button>}
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
              {current.kind === 'human' && game.phase === 'await_roll' && <div className="purchase-actions">
                <p className="purchase-info">手牌：奖励卡 {current.cards?.reward??0} 张 · 步数卡 {current.cards?.stride??0} 张{(game.pendingMoveBonus??0)>0?` · 已加步数 ${game.pendingMoveBonus}`:''}</p>
                {(current.cards?.reward??0)>0&&<button type="button" className="secondary-btn" onClick={()=>this.dispatch('use_card',undefined,'reward')}>使用奖励卡（+{game.cardRules?.rewardCash??80} 游戏币）</button>}
                {(current.cards?.stride??0)>0&&(game.pendingMoveBonus??0)===0&&<button type="button" className="secondary-btn" onClick={()=>this.dispatch('use_card',undefined,'stride')}>使用步数卡（+{game.cardRules?.moveBonus??2} 格）</button>}
                <button type="button" className="primary-btn" onClick={() => this.dispatch('roll')}>掷骰前进 <span>🎲</span></button>
              </div>}
              {current.kind === 'human' && game.phase === 'await_decision' && <div className="purchase-actions">
                <p className="purchase-info">{targetTile.title}　售价 <b>{targetTile.price}</b>　过路费 <b>{targetTile.rent}</b></p>
                <button type="button" className="primary-btn" onClick={() => this.dispatch('buy_property')} disabled={!hasMoneyForLand}>购买地产 <span>⌂</span></button>
                {!hasMoneyForLand && <p className="insufficient-msg">资金不足，不能购买此地。</p>}
                <button type="button" className="secondary-btn" onClick={() => this.dispatch('decline_property')}>放弃购买，继续回合 →</button>
              </div>}
              {current.kind === 'human' && game.phase === 'await_end_turn' && <div className="purchase-actions">
                {game.tiles.filter(t=>t.kind==='property'&&t.ownerId===current.id&&(t.level??0)<2).map(tile=><button type="button" key={tile.id} className="secondary-btn" disabled={current.cash<(tile.upgradeCosts?.[tile.level??0]??Infinity)} onClick={()=>this.dispatch('upgrade_property',tile.id)}>升级 {tile.title} → {(tile.level??0)+1} 级 · 费用 {tile.upgradeCosts?.[tile.level??0]}</button>)}
                <button type="button" className="primary-btn" onClick={() => this.dispatch('end_turn')}>结束当前回合 <span>→</span></button>
              </div>}
              {game.phase === 'finished' && <div className="result-box" role="status"><strong>{game.winnerId ? `${game.players.find(p => p.id === game.winnerId)?.name}获胜！` : '双方平局！'}</strong><p>{[...game.events].reverse().find(e => e.type === 'game_finished')?.details?.reason === 'bankruptcy' ? '结束原因：一方无法付清租金' : '结束原因：达到回合上限'}</p><p>最终净资产：玩家 {netWorth(game,'p1')} · 电脑 {netWorth(game,'p2')}</p><p>本局种子：{this.state.activeSeed}</p><button type="button" className="primary-btn" onClick={this.reset}>再来一局 <span>↻</span></button></div>}
              <p className="turn-tip" role="status">{message}</p>
            </div>
            <div className="saves-card">
              <div className="card-label">本地存档</div>
              <p className="save-message" role="status">{this.state.saveStatus}</p>
              <button type="button" className="secondary-btn" disabled={game.status==='setup'||this.state.storageBusy} onClick={()=>void this.newManualSlot()}>创建手动存档</button>
              <ul className="save-list">{this.state.saveSlots.map(slot=><li key={slot.id}>
                <div><strong>{slot.name}</strong><small>{slot.kind==='auto'?'自动':'手动'} · {new Date(slot.updatedAt).toLocaleString('zh-CN')}</small></div>
                <div className="save-actions">
                  <button type="button" disabled={this.state.storageBusy} onClick={()=>void this.restoreSlot(slot)}>读取</button>
                  <button type="button" disabled={this.state.storageBusy} onClick={()=>void this.exportSlot(slot)}>导出</button>
                  {slot.kind==='manual' && <button type="button" disabled={this.state.storageBusy||game.status==='setup'} onClick={()=>void this.overwriteSlot(slot)}>覆盖</button>}
                  <button type="button" disabled={this.state.storageBusy} onClick={()=>void this.removeSlot(slot)}>删除</button>
                </div>
              </li>)}</ul>
              <label className="import-label">从本机文件导入（只读取 JSON，不上传云端）
                <input type="file" accept=".json,application/json" aria-label="导入 JSON 存档文件" onChange={(event:{target:{files:FileList|null;value:string}})=>void this.selectImport(event)} />
              </label>
              {this.state.importPreview && <div className="import-preview" role="region" aria-label="存档导入预览">
                <strong>导入预览：第 {this.state.importPreview.game.round} 轮</strong>
                <p>玩家现金 {this.state.importPreview.game.players[0].cash}，电脑现金 {this.state.importPreview.game.players[1].cash}；
                已有地产 {this.state.importPreview.game.tiles.filter(t=>t.ownerId!==null).length} 块；
                当前阶段 {this.state.importPreview.game.phase}</p>
                <label>存档名称 <input aria-label="导入存档名称" type="text" maxLength={60} value={this.state.importName} onChange={(e:{target:{value:string}})=>this.setState({importName:e.target.value})}/></label>
                {this.state.saveSlots.some(s=>s.name===this.state.importName.trim())?<div className="save-actions">
                  <button type="button" onClick={()=>void this.applyImport('overwrite')}>覆盖同名存档</button>
                  <button type="button" onClick={()=>void this.applyImport('new')}>另存为副本</button>
                </div>:<button type="button" className="secondary-btn" onClick={()=>void this.applyImport('new')}>确认导入存档</button>}
                <button type="button" className="secondary-btn" onClick={()=>this.setState({importPreview:null,importName:'',saveStatus:'已取消导入'})}>取消导入</button>
              </div>}
            </div>
            <div className="players-card"><div className="card-label">玩家状态</div>{game.players.map(p => <div key={p.id} className={`player-line ${current.id === p.id && game.status === 'playing' ? 'is-current' : ''}`}><span className={`player-dot ${p.kind}`}>{p.kind === 'human' ? '人' : '机'}</span><div><strong>{p.name}</strong><small>{p.position} 号格 · 现金 {p.cash.toLocaleString('zh-CN')} · 资产 {netWorth(game,p.id).toLocaleString('zh-CN')}{p.bankrupt ? ' · 已破产' : ''}</small></div><span className="player-kind">{p.kind === 'human' ? '真人' : '电脑'}</span></div>)}</div>
            <div className="activity-card"><div className="card-label">最近事件</div><ol>{lastEvents.map((e,i) => <li key={`${game.events.length}-${i}`}>{this.describeEvent(e)}</li>)}</ol></div>
            <div className="info-card"><strong>玩法说明</strong><p>① 点击「开始游戏」，轮到玩家时掷骰前进。② 到无主地产可买入或放弃；经过对手地产会自动付租。③ 处理完地块后结束回合，电脑会自动行动。</p><p>付不起租金立即破产；否则最多玩 60 轮，最终按现金加土地原价计算净资产。电脑购地后至少保留 200 游戏币。</p><p>P2 已支持地产升级、机会格、奖励卡和步数卡；卡片在卡片站获得，只能在掷骰前使用。存档与离线游玩均在本机完成。</p></div>
          </aside>
        </div>
        <footer className="footer">纯前端 · 简体中文 · 不需要账号　｜　IndexedDB 本机存档 · 不上传云端</footer>
      </main>
    );
  }
}
const root = document.getElementById('root');
if (!root) throw new Error('找不到游戏页面根节点');
ReactDOM.render(React.createElement(App, {}), root);
