/** Reproducible full-engine tournament; no browser, networking or seed-specific policy. */
import { runSimulation } from './simulator.js';
import { DEFAULT_CONFIG, HARBOR_CONFIG } from './config.js';
import { COMPUTER_STYLES } from './strategic-agent.js';
export function runStyleBenchmark(games = 1000) {
    if (!Number.isSafeInteger(games) || games < 1 || games > 10000)
        throw new Error('评测对局数必须在 1 至 10000');
    const results = Object.fromEntries(COMPUTER_STYLES.map(s => [s, { games: 0, wins: 0, bankruptcies: 0,
            actionSelection: {} }]));
    const byPlayerCount = {}, byMap = {};
    let totalActions = 0, illegalActions = 0, totalRounds = 0, totalTurns = 0;
    for (let i = 0; i < games; i++) {
        const count = 2 + i % 3;
        const base = i % 2 === 0 ? DEFAULT_CONFIG : HARBOR_CONFIG;
        const maxRounds = [12, 24, 36, 60][i % 4];
        const initialCash = [450, 800, 1500, 2500, 3500][i % 5];
        const names = COMPUTER_STYLES;
        const players = Array.from({ length: count }, (_, seat) => ({
            id: 'p' + (seat + 1), name: '电脑' + (seat + 1), kind: 'computer',
            computerStyle: names[(seat + Math.floor(i / 3)) % names.length]
        }));
        const config = { ...base, players, maxRounds, initialCash, strategyEnabled: true,
            specialEnabled: true, bankEnabled: true, loanEnabled: true, marketEnabled: true, automaticLiquidation: true };
        const seed = 12345 + i * 7919;
        // Rejected/unfinished games are fatal, never omitted from aggregates.
        const game = runSimulation(seed, { config, maxActions: maxRounds * count * 24 });
        if (game.finalState.status !== 'finished' || game.rejections !== 0)
            throw new Error('评测未完成 seed=' + seed);
        totalActions += game.actions;
        illegalActions += game.rejections;
        totalRounds += game.finalState.round;
        totalTurns += game.playerTurns;
        byPlayerCount[String(count)] = (byPlayerCount[String(count)] ?? 0) + 1;
        byMap[base.map?.id ?? 'classic-24'] = (byMap[base.map?.id ?? 'classic-24'] ?? 0) + 1;
        for (const player of game.finalState.players) {
            const style = player.computerStyle;
            const row = results[style];
            row.games++;
            if (game.finalState.winnerId === player.id)
                row.wins++;
            if (player.bankrupt)
                row.bankruptcies++;
        }
        for (const trace of game.trace) {
            const parts = trace.split(':');
            const actor = game.finalState.players.find(p => p.id === parts[1]);
            if (!actor?.computerStyle)
                throw new Error('未知评测行动者');
            const distribution = results[actor.computerStyle].actionSelection;
            distribution[parts[2]] = (distribution[parts[2]] ?? 0) + 1;
        }
    }
    const byStyle = Object.fromEntries(COMPUTER_STYLES.map(style => {
        const stats = results[style];
        const actionSelection = Object.fromEntries(Object.entries(stats.actionSelection).sort(([a], [b]) => a.localeCompare(b)));
        return [style, { ...stats, winRate: stats.wins / stats.games, bankruptcyRate: stats.bankruptcies / stats.games, actionSelection }];
    }));
    return { games, totalActions, illegalActions, totalRounds, averageRounds: totalRounds / games,
        totalTurns, averageTurns: totalTurns / games, byStyle, byPlayerCount, byMap };
}
