((root) => {
  root.getWorldKeywords = (): string[] => {
    return (document.getElementById("world") as null|HTMLInputElement)?.value
      .split(',')
      .map(x => x
        .split(' ')
        .map(y => y.trim())
        .filter(y => !!y)
        .join(' ')
      )
      .filter(x => x !== '')?? [];
  }
})(window.bjoernbuettner)
