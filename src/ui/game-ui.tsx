import * as React from "react";
import { MASCOT_SEAT_COLORS } from "../demo3d/world/seats.js";

/** Compact HUD amounts; the asset sheet always keeps the exact integer. */
export function compactCash(value: number): string {
  const unit =
    value >= 100_000_000 ? 100_000_000 : value >= 1_000_000 ? 10_000 : 1;
  if (unit === 1) return value.toLocaleString("zh-CN");
  return (
    (Math.floor((value / unit) * 10) / 10).toLocaleString("zh-CN") +
    (unit === 100_000_000 ? " 亿" : " 万")
  );
}

/** A seat's colour and silhouette match its actual piece in the 3D world. */
export function SeatAvatar({
  seat,
  small = false,
}: {
  seat: number;
  small?: boolean;
}): React.JSX.Element {
  const color = MASCOT_SEAT_COLORS[seat] ?? MASCOT_SEAT_COLORS[0];
  return (
    <span
      className={`seat-avatar${small ? " small" : ""}`}
      style={{ "--seat-color": color } as React.CSSProperties}
      aria-label={`第 ${seat + 1} 位玩家`}
    >
      <svg viewBox="0 0 48 48" aria-hidden="true">
        <g fill={color}>
          {seat === 0 ? (
            <path d="M8 23 7 5 21 15H28L41 5 40 25Z" />
          ) : (
            <>
              <circle cx="11" cy="12" r="8" />
              <circle cx="37" cy="12" r="8" />
            </>
          )}
          <ellipse cx="24" cy="26" rx="19" ry="17" />
        </g>
        <ellipse cx="24" cy="32" rx="12" ry="8" fill="#fff0d3" />
        <g fill="#183a38">
          <circle cx="16" cy="25" r="2" />
          <circle cx="32" cy="25" r="2" />
          <path d="m21 31 3 3 3-3Z" />
        </g>
      </svg>
      <b>{seat + 1}</b>
    </span>
  );
}

/** Repository-native vector artwork: no remote assets or title-screen WebGL. */
export function TownIllustration({
  harbor = false,
}: {
  harbor?: boolean;
}): React.JSX.Element {
  const plots = Array.from({ length: 7 }, (_, i) => i);
  const House = ({
    x,
    y,
    color,
    scale = 1,
  }: {
    x: number;
    y: number;
    color: string;
    scale?: number;
  }) => (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <path
        d="m0 0 35 20 35-20-35-20Z"
        fill="#71896a"
        opacity=".2"
        transform="translate(7 12)"
      />
      <path d="M0-32 35-12V20L0 0Z" fill={color} />
      <path d="m35-12 35-20V0L35 20Z" fill="#f7e5b9" />
      <path d="m-6-31 29-33 53 30-41 27Z" fill="#b96548" />
      <path d="m23-64 53 30-23-33Z" fill="#d7865a" />
      <path d="m13-17 10 6V9L13 3Z" fill="#496459" />
      <path d="m47-7 12-7V-3L47 4Z" fill="#719da0" />
      <path d="m46-8 14-8" stroke="#fff2ca" strokeWidth="3" />
    </g>
  );
  return (
    <svg
      className="town-illustration"
      viewBox="0 0 760 650"
      role="img"
      aria-label={harbor ? "海港环线地图插画" : "微缩小镇棋盘插画"}
    >
      <defs>
        <linearGradient id="island" x2="0" y2="1">
          <stop stopColor="#d5dca5" />
          <stop offset="1" stopColor="#a9be87" />
        </linearGradient>
        <linearGradient id="sea" x2="1" y2="1">
          <stop stopColor="#b4d8cd" />
          <stop offset="1" stopColor="#81b9b2" />
        </linearGradient>
      </defs>
      <ellipse
        cx="402"
        cy="485"
        rx="300"
        ry="78"
        fill="#4f8170"
        opacity=".13"
      />
      <path
        d="m60 344 326-190 322 184-324 192Z"
        fill="#618c78"
        opacity=".18"
        transform="translate(8 28)"
      />
      <path d="m52 315 326-190 324 187v38L378 542 52 354Z" fill="#b58c5e" />
      <path d="m378 504 324-192v38L378 542Z" fill="#987249" />
      <path d="m52 315 326-190 324 187-324 192Z" fill="url(#island)" />
      {harbor && <path d="m52 315 326-190 50 29-326 190Z" fill="url(#sea)" />}
      <g transform="matrix(.866 .5 -.866 .5 378 139)">
        <rect x="24" y="24" width="320" height="320" rx="18" fill="#86a87d" />
        <rect
          x="38"
          y="38"
          width="292"
          height="292"
          rx="12"
          fill="none"
          stroke="#fcf3d7"
          strokeWidth="34"
        />
        {plots.map((i) => (
          <g key={i} stroke="#bbc9a4" strokeWidth="2">
            <path
              d={`M${40 + i * 42} 20v36M${40 + i * 42} 311v36M20 ${40 + i * 42}h36M311 ${40 + i * 42}h36`}
            />
          </g>
        ))}
        <rect x="103" y="99" width="157" height="161" rx="16" fill="#b8c997" />
        <path d="M129 192h110M183 131v106" stroke="#dae0ad" strokeWidth="14" />
        <rect x="24" y="24" width="34" height="34" rx="5" fill="#edc35b" />
      </g>
      <House x={300} y={271} color="#edc488" />
      <House x={425} y={252} color="#e2b07e" scale={0.85} />
      <House x={458} y={390} color="#d5a77b" scale={1.05} />
      <House x={220} y={377} color="#f0d69c" scale={0.9} />
      {[
        { x: 153, y: 317 },
        { x: 540, y: 347 },
        { x: 366, y: 444 },
        { x: 374, y: 194 },
        { x: 619, y: 339 },
      ].map(({ x, y }) => (
        <g key={x} transform={`translate(${x} ${y})`}>
          <ellipse cy="8" rx="24" ry="11" fill="#769569" opacity=".25" />
          <path d="M0 0v-45" stroke="#9a7851" strokeWidth="8" />
          <path d="m-25-43 9-26 23-10 23 23-5 29-27 10Z" fill="#568d69" />
          <path d="m-16-69 23-10 9 29-30 8Z" fill="#76ac79" />
        </g>
      ))}
      <g transform="translate(534 254)">
        <ellipse cy="17" rx="22" ry="10" fill="#53705c" opacity=".2" />
        <path d="m-17-11 2-29 12 10h10l12-10-2 29Z" fill="#f08e61" />
        <ellipse cy="-7" rx="19" ry="20" fill="#f08e61" />
        <ellipse cy="-2" rx="12" ry="8" fill="#fff0d3" />
        <g fill="#264b3e">
          <circle cx="-8" cy="-13" r="2" />
          <circle cx="8" cy="-13" r="2" />
          <path d="m-3-3 3 3 3-3Z" />
        </g>
      </g>
      <g transform="translate(258 198) rotate(-12)">
        <rect
          x="-23"
          y="-23"
          width="46"
          height="46"
          rx="11"
          fill="#fff9e8"
          stroke="#d6c9a1"
          strokeWidth="2"
        />
        {[-10, 10].flatMap((x) =>
          [-10, 10].map((y) => (
            <circle key={`${x}${y}`} cx={x} cy={y} r="3.5" fill="#355a45" />
          )),
        )}
      </g>
    </svg>
  );
}

