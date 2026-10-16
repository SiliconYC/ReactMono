/** Turn movement, landing settlement and round-end decisions. */
import type { GameState, Player, ActionResult, GameEvent, CardKind, Phase } from './types.js';
import { nextDie } from './random.js';
import { netWorth } from './property.js';
import { DEFAULT_CARD_RULES } from './config.js';
import { accept, reject } from './transitions.js';
export function rollTurn(state: GameState, actor: Player): ActionResult {
      if (state.phase !== 'await_roll') return reject(state,'INVALID_PHASE');
      const { value, nextState } = nextDie(state.randomState);
      const bonus=state.pendingMoveBonus??0;
      const position = (actor.position + value + bonus) % state.tiles.length;
      const landed = state.tiles[position];
      const events: GameEvent[] = [
        { type: 'die_rolled', actorId: actor.id, details: { value, bonus } },
        { type: 'player_moved', actorId: actor.id, details: { from: actor.position, to: position } },
        { type: 'tile_landed', actorId: actor.id, details: { tileId: landed.id, title: landed.title } }
      ];
      let movingPlayers = state.players.map(p => p.id === actor.id ? { ...p, position } : p);
      let finalRandomState=nextState;
      if (landed.kind === 'property' && landed.ownerId && landed.ownerId !== actor.id) {
        const landlord = state.players.find(p => p.id === landed.ownerId);
        if (!landlord) return reject(state,'INVALID_PHASE');
        const due = (landed.level??0)===0 ? (landed.rent??0) : (landed.levelRents?.[landed.level??0]??0);
        const paid = Math.min(actor.cash, due);
        const insolvent = paid < due;
        const players = movingPlayers.map(p => p.id === actor.id
          ? { ...p, cash: p.cash - paid, bankrupt: insolvent }
          : p.id === landlord.id ? { ...p, cash: p.cash + paid } : p);
        events.push({ type: 'rent_paid', actorId: actor.id, details: {
          tileId: landed.id, fromId: actor.id, toId: landlord.id, due, amount: paid
        } });
        // Multiplayer: eliminate only the insolvent player; keep surviving players' turns.
        const alive=players.filter(p=>!p.bankrupt);
        const next=insolvent && alive.length>1 ? nextActiveIndex(players,state.currentPlayerIndex) : state.currentPlayerIndex;
        const wrapped=insolvent && next<=state.currentPlayerIndex;
        const roundLimit=insolvent && alive.length>1 && wrapped && state.round>=state.maxRounds;
        const finished=insolvent && (alive.length===1 || roundLimit);
        const winnerId=alive.length===1 ? alive[0].id : roundLimit ? leadingPlayer(state,players) : null;
        if (insolvent) {
          events.push({ type: 'player_bankrupt', actorId: actor.id, details: { creditorId: landlord.id } });
          if(finished)events.push({type:'game_finished',details:roundLimit
            ? {reason:'round_limit',draw:winnerId===null?1:0,...(winnerId?{winnerId}:{})}
            : {reason:'bankruptcy',winnerId:winnerId!}});
        }
        return accept(state, events, {
          randomState: nextState, players, pendingMoveBonus:0,
          // P3-06 will add optional asset liquidation; until then properties revert to unowned.
          tiles: insolvent ? state.tiles.map(t => t.ownerId === actor.id ? { ...t, ownerId: null, level:0 } : t) : state.tiles,
          status: finished ? 'finished' : 'playing',
          winnerId: finished ? winnerId : state.winnerId,
          phase: finished ? 'finished' : insolvent ? 'await_roll' : 'await_end_turn',
          currentPlayerIndex: next,
          round: !finished && wrapped ? state.round+1 : state.round
        });
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
        if(held.reward+held.stride<(state.cardRules?.maxHand??DEFAULT_CARD_RULES.maxHand)){
          const draw=nextDie(finalRandomState);finalRandomState=draw.nextState;
          const kind:CardKind=draw.value%2===1?'reward':'stride';
          movingPlayers=movingPlayers.map(p=>p.id===actor.id?{...p,cards:{...held,[kind]:held[kind]+1}}:p);
          events.push({type:'card_received',actorId:actor.id,details:{tileId:landed.id,cardType:kind}});
        }
      }
      const phase: Phase = landed.kind === 'property' && landed.ownerId === null
        ? 'await_decision' : 'await_end_turn';
      return accept(state, events, {
        randomState: finalRandomState,
        players: movingPlayers,
        pendingMoveBonus:0,
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
  const live=players.filter(p=>!p.bankrupt);
  const scores=live.map(p=>({id:p.id,value:netWorth({...state,players},p.id)}));
  const high=Math.max(...scores.map(x=>x.value));
  const leaders=scores.filter(x=>x.value===high);
  return leaders.length===1?leaders[0].id:null;
}
export function endTurn(state: GameState, actor: Player): ActionResult {
  if(state.phase!=='await_end_turn')return reject(state,'INVALID_PHASE');
  const next=nextActiveIndex(state.players,state.currentPlayerIndex);
  const wrapped=next<=state.currentPlayerIndex;
  const finished=wrapped && state.round>=state.maxRounds;
  const assets=state.players.map(p=>netWorth(state,p.id));
  const winnerId=finished?leadingPlayer(state,state.players):null;
  const events: GameEvent[]=[{type:'turn_ended',actorId:actor.id}];
  if(finished)events.push({type:'game_finished',details:{
    reason:'round_limit',draw:winnerId===null?1:0,
    firstNetWorth:assets[0],secondNetWorth:assets[1],
    ...(winnerId?{winnerId}:{})
  }});
  return accept(state,events,{
    status:finished?'finished':'playing',
    phase:finished?'finished':'await_roll',
    currentPlayerIndex:next,
    round:!finished&&wrapped?state.round+1:state.round,
    winnerId
  });
}
