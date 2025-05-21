document.addEventListener('DOMContentLoaded', function() {
    // Import SignaturePad and bootstrap
    const SignaturePad = window.SignaturePad;
    const bootstrap = window.bootstrap;

    // Initialize signature pad
    const canvas = document.getElementById('signature-pad');
    if (!canvas) return;
    
    const signaturePad = new SignaturePad(canvas, {
        backgroundColor: 'rgba(255, 255, 255, 0.1)',
        penColor: 'black',
        minWidth: 1,
        maxWidth: 3
    });
    
    // Adjust canvas size
    function resizeCanvas() {
        const ratio = Math.max(window.devicePixelRatio || 1, 1);
        canvas.width = canvas.offsetWidth * ratio;
        canvas.height = canvas.offsetHeight * ratio;
        canvas.getContext("2d").scale(ratio, ratio);
        signaturePad.clear(); // Otherwise the canvas will be filled with the previous signature
    }
    
    window.addEventListener("resize", resizeCanvas);
    resizeCanvas();
    
    // Clear signature
    const clearButton = document.getElementById('clear-signature');
    if (clearButton) {
        clearButton.addEventListener('click', function() {
            signaturePad.clear();
        });
    }
    
    // Save signature
    const saveButton = document.getElementById('save-signature');
    const signaturePreview = document.getElementById('signature-preview');
    const signatureData = document.getElementById('signature-data');
    
    if (saveButton && signaturePreview && signatureData) {
        saveButton.addEventListener('click', function() {
            if (signaturePad.isEmpty()) {
                alert('Please provide a signature first.');
                return;
            }
            
            const dataURL = signaturePad.toDataURL();
            signaturePreview.src = dataURL;
            signaturePreview.style.display = 'block';
            signatureData.value = dataURL;
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('signatureModal'));
            modal.hide();
        });
    }
});