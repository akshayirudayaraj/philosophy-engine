import coreWebVitals from "eslint-config-next/core-web-vitals";
import typescript from "eslint-config-next/typescript";

const eslintConfig = [
  // `next lint` (removed in Next 16) scoped linting to source; replicate that by
  // ignoring build output and generated files now that we invoke eslint directly.
  { ignores: [".next/**", "out/**", "build/**", "next-env.d.ts"] },
  ...coreWebVitals,
  ...typescript,
];

export default eslintConfig;
