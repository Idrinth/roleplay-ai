(async(root) => {
  const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_-.:,;+*~#<>!§$%&/()?='.split('');
  const random = () => Math.random() * chars.length;
  const randChar = () => chars[Math.floor(random())] as string;
  root.password = (minChars: number = 8, maxChars: number = 24) => {
    if (minChars > maxChars) {
      maxChars = minChars;
    }
    let out = '';
    const length = minChars + Math.floor(Math.random() * (maxChars - minChars));
    for (let i = 0; i < length; i++) {
      chars.sort(() => Math.random() > 0.5 ? -1 : 1);
      out += randChar();
    }
    return out;
  }
})(window.bjoernbuettner);
