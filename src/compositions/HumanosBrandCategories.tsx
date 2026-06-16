import React from 'react';
import {HumanosBrandReveal} from '../components/HumanosBrandReveal';
import {humanosPreviewConfig} from '../config/humanosConfig';

export const HumanosBrandCategories: React.FC = () => {
  return <HumanosBrandReveal {...humanosPreviewConfig.brandReveal} title="" />;
};
