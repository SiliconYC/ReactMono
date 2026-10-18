/** Distinct four-seat markers keep 2–4 player pieces readable on shared tiles. */
export const MASCOT_SEAT_COLORS = ['#ff715b', '#4f7cff', '#28a77b', '#c45bb4'] as const;
export const MASCOT_SEAT_OFFSETS = [
  [-0.24, 0.24], [0.24, -0.24], [-0.24, -0.24], [0.24, 0.24]
] as const;

export function mascotSeatLayout(seat: number): Readonly<{color: string; x: number; z: number}> {
  const index = Number.isInteger(seat) && seat >= 0 && seat < MASCOT_SEAT_COLORS.length ? seat : 0;
  const [x, z] = MASCOT_SEAT_OFFSETS[index];
  return {color: MASCOT_SEAT_COLORS[index], x, z};
}
