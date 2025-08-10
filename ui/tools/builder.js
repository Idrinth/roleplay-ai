import {readdirSync, writeFileSync, readFileSync, mkdirSync, existsSync, rmSync} from 'node:fs';
import {minify} from 'minify';
import { hash } from 'node:crypto';
import {compile} from 'sass';

if (existsSync(process.cwd() + '/dist')) {
  rmSync(process.cwd() + '/dist', {recursive: true});
}
mkdirSync(process.cwd()+'/dist');
const config = JSON.parse(readFileSync(process.cwd() + '/.minify.json', 'utf8'))

const TO_MERGE = {
  'shared-##.min.js': [
    'root.js',
    'get-from-api.js',
    'button.js',
    'dark-light-switch.js',
    'modals.js',
    'paypal-donate-sdk.min.js',
    'paypal.js',
    'list-existing-chats-handler.js',
  ],
  'chat-##.min.js': [
    'showdown.min.js',
    'js-yaml.min.js',
    'purify.min.js',
    'document-upload.js',
    'chat.js',
    'on-hover-focus.js',
  ]
}

for(const file of readdirSync(process.cwd() + '/src', 'utf-8')) {
  if (file.endsWith('.scss')) {
    writeFileSync(process.cwd() + '/public/' + file.replace('.scss', '.css'), compile(process.cwd() + '/src/' + file).css, "utf8")
  }
}

for(const file of readdirSync(process.cwd() + '/public', 'utf-8')) {
  if (file.endsWith('.js')) {
    writeFileSync(process.cwd() + '/public/' + file, readFileSync(process.cwd() + '/public/' + file, 'utf8').replace(/export \{};/g, ''), "utf8");
  }
}

for(const file of readdirSync(process.cwd() + '/public', 'utf-8')){
  if (file.endsWith('.js') || file.endsWith('.html') || file.endsWith('.css')) {
    try {
      const data = await minify(process.cwd() + '/public/' + file, config);
      if (data) {
        writeFileSync(process.cwd() + '/dist/' + file, data);
      } else {
        console.error(`Failed to minify: ${file}`);
        writeFileSync(process.cwd() + '/dist/' + file, readFileSync(process.cwd() + '/public/' + file, 'binary'), 'binary');
      }
    } catch (e) {
      console.error(`Failed to minify ${file}: `, e);
      writeFileSync(process.cwd() + '/dist/' + file, readFileSync(process.cwd() + '/public/' + file, 'binary'), 'binary');
    }
  } else {
    writeFileSync(process.cwd() + '/dist/'+file, readFileSync(process.cwd() +'/public/'+file, 'binary'), 'binary');
  }
}

for (const library of [
  'node_modules/js-yaml/dist/js-yaml.min.js',
  'node_modules/showdown/dist/showdown.min.js',
  'node_modules/dompurify/dist/purify.min.js',
]) {
  writeFileSync(process.cwd() + '/dist/'+library.replace(/\\/g, '/').split('/').pop(), readFileSync(library, 'utf8'), 'utf8');
}

const paypalSDK = await fetch('https://www.paypalobjects.com/donate/sdk/donate-sdk.js');
if (!paypalSDK.ok) {
  throw new Error('PayPalSDK failed downloading.');
}
writeFileSync(process.cwd() + '/dist/paypal-donate-sdk.min.js', await paypalSDK.text(), 'utf8');

for (const target of Object.keys(TO_MERGE)) {
  let out = [];
  for (const file of TO_MERGE[target]) {
    if (! existsSync(`${process.cwd()}/dist/${file}`)) {
      throw new Error(`${file} couldn't be found.`);
    }
    out.push(readFileSync(`${process.cwd()}/dist/${file}`, 'utf8'));
  }
  const content = out.join('\n');
  const contentHash = hash('md5', content, 'hex');
  const name = target.replace('##', contentHash);
  writeFileSync(`${process.cwd()}/dist/${name}`, content, 'utf8');
  for(const file of readdirSync(process.cwd() + '/dist', 'utf-8')){
    if (file.endsWith('.html')) {
      writeFileSync(
        `${process.cwd()}/dist/${file}`,
        readFileSync(`${process.cwd()}/dist/${file}`, 'utf8')
          .replace(`/${target}`, `/${name}`),
        'utf8'
      );
    }
  }
}
