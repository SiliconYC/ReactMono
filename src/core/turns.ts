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
        if (insolvent) {
          events.push({ type: 'player_bankrupt', actorId: actor.id, details: { creditorId: landlord.id } });
          events.push({ type: 'game_finished', details: { reason: 'bankruptcy', winnerId: landlord.id } });
        }
        return accept(state, events, {
          randomState: nextState, players, pendingMoveBonus:0,
          // 结束比赛后被淘汰者的土地回到无主状态；本阶段不实现清算/拍卖。
          tiles: insolvent ? state.tiles.map(t => t.ownerId === actor.id ? { ...t, ownerId: null, level:0 } : t) : state.tiles,
          status: insolvent ? 'finished' : 'playing',
          winnerId: insolvent ? landlord.id : state.winnerId,
          phase: insolvent ? 'finished' : 'await_end_turn'
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
export function endTurn(state: GameState, actor: Player): ActionResult {
      if (state.phase !== 'await_end_turn') return reject(state,'INVALID_PHASE');
      const lastPlayer = state.currentPlayerIndex === state.players.length - 1;
      const finished = lastPlayer && state.round >= state.maxRounds;
      const assets = state.players.map(p => netWorth(state, p.id));
      const winnerId = finished && assets[0] !== assets[1]
        ? state.players[assets[0] > assets[1] ? 0 : 1].id : null;
      const events: GameEvent[] = [{ type: 'turn_ended', actorId: actor.id }];
      if (finished) events.push({ type: 'game_finished', details: {
        reason: 'round_limit', draw: winnerId === null ? 1 : 0,
        firstNetWorth: assets[0], secondNetWorth: assets[1],
        ...(winnerId ? { winnerId } : {})
      } });
      return accept(state, events, {
        status: finished ? 'finished' : 'playing',
        phase: finished ? 'finished' : 'await_roll',
        currentPlayerIndex: (state.currentPlayerIndex + 1) % state.players.length,
        round: !finished && lastPlayer ? state.round + 1 : state.round,
        winnerId
      });
}
