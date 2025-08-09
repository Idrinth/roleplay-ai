(async(root) => {
  const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_-.:,;+*~#<>!§$%&/()?='.split('');
  const randChar = () => chars[Math.floor(Math.random() * chars.length)] as string;
  root.password = (minChars: number = 8, maxChars: number = 24) => {
    if (minChars > maxChars) {
      maxChars = minChars;
    }
    let out = '';
    const length = minChars + Math.floor(Math.random() * (maxChars - minChars));
    for (let i = 0; i < length; i++) {
      out += randChar();
    }
    return out;
  }
})(window.bjoernbuettner);
