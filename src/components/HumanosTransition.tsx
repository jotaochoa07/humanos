import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {HUMANOS_COLORS} from '../styles/tokens';

export type HumanosTransitionProps = {
  accentColor?: string;
};

export const HumanosTransition: React.FC<HumanosTransitionProps> = ({
  accentColor = HUMANOS_COLORS.cyan,
}) => {
  const frame = useCurrentFrame();
  const pulse = interpolate(frame, [0, 3, 7], [0, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: HUMANOS_COLORS.black}}>
      <div
        style={{
          position: 'absolute',
          left: 320,
          top: 960,
          width: 440,
          height: 2,
          backgroundColor: accentColor,
          opacity: pulse * 0.7,
          transform: `scaleX(${0.2 + pulse * 0.8})`,
          transformOrigin: 'center',
        }}
      />
    </AbsoluteFill>
  );
};
