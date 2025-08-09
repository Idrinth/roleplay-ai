import js from "@eslint/js";
import globals from "globals";
import tseslint from 'typescript-eslint';

export default tseslint.config(
  js.configs.recommended,
  tseslint.configs.recommended,
  {
		files: ["**/*.ts"],
		languageOptions: {
			ecmaVersion: 2022,
      parser: tseslint.parser,
			globals: {
				...globals.browser,
        jsyaml: true,
        showdown: true,
        PayPal: true,
        bjoernbuettner: true,
			},
		},
    rules: {
      'no-unused-vars': 'off',
    },
    linterOptions: {
			noInlineConfig: true,
		},
	}
);
