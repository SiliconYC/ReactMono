type CashPlayer = { readonly id: string; readonly cash: number };
export function syncDebugCashInputs(
  drafts: Readonly<Record<string, string>>,
  previous: readonly CashPlayer[] | null,
  next: readonly CashPlayer[],
): Record<string, string> {
  return Object.fromEntries(next.map(player => [player.id,
    previous?.find(old => old.id === player.id)?.cash === player.cash
      ? drafts[player.id] ?? String(player.cash)
      : String(player.cash),
  ]));
}
