import { ShaderGradient, ShaderGradientCanvas } from '@shadergradient/react';

/**
 * WebGL gradient behind the landing hero. Default-exported so Landing can
 * `React.lazy()` it: three.js + @react-three/fiber land in their own chunk
 * and never block first paint. `lightType="3d"` avoids the env-map HDR
 * download that the `env` lighting mode fetches.
 */
export default function ShaderHero() {
  return (
    <ShaderGradientCanvas style={{ position: 'absolute', inset: 0 }} pixelDensity={1} fov={45} pointerEvents="none" lazyLoad>
      <ShaderGradient
        control="props"
        type="waterPlane"
        animate="on"
        uSpeed={0.12}
        uStrength={2.2}
        uDensity={1.4}
        uFrequency={5.5}
        uAmplitude={0}
        color1="#2d7ff9"
        color2="#05060f"
        color3="#8b5cf6"
        positionX={0}
        positionY={0}
        positionZ={0}
        rotationX={50}
        rotationY={0}
        rotationZ={-60}
        cAzimuthAngle={180}
        cPolarAngle={80}
        cDistance={2.8}
        cameraZoom={9.1}
        lightType="3d"
        brightness={1.1}
        reflection={0.1}
        grain="on"
        grainBlending={0.25}
      />
    </ShaderGradientCanvas>
  );
}
