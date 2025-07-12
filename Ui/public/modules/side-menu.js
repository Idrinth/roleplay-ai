const bookMarker = document.querySelector("#book-marker");
const sideMenuContainer = document.querySelector("#side-menu-container");

function toggleSideMenu() {
    const menuIsVisible = sideMenuContainer.classList.contains('visible-side-menu');
    if (menuIsVisible) {
        sideMenuContainer.classList.remove("visible-side-menu");
        return;
    }
    sideMenuContainer.classList.add("visible-side-menu");
}

bookMarker.addEventListener('click', toggleSideMenu);