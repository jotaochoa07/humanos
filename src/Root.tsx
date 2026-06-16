import React from 'react';
import {Composition} from 'remotion';
import {HumanosBrandReveal} from './components/HumanosBrandReveal';
import {HumanosCharacterCard} from './components/HumanosCharacterCard';
import {HumanosEndCard} from './components/HumanosEndCard';
import {HumanosLogoReveal} from './components/HumanosLogoReveal';
import {HumanosTransition} from './components/HumanosTransition';
import {HumanosBackgroundLoop, LongBrandCategories, LongCyanLinePulse} from './components/capcut/BrandingUtilityAssets';
import {SlowCategoryThoughts} from './components/capcut/SlowCategoryThoughts';
import {CharacterCardBackgroundGradeOverlay, CharacterCardGrainOverlay, CharacterCardTextTimingReference, CharacterCardVignetteOverlay} from './components/capcut/CharacterCardOverlays';
import {HumanosPreview} from './compositions/HumanosPreview';
import {HumanosBrandCategories} from './compositions/HumanosBrandCategories';
import {humanosPreviewConfig} from './config/humanosConfig';
import {HUMANOS_VIDEO} from './styles/tokens';

export const RemotionRoot: React.FC = () => {
  return (
    <>


      <Composition
        id="CategoryThoughtsSetA"
        component={SlowCategoryThoughts}
        durationInFrames={120}
        fps={HUMANOS_VIDEO.fps}
        width={HUMANOS_VIDEO.width}
        height={HUMANOS_VIDEO.height}
        defaultProps={{
          categories: ['FOUNDERS', 'BUILDERS', 'INVENTORS', 'DREAMERS', 'CREATORS', 'MAKERS'],
        }}
      />
      <Composition
        id="CategoryThoughtsSetB"
        component={SlowCategoryThoughts}
        durationInFrames={120}
        fps={HUMANOS_VIDEO.fps}
        width={HUMANOS_VIDEO.width}
        height={HUMANOS_VIDEO.height}
        defaultProps={{
          categories: ['SCIENTISTS', 'EXPLORERS', 'ENGINEERS', 'VISIONARIES'],
        }}
      />
      <Composition
        id="CategoryThoughtsSetC"
        component={SlowCategoryThoughts}
        durationInFrames={120}
        fps={HUMANOS_VIDEO.fps}
        width={HUMANOS_VIDEO.width}
        height={HUMANOS_VIDEO.height}
        defaultProps={{
          categories: ['ENTREPRENEURS', 'DESIGNERS', 'ARTISTS', 'MAKERS', 'DREAMERS'],
        }}
      />
      <Composition
        id="LongBrandCategories"
        component={LongBrandCategories}
        durationInFrames={120}
        fps={HUMANOS_VIDEO.fps}
        width={HUMANOS_VIDEO.width}
        height={HUMANOS_VIDEO.height}
      />
      <Composition
        id="LongCyanLinePulse"
        component={LongCyanLinePulse}
        durationInFrames={90}
        fps={HUMANOS_VIDEO.fps}
        width={HUMANOS_VIDEO.width}
        height={HUMANOS_VIDEO.height}
      />
      <Composition
        id="HumanosBackgroundLoop"
        component={HumanosBackgroundLoop}
        durationInFrames={120}
        fps={HUMANOS_VIDEO.fps}
        width={HUMANOS_VIDEO.width}
        height={HUMANOS_VIDEO.height}
      />
      <Composition
        id="HumanosPreview"
        component={HumanosPreview}
        durationInFrames={232}
        fps={HUMANOS_VIDEO.fps}
        width={HUMANOS_VIDEO.width}
        height={HUMANOS_VIDEO.height}
      />

      <Composition
        id="HumanosBrandCategories"
        component={HumanosBrandCategories}
        durationInFrames={44}
        fps={HUMANOS_VIDEO.fps}
        width={HUMANOS_VIDEO.width}
        height={HUMANOS_VIDEO.height}
      />
      <Composition
        id="HumanosBrandReveal"
        component={HumanosBrandReveal}
        durationInFrames={66}
        fps={HUMANOS_VIDEO.fps}
        width={HUMANOS_VIDEO.width}
        height={HUMANOS_VIDEO.height}
        defaultProps={{
          title: humanosPreviewConfig.brandReveal.title,
          categories: humanosPreviewConfig.brandReveal.categories,
        }}
      />

      <Composition
        id="HumanosLogoReveal"
        component={HumanosLogoReveal}
        durationInFrames={40}
        fps={HUMANOS_VIDEO.fps}
        width={HUMANOS_VIDEO.width}
        height={HUMANOS_VIDEO.height}
        defaultProps={{
          title: humanosPreviewConfig.brandReveal.title,
        }}
      />
      <Composition
        id="HumanosCharacterCard"
        component={HumanosCharacterCard}
        durationInFrames={60}
        fps={HUMANOS_VIDEO.fps}
        width={HUMANOS_VIDEO.width}
        height={HUMANOS_VIDEO.height}
        defaultProps={{
          name: humanosPreviewConfig.characterCard.name,
          descriptor: humanosPreviewConfig.characterCard.descriptor,
          imageSrc: humanosPreviewConfig.characterCard.imageSrc,
        }}
      />

      <Composition
        id="JanKoumCharacterCardA"
        component={HumanosCharacterCard}
        durationInFrames={60}
        fps={HUMANOS_VIDEO.fps}
        width={HUMANOS_VIDEO.width}
        height={HUMANOS_VIDEO.height}
        defaultProps={humanosPreviewConfig.characterCardVariantA}
      />
      <Composition
        id="JanKoumCharacterCardB"
        component={HumanosCharacterCard}
        durationInFrames={60}
        fps={HUMANOS_VIDEO.fps}
        width={HUMANOS_VIDEO.width}
        height={HUMANOS_VIDEO.height}
        defaultProps={humanosPreviewConfig.characterCard}
      />
      <Composition
        id="HumanosTransition"
        component={HumanosTransition}
        durationInFrames={8}
        fps={HUMANOS_VIDEO.fps}
        width={HUMANOS_VIDEO.width}
        height={HUMANOS_VIDEO.height}
      />

      <Composition
        id="CharacterCardBackgroundGradeOverlay"
        component={CharacterCardBackgroundGradeOverlay}
        durationInFrames={60}
        fps={HUMANOS_VIDEO.fps}
        width={HUMANOS_VIDEO.width}
        height={HUMANOS_VIDEO.height}
      />
      <Composition
        id="CharacterCardGrainOverlay"
        component={CharacterCardGrainOverlay}
        durationInFrames={60}
        fps={HUMANOS_VIDEO.fps}
        width={HUMANOS_VIDEO.width}
        height={HUMANOS_VIDEO.height}
      />
      <Composition
        id="CharacterCardVignetteOverlay"
        component={CharacterCardVignetteOverlay}
        durationInFrames={60}
        fps={HUMANOS_VIDEO.fps}
        width={HUMANOS_VIDEO.width}
        height={HUMANOS_VIDEO.height}
      />
      <Composition
        id="CharacterCardTextTimingReference"
        component={CharacterCardTextTimingReference}
        durationInFrames={60}
        fps={HUMANOS_VIDEO.fps}
        width={HUMANOS_VIDEO.width}
        height={HUMANOS_VIDEO.height}
      />
      <Composition
        id="HumanosEndCard"
        component={HumanosEndCard}
        durationInFrames={72}
        fps={HUMANOS_VIDEO.fps}
        width={HUMANOS_VIDEO.width}
        height={HUMANOS_VIDEO.height}
        defaultProps={{
          phrase: humanosPreviewConfig.endCard.phrase,
          brand: humanosPreviewConfig.endCard.brand,
        }}
      />
    </>
  );
};
