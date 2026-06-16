import React from 'react';
import {AbsoluteFill, Easing, Img, interpolate, useCurrentFrame} from 'remotion';
import {HUMANOS_COLORS, HUMANOS_TYPE} from '../styles/tokens';

export type HumanosCharacterCardProps = {
  archetype?: string;
  name: string;
  descriptor: string;
  imageSrc: string;
  accentColor?: string;
  layoutVariant?: 'signature' | 'portraitDominant';
};

export const HumanosCharacterCard: React.FC<HumanosCharacterCardProps> = ({
  archetype = 'BUILDER',
  name,
  descriptor,
  imageSrc,
  accentColor = HUMANOS_COLORS.cyan,
  layoutVariant = 'portraitDominant',
}) => {
  const frame = useCurrentFrame();
  const isPortraitDominant = layoutVariant === 'portraitDominant';
  const imageOpacity = interpolate(frame, [0, 16], [0, 0.92], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const archetypeOpacity = interpolate(frame, [10, 22], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const nameOpacity = interpolate(frame, [20, 34], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const descriptorOpacity = interpolate(frame, [31, 44], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const textY = interpolate(frame, [18, 34], [24, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const breath = Math.sin(frame / 24) * 0.006;

  return (
    <AbsoluteFill style={{backgroundColor: HUMANOS_COLORS.black, overflow: 'hidden'}}>
      <Img
        src={imageSrc}
        style={{
          position: 'absolute',
          left: isPortraitDominant ? '-22%' : '-10%',
          top: isPortraitDominant ? '-10%' : '-4%',
          width: isPortraitDominant ? '144%' : '120%',
          height: isPortraitDominant ? '118%' : '104%',
          objectFit: 'cover',
          objectPosition: isPortraitDominant ? '49% 20%' : '50% 34%',
          opacity: imageOpacity,
          filter: 'grayscale(1) contrast(1.34) brightness(0.68) saturate(0)',
          transform: `scale(${(isPortraitDominant ? 1.16 : 1.08) + breath})`,
        }}
      />
      <AbsoluteFill
        style={{
          opacity: 0.05,
          backgroundImage:
            'radial-gradient(circle, rgba(255,255,255,0.55) 0 1px, transparent 1px)',
          backgroundSize: '10px 12px',
          mixBlendMode: 'screen',
        }}
      />
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(2,3,4,0.06) 0%, rgba(2,3,4,0.12) 36%, rgba(2,3,4,0.9) 100%)',
        }}
      />
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(circle at 50% 28%, rgba(255,255,255,0.06), rgba(2,3,4,0) 34%), radial-gradient(circle at 50% 50%, rgba(2,3,4,0) 0%, rgba(2,3,4,0.45) 76%)',
        }}
      />

      <div
        style={{
          position: 'absolute',
          left: isPortraitDominant ? 76 : 78,
          right: 78,
          bottom: isPortraitDominant ? 120 : 176,
          transform: `translateY(${textY}px)`,
        }}
      >
        <div
          style={{
            color: HUMANOS_COLORS.mutedWhite,
            fontFamily: HUMANOS_TYPE.brand,
            fontSize: 40,
            lineHeight: 1,
            fontWeight: 700,
            letterSpacing: 9,
            opacity: archetypeOpacity * 0.94,
            marginBottom: 24,
            transform: `scale(${interpolate(frame, [10, 24], [0.965, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)})})`,
            transformOrigin: 'left center',
          }}
        >
          {archetype}
        </div>
        <div
          style={{
            color: accentColor,
            fontFamily: HUMANOS_TYPE.brand,
            fontSize: isPortraitDominant ? 74 : 62,
            lineHeight: 0.94,
            fontWeight: 700,
            letterSpacing: 3.2,
            textTransform: 'uppercase',
            opacity: nameOpacity,
          }}
        >
          {name}
        </div>
        <div
          style={{
            marginTop: 24,
            color: HUMANOS_COLORS.white,
            fontFamily: HUMANOS_TYPE.body,
            fontSize: 40,
            lineHeight: 1.25,
            fontWeight: 500,
            letterSpacing: 0.3,
            opacity: descriptorOpacity,
          }}
        >
          {descriptor}
        </div>
      </div>
    </AbsoluteFill>
  );
};
