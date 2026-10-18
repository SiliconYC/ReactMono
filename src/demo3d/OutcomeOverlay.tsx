import { netWorth, type GameState } from '../core/game.js';
import type { OutcomeCue } from './outcomes.js';
import './outcomes.css';

type OutcomeOverlayProps = Readonly<{
  game: GameState;
  cue: OutcomeCue;
  reducedMotion: boolean;
  onSkip: () => void;
}>;

function OutcomeEmblem({ stage }: { stage: OutcomeCue['stage'] }): React.JSX.Element {
  return (
    <svg className="outcome-emblem" viewBox="0 0 96 96" fill="none" aria-hidden="true">
      <circle cx="48" cy="48" r="44" fill="currentColor" opacity=".12" />
      {stage === 'victory' ? (
        <g stroke="currentColor" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M32 24h32v15c0 14-7 22-16 22s-16-8-16-22V24Z" fill="currentColor" fillOpacity=".25" />
          <path d="M32 30H21v9c0 10 7 16 15 16M64 30h11v9c0 10-7 16-15 16M48 61v13M35 76h26" />
          <path d="m48 32 3 7 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1 3-7Z" fill="currentColor" strokeWidth="2" />
        </g>
      ) : stage === 'draw' ? (
        <g stroke="currentColor" strokeWidth="5" strokeLinecap="round">
          <circle cx="35" cy="48" r="18" fill="currentColor" fillOpacity=".12" />
          <circle cx="61" cy="48" r="18" fill="currentColor" fillOpacity=".12" />
          <path d="M42 44h12M42 52h12" />
        </g>
      ) : (
        <g stroke="currentColor" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M28 43h40v28H28zM39 43v-8h18v8M28 53h40M46 51v7h5v-7" fill="currentColor" fillOpacity=".14" />
          <path d="m28 25 4 5m36-5-4 5M48 21v7" />
        </g>
      )}
    </svg>
  );
}

/** A temporary announcement only. The parent owns its lifetime and the final results. */
export function OutcomeOverlay({ game, cue, reducedMotion, onSkip }: OutcomeOverlayProps): React.JSX.Element {
  const actor = game.players.find(player => player.id === cue.actorId);
  const label = cue.stage === 'bankrupt' ? '破产退场' : cue.stage === 'victory' ? '胜利庆祝' : '平局结果';
  const title = cue.stage === 'bankrupt'
    ? `${actor?.name ?? '玩家'}，本局辛苦了`
    : cue.stage === 'victory' ? `${actor?.name ?? '获胜玩家'}赢得胜利！` : '势均力敌，平局收官';
  const description = cue.stage === 'bankrupt'
    ? '本次租金未能付清，本局经营暂告一段落。带着经验，下次再来小镇吧。'
    : cue.stage === 'victory'
      ? game.players.filter(player => !player.bankrupt).length === 1
        ? '坚持到了最后，小镇为你喝彩。' : '轮次已满，凭借最高净资产赢得本局。'
      : '轮次已满，最高净资产并列。感谢每一位小镇经营者。';

  return (
    <div className="outcome-layer" data-reduced-motion={String(reducedMotion)}>
      <section
        key={`${cue.stage}-${cue.actorId}-${cue.nonce}`}
        className={`outcome-card outcome-card--${cue.stage}`}
        role="status"
        aria-live="polite"
        aria-atomic="true"
        aria-label={label}
        data-testid="outcome-overlay"
        data-stage={cue.stage}
        data-actor-id={cue.actorId ?? ''}
      >
        <OutcomeEmblem stage={cue.stage} />
        <div className="outcome-copy">
          <p className="outcome-eyebrow">{label}</p>
          <h2>{title}</h2>
          <p className="outcome-description">{description}</p>
          {cue.stage === 'victory' && actor && (
            <p className="outcome-score">最终净资产 <strong>¥{netWorth(game, actor.id).toLocaleString('zh-CN')}</strong></p>
          )}
        </div>
        <button type="button" className="outcome-skip" onClick={onSkip}>跳过演出</button>
      </section>
    </div>
  );
}
