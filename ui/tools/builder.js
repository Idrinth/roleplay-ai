import {readdirSync, writeFileSync, readFileSync, mkdirSync, existsSync, rmSync} from 'node:fs';
import {minify} from 'minify';
import { hash } from 'node:crypto';
import {compile} from 'sass';
import sharp from 'sharp';
import * as path from "node:path";

if (existsSync(process.cwd() + '/dist')) {
  rmSync(process.cwd() + '/dist', {recursive: true});
}
mkdirSync(process.cwd()+'/dist');
mkdirSync(process.cwd()+'/dist/audio');
const config = JSON.parse(readFileSync(process.cwd() + '/.minify.json', 'utf8'))

const TO_MERGE = {
  'shared-##.min.js': [
    'root.js',
    'get-from-api.js',
    'is-object-with-property.js',
    'get-current-user.js',
    'button.js',
    'dark-light-switch.js',
    'modals.js',
    'list-existing-chats-handler.js',
    'swipe.js',
    'share.js',
    'image-popup.js',
  ],
  'chat-##.min.js': [
    'ratelimit.js',
    'random.js',
    'get-world-keywords.js',
    'audio-list.js',
    'audio.js',
    'showdown.min.js',
    'password.js',
    'js-yaml.min.js',
    'purify.min.js',
    'document-upload.js',
    'chat.js',
    'on-hover-focus.js',
  ]
}

const audios = [];
for (const keyword of readdirSync(process.cwd() + '/audio')) {
  mkdirSync(process.cwd() + '/dist/audio/' + keyword);
  for (const file of readdirSync(process.cwd() + '/audio/' + keyword)) {
    audios.push({
      keyword: keyword.replace(/-/g, ' '),
      src: `/audio/${keyword}/${file}`,
    });
    writeFileSync(process.cwd() + `/dist/audio/${keyword}/${file}`, readFileSync(process.cwd() + `/audio/${keyword}/${file}`, 'binary'), 'binary');
  }
}
writeFileSync(
  process.cwd() + '/public/audio-list.js',
  'window.bjoernbuettner.audios=' + JSON.stringify(audios).replace(/"keyword":/g, 'keyword:').replace(/"src":/g, 'src:') + ';',
  'utf8'
);

for(const file of readdirSync(process.cwd() + '/src', 'utf-8')) {
  if (file.endsWith('.scss')) {
    writeFileSync(process.cwd() + '/public/' + file.replace('.scss', '.css'), compile(process.cwd() + '/src/' + file).css, "utf8")
  }
}

for(const file of readdirSync(process.cwd() + '/public', 'utf-8')) {
  if (file.endsWith('.js')) {
    writeFileSync(
      process.cwd() + '/public/' + file,
      readFileSync(process.cwd() + '/public/' + file, 'utf8').replace(/export \{};/g, ''),
      "utf8"
    );
  }
}
if (!process.env.DESIRED_ROOT) {
  process.env.DESIRED_ROOT = 'localhost';
}

const JS_FILE_MAPPINGS = {};

