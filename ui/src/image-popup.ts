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
     imgWrapper.setAttribute('title', 'click to close');
     imgWrapper.setAttribute('id', 'fullscreen-image');
     imgWrapper.addEventListener('click', () => {
       document.body.removeChild(imgWrapper);
     });
     imgWrapper.appendChild(imgWrapperInner);
     document.body.appendChild(imgWrapper);
     if (picture.hasAttribute('data-video')) {
       const frame = document.createElement('iframe');
       frame.setAttribute('src', picture.getAttribute('data-video') || '');
       frame.setAttribute('class', 'youtube-iframe');
       frame.setAttribute('allow', 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share');
       frame.setAttribute('allowfullscreen', 'allowfullscreen');
       frame.setAttribute('referrerpolicy', 'strict-origin-when-cross-origin');
       frame.addEventListener('click', (event: MouseEvent) => {
         event.stopPropagation();
       });
       imgWrapperInner.appendChild(frame);
       return;
     }
     const img = document.createElement('img');
     img.setAttribute('src', lastElementChild.getAttribute('src') || '');
     img.setAttribute('alt', lastElementChild.getAttribute('alt') || '');
     img.addEventListener('click', (event: MouseEvent) => {
       event.stopPropagation();
     });
     imgWrapperInner.appendChild(img);
   });
  }
 const pictures = document.getElementsByTagName('picture');
 for (let i = 0; i < pictures.length; i++) {
   const picture = pictures[i];
   setHandler(picture);
 }
})();
