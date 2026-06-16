import React from 'react';
import {Sequence} from 'remotion';
import {HumanosBrandReveal} from '../components/HumanosBrandReveal';
import {HumanosCharacterCard} from '../components/HumanosCharacterCard';
import {HumanosEndCard} from '../components/HumanosEndCard';
import {HumanosLogoReveal} from '../components/HumanosLogoReveal';
import {HumanosTransition} from '../components/HumanosTransition';
import {humanosPreviewConfig} from '../config/humanosConfig';

export const HumanosPreview: React.FC = () => {
  return (
    <>
      <Sequence from={0} durationInFrames={44}>
        <HumanosBrandReveal {...humanosPreviewConfig.brandReveal} title="" />
      </Sequence>
      <Sequence from={44} durationInFrames={40}>
        <HumanosLogoReveal title={humanosPreviewConfig.brandReveal.title} />
      </Sequence>
      <Sequence from={84} durationInFrames={18}>
        <HumanosTransition />
      </Sequence>
      <Sequence from={92} durationInFrames={60}>
        <HumanosCharacterCard {...humanosPreviewConfig.characterCard} />
      </Sequence>
      <Sequence from={152} durationInFrames={8}>
        <HumanosTransition />
      </Sequence>
      <Sequence from={160} durationInFrames={72}>
        <HumanosEndCard {...humanosPreviewConfig.endCard} />
      </Sequence>
    </>
  );
};
