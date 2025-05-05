document.addEventListener('DOMContentLoaded', function() {
    const unsaveModal = document.getElementById('unsave-modal');
    const cancelUnsaveBtn = document.getElementById('cancel-unsave');
    const confirmUnsaveBtn = document.getElementById('confirm-unsave');
    let currentUnsaveForm = null;

    // Add click event listeners to all unsave buttons
    document.querySelectorAll('.unsave-btn').forEach(button => {
        button.addEventListener('click', function() {
            currentUnsaveForm = document.getElementById(this.dataset.formId);
            unsaveModal.style.display = 'flex';
        });
    });

    // Handle cancel button click
    cancelUnsaveBtn.addEventListener('click', function() {
        unsaveModal.style.display = 'none';
        currentUnsaveForm = null;
    });

    // Handle confirm button click
    confirmUnsaveBtn.addEventListener('click', function() {
        if (currentUnsaveForm) {
            currentUnsaveForm.submit();
        }
    });

    // Close modal when clicking outside
    unsaveModal.addEventListener('click', function(e) {
        if (e.target === unsaveModal) {
            unsaveModal.style.display = 'none';
            currentUnsaveForm = null;
        }
    });
}); 