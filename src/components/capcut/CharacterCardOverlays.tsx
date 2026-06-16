import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';
import {HUMANOS_COLORS, HUMANOS_TYPE} from '../../styles/tokens';

type OverlayProps = {
  accentColor?: string;
};

export const CharacterCardBackgroundGradeOverlay: React.FC = () => {
  return (
    <AbsoluteFill style={{backgroundColor: 'transparent'}}>
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(2,3,4,0.06) 0%, rgba(2,3,4,0.12) 36%, rgba(2,3,4,0.9) 100%)',
        }}
      />
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(circle at 50% 28%, rgba(255,255,255,0.06), rgba(2,3,4,0) 34%)',
        }}
      />
    </AbsoluteFill>
  );
};

export const CharacterCardGrainOverlay: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill
      style={{
        backgroundColor: 'transparent',
        opacity: 0.05,
        backgroundImage:
          'radial-gradient(circle, rgba(255,255,255,0.55) 0 1px, transparent 1px)',
        backgroundSize: `${10 + (frame % 2)}px ${12 + (frame % 3)}px`,
        mixBlendMode: 'screen',
      }}
    />
  );
};

export const CharacterCardVignetteOverlay: React.FC = () => {
  return (
    <AbsoluteFill
      style={{
        background:
          'radial-gradient(circle at 50% 50%, rgba(2,3,4,0) 0%, rgba(2,3,4,0.12) 48%, rgba(2,3,4,0.56) 100%)',
      }}
    />
  );
};

export const CharacterCardTextTimingReference: React.FC<OverlayProps> = ({
  accentColor = HUMANOS_COLORS.cyan,
}) => {
  const frame = useCurrentFrame();
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

  return (
    <AbsoluteFill style={{backgroundColor: 'transparent'}}>
      <div
        style={{
          position: 'absolute',
          left: 76,
          right: 78,
          bottom: 120,
          fontFamily: HUMANOS_TYPE.body,
        }}
      >
        <div
          style={{
            color: HUMANOS_COLORS.mutedWhite,
            fontFamily: HUMANOS_TYPE.brand,
            fontSize: 34,
            lineHeight: 1,
            fontWeight: 700,
            letterSpacing: 9,
            opacity: archetypeOpacity * 0.94,
            marginBottom: 24,
          }}
        >
          BUILDER
        </div>
        <div
          style={{
            color: accentColor,
            fontFamily: HUMANOS_TYPE.brand,
            fontSize: 74,
            lineHeight: 0.94,
            fontWeight: 700,
            letterSpacing: 3.2,
            textTransform: 'uppercase',
            opacity: nameOpacity,
          }}
        >
          JAN KOUM
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
          Fundador de WhatsApp
        </div>
      </div>
    </AbsoluteFill>
  );
};
