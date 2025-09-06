(async(root) => {
  const data = await root.getFromAPI('statistics', 'GET') as {error?: string};
  if (root.isObjectWithProperty(data, 'error')) {
    return;
  }
  const statistics = document.getElementById('statistics');
  if (statistics) {
    const isAllowedNumber = (a: unknown) => Number.isInteger(a) && !Number.isNaN(a) && a as number > 0;
    for (const statistic of Object.keys(data)) {
      if (root.isObjectWithProperty(data, statistic) && isAllowedNumber(data[statistic])) {
        const statisticElement = document.createElement('li');
        const label = document.createElement('span');
        label.innerText = statistic;
        const number = document.createElement('span');
        number.innerText = data[statistic] as string;
        statisticElement.appendChild(label);
        statisticElement.appendChild(number);
        statistics.appendChild(statisticElement);
      }
    }
  }
})(window.bjoernbuettner);
