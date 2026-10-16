import { applyAction, createGame, type GameAction, type CardKind, type GameEvent, type GameState, type Tile, type GameMap, type PlayerConfig, DEFAULT_CONFIG, HARBOR_CONFIG, netWorth, resaleValue, loanLimit, STOCKS, quoteMarket, type StockId } from '../core/game.js';
import { chooseComputerAction } from '../core/agent.js';
import { COMPUTER_STYLES, COMPUTER_STYLE_NAMES } from '../core/strategic-agent.js';
import { listSlots, readSlot, writeSlot, deleteSlot, type SlotSummary } from '../storage/indexeddb.js';
import { deserializeGame, MAX_SAVE_CHARS, type SaveEnvelope } from '../core/save.js';

interface UiState { readonly game: GameState; readonly message: string; readonly seedInput: string; readonly bankAmountInput: string; readonly stockAmountInput: string; readonly strategyDieInput:string; readonly roadblockTileInput:string; readonly playerSetup: readonly PlayerConfig[]; readonly roundsInput: string; readonly selectedMapId:string; readonly selectedTileId:number|null; readonly awaitingHandoff: boolean; readonly fastMode: boolean; readonly specialEnabled:boolean; readonly activeSeed: number | null; readonly saveSlots: readonly SlotSummary[]; readonly saveStatus: string; readonly storageBusy: boolean; readonly importPreview: SaveEnvelope | null; readonly importName: string; readonly offline: boolean; readonly pwaUpdate: boolean; readonly pwaMessage: string; }

/** Read screen positions from map data, never infer them from the tile ID. */
function cellPosition(map:GameMap,index:number):{gridColumn:number;gridRow:number}{
  const point=map.cells[index];
  return {gridColumn:point.column,gridRow:point.row};
}

const kindLabel: Record<Tile['kind'], string> = { start: '起点', property: '地产', neutral: '休息' };

