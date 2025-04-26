
// toggle feature to  shows or hide elements

document.addEventListener('DOMContentLoaded', () => {
    const toggleButtons = document.querySelectorAll('[data-toggle]');
    toggleButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-toggle');
            const target = document.getElementById(targetId);
            if (target) {
                target.style.display = target.style.display === 'none' ? 'block' : 'none';
            }
        });
    });
});
