import { useEffect, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { Dice } from './Dice.js';
import { positionForTile } from './layout.js';

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
  active: boolean;
  motion: MotionCue | null;
  reducedMotion: boolean;
  onMotionComplete: () => void;
  onStep: (tileId: number) => void;
  dieValue: number | null;
  dieNonce: number;
  trackedPosition: THREE.Vector3;
}>;

const PLAYER_COLORS = ['#ff715b', '#4f7cff'] as const;

export function Mascot({
  id,
  seat,
  tileId,
  active,
  motion,
  reducedMotion,
  onMotionComplete,
  onStep,
  dieValue,
  dieNonce,
  trackedPosition
}: MascotProps): React.JSX.Element {
  const root = useRef<THREE.Group>(null);
  const visual = useRef<THREE.Group>(null);
  const startedAt = useRef(0);
  const completed = useRef(false);
  const reportedStep = useRef(-1);
  const isMoving = motion?.actorId === id && motion.path.length > 0;
  const offset = seat === 0 ? -0.22 : 0.22;

  useEffect(() => {
    if (!isMoving) return;
    startedAt.current = performance.now() / 1000;
    completed.current = false;
    reportedStep.current = -1;
    if (reducedMotion) {
      const finalTile = motion.path[motion.path.length - 1];
      const final = positionForTile(finalTile);
      root.current?.position.set(final.x + offset, 0.27, final.z - offset);
      onStep(finalTile);
      queueMicrotask(onMotionComplete);
    }
  }, [isMoving, motion?.nonce, motion, offset, onMotionComplete, onStep, reducedMotion]);

  useFrame(({ clock }) => {
    const group = root.current;
    const body = visual.current;
    if (group === null || body === null) return;

    const idle = clock.elapsedTime * 2.2 + seat;
    body.position.y = Math.sin(idle) * 0.025;
    body.rotation.z = Math.sin(idle * 0.55) * 0.025;

    if (!isMoving || reducedMotion || motion === null) {
      const point = positionForTile(tileId);
      group.position.x = THREE.MathUtils.lerp(group.position.x, point.x + offset, 0.2);
      group.position.z = THREE.MathUtils.lerp(group.position.z, point.z - offset, 0.2);
      group.position.y = 0.27;
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
    const from = positionForTile(fromTile);
    const to = positionForTile(toTile);
    const local = THREE.MathUtils.clamp((travelTime - segment * stepDuration) / stepDuration, 0, 1);
    const eased = local * local * (3 - 2 * local);
    group.position.set(
      THREE.MathUtils.lerp(from.x, to.x, eased),
      0.27 + Math.sin(local * Math.PI) * 0.24,
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
      const final = positionForTile(motion.path[motion.path.length - 1]);
      group.position.set(final.x + offset, 0.27, final.z - offset);
      onStep(motion.path[motion.path.length - 1]);
      onMotionComplete();
    }
  });

  const color = PLAYER_COLORS[seat] ?? PLAYER_COLORS[0];
  const isFox = seat === 0;
  return (
    <group ref={root}>
      {active && <Dice value={dieValue} nonce={dieNonce} reducedMotion={reducedMotion} />}
      <mesh position={[0, -0.2, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <circleGeometry args={[0.43, 20]} />
        <meshBasicMaterial color="#173b36" transparent opacity={0.2} depthWrite={false} />
      </mesh>
      {active && (
        <mesh position={[0, -0.12, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[0.46, 0.58, 24]} />
          <meshBasicMaterial color="#ffe27b" transparent opacity={0.95} side={THREE.DoubleSide} />
        </mesh>
      )}
      <group ref={visual} scale={active ? 1.06 : 1}>
        <mesh position={[0, 0.48, 0]} castShadow>
          <sphereGeometry args={[0.38, 9, 7]} />
          <meshStandardMaterial color={color} roughness={0.78} />
        </mesh>
        <mesh position={[0, 0.94, 0.02]} castShadow>
          <sphereGeometry args={[0.43, 9, 7]} />
          <meshStandardMaterial color={isFox ? '#ff8b62' : '#6f8df6'} roughness={0.72} />
        </mesh>
        {isFox ? (
          <>
            <mesh position={[-0.26, 1.27, 0]} rotation={[0, 0, -0.16]} castShadow>
              <coneGeometry args={[0.22, 0.48, 4]} />
              <meshStandardMaterial color="#ff8b62" roughness={0.75} />
            </mesh>
            <mesh position={[0.26, 1.27, 0]} rotation={[0, 0, 0.16]} castShadow>
              <coneGeometry args={[0.22, 0.48, 4]} />
              <meshStandardMaterial color="#ff8b62" roughness={0.75} />
            </mesh>
          </>
        ) : (
          <>
            <mesh position={[-0.28, 1.2, 0]} castShadow>
              <sphereGeometry args={[0.18, 8, 6]} />
              <meshStandardMaterial color="#5472dc" roughness={0.8} />
            </mesh>
            <mesh position={[0.28, 1.2, 0]} castShadow>
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

