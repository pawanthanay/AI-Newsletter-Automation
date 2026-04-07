document.addEventListener('DOMContentLoaded', () => {
    const generateBtn = document.getElementById('generateBtn');
    const btnText = generateBtn.querySelector('.btn-text');
    const statusContainer = document.getElementById('statusContainer');
    const spinner = document.getElementById('spinner');
    const statusMessage = document.getElementById('statusMessage');

    // Check if server is reachable on load
    fetch('http://127.0.0.1:5001/ping')
        .then(res => res.json())
        .catch(() => {
            showStatus("Local API Server not running. Run start_server.sh", "error");
            generateBtn.disabled = true;
        });

    generateBtn.addEventListener('click', async () => {
        // UI Loading State
        generateBtn.disabled = true;
        btnText.textContent = "Fetching...";
        statusContainer.classList.remove('hidden');
        spinner.classList.remove('hidden');
        
        statusMessage.textContent = "Scraping X & generating newsletter...";
        statusMessage.className = "status-message";

        try {
            // Trigger the local python API
            const response = await fetch('http://127.0.0.1:5001/generate', {
                method: 'GET',
            });
            
            const data = await response.json();

            if (response.ok) {
                showStatus("🎉 Complete! Check your email.", "success");
                btnText.textContent = "Sent successfully!";
            } else {
                showStatus(`❌ ${data.message}`, "error");
                btnText.textContent = "Failed";
            }
        } catch (error) {
            showStatus("❌ Failed to connect to local server. Is start_server.sh running?", "error");
            btnText.textContent = "Error";
        } finally {
            spinner.classList.add('hidden');
            setTimeout(() => {
                if (!generateBtn.disabled || btnText.textContent === "Sent successfully!") {
                    // Reset button after 3 seconds on success
                    generateBtn.disabled = false;
                    btnText.textContent = "Get AI Updates";
                }
            }, 3000);
        }
    });

    function showStatus(text, type) {
        statusContainer.classList.remove('hidden');
        statusMessage.textContent = text;
        statusMessage.className = `status-message ${type}`;
    }
});
