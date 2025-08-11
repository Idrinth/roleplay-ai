((root) => {
  root.randomFloat = (excludedMaximum: number): number => {
    return Math.random() * excludedMaximum;
  }
  root.randomInt = (excludedMaximum: number): number => {
    return Math.floor(root.randomFloat(excludedMaximum));
  }
  root.randomBool = (): boolean => {
    return Math.random() >= 0.5;
  }
  root.randomString = (list: string[]): string => {
    const randomised = [...list].sort(() => root.randomBool() ? 1 : -1)
    return randomised[root.randomInt(list.length)] as string;
  }
})(window.bjoernbuettner)
