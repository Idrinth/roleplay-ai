(async (root) => {
  root.getMatchingSongs = (keyword: string): string[] => {
    const lowerCaseKeyword = keyword
      .toLowerCase()
      .replaceAll('-', ' ')
      .replaceAll('_', ' ');
    const possibleAudios = [];
    for (const set of root.audios) {
      if (lowerCaseKeyword == set.keyword) {
        possibleAudios.push(set.src);
      }
    }
    if (possibleAudios.length === 0) {
      for (const set of root.audios) {
        if (lowerCaseKeyword.includes(set.keyword)) {
          possibleAudios.push(set.src);
        }
      }
    }
    return possibleAudios;
  }
  const audio = document.getElementById('music') as null|HTMLAudioElement;
  const select = document.getElementById('music-select') as null|HTMLSelectElement;
  if (!Array.isArray(root.audios) || root.audios.length === 0 || !audio || !select) {
    return;
  }
  audio.volume = 0;
  let isPlaying = false;
  const setUcFirstInnerTextIfExists = (text: string|undefined, id: string) => {
    const element = document.getElementById(id);
    if (text && element) {
      element.innerText = text
        .split(" ")
        .filter(textElement => !!textElement)
        .map(textElement => textElement.substring(0, 1).toUpperCase() + textElement.substring(1))
        .join(" ");
    }
  }
  const setRandomAudio = async() => {
    const possibleAudios = [];
    for (const keyword in root.getWorldKeywords()) {
      possibleAudios.push(...root.getMatchingSongs(keyword));
    }
    if (possibleAudios.length === 0) {
      for (const set of root.audios) {
        possibleAudios.push(set.src);
      }
    }
    const src = root.randomString(possibleAudios);
    const [,, category, name] = src.split('/');
    setUcFirstInnerTextIfExists(category?.replaceAll('-', ' '), 'songcategory');
    setUcFirstInnerTextIfExists(name?.split('.')[0]?.replaceAll('_', ' '), 'songname');
    audio.setAttribute('src', src);
    if (!isPlaying) {
      try {
        audio.volume = 0.01;
        await audio.play();
        select.selectedIndex = 1;
        isPlaying = true;
      } catch (e) {
        console.error(e);
        try {
          audio.volume = 0;
          await audio.play();
          isPlaying = true;
        } catch (e) {
          console.error(e);
        }
      }
      return;
    }
    try {
      await audio.play();
      isPlaying = true;
    } catch (e) {
      console.error(e);
    }
  }
  audio.addEventListener('ended', setRandomAudio);
  select.addEventListener('change', async() => {
    if (!isPlaying) {
      try {
        await audio.play();
        isPlaying = true;
      } catch (e) {
        console.error(e);
      }
    }
    audio.volume = Number.parseFloat(select.value)
  });
  await setRandomAudio();
})(window.bjoernbuettner);
