
document.addEventListener('DOMContentLoaded', function() {
    const optionsButtons = document.querySelectorAll('.options-button');

    optionsButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            // Prevent the click on the dropdown button or menu itself from 
            // being treated like a click outside the menu, which would immediately close it
            event.stopPropagation();  
            const dropdown = this.nextElementSibling;  // Get the dropdown div right after the button

            closeAllDropdowns(dropdown);

            dropdown.classList.toggle('menu-open');  // Toggle the current dropdown
        });
    });

    // Close dropdown if clicking outside
    document.addEventListener('click', function(event) {
        closeAllDropdowns();
    });

    function closeAllDropdowns(excludeDropdown = null) {
        const allDropdowns = document.querySelectorAll('.options-dropdown');
        allDropdowns.forEach(dropdown => {
            if (dropdown !== excludeDropdown && dropdown.classList.contains('menu-open')) {
                dropdown.classList.remove('menu-open');
            }
        });
    }

    // Prevent dropdown clicks from closing the menu immediately
    document.querySelectorAll('.options-dropdown').forEach(dropdown => {
       dropdown.addEventListener('click', function(event) {
           event.stopPropagation();
       });
    });

});
