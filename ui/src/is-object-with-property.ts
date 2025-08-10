((root) => {
  root.isObjectWithProperty = (value: any, key: string): boolean => {
    return typeof value === 'object' && value !== null && Object.hasOwn(value, key);
  }
})(window.bjoernbuettner)
