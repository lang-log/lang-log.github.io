// ESLint settings (flat config) for the JavaScript in this repository; see
// .claude/rules/code-quality.md. Only the recommended rules, which find likely errors; layout is
// left to Prettier.
import js from '@eslint/js';
import globals from 'globals';

export default [
  {
    ignores: [
      '_preview/',
      // Until pull request #56 (fonts for Japanese, Chinese and Korean) is merged, so that it does
      // not conflict. Then fix the findings in this file in its own pull request and remove it.
      'dist/tree.js',
    ],
  },
  js.configs.recommended,
  {
    // Classic scripts loaded by the pages with <script src>, in the browser.
    files: ['dist/**/*.js'],
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: 'script',
      globals: { ...globals.browser },
    },
  },
  {
    // Checks run with Node.js by tools/build_site.sh.
    files: ['tools/**/*.js'],
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: 'commonjs',
      globals: { ...globals.node },
    },
  },
  {
    files: ['*.mjs'],
    languageOptions: {
      sourceType: 'module',
      globals: { ...globals.node },
    },
  },
];
