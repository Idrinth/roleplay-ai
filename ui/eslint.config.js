import js from "@eslint/js";
import { defineConfig } from "eslint/config";
import globals from "globals";

export default defineConfig([
	{
		files: ["**/*.js"],
		languageOptions: {
			ecmaVersion: 2022,
			globals: {
				...globals.browser,
        jsyaml: true,
        showdown: true,
        PayPal: true,
			},
		},
    plugins: {
			js,
		},
    linterOptions: {
			noInlineConfig: true,
		},
		extends: ["js/recommended"],
	},
]);
