document.addEventListener("DOMContentLoaded", function () {
    const carousel = document.querySelector(".carousel-images");
    const prevButton = document.querySelector(".nav.prev");
    const nextButton = document.querySelector(".nav.next");
    const images = document.querySelectorAll(".carousel-img-wrapper");

    let index = 0;
    const totalImages = images.length;

    function updateCarousel() {
        const offset = -index * 100;
        carousel.style.transform = `translateX(${offset}%)`;
    }

    nextButton.addEventListener("click", function () {
        index = (index + 1) % totalImages;
        updateCarousel();
    });

    prevButton.addEventListener("click", function () {
        index = (index - 1 + totalImages) % totalImages;
        updateCarousel();
    });

    // Автоматическая прокрутка каждые 5 секунд
    setInterval(() => {
        index = (index + 1) % totalImages;
        updateCarousel();
    }, 5000);
});
