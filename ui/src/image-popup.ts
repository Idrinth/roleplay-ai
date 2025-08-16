(() => {
  const setHandler = (picture: HTMLPictureElement|undefined) => {
   if (!picture) {
     return;
   }
   const lastElementChild = picture.lastElementChild as HTMLImageElement|undefined;
   if (!lastElementChild) {
     return;
   }
   picture.addEventListener('click', () => {
     const imgWrapper = document.createElement('div');
     const imgWrapperInner = document.createElement('div');
     const img = document.createElement('img');
     img.setAttribute('src', lastElementChild.getAttribute('src') || '');
     img.setAttribute('alt', lastElementChild.getAttribute('alt') || '');
     imgWrapper.appendChild(imgWrapperInner);
     imgWrapperInner.appendChild(img);
     imgWrapper.setAttribute('title', 'click to close');
     imgWrapper.setAttribute('id', 'fullscreen-image');
     imgWrapper.addEventListener('click', () => {
       document.body.removeChild(imgWrapper);
     })
     document.body.appendChild(imgWrapper);
   });
  }
 const pictures = document.getElementsByTagName('picture');
 for (let i = 0; i < pictures.length; i++) {
   const picture = pictures[i];
   setHandler(picture);
 }
})();
