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
        const setKeyword = String(set.keyword ?? '')
          .toLowerCase()
          .replaceAll('-', ' ')
          .replaceAll('_', ' ');
        if (setKeyword.includes(lowerCaseKeyword) || lowerCaseKeyword.includes(set.keyword)) {
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
  select.selectedIndex = 0;
  const toUcFirstText = (text: string) => {
    return text
      .replaceAll('-', ' ')
      .replaceAll('_', ' ')
      .split(" ")
      .filter(textElement => !!textElement)
      .map(textElement => textElement.substring(0, 1).toUpperCase() + textElement.substring(1))
      .join(" ");
  }
  const pathToCategoryNameAndPath = (path: string) => {
    const pathParts = path.split('/');
    const name = pathParts.pop()?.replaceAll('.mp3', '') ?? '';
    const category = pathParts.pop() ?? '';
    return [category, name, path]
  }
  const setRandomAudio = async() => {
    const possibleAudios = [];
    for (const keyword of root.getWorldKeywords()) {
      possibleAudios.push(...root.getMatchingSongs(keyword));
    }
    if (possibleAudios.length === 0) {
      for (const set of root.audios) {
        possibleAudios.push(set.src);
      }
    }
    const [category, name, selectedAudioPath] = pathToCategoryNameAndPath(root.randomString(possibleAudios));
    select.setAttribute('title', name && category ?`${toUcFirstText(name)} (${toUcFirstText(category)})` : '');
    audio.setAttribute('src', selectedAudioPath as string);
    await audio.play();
  }
  audio.addEventListener('ended', setRandomAudio);
  select.addEventListener('change', async() => {
    await audio.play();
    audio.volume = Number.parseFloat(select.value)
  });
  await setRandomAudio();
  const world = document.getElementById('world') as HTMLInputElement;
  if (!world) {
    return;
  }
  world.addEventListener('change', setRandomAudio);
})(window.bjoernbuettner);
