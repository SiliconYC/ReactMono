/** Translates only this action's real events; never settles rules or replays old results. */
export function outcomeSequence(events, game) {
    const cues = [];
    for (const event of events) {
        if (event.type === 'player_bankrupt' && event.actorId) {
            cues.push({ stage: 'bankrupt', actorId: event.actorId, winnerId: null, nonce: game.revision + cues.length });
        }
    }
    if (events.some(event => event.type === 'game_finished')) {
        cues.push({
            stage: game.winnerId === null ? 'draw' : 'victory',
            actorId: game.winnerId,
            winnerId: game.winnerId,
            nonce: game.revision + cues.length
        });
    }
    return cues;
}
