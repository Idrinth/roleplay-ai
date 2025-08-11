((root) => {
  const secureRandomUnit = (): number => {
    if (window.crypto && window.crypto.getRandomValues) {
      return (window.crypto.getRandomValues(new Uint32Array(1))[0]??0)/0x1_0000_0000;
    }
    return Math.random();
  }
  root.randomFloat = (excludedMaximum: number): number => {
    return secureRandomUnit() * excludedMaximum;
  }
  root.randomInt = (excludedMaximum: number): number => {
    return Math.floor(root.randomFloat(excludedMaximum));
  }
  root.randomBool = (): boolean => {
    return secureRandomUnit() >= 0.5;
  }
  root.randomString = (list: string[]): string => {
    const randomised = [...list].sort(() => root.randomBool() ? 1 : -1)
    return randomised[root.randomInt(list.length)] as string;
  }
})(window.bjoernbuettner)
