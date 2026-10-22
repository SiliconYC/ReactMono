/** Turn movement, landing settlement and round-end decisions. */
import type { GameState, Player, ActionResult, GameEvent, CardKind, Phase } from './types.js';
import { nextDie } from './random.js';
import { advancePosition } from './maps.js';
import { netWorth, liquidateForRent } from './property.js';
import { propertyRent } from './property-groups.js';
import { advanceMarket } from './market.js';
import { liquidateStocksForRent } from './stocks.js';
import { foreclose, settleLoanRound } from './loan.js';
import { coverRentFromBank, settleBankRound } from './bank.js';
import { DEFAULT_CARD_RULES } from './config.js';
import { handSize } from './cards.js';
import { accept, reject } from './transitions.js';
import { assertMoneyState, checkedMoneyAdd } from './money.js';
export function rollTurn(state: GameState, actor: Player): ActionResult {
      if (state.phase !== 'await_roll'||actor.detention!==undefined) return reject(state,'INVALID_PHASE');
      assertMoneyState(state);
      const draw = nextDie(state.randomState);
      const value = state.strategyEnabled===true && (state.pendingDie??0)>0 ? state.pendingDie! : draw.value;
      const nextState=draw.nextState; // consume RNG even for remote dice so replay is stable
      const bonus=state.pendingMoveBonus??0;
      let position=advancePosition(state.map,actor.position,value+bonus);
      const expiredBlocks=(state.roadblocks??[]).filter(b=>b.expiresRound<state.round ||
        state.players.some(p=>p.id===b.ownerId&&p.bankrupt));
      let blocks=(state.roadblocks??[]).filter(b=>!expiredBlocks.includes(b));
      let hit:number|undefined;
      for(let step=1;step<=value+bonus;step++){
        const traversed=advancePosition(state.map,actor.position,step);
        if(blocks.some(b=>b.tileId===traversed&&b.ownerId!==actor.id)){
          position=traversed;hit=traversed;blocks=blocks.filter(b=>b.tileId!==traversed);break;
        }
      }
      const landed = state.tiles[position];
      const events: GameEvent[] = [
        { type: 'die_rolled', actorId: actor.id, details: { value, bonus,...((state.pendingDie??0)>0?{remote:1}:{}) } },
        { type: 'player_moved', actorId: actor.id, details: { from: actor.position, to: position } },
        { type: 'tile_landed', actorId: actor.id, details: { tileId: landed.id, title: landed.title } },
        ...(hit===undefined?[]:[{type:'roadblock_triggered' as const,actorId:actor.id,details:{tileId:hit}}]),
        ...expiredBlocks.map(b=>({type:'card_expired' as const,actorId:b.ownerId,details:{cardType:'roadblock',tileId:b.tileId}}))
      ];
      if(state.pendingRentWaiver===true &&
        !(landed.kind==='property'&&landed.ownerId!==null&&landed.ownerId!==actor.id&&landed.mortgaged!==true)){
        events.push({type:'card_expired',actorId:actor.id,details:{cardType:'rent_free'}});
      }
      let movingPlayers = state.players.map(p => p.id === actor.id ? { ...p, position } : p);
      let finalRandomState=nextState;
      if (landed.kind === 'property' && landed.ownerId && landed.ownerId !== actor.id) {
        const landlord = state.players.find(p => p.id === landed.ownerId);
        if (!landlord) return reject(state,'INVALID_PHASE');
        const baseDue = propertyRent(state,landed.id);
        const due = state.pendingRentWaiver===true?0:baseDue;
        if(baseDue>0&&state.pendingRentWaiver===true)events.push({type:'rent_waived',actorId:actor.id,details:{tileId:landed.id,amount:baseDue}});
        const funds=coverRentFromBank(state,actor,due);
        if(funds.amount>0)events.push({type:'bank_withdrawn',actorId:actor.id,details:{amount:funds.amount,reason:'rent'}});
        const stockRescue=state.market!==undefined
          ? liquidateStocksForRent(state,{...actor,cash:funds.cash},due)
          : {cash:funds.cash,holdings:actor.holdings,events:[]};
        events.push(...stockRescue.events);
        let rescue=state.automaticLiquidation===true
          ? liquidateForRent(state,{...actor,cash:stockRescue.cash},due,landlord.id)
          : {cash:stockRescue.cash,tiles:state.tiles,events:[]};
        events.push(...rescue.events);
        let loanBalance=actor.loanBalance??0;
        // Rent deficit: pledge is seized by the bank, only collateral proceeds in excess
        // of the secured loan may pay the landlord. No bank debt survives foreclosure.
        if(rescue.cash<due && state.loan && loanBalance>0){
          const seized=foreclose(state,{...actor,cash:0},rescue.tiles);
          rescue={...rescue,cash:checkedMoneyAdd(rescue.cash,seized.player.cash),tiles:seized.tiles};
          loanBalance=0;
          events.push(...seized.events);
        }
        const paid = Math.min(rescue.cash, due);
        const insolvent = paid < due;
        const players = movingPlayers.map(p => p.id === actor.id
          ? { ...p, cash: rescue.cash - paid, ...(funds.amount>0?{bankBalance:funds.bankBalance}:{}), bankrupt: insolvent, ...(state.loan?{loanBalance}:{} ), ...(stockRescue.holdings!==undefined?{holdings:stockRescue.holdings}:{}) }
          : p.id === landlord.id ? { ...p, cash: checkedMoneyAdd(p.cash,paid) } : p);
        events.push({ type: 'rent_paid', actorId: actor.id, details: {
          tileId: landed.id, fromId: actor.id, toId: landlord.id, due, amount: paid
        } });
        // Multiplayer: eliminate only the insolvent player; keep surviving players' turns.
        const alive=players.filter(p=>!p.bankrupt);
        const next=insolvent && alive.length>1 ? nextActiveIndex(players,state.currentPlayerIndex) : state.currentPlayerIndex;
        const wrapped=insolvent && next<=state.currentPlayerIndex;
        const roundLimit=state.endCondition!=='bankruptcy' && insolvent && alive.length>1 && wrapped && state.round>=state.maxRounds;
        const finished=insolvent && (alive.length===1 || roundLimit);
        const winnerId=alive.length===1 ? alive[0].id : roundLimit ? leadingPlayer({...state,tiles:rescue.tiles},players) : null;
        if (insolvent) {
          events.push({ type: 'player_bankrupt', actorId: actor.id, details: { creditorId: landlord.id } });
          if(finished)events.push({type:'game_finished',details:roundLimit
            ? {reason:'round_limit',draw:winnerId===null?1:0,...(winnerId?{winnerId}:{})}
            : {reason:'bankruptcy',winnerId:winnerId!}});
        }
        const interest=state.bank&&!finished&&wrapped?settleBankRound(state,players,state.round+1):null;
        if(interest)events.push(...interest.events);
        const clearedTiles=insolvent?rescue.tiles.map(t=>{
          if(t.ownerId!==actor.id)return t;
          const {mortgaged:_unused,...rest}=t;
          return {...rest,ownerId:null,level:0};
        }):rescue.tiles;
        const loanSettle=state.loan&&!finished&&wrapped
          ?settleLoanRound(state,interest?.players??players,clearedTiles,state.round+1):null;
        if(loanSettle)events.push(...loanSettle.events);
        return accept(state, events, {
          randomState: nextState, players:loanSettle?.players??interest?.players??players, pendingMoveBonus:0,
          ...(state.strategyEnabled===true?{pendingDie:0,pendingRentWaiver:false,
            roadblocks:blocks.filter(b=>!(insolvent&&b.ownerId===actor.id))}:{}),
          ...(interest?{bank:interest.bank}:{}),
          ...(loanSettle?{loan:loanSettle.loan}:{}),
          // Auction at defined resale value before paying rent; residual insolvency releases all land.
          tiles: loanSettle?.tiles??clearedTiles,
          status: finished ? 'finished' : 'playing',
          winnerId: finished ? winnerId : state.winnerId,
          phase: finished ? 'finished' : insolvent ? 'await_roll' : 'await_end_turn',
          currentPlayerIndex: next,
          round: !finished && wrapped ? state.round+1 : state.round,
          ...(state.market && !finished && wrapped ? {market:advanceMarket(state.market,state.round+1)} : {})
        });
      }
      if(landed.facility==='hospital'||landed.facility==='prison'){
        const kind=landed.facility;
        const turns=kind==='hospital'?state.facilityRules!.hospitalTurns:state.facilityRules!.prisonTurns;
        const fee=kind==='hospital'?state.facilityRules!.hospitalFee:state.facilityRules!.prisonFee;
        const owner=movingPlayers.find(p=>p.id===actor.id)!;
        const paid=Math.min(owner.cash,fee);
        movingPlayers=movingPlayers.map(p=>p.id===actor.id?{...p,cash:p.cash-paid,
          detention:{kind,remaining:turns}}:p);
        events.push({type:'facility_entered',actorId:actor.id,details:{kind,tileId:landed.id,turns,due:fee,amount:paid}});
      }else if(landed.facility==='shop'){
        events.push({type:'facility_entered',actorId:actor.id,details:{kind:'shop',tileId:landed.id,amount:0}});
      }
      if(landed.kind==='neutral'&&landed.eventBonus!==undefined&&landed.eventFee!==undefined){
        const draw=nextDie(finalRandomState);
        finalRandomState=draw.nextState;
        if(draw.value%2===1){
          movingPlayers=movingPlayers.map(p=>p.id===actor.id?{...p,cash:p.cash+landed.eventBonus!}:p);
          events.push({type:'event_bonus',actorId:actor.id,details:{tileId:landed.id,amount:landed.eventBonus,draw:draw.value}});
        }else{
          const paid=Math.min(actor.cash,landed.eventFee);
          movingPlayers=movingPlayers.map(p=>p.id===actor.id?{...p,cash:p.cash-paid}:p);
          events.push({type:'event_fee',actorId:actor.id,details:{tileId:landed.id,due:landed.eventFee,amount:paid,draw:draw.value}});
        }
      }
      if(landed.cardStation){
        const owner=movingPlayers.find(p=>p.id===actor.id)!;
        const held=owner.cards??{reward:0,stride:0};
        if(handSize(held)<(state.cardRules?.maxHand??DEFAULT_CARD_RULES.maxHand)){
          const draw=nextDie(finalRandomState);finalRandomState=draw.nextState;
          const kind:CardKind=state.strategyEnabled===true
            ? (['reward','stride','remote','roadblock','rent_free','reward'] as const)[draw.value-1]
            : draw.value%2===1?'reward':'stride';
          movingPlayers=movingPlayers.map(p=>p.id===actor.id?{...p,cards:{...held,[kind]:(held[kind]??0)+1}}:p);
          events.push({type:'card_received',actorId:actor.id,details:{tileId:landed.id,cardType:kind}});
        }
      }
      const phase: Phase = landed.facility==='shop'?'await_shop'
        :landed.kind === 'property' && landed.ownerId === null?'await_decision':'await_end_turn';
      return accept(state, events, {
        randomState: finalRandomState,
        players: movingPlayers,
        pendingMoveBonus:0,
        ...(state.strategyEnabled===true?{pendingDie:0,pendingRentWaiver:false,roadblocks:blocks}:{}),
        phase
      });
}
/** The next live participant, wrapping past bankrupt seats. */
export function nextActiveIndex(players: readonly Player[], current: number): number {
  for(let step=1;step<=players.length;step++){
    const index=(current+step)%players.length;
    if(!players[index].bankrupt)return index;
  }
  throw new Error('无存活玩家，回合状态无效');
}
function leadingPlayer(state: GameState, players: readonly Player[]): string | null {
  assertMoneyState({...state,players});
  const live=players.filter(p=>!p.bankrupt);
  const scores=live.map(p=>({id:p.id,value:netWorth({...state,players},p.id)}));
  const high=Math.max(...scores.map(x=>x.value));
  const leaders=scores.filter(x=>x.value===high);
  return leaders.length===1?leaders[0].id:null;
}
export function endTurn(state: GameState, actor: Player): ActionResult {
  if(state.phase!=='await_end_turn')return reject(state,'INVALID_PHASE');
  assertMoneyState(state);
  const next=nextActiveIndex(state.players,state.currentPlayerIndex);
  const wrapped=next<=state.currentPlayerIndex;
  const finished=state.endCondition!=='bankruptcy' && wrapped && state.round>=state.maxRounds;
  const assets=state.players.map(p=>netWorth(state,p.id));
  const winnerId=finished?leadingPlayer(state,state.players):null;
  const events: GameEvent[]=[{type:'turn_ended',actorId:actor.id}];
  if(finished)events.push({type:'game_finished',details:{
    reason:'round_limit',draw:winnerId===null?1:0,
    firstNetWorth:assets[0],secondNetWorth:assets[1],
    ...(winnerId?{winnerId}:{})
  }});
  const interest=state.bank&&!finished&&wrapped?settleBankRound(state,state.players,state.round+1):null;
  if(interest)events.push(...interest.events);
  const loanSettle=state.loan&&!finished&&wrapped?settleLoanRound(state,interest?.players??state.players,state.tiles,state.round+1):null;
  if(loanSettle)events.push(...loanSettle.events);
  return accept(state,events,{
    ...(interest?{bank:interest.bank,players:interest.players}:{}),
    ...(loanSettle?{loan:loanSettle.loan,players:loanSettle.players,tiles:loanSettle.tiles}:{}),
    status:finished?'finished':'playing',
    phase:finished?'finished':'await_roll',
    currentPlayerIndex:next,
    round:!finished&&wrapped?state.round+1:state.round,
    ...(state.market && !finished && wrapped ? {market:advanceMarket(state.market,state.round+1)} : {}),
    winnerId
  });
}
