(async (root) => {
  const audio = document.getElementById('music') as null|HTMLAudioElement;
  const audioButton = document.getElementById('music-button') as null|HTMLButtonElement;
  if (!Array.isArray(root.audios) || root.audios.length === 0 || !audio || !audioButton) {
    return;
  }
  audio.volume = 0.01;
  let isPlaying = false;
  const rand = (possibleAudios: string[]) => Math.random() * possibleAudios.length;
  const setRandomAudio = () => {
    const keywords = (document.getElementById("world") as null|HTMLInputElement)?.value.split(',').map(x => x.toLowerCase().trim()).filter(x => x !== '') ?? [];
    const possibleAudios = [];
    for (const set of root.audios) {
      if (keywords.includes(set.keyword) || keywords.length === 0) {
        possibleAudios.push(set.src);
      }
    }
    if (possibleAudios.length === 0) {
      for (const set of root.audios) {
        for (const keyword of keywords) {
          if (keyword.includes(set.keyword)) {
            possibleAudios.push(set.src);
            break;
          }
        }
      }
    }
    if (possibleAudios.length === 0) {
      for (const set of root.audios) {
        possibleAudios.push(set.src);
      }
    }
    audio.setAttribute('src', possibleAudios[Math.floor(rand(possibleAudios))] as string);
    try {
      audio.play();
      isPlaying = true;
    } catch (e) {
      // expected on first load
    }
  }
  audio.addEventListener('ended', setRandomAudio);
  audioButton.addEventListener('click', () => {
    isPlaying ? audio.pause() : audio.play();
    isPlaying = !isPlaying;
  });
  setRandomAudio();
})(window.bjoernbuettner);
