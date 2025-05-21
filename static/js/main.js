// Custom JavaScript for ICT Resource Management System

// Import Bootstrap
const bootstrap = window.bootstrap;

document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add confirmation for delete actions
    const deleteButtons = document.querySelectorAll('.btn-delete, .delete-action');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });

    // Add confirmation for status changes
    const statusButtons = document.querySelectorAll('.status-action');
    statusButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const action = this.dataset.action || 'change the status of';
            const item = this.dataset.item || 'this item';
            
            if (!confirm(`Are you sure you want to ${action} ${item}?`)) {
                e.preventDefault();
            }
        });
    });

    // Physical copy checkbox warning
    const physicalCopyCheckbox = document.getElementById('id_physical_copy_stamped');
    const approveButton = document.querySelector('button[value="approved"]');
    
    if (physicalCopyCheckbox && approveButton) {
        approveButton.addEventListener('click', function(e) {
            if (!physicalCopyCheckbox.checked) {
                e.preventDefault();
                alert('Please confirm that the physical copy has been stamped before approving the request.');
            }
        });
    }

    // Print functionality
    const printButtons = document.querySelectorAll('.btn-print, [data-action="print"]');
    printButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            window.print();
        });
    });

    // Add print functionality to print list buttons
    const printListButtons = document.querySelectorAll('.btn-print-list');
    printListButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            window.print();
        });
    });
});