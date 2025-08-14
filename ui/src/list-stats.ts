(async(root) => {
  const data = await root.getFromAPI('statistics', 'GET') as {};
  if (root.isObjectWithProperty(data, 'error')) {
    return;
  }
  const statistics = document.getElementById('statistics');
  if (statistics) {
    for (const statistic of Object.keys(data)) {
      if (root.isObjectWithProperty(data, statistic)) {
        const statisticElement = document.createElement('li');
        statisticElement.innerText = (data[statistic] as string) + ' ' + statistic;
        statistics.appendChild(statisticElement);
      }
    }
  }
})(window.bjoernbuettner);