class App extends React.Component<object, UiState> {
  constructor(props: object) {
    super(props);
    this.state = { game: createGame(20261015), seedInput: '20261015', bankAmountInput:'100', stockAmountInput:'1', strategyDieInput:'1', roadblockTileInput:'1', playerSetup: [{id:'p1',name:'玩家',kind:'human'},{id:'p2',name:'电脑',kind:'computer',computerStyle:'balanced'}], roundsInput:'60', selectedMapId:'classic-24', selectedTileId:0, awaitingHandoff:false, fastMode: false, specialEnabled:false, activeSeed: null, saveSlots: [], saveStatus: '正在读取本地存档…', storageBusy: false, importPreview: null, importName: '', offline: typeof navigator==='undefined'?false:!navigator.onLine, pwaUpdate:false, pwaMessage:'', message: '设置对局种子并点击「开始游戏」，然后掷骰沿着 24 格棋盘前进。' };
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
      this.setState({game:saved.game,activeSeed:null,storageBusy:false,awaitingHandoff:false,
        roundsInput:String(saved.game.maxRounds),selectedMapId:saved.game.map.id,selectedTileId:saved.game.players[saved.game.currentPlayerIndex].position,
        playerSetup:saved.game.players.map(p=>({id:p.id,name:p.name,kind:p.kind,...(p.computerStyle?{computerStyle:p.computerStyle}:{})})),
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
    const base=this.state.selectedMapId==='harbor-20'?HARBOR_CONFIG:DEFAULT_CONFIG;
    this.setState({ game: createGame(20261015,base), activeSeed: null, selectedTileId:0, awaitingHandoff:false, message: '已返回新游戏页面。可调整种子及地图后重新开始。' });
  };
  /** Keep stable IDs when the local seating plan changes. */
  private setPlayerCount = (count: number): void => {
    if(!Number.isInteger(count)||count<2||count>4)return;
    const roster=Array.from({length:count},(_,i)=>this.state.playerSetup[i]??{
      id:'p'+(i+1),name:'玩家'+(i+1),kind:'human' as const
    });
    this.setState({playerSetup:roster});
  };
  private updatePlayer = (index:number,field:'name'|'kind',value:string):void=>{
    const roster=this.state.playerSetup.map((p,i)=>{
      if(i!==index)return p;
      const {computerStyle:_previous,...rest}=p;
      return field==='kind' ? {...rest,kind:value as 'human'|'computer',...(value==='computer'?{computerStyle:p.computerStyle??'balanced'}:{})}
        : {...p,name:value};
    });
    this.setState({playerSetup:roster});
  };
  private selectMap = (id:string):void=>{
    if(id!=='classic-24'&&id!=='harbor-20')return;
    const base=id==='harbor-20'?HARBOR_CONFIG:DEFAULT_CONFIG;
    this.setState({selectedMapId:id,selectedTileId:0,game:createGame(20261015,{...base,players:this.state.playerSetup}),
      message:id==='harbor-20'?'已选择海港环线：20 格，独立价格及海港主题地产。':'已选择经典环线：24 格，原有规则完整保留。'});
  };
  private acknowledgeHandoff = ():void=>{
    this.setState({awaitingHandoff:false,message:'已轮到'+this.state.game.players[this.state.game.currentPlayerIndex].name+'操作。'});
  };
  startGame = (): void => {
    const seed = Number(this.state.seedInput.trim());
    if (!/^\d{1,10}$/.test(this.state.seedInput.trim()) || !Number.isSafeInteger(seed) || seed > 4294967295) {
      this.setState({ message: '对局种子请输入 0 至 4294967295 之间的整数。' });
      return;
    }
    const rawRounds=this.state.roundsInput.trim();
    const rounds=Number(rawRounds);
    if(!/^[0-9]{1,3}$/.test(rawRounds)||!Number.isSafeInteger(rounds)||rounds<1||rounds>200){
      this.setState({message:'最大轮数必须是 1 至 200 的整数。'});return;
    }
    const roster=this.state.playerSetup.map(p=>({...p,name:p.name.trim(),
      ...(p.kind==='computer'?{computerStyle:p.computerStyle??'balanced'}:{})}));
    if(roster.some(p=>!p.name||p.name.length>24)||new Set(roster.map(p=>p.name)).size!==roster.length){
      this.setState({message:'所有玩家都必须填写不同的姓名（最多 24 字）。'});return;
    }
    let fresh:GameState;
    try{fresh=createGame(seed,{...(this.state.selectedMapId==='harbor-20'?HARBOR_CONFIG:DEFAULT_CONFIG),players:roster,maxRounds:rounds,automaticLiquidation:true,bankEnabled:true,loanEnabled:true,marketEnabled:true,strategyEnabled:true,specialEnabled:this.state.specialEnabled});}
    catch(e){this.setState({message:'开局配置无效：'+(e instanceof Error?e.message:String(e))});return;}
    this.saveEpoch++;
    this.stopTimer();
    const result = applyAction(fresh, { type: 'start_game', actorId: fresh.players[0].id });
    if (!result.ok) { this.setState({ message: '无法开始对局，请重新开局。' }); return; }
    this.setState({ game: result.state, activeSeed: seed,selectedTileId:0, awaitingHandoff:false, message: '游戏已开始！轮到'+fresh.players[0].name+'掷骰。' });
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

  dispatch = (type: GameAction['type'],tileId?:number,cardType?:CardKind,stockId?:StockId): void => {
    if(this.state.storageBusy||this.state.awaitingHandoff)return;
    const { game } = this.state;
    const actor = game.players[game.currentPlayerIndex];
    if (actor.kind === 'computer') return;
    const bankAmount=/^[1-9][0-9]{0,12}$/.test(this.state.bankAmountInput.trim())?Number(this.state.bankAmountInput.trim()):NaN;
    const stockAmount=/^[1-9][0-9]{0,6}$/.test(this.state.stockAmountInput.trim())?Number(this.state.stockAmountInput.trim()):NaN;
    const action:GameAction=(type==='buy_stock'||type==='sell_stock')?{type,actorId:actor.id,stockId:stockId??'SEA',quantity:stockAmount}
      :(type==='upgrade_property'||type==='sell_property'||type==='mortgage_property'||type==='release_mortgage')?{type,actorId:actor.id,tileId:tileId??-1}
      :type==='deposit_bank'||type==='withdraw_bank'||type==='borrow_loan'||type==='repay_loan'?{type,actorId:actor.id,amount:bankAmount}
      :type==='buy_shop_card'?{type,actorId:actor.id,cardType:cardType??'reward'}
      :type==='use_card'?{type,actorId:actor.id,cardType:cardType??'reward',
          ...(cardType==='remote'?{dieValue:Number(this.state.strategyDieInput)}:{}),
          ...(cardType==='roadblock'?{tileId:Number(game.tiles.some(t=>t.id===Number(this.state.roadblockTileInput)&&t.id!==0&&t.id!==actor.position&&!game.players.some(p=>!p.bankrupt&&p.position===t.id)&&!game.roadblocks?.some(b=>b.tileId===t.id))?this.state.roadblockTileInput:game.tiles.find(t=>t.id!==0&&t.id!==actor.position&&!game.players.some(p=>!p.bankrupt&&p.position===t.id)&&!game.roadblocks?.some(b=>b.tileId===t.id))?.id??-1)}:{})}:{type,actorId:actor.id};
    const highRisk=type==='mortgage_property'||type==='borrow_loan'||
      ((type==='buy_stock'||type==='sell_stock')&&Number.isFinite(stockAmount)&&stockAmount>=50);
    if(highRisk){
      const detail=type==='mortgage_property'?'确认抵押地产？抵押后该地产暂不收租，贷款违约可能被银行收回。'
        :type==='borrow_loan'?'确认借入 '+bankAmount+' 游戏币？贷款计息且可能触发抵押物清算。'
        :'确认'+(type==='buy_stock'?'买入':'卖出')+' '+stockAmount+' 股？股票成交后价格会波动，且需支付手续费。';
      if(!window.confirm(detail)){this.setState({message:'已取消操作，本局资产没有变化。'});return;}
    }
    const result = applyAction(game,action);
    if (!result.ok) {
      const bankAction=type==='deposit_bank'||type==='withdraw_bank'||type==='borrow_loan'||type==='repay_loan';
      const stockAction=type==='buy_stock'||type==='sell_stock';
      const reason=result.reason==='INVALID_ACTOR'?'当前操作玩家已变更，请查看上方高亮玩家。'
        :stockAction ? (result.reason==='INSUFFICIENT_FUNDS'?'股票交易未执行：现金不足或持仓数量不够。':'股票交易未执行：请输入有效股数，交易仅限当前玩家的结算阶段。')
        :bankAction ? (result.reason==='INSUFFICIENT_FUNDS'?'银行或借贷操作未执行：现金、存款或可借额度不足。':'银行或借贷操作未执行：金额必须是有效正整数，且只能在本人结算阶段操作。')
        :result.reason==='INSUFFICIENT_FUNDS'?'操作未执行：现金不足。':'操作未执行：当前阶段或目标不合法，请检查所选地产、卡片目标和行动玩家。';
      this.setState({ message: reason });
      return;
    }
    const next=result.state.players[result.state.currentPlayerIndex];
    const handoff=type==='end_turn' && result.state.status==='playing'
      && next.kind==='human' && next.id!==actor.id;
    this.setState({ game: result.state, awaitingHandoff:handoff,
      message:handoff?'请将设备交给 '+next.name+'；确认就位后方可继续。':this.describe(result.events, result.state, actor.name) });
  };

  describe = (events: readonly GameEvent[], state: GameState, actorName: string): string => {
    const finished = events.find(e => e.type === 'game_finished');
    if (finished) {
      const winner = state.players.find(p => p.id === state.winnerId);
      const reason = finished.details?.reason === 'bankruptcy' ? '租金不足，发生破产。' : '达到 60 轮上限。';
      return `${reason}${winner ? `赢家是${winner.name}！` : '双方净资产相同，平局！'}`;
    }
    if (events.some(e => e.type === 'game_started')) return '对局已开始！';
    const stockEvent=events.find(e=>e.type==='stock_bought'||e.type==='stock_sold'||e.type==='stock_liquidated');
    if(stockEvent)return this.describeEvent(stockEvent);
    const bankEvent=events.find(e=>e.type==='bank_deposited'||e.type==='bank_withdrawn');
    if(bankEvent)return bankEvent.type==='bank_deposited'?`${actorName}存入银行 ${bankEvent.details?.amount} 游戏币。`:`${actorName}取出存款 ${bankEvent.details?.amount} 游戏币。`;
    const loanEvent=events.find(e=>['property_mortgaged','property_released','loan_borrowed','loan_repaid','loan_default','loan_interest'].includes(e.type));
    if(loanEvent)return this.describeEvent(loanEvent);
    const interest=events.filter(e=>e.type==='bank_interest');
    if(interest.length)return `本轮银行结息 ${interest.length} 笔，总计 ${interest.reduce((sum,e)=>sum+Number(e.details?.amount??0),0)} 游戏币。`;
    const upgraded=events.find(e=>e.type==='property_upgraded');
    if(upgraded)return `${actorName}升级了 ${upgraded.details?.tileId} 号地产至 ${upgraded.details?.level} 级，花费 ${upgraded.details?.amount} 游戏币。`;
    const used=events.find(e=>e.type==='card_used');
    if(used)return used.details?.cardType==='reward'?`${actorName}使用奖励卡，获得 ${used.details?.amount} 游戏币。`:
      used.details?.cardType==='stride'?`${actorName}使用步数卡，下次掷骰额外前进 ${used.details?.moveBonus} 格。`:
      this.describeEvent(used);
    const special=events.find(e=>e.type==='event_bonus'||e.type==='event_fee');
    if(special)return special.type==='event_bonus' ? `${actorName}触发幸运事件，获得 ${special.details?.amount} 游戏币。` : `${actorName}触发费用事件，支付 ${special.details?.amount} 游戏币（应付 ${special.details?.due}）。`;
    const bought = events.find(e => e.type === 'property_bought');
    if (bought) return `${actorName}花费 ${bought.details?.amount} 游戏币购买了 ${bought.details?.tileId} 号地产。现在可以结束回合。`;
    const sold=events.find(e=>e.type==='property_sold');
    if(sold)return `${actorName}出售了 ${sold.details?.tileId} 号地产，获得 ${sold.details?.amount} 游戏币。`;
    const rent = events.find(e => e.type === 'rent_paid');
    if (rent) return `${actorName}落在对手地产，${events.some(e=>e.type==='property_liquidated')?'已自动出售地产救急，':''}支付 ${rent.details?.amount} 游戏币租金。${state.status==='playing'?'现在可以结束回合。':''}`;
    const dice = events.find(e => e.type === 'die_rolled');
    if (dice) {
      const tile = state.tiles[state.players[state.currentPlayerIndex].position];
      return `${actorName}掷出 ${dice.details?.value} 点，走到了「${tile.title}」。${state.phase === 'await_decision' ? `可支付 ${tile.price} 游戏币买地，或选择放弃。` : '可以结束本回合。'}`;
    }
    if (events.some(e => e.type === 'property_declined')) return '本次放弃购买，没有扣除游戏币。可以结束回合。';
    if (events.some(e => e.type === 'turn_ended')) return `轮到${state.players[state.currentPlayerIndex].name}行动，点击掷骰继续。`;
    return '操作完成。';
  };

  private cardName=(kind:unknown):string=>({
    reward:'奖励卡',stride:'步数卡',remote:'遥控骰子',roadblock:'路障',rent_free:'免租卡'
  } as Record<string,string>)[String(kind)]??'卡片';

  describeEvent = (event: GameEvent): string => {
    const person = this.state.game.players.find(p => p.id === event.actorId)?.name ?? '系统';
    switch (event.type) {
      case 'game_started': return '对局开始';
      case 'die_rolled': return `${person}掷出 ${event.details?.value} 点`;
      case 'tile_landed': return `${person}到达「${event.details?.title}」`;
      case 'card_received': return `${person}在卡片站获得${this.cardName(event.details?.cardType)}`;
      case 'card_used': return `${person}使用${this.cardName(event.details?.cardType)}${event.details?.cardType==='roadblock'?'，放在 '+event.details?.tileId+' 号格':event.details?.cardType==='remote'?'，指定骰点 '+event.details?.dieValue:''}`;
      case 'roadblock_triggered': return `${person}碰到 ${event.details?.tileId} 号格路障，提前停下`;
      case 'rent_waived': return `${person}免除 ${event.details?.amount} 游戏币租金`;
      case 'facility_entered': return `${person}来到${event.details?.kind==='hospital'?'医院':event.details?.kind==='prison'?'监狱':'商店'}${event.details?.turns?'，需跳过 '+event.details.turns+' 回合':'，可以购买道具'}`;
      case 'detention_skipped': return `${person}暂停行动，剩余 ${event.details?.remaining} 回合`;
      case 'detention_released': return `${person}获准离开${event.details?.kind==='hospital'?'医院':'监狱'}`;
      case 'shop_purchased': return `${person}花费 ${event.details?.amount} 游戏币购买${this.cardName(event.details?.cardType)}`;
      case 'shop_left': return `${person}离开商店`;
      case 'card_expired': return event.details?.cardType==='roadblock'?`${person}放置在 ${event.details?.tileId} 号格的路障已过期`:`${person}的免租保护已到期`;
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
      case 'bank_withdrawn': return `${person}${event.details?.reason==='rent'?'自动取款支付租金':'从银行取出'} ${event.details?.amount} 游戏币`;
      case 'bank_interest': return `${person}获得本轮银行利息 ${event.details?.amount} 游戏币`;
      case 'rent_paid': return `${person}支付租金 ${event.details?.amount}`;
      case 'player_bankrupt': return `${person}破产`;
      case 'game_finished': return '对局结束';
      case 'property_declined': return `${person}放弃购买`;
      case 'turn_ended': return `${person}结束回合`;
      case 'player_moved': return `${person}移动到 ${event.details?.to} 号格`;
    }
  };

  /** Pure presentation: a board button selects a map node; the engine owns all movement and economy. */
  renderTile = (tile: Tile): unknown => {
    const { game } = this.state;
    const residents = game.players.filter(p => p.position === tile.id && !p.bankrupt);
    const owner = game.players.find(p => p.id === tile.ownerId);
    const type = tile.facility??(tile.kind==='start'?'start':tile.kind==='property'?'property':
      tile.cardStation?'card':tile.eventBonus!==undefined?'chance':'rest');
    const blocked=game.roadblocks?.some(b=>b.tileId===tile.id)??false;
    const selected=this.state.selectedTileId===tile.id;
    const active=game.status==='playing'&&residents.some(p=>p.id===game.players[game.currentPlayerIndex].id);
    const level=tile.level??0;
    const roadblockSelectable=tile.id!==0&&tile.id!==game.players[game.currentPlayerIndex].position&&
      residents.length===0&&!blocked;
    const label=`${tile.id} 号地块，${tile.title}${owner?'，'+owner.name+'所有，'+level+'级':''}${tile.mortgaged?'，已抵押':''}${blocked?'，有路障':''}${residents.length?'，停留玩家：'+residents.map(p=>p.name).join('、'):''}`;
    return (
      <button type="button" key={tile.id}
        className={`tile tile-${tile.kind} tile-art-${type} ${tile.ownerId?`tile-owned-${tile.ownerId}`:''} ${residents.length?'tile-occupied':''} ${active?'tile-current':''} ${tile.mortgaged?'tile-mortgaged':''} ${blocked?'tile-blocked':''}`}
        style={cellPosition(game.map,tile.id)} data-tile-id={tile.id} data-owner-id={tile.ownerId??''}
        data-level={level} data-mortgaged={String(!!tile.mortgaged)} data-residents={residents.length}
        aria-label={label} aria-pressed={selected} title={label}
        onClick={()=>this.setState({selectedTileId:tile.id,...(roadblockSelectable?{roadblockTileInput:String(tile.id)}:{})})}>
        <span className="tile-index">{String(tile.id).padStart(2,'0')}{blocked?' 🚧':''}</span>
        <span className="tile-artwork" aria-hidden="true"><i className="art-roof"/><i className="art-body"/><i className="art-detail"/></span>
        <span className="tile-name">{tile.facility==='hospital'?'医院':tile.facility==='prison'?'监狱':tile.facility==='shop'?'商店':tile.kind==='property'?tile.title:tile.eventBonus!==undefined?'机会':tile.cardStation?'卡片':kindLabel[tile.kind]}</span>
        {tile.kind==='property'&&<span className="tile-value">{owner?`${level}级 · ${tile.mortgaged?'抵押':owner.name}`:`¥${tile.price}`}</span>}
        {tile.mortgaged&&<span className="tile-mortgage" aria-hidden="true">押</span>}
        {tile.kind==='property'&&owner&&<span className="tile-level" aria-label={`建筑等级 ${level}`}>{'●'.repeat(level+1)}</span>}
        <span className="pieces" aria-label={residents.map(p=>p.name).join('、')}>
          {residents.map(p=><span key={p.id} className={`piece piece-${game.players.indexOf(p)+1} ${p.kind}`} title={p.name} aria-label={p.name}>{game.players.indexOf(p)+1}</span>)}
        </span>
      </button>
    );
  };

  render(): unknown {
    const { game, message } = this.state;
    const current = game.players[game.currentPlayerIndex];
    const previousRoll = [...game.events].reverse().find(e => e.type === 'die_rolled');
    const phaseDescription = game.status === 'setup' ? '准备开局'
      : game.status === 'finished' ? '对局已结束'
      : game.phase === 'await_shop' ? '正在商店购物'
      : current.detention!==undefined ? '暂停行动 · 剩余 '+current.detention.remaining+' 回合'
      : game.phase === 'await_roll' ? '等待掷骰'
      : game.phase === 'await_decision' ? '等待处理地产'
      : '等待结束回合';
    const targetTile = game.tiles[current.position];
    const hasMoneyForLand = targetTile.kind === 'property' && targetTile.ownerId === null && current.cash >= (targetTile.price ?? 0);
    const lastEvents = game.events.filter(e => !['player_moved'].includes(e.type)).slice(-6).reverse();
    const currentShop=game.shops?.find(s=>s.tileId===current.position);
    const cardKinds=['reward','stride','remote','roadblock','rent_free'] as const;
    const availableRoadblocks=game.tiles.filter(t=>t.id!==0&&t.id!==current.position&&
      !game.players.some(p=>!p.bankrupt&&p.position===t.id)&&!game.roadblocks?.some(b=>b.tileId===t.id));
    return (
      <main className="app-shell" data-game-status={game.status} data-game-phase={game.phase} data-game-revision={game.revision} data-map-id={game.map.id}>
        <header className="topbar">
          <div className="brand"><span className="brand-mark">富</span><span>大富翁 <small>ReactMono</small></span></div>
          <span className="version-tag">P3 · 多人对局</span>
          <span className="network-indicator" role="status">{this.state.offline?'已断网 · 可用本地缓存':'已联网'}{this.state.pwaMessage?' · '+this.state.pwaMessage:''}</span>
          {this.state.pwaUpdate&&<button className="secondary-btn" type="button" onClick={()=>void this.applyPwaUpdate()}>检测到新版，保存并更新</button>}
        </header>
        <section className="headline"><div><span className="section-eyebrow">{game.tiles.length} 格 · 两张地图 · 2～4 人 · 本机轮流</span><h1>每一步，都是一笔生意。</h1><p>邀请朋友在同一设备轮流行动，也可以与一名或多名电脑玩家对抗。所有对局都在本地完成。</p></div><button type="button" className="reset-btn" onClick={this.reset}>↻ 重新开局</button></section>
        {game.status!=='setup'&&<section className="asset-overview" aria-label="多人资产总览">
          <div className="asset-heading"><strong>多人资产总览</strong><span>第 {game.round} / {game.maxRounds} 轮 · 当前：{current.name}</span></div>
          <div className="asset-grid">
            {game.players.map(p=>{
              const properties=game.tiles.filter(t=>t.kind==='property'&&t.ownerId===p.id);
              const shares=STOCKS.reduce((total,stock)=>total+(p.holdings?.[stock.id]?.quantity??0),0);
              const shareValue=game.market?STOCKS.reduce((total,stock)=>total+(p.holdings?.[stock.id]?.quantity??0)*quoteMarket(game.market!,stock.id),0):0;
              return <div className={`asset-player ${game.status==='playing'&&p.id===current.id?'is-active':''} ${p.bankrupt?'is-bankrupt':''}`} key={p.id} data-player-id={p.id} data-active-player={String(game.status==='playing'&&p.id===current.id)}>
                <div className="asset-identity"><span className={`player-dot ${p.kind}`}>{p.kind==='human'?'人':'机'}</span><strong>{p.name}</strong><span className="asset-turn-tag">{p.bankrupt?'已破产':p.id===current.id&&game.status==='playing'?'当前操作':p.kind==='computer'?'电脑':'真人'}</span></div>
                <dl className="asset-metrics">
                  <div><dt>现金</dt><dd>{p.cash.toLocaleString('zh-CN')}</dd></div>
                  <div><dt>银行存款</dt><dd>{(p.bankBalance??0).toLocaleString('zh-CN')}</dd></div>
                  <div><dt>地产</dt><dd>{properties.length} 块{properties.some(t=>t.mortgaged)?` · 抵押 ${properties.filter(t=>t.mortgaged).length}`:''}</dd></div>
                  <div><dt>股票</dt><dd>{shares} 股 · {shareValue.toLocaleString('zh-CN')} 币</dd></div>
                  <div><dt>贷款</dt><dd>{(p.loanBalance??0).toLocaleString('zh-CN')}</dd></div>
                  <div className="asset-net"><dt>净资产</dt><dd>{netWorth(game,p.id).toLocaleString('zh-CN')}</dd></div>
                </dl>
                {p.detention&&<small className="asset-status">{p.detention.kind==='hospital'?'医院':'监狱'} · 还需停留 {p.detention.remaining} 回合</small>}
              </div>;
            })}
          </div>
        </section>}
        <div className="layout">
          <section className="board-card" aria-label={`${game.tiles.length} 格游戏棋盘`}>
            <div className="board-viewport" tabIndex={0} aria-label="棋盘浏览区；窄屏可横向滚动">
              <div className={`board board-${game.map.id==='harbor-20'?'harbor':'classic'}`} data-board-theme={game.map.id}
                style={{
                  gridTemplateColumns:`repeat(${game.map.columns},minmax(0,1fr))`,
                  gridTemplateRows:`repeat(${game.map.rows},minmax(0,1fr))`,
                  aspectRatio:`${game.map.columns}/${game.map.rows}`
                }}>
                {game.tiles.map(this.renderTile)}
                {game.map.columns>2&&game.map.rows>2&&game.map.cells.every(p=>p.row===1||p.row===game.map.rows||p.column===1||p.column===game.map.columns)&&
                <div className="board-center" style={{gridColumn:`2/${game.map.columns}`,gridRow:`2/${game.map.rows}`}}>
                  <div className="scene-horizon" aria-hidden="true">
                    <span className="scene-hill"/><span className="scene-house house-one"/><span className="scene-house house-two"/>
                    <span className="scene-tree tree-one"/><span className="scene-tree tree-two"/>
                    <span className="scene-boat"/>
                  </div>
                  <div className="scene-info">
                    <div className="center-title">{game.map.id==='harbor-20'?'海风港':'纸艺小镇'}</div>
                    <div className="board-center-label">第 {game.round} / {game.maxRounds} 轮</div>
                    <div className="dice-display" aria-label="上一次骰子点数">{previousRoll ? '⚀⚁⚂⚃⚄⚅'[Number(previousRoll.details?.value)-1] : '⚄'}</div>
                    <div className="center-subtitle">{previousRoll?`掷出 ${previousRoll.details?.value} 点`:'准备出发'}</div>
                  </div>
                </div>}
              </div>
            </div>
            {this.state.selectedTileId!==null&&game.tiles[this.state.selectedTileId]&&(()=>{
              const tile=game.tiles[this.state.selectedTileId!], owner=game.players.find(p=>p.id===tile.ownerId);
              return <div className="board-inspector" role="status" aria-live="polite">
                <strong>{tile.id} · {tile.title}</strong>
                <span>{tile.kind==='property'?`售价 ${tile.price} · ${owner?`归属 ${owner.name} · ${tile.level??0} 级 · ${tile.mortgaged?'已抵押':'当前租金 '+(tile.levelRents?.[tile.level??0]??tile.rent)}`:'尚未出售'}`:
                  tile.facility?{hospital:'医院',prison:'监狱',shop:'商店'}[tile.facility]:tile.cardStation?'卡片站':tile.eventBonus!==undefined?'机会事件':'公共地块'}
                  {game.roadblocks?.some(b=>b.tileId===tile.id)?' · 有路障':''}</span>
              </div>;
            })()}
          </section>
          <aside className="sidebar">
            <div className="turn-card">
              <div className="card-label">当前行动</div>
              <div className="turn-person"><span className={`portrait ${current.kind}`}>{current.kind === 'human' ? '人' : '机'}</span><div><strong>{current.name}</strong><small>{phaseDescription}</small></div></div>
              <div className="turn-position">位置：<b>{current.position} 号格</b><span>·</span>资金：<b>{current.cash.toLocaleString('zh-CN')}</b>{game.bank&&<span> · 银行存款：<b>{(current.bankBalance??0).toLocaleString('zh-CN')}</b></span>}{game.loan&&<span> · 贷款：<b>{(current.loanBalance??0).toLocaleString('zh-CN')}</b> · 净资产：<b>{netWorth(game,current.id).toLocaleString('zh-CN')}</b></span>}</div>
              {game.status === 'setup' && <div className="start-form">
                <label className="field-label" htmlFor="game-map">游戏地图 <small>经典环线 24 格；原创海港 20 格（价格与地名不同）</small></label>
                 <select id="game-map" aria-label="游戏地图" value={this.state.selectedMapId} onChange={(event:{target:{value:string}})=>this.selectMap(event.target.value)}>
                   <option value="classic-24">经典环线 · 24 格</option><option value="harbor-20">海港环线 · 20 格</option>
                 </select>
                 <label className="field-label" htmlFor="game-seed">对局种子 <small>相同种子可重现骰子结果</small></label>
                <input id="game-seed" aria-label="对局种子" inputMode="numeric" type="text" maxLength={10} value={this.state.seedInput} onChange={(event: {target:{value:string}}) => this.setState({ seedInput: event.target.value })} />
                <label className="field-label" htmlFor="player-count">玩家人数</label>
                <select id="player-count" aria-label="玩家人数" value={this.state.playerSetup.length} onChange={(event:{target:{value:string}})=>this.setPlayerCount(Number(event.target.value))}>
                  {[2,3,4].map(n=><option key={n} value={n}>{n} 人</option>)}
                </select>
                <div className="setup-roster">
                  {this.state.playerSetup.map((p,i)=><div className="setup-player" key={p.id}>
                    <label>第 {i+1} 位玩家姓名<input aria-label={`第 ${i+1} 位玩家姓名`} type="text" maxLength={24} value={p.name} onChange={(event:{target:{value:string}})=>this.updatePlayer(i,'name',event.target.value)}/></label>
                    <label>类型<select aria-label={`第 ${i+1} 位玩家类型`} value={p.kind??(i===0?'human':'computer')} onChange={(event:{target:{value:string}})=>this.updatePlayer(i,'kind',event.target.value)}>
                      <option value="human">真人</option><option value="computer">电脑</option>
                    </select></label>
                    {p.kind==='computer'&&<label>电脑策略<select aria-label={`第 ${i+1} 位电脑策略`} value={p.computerStyle??'balanced'} onChange={(event:{target:{value:string}})=>this.setState({playerSetup:this.state.playerSetup.map((item,j)=>j===i?{...item,computerStyle:event.target.value as typeof COMPUTER_STYLES[number]}:item)})}>
                      {COMPUTER_STYLES.map(style=><option key={style} value={style}>{COMPUTER_STYLE_NAMES[style]}</option>)}
                    </select></label>}
                  </div>)}
                </div>
                <label className="field-label" htmlFor="max-rounds">最多轮数</label>
                <input id="max-rounds" aria-label="最多轮数" type="text" inputMode="numeric" maxLength={3} value={this.state.roundsInput} onChange={(event:{target:{value:string}})=>this.setState({roundsInput:event.target.value})}/>
                <label className="fast-setting"><input type="checkbox" aria-label="启用医院、监狱与商店" checked={this.state.specialEnabled} onChange={(event:{target:{checked:boolean}})=>this.setState({specialEnabled:event.target.checked})}/>启用医院、监狱与商店（经典设施，可关闭保留旧版地图）</label>
                <label className="fast-setting"><input type="checkbox" aria-label="快速模式" checked={this.state.fastMode} onChange={(event: {target:{checked:boolean}}) => this.setState({ fastMode: event.target.checked })} />快速模式（缩短电脑操作间隔）</label>
                <button type="button" className="primary-btn" onClick={this.startGame}>开始游戏 <span>→</span></button>
              </div>}
              {this.state.awaitingHandoff && game.status==='playing' && <div className="handoff-panel" role="status">
                <strong>轮到 {current.name}</strong>
                <p>请把设备交给这名玩家，准备好以后确认。上一位玩家不能继续操作。</p>
                <button type="button" className="primary-btn" onClick={this.acknowledgeHandoff}>我已就位，开始操作</button>
              </div>}
              {current.kind === 'computer' && game.status === 'playing' && <p className="computer-thinking" role="status">电脑正在自动操作（{current.computerStyle?COMPUTER_STYLE_NAMES[current.computerStyle]:'经典'}策略）…</p>}
              {current.kind === 'human' && !this.state.awaitingHandoff && game.phase === 'await_roll' && current.detention===undefined && <div className="purchase-actions">
                <p className="purchase-info">手牌：奖励 {current.cards?.reward??0} · 步数 {current.cards?.stride??0}{game.strategyEnabled?' · 遥控 '+(current.cards?.remote??0)+' · 路障 '+(current.cards?.roadblock??0)+' · 免租 '+(current.cards?.rent_free??0):''}{(game.pendingMoveBonus??0)>0?` · 已加步数 ${game.pendingMoveBonus}`:''}{(game.pendingDie??0)>0?` · 已指定骰点 ${game.pendingDie}`:''}{game.pendingRentWaiver?' · 本次免租':''}</p>
                {(current.cards?.reward??0)>0&&<button type="button" className="secondary-btn" onClick={()=>this.dispatch('use_card',undefined,'reward')}>使用奖励卡（+{game.cardRules?.rewardCash??80} 游戏币）</button>}
                {(current.cards?.stride??0)>0&&(game.pendingMoveBonus??0)===0&&<button type="button" className="secondary-btn" onClick={()=>this.dispatch('use_card',undefined,'stride')}>使用步数卡（+{game.cardRules?.moveBonus??2} 格）</button>}
                {game.strategyEnabled&&(current.cards?.remote??0)>0&&(game.pendingDie??0)===0&&<div className="purchase-info">
                  <label htmlFor="remote-die">遥控骰点 </label>
                  <select id="remote-die" aria-label="遥控骰点" value={this.state.strategyDieInput} onChange={(e:{target:{value:string}})=>this.setState({strategyDieInput:e.target.value})}>
                    {[1,2,3,4,5,6].map(n=><option key={n} value={n}>{n} 点</option>)}
                  </select>
                  <button type="button" className="secondary-btn" onClick={()=>this.dispatch('use_card',undefined,'remote')}>使用遥控骰子</button>
                </div>}
                {game.strategyEnabled&&(current.cards?.roadblock??0)>0&&<div className="purchase-info">
                  <label htmlFor="roadblock-tile">放置路障 </label>
                  <select id="roadblock-tile" aria-label="路障目标格" value={availableRoadblocks.some(t=>String(t.id)===this.state.roadblockTileInput)?this.state.roadblockTileInput:String(availableRoadblocks[0]?.id??'')} onChange={(e:{target:{value:string}})=>this.setState({roadblockTileInput:e.target.value})}>
                    {availableRoadblocks.map(t=><option key={t.id} value={t.id}>{t.id} · {t.title}</option>)}
                  </select>
                  <button type="button" className="secondary-btn" disabled={availableRoadblocks.length===0} onClick={()=>this.dispatch('use_card',undefined,'roadblock')}>放置路障</button>
                </div>}
                {game.strategyEnabled&&(current.cards?.rent_free??0)>0&&!game.pendingRentWaiver&&<button type="button" className="secondary-btn" onClick={()=>this.dispatch('use_card',undefined,'rent_free')}>使用免租卡（本次掷骰有效）</button>}
                <button type="button" className="primary-btn" onClick={() => this.dispatch('roll')}>掷骰前进 <span>🎲</span></button>
              </div>}
              {current.kind === 'human' && !this.state.awaitingHandoff && game.phase==='await_roll' && current.detention!==undefined && <div className="purchase-actions">
                <p className="purchase-info">正在{current.detention.kind==='hospital'?'住院':'服刑'} · 剩余 {current.detention.remaining} 次轮到你的回合</p>
                <button type="button" className="primary-btn" onClick={()=>this.dispatch('skip_turn')}>跳过当前停留回合</button>
              </div>}
              {current.kind==='human'&&!this.state.awaitingHandoff&&game.phase==='await_shop'&&<div className="purchase-actions">
                <p className="purchase-info">商店 · 现金 {current.cash} · 手牌上限 {game.cardRules?.maxHand??3}</p>
                {cardKinds.map(k=><button key={k} type="button" className="secondary-btn"
                  disabled={!currentShop||(currentShop.cards[k]??0)<1||current.cash<(game.facilityRules?.prices[k]??Infinity)||
                    cardKinds.reduce((sum,x)=>sum+(current.cards?.[x]??0),0)>=(game.cardRules?.maxHand??3)}
                  onClick={()=>this.dispatch('buy_shop_card',undefined,k)}>
                    购买{this.cardName(k)} · {game.facilityRules?.prices[k]??0} 币 · 剩余 {currentShop?.cards[k]??0}
                  </button>)}
                <button type="button" className="primary-btn" onClick={()=>this.dispatch('leave_shop')}>离开商店</button>
              </div>}
              {current.kind === 'human' && !this.state.awaitingHandoff && game.phase === 'await_decision' && <div className="purchase-actions">
                <p className="purchase-info">{targetTile.title}　售价 <b>{targetTile.price}</b>　过路费 <b>{targetTile.rent}</b></p>
                <button type="button" className="primary-btn" onClick={() => this.dispatch('buy_property')} disabled={!hasMoneyForLand}>购买地产 <span>⌂</span></button>
                {!hasMoneyForLand && <p className="insufficient-msg">资金不足，不能购买此地。</p>}
                <button type="button" className="secondary-btn" onClick={() => this.dispatch('decline_property')}>放弃购买，继续回合 →</button>
              </div>}
              {current.kind === 'human' && !this.state.awaitingHandoff && game.phase === 'await_end_turn' && <div className="purchase-actions">
                <div className="action-navigation" role="navigation" aria-label="交易操作快捷入口">
                  {([{id:'property-management',label:'地产管理'},...(game.bank?[{id:'bank-actions',label:'银行存取'}]:[]),...(game.loan?[{id:'loan-actions',label:'贷款与抵押入口'}]:[]),...(game.market?[{id:'stock-actions',label:'股票交易'}]:[])]).map(link=>
                    <button key={link.id} type="button" onClick={()=>document.getElementById(link.id)?.scrollIntoView({behavior:'smooth',block:'start'})}>{link.label} ↓</button>)}
                </div>
                <strong id="property-management" className="management-heading">地产管理 · {current.name}</strong>
                {game.tiles.filter(t=>t.kind==='property'&&t.ownerId===current.id&&t.mortgaged!==true&&(t.level??0)<2).map(tile=><button type="button" key={tile.id} className="secondary-btn" disabled={current.cash<(tile.upgradeCosts?.[tile.level??0]??Infinity)} onClick={()=>this.dispatch('upgrade_property',tile.id)}>升级 {tile.title} → {(tile.level??0)+1} 级 · 费用 {tile.upgradeCosts?.[tile.level??0]}</button>)}
                {game.tiles.filter(t=>t.kind==='property'&&t.ownerId===current.id&&t.mortgaged!==true).map(tile=><button type="button" key={'sell-'+tile.id} className="secondary-btn" onClick={()=>{
                  if(window.confirm('确认出售「'+tile.title+'」？价格 '+resaleValue(tile,game.resaleRules)+' 游戏币，建筑升级不返还原价。'))this.dispatch('sell_property',tile.id);
                }}>出售 {tile.title} · 回收 {resaleValue(tile,game.resaleRules)} 游戏币</button>)}
                {game.bank&&<div id="bank-actions" className="bank-actions" role="group" aria-label="银行操作">
                  <strong className="management-heading">银行存取 · {current.name}</strong>
                  <p className="purchase-info">银行：每完成一轮按 {game.bank.interestBps/100}% 结息，现金与存款分开计算，欠租时优先自动取款。</p>
                  <label htmlFor="bank-amount">银行交易金额（游戏币）</label>
                  <input id="bank-amount" aria-label="银行交易金额" inputMode="numeric" type="text" value={this.state.bankAmountInput} onChange={(e:{target:{value:string}})=>this.setState({bankAmountInput:e.target.value})}/>
                  <button type="button" className="secondary-btn" disabled={!/^[1-9][0-9]*$/.test(this.state.bankAmountInput)||Number(this.state.bankAmountInput)>current.cash} onClick={()=>this.dispatch('deposit_bank')}>存入银行</button>
                  <button type="button" className="secondary-btn" disabled={!/^[1-9][0-9]*$/.test(this.state.bankAmountInput)||Number(this.state.bankAmountInput)>(current.bankBalance??0)} onClick={()=>this.dispatch('withdraw_bank')}>从银行取款</button>
                </div>}
                {game.loan&&<div id="loan-actions" className="bank-actions loan-actions" role="group" aria-label="地产抵押与贷款">
                  <strong className="management-heading">抵押借贷 · {current.name}</strong>
                   <p className="purchase-info">贷款 {(current.loanBalance??0).toLocaleString('zh-CN')} · 抵押额度 {loanLimit(game,current.id)} · 每轮利率 {game.loan.interestBps/100}%。抵押地产暂停租金、升级和出售；超额时银行收回抵押物。</p>
                   {game.tiles.filter(t=>t.kind==='property'&&t.ownerId===current.id).map(tile=>
                     <button type="button" key={'lien-'+tile.id} className="secondary-btn"
                       disabled={tile.mortgaged===true&&(current.loanBalance??0)>loanLimit(game,current.id,tile.id)}
                       onClick={()=>this.dispatch(tile.mortgaged===true?'release_mortgage':'mortgage_property',tile.id)}>
                       {tile.mortgaged===true?'解除抵押':'抵押'} {tile.title}
                     </button>)}
                   <p className="purchase-info">上方银行交易金额同样用于借贷。当前可借 {Math.max(0,loanLimit(game,current.id)-(current.loanBalance??0))} 游戏币。</p>
                   <button type="button" className="secondary-btn" disabled={!/^[1-9][0-9]*$/.test(this.state.bankAmountInput)||Number(this.state.bankAmountInput)>loanLimit(game,current.id)-(current.loanBalance??0)} onClick={()=>this.dispatch('borrow_loan')}>借入贷款</button>
                   <button type="button" className="secondary-btn" disabled={!/^[1-9][0-9]*$/.test(this.state.bankAmountInput)||Number(this.state.bankAmountInput)>Math.min(current.cash,current.loanBalance??0)} onClick={()=>this.dispatch('repay_loan')}>偿还贷款</button>
                 </div>}
                 {game.market&&<div id="stock-actions" className="bank-actions stock-actions" role="group" aria-label="股票交易">
                    <strong>虚拟股票交易所 · {current.name}</strong>
                    <p className="purchase-info">本轮报价 · 每笔交易手续费 0.5%，最低 1 游戏币。仅使用手持现金，按当前市场价成交；行情每轮变化。</p>
                    <label htmlFor="stock-amount">股票交易数量（股）</label>
                    <input id="stock-amount" type="text" aria-label="股票交易数量" inputMode="numeric"
                      value={this.state.stockAmountInput}
                      onChange={(event:{target:{value:string}})=>this.setState({stockAmountInput:event.target.value})}/>
                    {STOCKS.map(stock=>{
                      const quote=quoteMarket(game.market!,stock.id);
                      const lot=current.holdings?.[stock.id];
                      const held=lot?.quantity??0;
                      const marketValue=held*quote;
                      const pnl=marketValue-(lot?.costBasis??0);
                      return <div className="stock-entry" key={stock.id}>
                        <div><strong>{stock.name}</strong>（{stock.id}） · 报价 {quote} 游戏币</div>
                        <div className="purchase-info">持有 {held} 股 · 成本 {lot?.costBasis??0} · 市值 {marketValue} · 浮动盈亏 {pnl>=0?'+':''}{pnl}</div>
                        <button type="button" className="secondary-btn" disabled={!/^[1-9][0-9]*$/.test(this.state.stockAmountInput)||quote*Number(this.state.stockAmountInput)+Math.max(1,Math.ceil(quote*Number(this.state.stockAmountInput)*0.005))>current.cash} onClick={()=>this.dispatch('buy_stock',undefined,undefined,stock.id)}>买入 {stock.name}</button>
                        <button type="button" className="secondary-btn" disabled={!/^[1-9][0-9]*$/.test(this.state.stockAmountInput)||Number(this.state.stockAmountInput)>held} onClick={()=>this.dispatch('sell_stock',undefined,undefined,stock.id)}>卖出 {stock.name}</button>
                      </div>;
                    })}
                    <p className="purchase-info">持仓市值：{STOCKS.reduce((sum,stock)=>sum+(current.holdings?.[stock.id]?.quantity??0)*quoteMarket(game.market!,stock.id),0).toLocaleString('zh-CN')} 游戏币。</p>
                  </div>}
                  <button type="button" className="primary-btn" onClick={() => this.dispatch('end_turn')}>结束当前回合 <span>→</span></button>
              </div>}
              {game.phase === 'finished' && <div className="result-box" role="status"><strong>{game.winnerId ? `${game.players.find(p => p.id === game.winnerId)?.name}获胜！` : '净资产并列，平局！'}</strong><p>{[...game.events].reverse().find(e => e.type === 'game_finished')?.details?.reason === 'bankruptcy' ? '结束原因：一方无法付清租金' : '结束原因：达到回合上限'}</p><p>最终净资产：{game.players.map(p=>`${p.name} ${netWorth(game,p.id)}`).join(' · ')}</p><p>本局种子：{this.state.activeSeed}</p><button type="button" className="primary-btn" onClick={this.reset}>再来一局 <span>↻</span></button></div>}
              <p className="turn-tip" role="status">{message}</p>
            </div>
            <div className="saves-card">
              <div className="card-label">本地存档</div>
              <p className="save-warning">清除浏览器站点数据或卸载应用可能永久删除本地存档；请定期使用「导出」保存 JSON 备份。</p>
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
            <div className="players-card"><div className="card-label">玩家状态</div>{game.players.map(p => <div key={p.id} className={`player-line ${current.id === p.id && game.status === 'playing' ? 'is-current' : ''}`}><span className={`player-dot ${p.kind}`}>{p.kind === 'human' ? '人' : '机'}</span><div><strong>{p.name}</strong><small>{p.position} 号格 · 现金 {p.cash.toLocaleString('zh-CN')}{game.bank?` · 存款 ${(p.bankBalance??0).toLocaleString('zh-CN')}`:''}{game.market?` · 股票 ${Object.values(p.holdings??{}).reduce((sum,lot)=>sum+(lot?.quantity??0),0)} 股`:''}{game.loan?` · 贷款 ${(p.loanBalance??0).toLocaleString('zh-CN')}`:''} · 净资产 {netWorth(game,p.id).toLocaleString('zh-CN')}{p.detention?` · ${p.detention.kind==='hospital'?'住院':'入狱'}剩余 ${p.detention.remaining} 回合`:''}{p.bankrupt ? ' · 已破产' : ''}</small></div><span className="player-kind">{p.kind === 'human' ? '真人' : '电脑'}</span></div>)}</div>
            <div className="activity-card"><div className="card-label">最近事件</div><ol>{lastEvents.map((e,i) => <li key={`${game.events.length}-${i}`}>{this.describeEvent(e)}</li>)}</ol></div>
            <div className="info-card"><strong>玩法说明</strong><p>① 点击「开始游戏」，轮到玩家时掷骰前进。② 到无主地产可买入或放弃；经过对手地产会自动付租。③ 处理完地块后结束回合，电脑会自动行动。</p><p>付不起租金可能出售地产或破产；最终按现金、存款、地产成本、股票市值减贷款计算净资产。电脑购地后至少保留 200 游戏币。</p><p>卡片站可获得奖励、步数、遥控骰子、路障及免租卡；只在掷骰前使用。路障让对手提前停下，最多持续两轮；免租卡仅保护下一次落地。存档与离线游玩均在本机完成。</p></div>
          </aside>
        </div>
        <footer className="footer">纯前端 · 简体中文 · 不需要账号　｜　IndexedDB 本机存档 · 不上传云端　｜　<a className="visual-lab-link" href="./visual-lab.html">原创美术样例</a></footer>
      </main>
    );
  }
}
const root = document.getElementById('root');
if (!root) throw new Error('找不到游戏页面根节点');
ReactDOM.render(React.createElement(App, {}), root);
