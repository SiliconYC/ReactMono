import { nextDie } from './random.js';
import { advancePosition } from './maps.js';
import { netWorth, liquidateForRent } from './property.js';
import { advanceMarket } from './market.js';
import { foreclose, settleLoanRound } from './loan.js';
import { coverRentFromBank, settleBankRound } from './bank.js';
import { DEFAULT_CARD_RULES } from './config.js';
import { accept, reject } from './transitions.js';
export function rollTurn(state, actor) {
    if (state.phase !== 'await_roll')
        return reject(state, 'INVALID_PHASE');
    const { value, nextState } = nextDie(state.randomState);
    const bonus = state.pendingMoveBonus ?? 0;
    const position = advancePosition(state.map, actor.position, value + bonus);
    const landed = state.tiles[position];
    const events = [
        { type: 'die_rolled', actorId: actor.id, details: { value, bonus } },
        { type: 'player_moved', actorId: actor.id, details: { from: actor.position, to: position } },
        { type: 'tile_landed', actorId: actor.id, details: { tileId: landed.id, title: landed.title } }
    ];
    let movingPlayers = state.players.map(p => p.id === actor.id ? { ...p, position } : p);
    let finalRandomState = nextState;
    if (landed.kind === 'property' && landed.ownerId && landed.ownerId !== actor.id) {
        const landlord = state.players.find(p => p.id === landed.ownerId);
        if (!landlord)
            return reject(state, 'INVALID_PHASE');
        const due = landed.mortgaged === true ? 0 : (landed.level ?? 0) === 0 ? (landed.rent ?? 0) : (landed.levelRents?.[landed.level ?? 0] ?? 0);
        const funds = coverRentFromBank(state, actor, due);
        if (funds.amount > 0)
            events.push({ type: 'bank_withdrawn', actorId: actor.id, details: { amount: funds.amount, reason: 'rent' } });
        let rescue = state.automaticLiquidation === true
            ? liquidateForRent(state, { ...actor, cash: funds.cash }, due, landlord.id)
            : { cash: funds.cash, tiles: state.tiles, events: [] };
        events.push(...rescue.events);
        let loanBalance = actor.loanBalance ?? 0;
        // Rent deficit: pledge is seized by the bank, only collateral proceeds in excess
        // of the secured loan may pay the landlord. No bank debt survives foreclosure.
        if (rescue.cash < due && state.loan && loanBalance > 0) {
            const seized = foreclose(state, { ...actor, cash: 0 }, rescue.tiles);
            rescue = { ...rescue, cash: rescue.cash + seized.player.cash, tiles: seized.tiles };
            loanBalance = 0;
            events.push(...seized.events);
        }
        const paid = Math.min(rescue.cash, due);
        const insolvent = paid < due;
        const players = movingPlayers.map(p => p.id === actor.id
            ? { ...p, cash: rescue.cash - paid, ...(funds.amount > 0 ? { bankBalance: funds.bankBalance } : {}), bankrupt: insolvent, ...(state.loan ? { loanBalance } : {}) }
            : p.id === landlord.id ? { ...p, cash: p.cash + paid } : p);
        events.push({ type: 'rent_paid', actorId: actor.id, details: {
                tileId: landed.id, fromId: actor.id, toId: landlord.id, due, amount: paid
            } });
        // Multiplayer: eliminate only the insolvent player; keep surviving players' turns.
        const alive = players.filter(p => !p.bankrupt);
        const next = insolvent && alive.length > 1 ? nextActiveIndex(players, state.currentPlayerIndex) : state.currentPlayerIndex;
        const wrapped = insolvent && next <= state.currentPlayerIndex;
        const roundLimit = insolvent && alive.length > 1 && wrapped && state.round >= state.maxRounds;
        const finished = insolvent && (alive.length === 1 || roundLimit);
        const winnerId = alive.length === 1 ? alive[0].id : roundLimit ? leadingPlayer(state, players) : null;
        if (insolvent) {
            events.push({ type: 'player_bankrupt', actorId: actor.id, details: { creditorId: landlord.id } });
            if (finished)
                events.push({ type: 'game_finished', details: roundLimit
                        ? { reason: 'round_limit', draw: winnerId === null ? 1 : 0, ...(winnerId ? { winnerId } : {}) }
                        : { reason: 'bankruptcy', winnerId: winnerId } });
        }
        const interest = state.bank && !finished && wrapped ? settleBankRound(state, players, state.round + 1) : null;
        if (interest)
            events.push(...interest.events);
        const clearedTiles = insolvent ? rescue.tiles.map(t => {
            if (t.ownerId !== actor.id)
                return t;
            const { mortgaged: _unused, ...rest } = t;
            return { ...rest, ownerId: null, level: 0 };
        }) : rescue.tiles;
        const loanSettle = state.loan && !finished && wrapped
            ? settleLoanRound(state, interest?.players ?? players, clearedTiles, state.round + 1) : null;
        if (loanSettle)
            events.push(...loanSettle.events);
        return accept(state, events, {
            randomState: nextState, players: loanSettle?.players ?? interest?.players ?? players, pendingMoveBonus: 0,
            ...(interest ? { bank: interest.bank } : {}),
            ...(loanSettle ? { loan: loanSettle.loan } : {}),
            // Auction at defined resale value before paying rent; residual insolvency releases all land.
            tiles: loanSettle?.tiles ?? clearedTiles,
            status: finished ? 'finished' : 'playing',
            winnerId: finished ? winnerId : state.winnerId,
            phase: finished ? 'finished' : insolvent ? 'await_roll' : 'await_end_turn',
            currentPlayerIndex: next,
            round: !finished && wrapped ? state.round + 1 : state.round,
            ...(state.market && !finished && wrapped ? { market: advanceMarket(state.market, state.round + 1) } : {})
        });
    }
    if (landed.kind === 'neutral' && landed.eventBonus !== undefined && landed.eventFee !== undefined) {
        const draw = nextDie(finalRandomState);
        finalRandomState = draw.nextState;
        if (draw.value % 2 === 1) {
            movingPlayers = movingPlayers.map(p => p.id === actor.id ? { ...p, cash: p.cash + landed.eventBonus } : p);
            events.push({ type: 'event_bonus', actorId: actor.id, details: { tileId: landed.id, amount: landed.eventBonus, draw: draw.value } });
        }
        else {
            const paid = Math.min(actor.cash, landed.eventFee);
            movingPlayers = movingPlayers.map(p => p.id === actor.id ? { ...p, cash: p.cash - paid } : p);
            events.push({ type: 'event_fee', actorId: actor.id, details: { tileId: landed.id, due: landed.eventFee, amount: paid, draw: draw.value } });
        }
    }
    if (landed.cardStation) {
        const owner = movingPlayers.find(p => p.id === actor.id);
        const held = owner.cards ?? { reward: 0, stride: 0 };
        if (held.reward + held.stride < (state.cardRules?.maxHand ?? DEFAULT_CARD_RULES.maxHand)) {
            const draw = nextDie(finalRandomState);
            finalRandomState = draw.nextState;
            const kind = draw.value % 2 === 1 ? 'reward' : 'stride';
            movingPlayers = movingPlayers.map(p => p.id === actor.id ? { ...p, cards: { ...held, [kind]: held[kind] + 1 } } : p);
            events.push({ type: 'card_received', actorId: actor.id, details: { tileId: landed.id, cardType: kind } });
        }
    }
    const phase = landed.kind === 'property' && landed.ownerId === null
        ? 'await_decision' : 'await_end_turn';
    return accept(state, events, {
        randomState: finalRandomState,
        players: movingPlayers,
        pendingMoveBonus: 0,
        phase
    });
}
/** The next live participant, wrapping past bankrupt seats. */
export function nextActiveIndex(players, current) {
    for (let step = 1; step <= players.length; step++) {
        const index = (current + step) % players.length;
        if (!players[index].bankrupt)
            return index;
    }
    throw new Error('无存活玩家，回合状态无效');
}
function leadingPlayer(state, players) {
    const live = players.filter(p => !p.bankrupt);
    const scores = live.map(p => ({ id: p.id, value: netWorth({ ...state, players }, p.id) }));
    const high = Math.max(...scores.map(x => x.value));
    const leaders = scores.filter(x => x.value === high);
    return leaders.length === 1 ? leaders[0].id : null;
}
export function endTurn(state, actor) {
    if (state.phase !== 'await_end_turn')
        return reject(state, 'INVALID_PHASE');
    const next = nextActiveIndex(state.players, state.currentPlayerIndex);
    const wrapped = next <= state.currentPlayerIndex;
    const finished = wrapped && state.round >= state.maxRounds;
    const assets = state.players.map(p => netWorth(state, p.id));
    const winnerId = finished ? leadingPlayer(state, state.players) : null;
    const events = [{ type: 'turn_ended', actorId: actor.id }];
    if (finished)
        events.push({ type: 'game_finished', details: {
                reason: 'round_limit', draw: winnerId === null ? 1 : 0,
                firstNetWorth: assets[0], secondNetWorth: assets[1],
                ...(winnerId ? { winnerId } : {})
            } });
    const interest = state.bank && !finished && wrapped ? settleBankRound(state, state.players, state.round + 1) : null;
    if (interest)
        events.push(...interest.events);
    const loanSettle = state.loan && !finished && wrapped ? settleLoanRound(state, interest?.players ?? state.players, state.tiles, state.round + 1) : null;
    if (loanSettle)
        events.push(...loanSettle.events);
    return accept(state, events, {
        ...(interest ? { bank: interest.bank, players: interest.players } : {}),
        ...(loanSettle ? { loan: loanSettle.loan, players: loanSettle.players, tiles: loanSettle.tiles } : {}),
        status: finished ? 'finished' : 'playing',
        phase: finished ? 'finished' : 'await_roll',
        currentPlayerIndex: next,
        round: !finished && wrapped ? state.round + 1 : state.round,
        ...(state.market && !finished && wrapped ? { market: advanceMarket(state.market, state.round + 1) } : {}),
        winnerId
    });
}