export function Modal({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}): React.JSX.Element {
  const ref = React.useRef<HTMLDialogElement>(null);
  React.useLayoutEffect(() => {
    const previous =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    const dialog = ref.current!;
    dialog.showModal();
    return () => {
      dialog.close();
      previous?.isConnected && previous.focus();
    };
  }, []);
  React.useLayoutEffect(() => {
    const dialog = ref.current;
    if (dialog?.open && !dialog.contains(document.activeElement)) {
      dialog
        .querySelector<HTMLElement>(
          'button:not(:disabled),input:not(:disabled),select:not(:disabled),[tabindex="0"]',
        )
        ?.focus();
    }
  });
  return (
    <dialog
      className="game-dialog"
      ref={ref}
      aria-labelledby="dialog-title"
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      onClick={(event) => {
        if (event.target === event.currentTarget) {
          const box = event.currentTarget.getBoundingClientRect();
          if (
            event.clientX < box.left ||
            event.clientX > box.right ||
            event.clientY < box.top ||
            event.clientY > box.bottom
          )
            onClose();
        }
      }}
    >
      <header className="dialog-heading">
        <div>
          <span className="eyebrow">大富翁 2026 · 本机对局</span>
          <h2 id="dialog-title">{title}</h2>
        </div>
        <button
          type="button"
          className="icon-button"
          aria-label="关闭窗口"
          onClick={onClose}
        >
          ×
        </button>
      </header>
      <div className="dialog-body">{children}</div>
    </dialog>
  );
}

import { WorldCanvas } from "../demo3d/world/WorldCanvas.js";
/** HUD measurements are presentation inputs, independent of saves and game rules. */
export function MeasuredWorld(
  props: React.ComponentProps<typeof WorldCanvas>,
): React.JSX.Element {
  const [insets, setInsets] = React.useState({
    top: 76,
    right: 20,
    bottom: 180,
    left: 260,
  });
  React.useLayoutEffect(() => {
    const nodes = [".game-top", ".player-roster", ".action-dock"]
      .map((s) => document.querySelector<HTMLElement>(s))
      .filter((n): n is HTMLElement => !!n);
    const measure = () => {
      const top = nodes[0]?.getBoundingClientRect(),
        roster = nodes[1]?.getBoundingClientRect(),
        dock = nodes[2]?.getBoundingClientRect();
      const wide = window.innerWidth > 1060;
      const short = window.innerHeight <= 500 && window.innerWidth >= 651;
      const next = {
        top: Math.ceil(
          wide || short
            ? (top?.bottom ?? 64) + 16
            : (roster?.bottom ?? 100) + 12,
        ),
        right: short
          ? Math.ceil(
              window.innerWidth - (dock?.left ?? window.innerWidth - 296) + 18,
            )
          : 24,
        bottom: short ? 20 : Math.min(window.innerWidth<=600?278:230,Math.round(window.innerHeight*.36)),
        left: wide || short ? Math.ceil((roster?.right ?? 220) + 24) : 24,
      };
      setInsets((old) =>
        JSON.stringify(old) === JSON.stringify(next) ? old : next,
      );
    };
    const observer = new ResizeObserver(measure);
    nodes.forEach((n) => observer.observe(n));
    window.addEventListener("resize", measure);
    measure();
    return () => {
      observer.disconnect();
      window.removeEventListener("resize", measure);
    };
  }, []);
  return <WorldCanvas {...props} viewportInsets={insets} />;
}
