((root) => {
  root.isObjectWithProperty = <K extends PropertyKey>(value: unknown, key: string): value is object & Record<K, unknown> => {
    return typeof value === 'object'
      && value !== null
      && ((Object.hasOwn && Object.hasOwn(value, key)) || Object.prototype.hasOwnProperty.call(value, key));
  }
})(window.bjoernbuettner)
