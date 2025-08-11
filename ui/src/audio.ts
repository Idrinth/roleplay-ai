(async (root) => {
  root.getMatchingSongs = (keyword: string): string[] => {
    const possibleAudios = [];
    for (const set of root.audios) {
      if (keyword == set.keyword) {
        possibleAudios.push(set.src);
      }
    }
    if (possibleAudios.length === 0) {
      for (const set of root.audios) {
        if (keyword.includes(set.keyword)) {
          possibleAudios.push(set.src);
        }
      }
    }
    return possibleAudios;
  }
  const audio = document.getElementById('music') as null|HTMLAudioElement;
  const audioButton = document.getElementById('music-button') as null|HTMLButtonElement;
  if (!Array.isArray(root.audios) || root.audios.length === 0 || !audio || !audioButton) {
    return;
  }
  audio.volume = 0.01;
  let isPlaying = false;
  const setRandomAudio = () => {
    const keywords = (document.getElementById("world") as null|HTMLInputElement)?.value.split(',').map(x => x.toLowerCase().trim()).filter(x => x !== '') ?? [];
    const possibleAudios = [];
    for (const keyword in keywords) {
      possibleAudios.push(...root.getMatchingSongs(keyword));
    }
    if (possibleAudios.length === 0) {
      for (const set of root.audios) {
        possibleAudios.push(set.src);
      }
    }
    audio.setAttribute('src', root.randomString(possibleAudios));
    try {
      audio.play();
      isPlaying = true;
    } catch (e) {
      // expected on first load
      console.error(e);
    }
  }
  audio.addEventListener('ended', setRandomAudio);
  audioButton.addEventListener('click', async() => {
    if (!isPlaying) {
      try {
        await audio.play();
        isPlaying = true;
      } catch (e) {
        console.error(e);
      }
      return;
    }
    audio.pause();
    isPlaying = false;
  });
  setRandomAudio();
})(window.bjoernbuettner);
