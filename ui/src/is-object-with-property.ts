((root) => {
  root.isObjectWithProperty = (value: unknown, key: string): boolean => {
    return typeof value === 'object' && value !== null && Object.hasOwn(value, key);
  }
})(window.bjoernbuettner)
