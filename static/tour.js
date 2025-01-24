const images = document.querySelectorAll('.carousel-img-wrapper');
const prevButton = document.querySelector('.nav.prev');
const nextButton = document.querySelector('.nav.next');
const carouselImages = document.querySelector('.carousel-images');

let currentIndex = 0;

function updateCarousel() {
    const offset = -currentIndex * 100;
    carouselImages.style.transform = `translateX(${offset}%)`;
}

prevButton.addEventListener('click', () => {
    currentIndex = (currentIndex - 1 + images.length) % images.length;
    updateCarousel();
});

nextButton.addEventListener('click', () => {
    currentIndex = (currentIndex + 1) % images.length;
    updateCarousel();
});

updateCarousel();
