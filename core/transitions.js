export function reject(state, reason) {
    return { ok: false, reason, state, events: [] };
}
export function accept(state, events, changes) {
    return {
        ok: true,
        events,
        state: { ...state, ...changes, revision: state.revision + 1, events: [...state.events, ...events] }
    };
}
