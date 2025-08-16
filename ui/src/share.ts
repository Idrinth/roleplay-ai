((root) => {
  const shareData = {
    title: 'Wolfgang AI: My Epic Role-Play Adventure!',
    text: 'Join me in unlimited, privacy-first RPGs with Wolfgang AI. Check it out:',
    url: 'https://###DESIRED_ROOT###/',
  };
  const share = document.getElementById('share');
  if (!share) {
    return;
  }
  if (typeof window.navigator['share'] !== 'undefined') {
    const li = document.createElement('li');
    li.setAttribute('class', 'native-share');
    li.appendChild(root.button('Share', 'Share Wolfgang AI with your friends', async() => {
      await navigator.share(shareData);
    }, true))
    share.appendChild(li);
    return;
  }
  const liX = document.createElement('li');
  liX.setAttribute('class', 'twitter-share');
  liX.appendChild(root.button('X', 'Share Wolfgang AI with your friends on X', async(event: MouseEvent) => {
    event.preventDefault();
    const xUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(shareData.text)}&url=${encodeURIComponent(shareData.url)}&hashtags=RPG,AI,Gamemaster`;
    window.open(xUrl, '_blank', 'width=550,height=420');
  }, true))
  share.appendChild(liX);

  const liReddit = document.createElement('li');
  liReddit.setAttribute('class', 'reddit-share');
  liReddit.appendChild(root.button('Reddit', 'Share Wolfgang AI with your friends on Reddit', async(event: MouseEvent) => {
    event.preventDefault();
    const redditUrl = `https://www.reddit.com/submit?url=${encodeURIComponent(shareData.url)}&title=${encodeURIComponent(shareData.title)}`;
    window.open(redditUrl, '_blank', 'width=600,height=600');
  }, true))
  share.appendChild(liReddit);

  if (typeof window.navigator['clipboard'] !== 'undefined') {
    const liCopy = document.createElement('li');
    liCopy.setAttribute('class', 'copy-share');
    liCopy.appendChild(root.button('Copy', 'Share Wolfgang AI with your friends', async (event: MouseEvent) => {
      await window.navigator.clipboard.writeText(shareData.url);
    }, true))
    share.appendChild(liCopy);
  }
})(window.bjoernbuettner);
