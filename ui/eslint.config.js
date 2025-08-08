import js from "@eslint/js";
import { defineConfig } from "eslint/config";
import globals from "globals";
import typescriptPlugin from "@typescript-eslint/eslint-plugin"
import typescriptParser from "@typescript-eslint/parser"

export default defineConfig([
	{
		files: ["**/*.ts"],
		languageOptions: {
			ecmaVersion: 2022,
      parser: typescriptParser,
			globals: {
				...globals.browser,
        jsyaml: true,
        showdown: true,
        PayPal: true,
        bjoernbuettner: true,
			},
		},
    plugins: {
			js,
      typescriptPlugin,
		},
    linterOptions: {
			noInlineConfig: true,
		},
		extends: ["js/recommended"],
	},
]);