for(const file of readdirSync(process.cwd() + '/public', 'utf-8')){
  if (file.endsWith('.js') || file.endsWith('.html') || file.endsWith('.css')) {
    try {
      const data = await minify(process.cwd() + '/public/' + file, config);
      if (data) {
        if (file.endsWith('.js')) {
          writeFileSync(process.cwd() + '/dist/' + file, '(async()=>{' + data.replaceAll('###DESIRED_ROOT###', process.env.DESIRED_ROOT) + '})();');
          JS_FILE_MAPPINGS[file] = hash('md5', data, 'hex');
        } else {
          writeFileSync(process.cwd() + '/dist/' + file, data.replaceAll('###DESIRED_ROOT###', process.env.DESIRED_ROOT));
        }
      } else {
        console.error(`Failed to minify: ${file}`);
        writeFileSync(
          process.cwd() + '/dist/' + file,
          readFileSync(process.cwd() + '/public/' + file, 'utf8').replaceAll('###DESIRED_ROOT###', process.env.DESIRED_ROOT),
          'utf8'
        );
      }
    } catch (e) {
      console.error(`Failed to minify ${file}: `, e);
      writeFileSync(process.cwd() + '/dist/' + file, readFileSync(process.cwd() + '/public/' + file, 'utf8').replaceAll('###DESIRED_ROOT###', process.env.DESIRED_ROOT), 'utf8');
    }
  } else if(file.endsWith('.txt') || file.endsWith('.xml')) {
    writeFileSync(process.cwd() + '/dist/'+file, readFileSync(process.cwd() +'/public/'+file, 'utf8').replaceAll('###DESIRED_ROOT###', process.env.DESIRED_ROOT), 'utf8');
  } else if (file.endsWith('.jpg')) {
    writeFileSync(process.cwd() + '/dist/'+file, readFileSync(process.cwd() +'/public/'+file, 'binary'), 'binary');
    const fileName = file.replace(/\.jpg$/, '');
    await sharp(process.cwd() + '/dist/'+file)
      .webp({ quality: 85 })
      .toFile(`${process.cwd()}/dist/${fileName}.webp`);
    await sharp(process.cwd() + '/dist/'+file)
      .webp({ quality: 85 })
      .resize(1000)
      .toFile(`${process.cwd()}/dist/${fileName}.1000.webp`);
    await sharp(process.cwd() + '/dist/'+file)
      .webp({ quality: 85 })
      .resize(800)
      .toFile(`${process.cwd()}/dist/${fileName}.800.webp`);
    await sharp(process.cwd() + '/dist/'+file)
      .webp({ quality: 85 })
      .resize(600)
      .toFile(`${process.cwd()}/dist/${fileName}.600.webp`);
    await sharp(process.cwd() + '/dist/'+file)
      .webp({ quality: 85 })
      .resize(400)
      .toFile(`${process.cwd()}/dist/${fileName}.400.webp`);
    await sharp(process.cwd() + '/dist/'+file)
      .webp({ quality: 85 })
      .resize(200)
      .toFile(`${process.cwd()}/dist/${fileName}.200.webp`);
    await sharp(process.cwd() + '/dist/'+file)
      .avif({ quality: 75 })
      .toFile(`${process.cwd()}/dist/${fileName}.avif`);
    await sharp(process.cwd() + '/dist/'+file)
      .avif({ quality: 75 })
      .resize(1000)
      .toFile(`${process.cwd()}/dist/${fileName}.1000.avif`);
    await sharp(process.cwd() + '/dist/'+file)
      .avif({ quality: 75 })
      .resize(800)
      .toFile(`${process.cwd()}/dist/${fileName}.800.avif`);
    await sharp(process.cwd() + '/dist/'+file)
      .resize(600)
      .avif({ quality: 75 })
      .toFile(`${process.cwd()}/dist/${fileName}.600.avif`);
    await sharp(process.cwd() + '/dist/'+file)
      .avif({ quality: 75 })
      .resize(400)
      .toFile(`${process.cwd()}/dist/${fileName}.400.avif`)
    await sharp(process.cwd() + '/dist/'+file)
      .avif({ quality: 75 })
      .resize(200)
      .toFile(`${process.cwd()}/dist/${fileName}.200.avif`);
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

writeFileSync(process.cwd() + '/dist/contributors.svg', await(await fetch('https://contrib.rocks/image?repo=bjoern-buettner/roleplay-ai')).text(), 'utf8')

for (const target of Object.keys(TO_MERGE)) {
  let out = [];
  for (const file of TO_MERGE[target]) {
    if (! existsSync(`${process.cwd()}/dist/${file}`)) {
      throw new Error(`${file} couldn't be found.`);
    }
    out.push(readFileSync(`${process.cwd()}/dist/${file}`, 'utf8'));
  }
  const content = out.join('\n').replace(/\r/g, '').replace(/(\/\/# sourceMappingURL=.*)?\n{2,}/g, '\n');
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
const cssHash = hash('md5', readFileSync(process.cwd() + '/dist/styles.css', 'utf8'), 'hex');
for(const file of readdirSync(process.cwd() + '/dist', 'utf-8')){
  if (file.endsWith('.html')) {
    let data = readFileSync(`${process.cwd()}/dist/${file}`, 'utf8')
        .replace(`/styles.css`, `/styles.css?${cssHash}`);
    for (const jsFile of Object.keys(JS_FILE_MAPPINGS)) {
      data = data.replace(`/${jsFile}`, `/${jsFile}?${JS_FILE_MAPPINGS[jsFile]}`);
    }
    writeFileSync(
      `${process.cwd()}/dist/${file}`,
      data,
      'utf8'
    );
  }
}
