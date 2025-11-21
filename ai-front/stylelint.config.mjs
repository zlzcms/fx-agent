export default {
  extends: ['@vben/stylelint-config'],
  root: true,
  rules: {
    'selector-pseudo-class-no-unknown': [
      true,
      {
        ignorePseudoClasses: ['deep', 'global'],
      },
    ],
  },
};
