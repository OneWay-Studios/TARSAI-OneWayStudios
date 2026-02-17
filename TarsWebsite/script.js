document.addEventListener('DOMContentLoaded', () => {
    const downloadBtn = document.querySelector('.primary-btn');

    downloadBtn.addEventListener('click', (e) => {
        // This is where you'd point to your tars.py file
        console.log("Initiating TARS Transfer Protocol...");
        
        // Visual feedback
        downloadBtn.textContent = "TRANSFERRING...";
        setTimeout(() => {
            downloadBtn.textContent = "DOWNLOAD COMPLETE";
            downloadBtn.style.borderColor = "#fff";
        }, 2000);
    });

    // Smooth scroll for nav links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });
});