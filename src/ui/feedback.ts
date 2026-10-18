import type { GameEvent, GameState } from "../core/game.js";
export interface VisualCue {
  readonly text: string;
  readonly tone:
    | "move"
    | "money"
    | "card"
    | "danger"
    | "finish"
    | "dice"
    | "normal";
  readonly revision: number;
  readonly actorId: string | null;
  readonly path: readonly number[];
  readonly step: number;
}
export function walkPath(
  before: GameState,
  after: GameState,
  actorId: string,
): number[] {
  const from = before.players.find((p) => p.id === actorId)?.position;
  const to = after.players.find((p) => p.id === actorId)?.position;
  if (from === undefined || to === undefined || from === to) return [];
  const route = after.map.route,
    index = route.indexOf(from);
  if (index < 0) return [];
  const path: number[] = [];
  for (let i = 1; i <= route.length; i++) {
    const tile = route[(index + i) % route.length];
    path.push(tile);
    if (tile === to) return path;
  }
  return [];
}
export function eventCue(
  before: GameState,
  after: GameState,
  events: readonly GameEvent[],
): VisualCue | null {
  if (!events.length) return null;
  const high = [
    "game_finished",
    "player_bankrupt",
    "rent_paid",
    "property_bought",
    "card_used",
    "card_received",
    "facility_entered",
    "stock_bought",
    "stock_sold",
    "bank_deposited",
    "bank_withdrawn",
    "loan_borrowed",
    "loan_repaid",
    "event_bonus",
    "event_fee",
    "die_rolled",
    "player_moved",
  ];
  const event =
    high.map((type) => events.find((e) => e.type === type)).find(Boolean) ??
    events[0];
  const amount = event.details?.amount;
  const positive = new Set([
    "event_bonus",
    "bank_interest",
    "bank_withdrawn",
    "loan_borrowed",
    "property_sold",
    "stock_sold",
  ]);
  const negative = new Set([
    "event_fee",
    "bank_deposited",
    "loan_repaid",
    "property_bought",
    "property_upgraded",
    "stock_bought",
    "rent_paid",
  ]);
  const sign = positive.has(event.type)
    ? "+"
    : negative.has(event.type)
      ? "−"
      : "";
  const amountText =
    typeof amount === "number"
      ? " · " + sign + amount.toLocaleString("zh-CN") + " 币"
      : "";
  const tone =
    event.type === "game_finished"
      ? "finish"
      : event.type === "player_bankrupt" || event.type === "facility_entered"
        ? "danger"
        : event.type.includes("card")
          ? "card"
          : event.type === "die_rolled"
            ? "dice"
            : event.type === "player_moved"
              ? "move"
              : typeof amount === "number"
                ? "money"
                : "normal";
  const person =
    before.players.find((p) => p.id === event.actorId)?.name ?? "系统";
  const labels: Record<string, string> = {
    game_finished: "对局结束",
    player_bankrupt: "破产",
    rent_paid: "支付租金",
    property_bought: "买下地产",
    card_used: "使用卡片",
    card_received: "获得卡片",
    facility_entered: "进入特殊设施",
    stock_bought: "买入股票",
    stock_sold: "卖出股票",
    bank_deposited: "存入银行",
    bank_withdrawn: "银行取款",
    loan_borrowed: "借入贷款",
    loan_repaid: "偿还贷款",
    event_bonus: "幸运奖励",
    event_fee: "事件费用",
    die_rolled: "掷出 " + event.details?.value + " 点",
    player_moved: "前进",
  };
  const moved = events.find((e) => e.type === "player_moved");
  return {
    text: person + " · " + (labels[event.type] ?? "行动完成") + amountText,
    tone,
    revision: after.revision,
    actorId: moved?.actorId ?? event.actorId ?? null,
    path: moved?.actorId ? walkPath(before, after, moved.actorId) : [],
    step: 0,
  };
}

/** Passing the device between humans still matters when AI seats act in between. */
export function needsHumanHandoff(
  before: GameState,
  after: GameState,
): boolean {
  const previous = before.players[before.currentPlayerIndex],
    next = after.players[after.currentPlayerIndex];
  return (
    after.status === "playing" &&
    previous.id !== next.id &&
    next.kind === "human" &&
    before.players.filter((p) => p.kind === "human" && !p.bankrupt).length > 1
  );
}
