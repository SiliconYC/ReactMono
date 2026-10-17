export function rentCueFor(events) {
    const details = events.find(event => event.type === 'rent_paid')?.details;
    if (typeof details?.fromId !== 'string' || typeof details.toId !== 'string' ||
        typeof details.tileId !== 'number' || typeof details.amount !== 'number')
        return null;
    return { fromId: details.fromId, toId: details.toId, tileId: details.tileId, amount: details.amount };
}
