(async(root) => {
  const worldKeywords: string[] = [];
  const world = document.getElementById("world") as null|HTMLInputElement;
  const chatId = window.location.pathname.split("/").pop();
  if (!world || ! chatId) {
    throw new Error("Could not find the world!");
  }
  const setWorldKeywordsTitle = (element: Element|null, keywords: string[]) => {
    const expandedKeywords = [...keywords];
    for (const pos in keywords) {
      const keyword = keywords[pos] as string;
      const matchingSongs = root.getMatchingSongs(keyword);
      if (matchingSongs.length > 0) {
        expandedKeywords[pos] = keyword + '\n  ' + matchingSongs.length + ' songs';
      }
    }
    element?.setAttribute('title', expandedKeywords.join("\n"))
  }
  await (async () => {
    const response = await root.getFromAPI(`chat/${chatId}/world`,'GET');
    if (typeof response !== 'object' || response === null || !Object.hasOwn(response, 'world')) {
      return;
    }
    const keywords = (response as {world: string[]}).world;
    setWorldKeywordsTitle(world, keywords);
    world.value = keywords.join(", ")
    world.dispatchEvent(new Event('change'));
  })();
  const addWorldKeywords = () => {
    const keywords = world.value
      .replaceAll(';', ',')
      .toLowerCase()
      .split(',')
      .map(x => x
        .split(' ')
        .map(y => y.trim())
        .filter(y => !!y)
        .join(' ')
      )
      .filter(x => x !== '')?? [];
    for(const keyword of keywords) {
      if (!worldKeywords.includes(keyword)) {
        worldKeywords.push(keyword);
      }
    }
    world.value = '';
  };
  const worldChange = async() => {
    const keywords = [...worldKeywords];
    addWorldKeywords();
    if (keywords.join() === worldKeywords.join()) {
      return;
    }
    setWorldKeywordsTitle(world, keywords);
    await root.getFromAPI(`chat/${chatId}/world`, 'PUT', {
      keywords,
    });
    const keywordList = document.getElementById('keyword-list') as HTMLUListElement;
    if (!keywordList) {
      return;
    }
    for (const keyword of keywords) {
      let found = false;
      for (let i = 0; i < keywordList.childElementCount; i++) {
        if (keywordList.children[i]?.innerHTML === keyword) {
          found = true;
          break;
        }
      }
      if (!found) {
        const keywordElement = document.createElement('li');
        keywordElement.appendChild(root.button(keyword, 'Click to remove', () => {
          if (worldKeywords.includes(keyword)) {
            worldKeywords.splice(worldKeywords.indexOf(keyword), 1);
          }
          keywordList.removeChild(keywordElement);
          setWorldKeywordsTitle(world.previousElementSibling, worldKeywords);
          root.getFromAPI(`chat/${chatId}/world`, 'PUT', {
            worldKeywords,
          });
        }));
        keywordList.appendChild(keywordElement);
      }
    }
  };
  world.addEventListener('change', worldChange);
  world.addEventListener('keyup', (event: KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ',' || event.key === ';') {
      worldChange()
    }
  });
  root.getWorldKeywords = (): string[] => {
    return worldKeywords;
  }
})(window.bjoernbuettner)
