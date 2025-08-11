(async(root) => {
  const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_-.:,;+*~#<>!§$%&/()?='.split('');
  root.password = (minChars: number = 8, maxChars: number = 24) => {
    if (minChars > maxChars) {
      maxChars = minChars;
    }
    let out = '';
    const length = minChars + root.randomInt(maxChars - minChars);
    for (let i = 0; i < length; i++) {
      chars.sort(() => root.randomBool() ? -1 : 1);
      out += root.randomString(chars);
    }
    return out;
  }
})(window.bjoernbuettner);
