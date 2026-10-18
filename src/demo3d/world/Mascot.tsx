import { useEffect, useLayoutEffect, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { Dice } from './Dice.js';
import type { OutcomeCue } from '../outcomes.js';
import { ACTOR_ANCHOR_Y, ROAD_TILE_TOP, positionForTile } from './layout.js';
import type { GameMap } from '../../core/types.js';
import { mascotSeatLayout } from './seats.js';

export type MotionCue = Readonly<{
  actorId: string;
  fromTileId: number;
  path: readonly number[];
  nonce: number;
}>;

type MascotProps = Readonly<{
  id: string;
  seat: number;
  tileId: number;
  map: GameMap;
  active: boolean;
  motion: MotionCue | null;
  reducedMotion: boolean;
  onMotionComplete: () => void;
  onStep: (tileId: number) => void;
  dieValue: number | null;
  dieNonce: number;
  trackedPosition: THREE.Vector3;
  bankrupt?: boolean;
  awaitingExit?: boolean;
  outcome?: OutcomeCue | null;
}>;

export function Mascot({
  id,
  seat,
  tileId,
  map,
  active,
  motion,
  reducedMotion,
  onMotionComplete,
  onStep,
  dieValue,
  dieNonce,
  trackedPosition,
  bankrupt = false,
  awaitingExit = false,
  outcome = null
}: MascotProps): React.JSX.Element | null {
  const root = useRef<THREE.Group>(null);
  const visual = useRef<THREE.Group>(null);
  const startedAt = useRef(0);
  const outcomeElapsed = useRef(0);
  const leftPaw = useRef<THREE.Group>(null);
  const rightPaw = useRef<THREE.Group>(null);
  const completed = useRef(false);
  const reportedStep = useRef(-1);
  const isMoving = motion?.actorId === id && motion.path.length > 0;
  const seatLayout = mascotSeatLayout(seat);
  const {x: offsetX, z: offsetZ} = seatLayout;
  const actorOutcome = outcome?.actorId === id ? outcome : null;

  useLayoutEffect(() => {
    if (!reducedMotion || isMoving || !root.current) return;
    const point = positionForTile(tileId, map);
    root.current.position.set(point.x + offsetX, ACTOR_ANCHOR_Y, point.z + offsetZ);
    // CameraRig must see the settled target before the single demand frame.
    if (active) trackedPosition.copy(root.current.position);
  }, [reducedMotion, isMoving, tileId, map, offsetX, offsetZ, active, trackedPosition]);

  useLayoutEffect(() => {
    outcomeElapsed.current = 0;
    if (visual.current) {
      visual.current.position.set(0, 0, 0);
      visual.current.rotation.set(0, 0, 0);
      visual.current.scale.setScalar(active ? 1.06 : 1);
    }
  }, [outcome?.nonce, outcome?.stage, outcome?.actorId, bankrupt, awaitingExit, active, reducedMotion]);

  useEffect(() => {
    if (!isMoving) return;
    startedAt.current = performance.now() / 1000;
    completed.current = false;
    reportedStep.current = -1;
    if (reducedMotion) {
      const finalTile = motion.path[motion.path.length - 1];
      const final = positionForTile(finalTile, map);
      root.current?.position.set(final.x + offsetX, ACTOR_ANCHOR_Y, final.z + offsetZ);
      onStep(finalTile);
      queueMicrotask(onMotionComplete);
    }
  }, [isMoving, motion?.nonce, motion?.path, motion?.fromTileId, map, offsetX, offsetZ, onMotionComplete, onStep, reducedMotion]);

  useFrame(({ clock }, delta) => {
    const group = root.current;
    const body = visual.current;
    if (group === null || body === null) return;

    const idle = clock.elapsedTime * 2.2 + seat;
    body.position.set(0, reducedMotion ? 0 : Math.sin(idle) * 0.025, 0);
    body.rotation.set(0, 0, reducedMotion ? 0 : Math.sin(idle * 0.55) * 0.025);
    body.scale.setScalar(active ? 1.06 : 1);
    if (leftPaw.current) leftPaw.current.rotation.z = 0.2;
    if (rightPaw.current) rightPaw.current.rotation.z = -0.2;

    if (actorOutcome) {
      outcomeElapsed.current = Math.min(outcomeElapsed.current + delta, 2);
      const elapsed = outcomeElapsed.current;
      if (actorOutcome.stage === 'bankrupt') {
        const fall = reducedMotion ? 0.2 : THREE.MathUtils.smoothstep(elapsed, 0.1, 0.85);
        const shrink = reducedMotion ? 0 : THREE.MathUtils.smoothstep(elapsed, 0.95, 1.6);
        body.rotation.z = -fall * 1.15;
        body.position.y = -fall * 0.17;
        body.scale.setScalar((active ? 1.06 : 1) * (1 - shrink * 0.96));
      } else if (actorOutcome.stage === 'victory') {
        const progress = THREE.MathUtils.clamp(elapsed / 1.8, 0, 1);
        body.position.y = reducedMotion ? 0 : Math.abs(Math.sin(progress * Math.PI * 3)) * 0.35 * (1 - progress);
        body.rotation.z = reducedMotion ? 0 : Math.sin(progress * Math.PI * 4) * 0.08 * (1 - progress);
        if (leftPaw.current) leftPaw.current.rotation.z = -2.3;
        if (rightPaw.current) rightPaw.current.rotation.z = 2.3;
      }
    }

    if (!isMoving || reducedMotion || motion === null) {
      const point = positionForTile(tileId, map);
      group.position.x = reducedMotion ? point.x + offsetX : THREE.MathUtils.lerp(group.position.x, point.x + offsetX, 0.2);
      group.position.z = reducedMotion ? point.z + offsetZ : THREE.MathUtils.lerp(group.position.z, point.z + offsetZ, 0.2);
      group.position.y = ACTOR_ANCHOR_Y;
      if (active) trackedPosition.copy(group.position);
      return;
    }

    const elapsed = performance.now() / 1000 - startedAt.current;
    const diceDelay = 1.02;
    const stepDuration = 0.24;
    const travelTime = Math.max(0, elapsed - diceDelay);
    const segment = Math.min(motion.path.length - 1, Math.floor(travelTime / stepDuration));
    const fromTile = segment === 0 ? motion.fromTileId : motion.path[segment - 1];
    const toTile = motion.path[segment];
    const from = positionForTile(fromTile, map);
    const to = positionForTile(toTile, map);
    const local = THREE.MathUtils.clamp((travelTime - segment * stepDuration) / stepDuration, 0, 1);
    const eased = local * local * (3 - 2 * local);
    group.position.set(
      THREE.MathUtils.lerp(from.x, to.x, eased),
      ACTOR_ANCHOR_Y + Math.sin(local * Math.PI) * 0.24,
      THREE.MathUtils.lerp(from.z, to.z, eased)
    );
    group.rotation.y = THREE.MathUtils.lerp(group.rotation.y, Math.atan2(to.x - from.x, to.z - from.z), 0.2);

    if (active) trackedPosition.copy(group.position);

    if (segment !== reportedStep.current && local > 0.55) {
      reportedStep.current = segment;
      onStep(toTile);
    }

    if (travelTime >= motion.path.length * stepDuration + 0.18 && !completed.current) {
      completed.current = true;
      const final = positionForTile(motion.path[motion.path.length - 1], map);
      group.position.set(final.x + offsetX, ACTOR_ANCHOR_Y, final.z + offsetZ);
      onStep(motion.path[motion.path.length - 1]);
      onMotionComplete();
    }
  });

  if (bankrupt && !awaitingExit) return null;

  const color = seatLayout.color;
  const isFox = seat === 0;
  return (
    <group ref={root}>
      {active && !outcome && <Dice value={dieValue} nonce={dieNonce} reducedMotion={reducedMotion} />}
      <mesh position={[0, ROAD_TILE_TOP - ACTOR_ANCHOR_Y + 0.004, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[0.43, 20]} />
        <meshBasicMaterial color="#173b36" transparent opacity={0.2} depthWrite={false} />
      </mesh>
      {active && (
        <mesh position={[0, ROAD_TILE_TOP - ACTOR_ANCHOR_Y + 0.004, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.46, 0.58, 24]} />
          <meshBasicMaterial color="#ffe27b" transparent opacity={0.95} side={THREE.DoubleSide} />
        </mesh>
      )}
      <group ref={visual} scale={active ? 1.06 : 1}>
        <group ref={leftPaw} position={[-0.31, 0.61, 0.02]} rotation={[0, 0, 0.2]}>
          <mesh position={[-0.1, -0.13, 0]}>
            <sphereGeometry args={[0.15, 7, 5]} />
            <meshStandardMaterial color={color} roughness={0.78} />
          </mesh>
        </group>
        <group ref={rightPaw} position={[0.31, 0.61, 0.02]} rotation={[0, 0, -0.2]}>
          <mesh position={[0.1, -0.13, 0]}>
            <sphereGeometry args={[0.15, 7, 5]} />
            <meshStandardMaterial color={color} roughness={0.78} />
          </mesh>
        </group>
        <mesh position={[0, 0.48, 0]}>
          <sphereGeometry args={[0.38, 9, 7]} />
          <meshStandardMaterial color={color} roughness={0.78} />
        </mesh>
        <mesh position={[0, 0.94, 0.02]}>
          <sphereGeometry args={[0.43, 9, 7]} />
          <meshStandardMaterial color={isFox ? '#ff8b62' : '#6f8df6'} roughness={0.72} />
        </mesh>
        {isFox ? (
          <>
            <mesh position={[-0.26, 1.27, 0]} rotation={[0, 0, -0.16]}>
              <coneGeometry args={[0.22, 0.48, 4]} />
              <meshStandardMaterial color="#ff8b62" roughness={0.75} />
            </mesh>
            <mesh position={[0.26, 1.27, 0]} rotation={[0, 0, 0.16]}>
              <coneGeometry args={[0.22, 0.48, 4]} />
              <meshStandardMaterial color="#ff8b62" roughness={0.75} />
            </mesh>
          </>
        ) : (
          <>
            <mesh position={[-0.28, 1.2, 0]}>
              <sphereGeometry args={[0.18, 8, 6]} />
              <meshStandardMaterial color="#5472dc" roughness={0.8} />
            </mesh>
            <mesh position={[0.28, 1.2, 0]}>
              <sphereGeometry args={[0.18, 8, 6]} />
              <meshStandardMaterial color="#5472dc" roughness={0.8} />
            </mesh>
          </>
        )}
        <mesh position={[0, 0.9, 0.39]} scale={[1, 0.72, 0.42]}>
          <sphereGeometry args={[0.26, 8, 6]} />
          <meshStandardMaterial color="#fff0d3" roughness={0.88} />
        </mesh>
        {[-0.14, 0.14].map(x => (
          <mesh key={x} position={[x, 1.03, 0.4]}>
            <sphereGeometry args={[0.035, 7, 5]} />
            <meshBasicMaterial color="#183a38" />
          </mesh>
        ))}
        <mesh position={[0, 0.91, 0.52]}>
          <sphereGeometry args={[0.045, 7, 5]} />
          <meshBasicMaterial color="#183a38" />
        </mesh>
        <mesh position={[0, 0.67, 0.3]} rotation={[0.12, 0, 0]}>
          <torusGeometry args={[0.25, 0.055, 6, 16]} />
          <meshStandardMaterial color={isFox ? '#1d6c66' : '#ffcf5c'} roughness={0.65} />
        </mesh>
      </group>
    </group>
  );
}

