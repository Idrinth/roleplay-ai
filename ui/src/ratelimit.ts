((root) => {
  const loader = document.getElementById('loader');
  const sendButton = document.getElementById('send') as  null|HTMLButtonElement;
  const chatId = window.location.pathname.split('/')[2] ?? '';
  if (!sendButton || !chatId || chatId === 'new') {
    return;
  }
  let chatIsActive = false;
  let creditsAreEmpty = false;
  root.maySendMessage = async() => !creditsAreEmpty && !chatIsActive;
  window.setInterval(async () => {
    const response = await root.getFromAPI(
      `chat/${chatId}/active?${Date.now()}`,
      'GET',
      undefined,
      2400,
    );
    if (!root.isObjectWithProperty(response, 'active')) {
      loader?.setAttribute('style', '');
      chatIsActive = true;
      return;
    }
    chatIsActive = response['active'] as boolean;
    loader?.setAttribute('style', chatIsActive ? '' : 'display:none');
  }, 2500);
  let updateTimeout: null|number = null;
  const checkCredits = async () => {
    const response = await root.getFromAPI('ratelimits', 'GET');
    if (!root.isObjectWithProperty(response, 'remainingMessages')) {
      creditsAreEmpty = true;
      return;
    }
    creditsAreEmpty = ((response as {remainingMessages?: number})['remainingMessages'] ?? 0) < 1;
    if (root.isObjectWithProperty(response, 'lastIncremented') && root.isObjectWithProperty(response, 'incrementEverySeconds')) {
      const nextInSeconds = (response['incrementEverySeconds'] as number) - (Date.now() / 1000 - (response['lastIncremented'] as number));
      if (nextInSeconds > 0) {
        if (updateTimeout) {
          clearTimeout(updateTimeout);
          updateTimeout = null;
        }
        updateTimeout = window.setTimeout(checkCredits, nextInSeconds);
      }
    }
    const elementMessagesLeft = document.getElementById("messages-left");
    if (elementMessagesLeft) {
      elementMessagesLeft.innerText = response['remainingMessages'] as string;
    }
    if (root.isObjectWithProperty(response, 'incrementEverySeconds') && elementMessagesLeft) {
      elementMessagesLeft.parentElement?.setAttribute('title', `Recharges by one every ${response['incrementEverySeconds']}seconds`)
    }
    if (root.isObjectWithProperty(response, 'maximumRemainingMessages')) {
      const elementMessagesMaximum = document.getElementById("messages-maximum");
      if (elementMessagesMaximum) {
        elementMessagesMaximum.innerText = response['maximumRemainingMessages'] as string;
      }
    }
  }
  sendButton.addEventListener('focusin', checkCredits);
  sendButton.addEventListener('mouseenter', checkCredits);
  checkCredits()
})(window.bjoernbuettner);
