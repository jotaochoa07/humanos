import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from 'remotion';
import {HUMANOS_COLORS, HUMANOS_TYPE} from '../styles/tokens';

export type HumanosLogoRevealProps = {
  title: string;
  accentColor?: string;
};

export const HumanosLogoReveal: React.FC<HumanosLogoRevealProps> = ({
  title,
  accentColor = HUMANOS_COLORS.cyan,
}) => {
  const frame = useCurrentFrame();
  const breath = Math.sin(frame / 24) * 0.008;
  const logoOpacity = interpolate(frame, [4, 16, 28, 36], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const logoScale = interpolate(frame, [4, 22], [0.94, 1.025], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const pulseOpacity = interpolate(frame, [0, 4, 8], [0, 0.52, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor: HUMANOS_COLORS.black, overflow: 'hidden'}}>
      <AbsoluteFill
        style={{
          transform: `scale(${1 + breath})`,
          background:
            'radial-gradient(circle at 50% 50%, rgba(255,255,255,0.055), rgba(2,3,4,0) 44%)',
        }}
      />
      <AbsoluteFill
        style={{
          opacity: 0.04,
          backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.5) 0 1px, transparent 1px)',
          backgroundSize: '11px 13px',
          mixBlendMode: 'screen',
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: 346,
          top: 960,
          width: 388,
          height: 2,
          backgroundColor: accentColor,
          opacity: pulseOpacity,
          transform: `scaleX(${interpolate(frame, [0, 4], [0.08, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          })})`,
          transformOrigin: 'center',
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: HUMANOS_COLORS.white,
          fontFamily: HUMANOS_TYPE.brand,
          fontSize: 112,
          letterSpacing: 17,
          fontWeight: 700,
          opacity: logoOpacity,
          transform: `scale(${logoScale})`,
        }}
      >
        {title}
      </div>
    </AbsoluteFill>
  );
};
