document.addEventListener('DOMContentLoaded', function() {
    const submitButton = document.getElementById('submit_prompt');
    const userInputArea = document.getElementById('user_input');
    const modelResponseArea = document.getElementById('model_response');
    const modelSelection = document.getElementById('model_selection');

    if (submitButton) {
        submitButton.addEventListener('click', function() {
            const userInput = userInputArea.value;
            const selectedModel = modelSelection.value;

            if (!userInput.trim()) {
                modelResponseArea.innerText = "Please enter some text.";
                modelResponseArea.classList.remove('loading');
                return;
            }

            modelResponseArea.innerText = "Loading response...";
            modelResponseArea.classList.add('loading'); // Add loading class

            fetch('/api/interact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    'user_input': userInput,
                    'selected_model': selectedModel
                })
            })
            .then(response => {
                modelResponseArea.classList.remove('loading'); // Remove loading class
                if (!response.ok) {
                    // Try to parse error from JSON response body
                    return response.json().then(errData => {
                        throw new Error(errData.error || 'Network response was not ok: ' + response.statusText);
                    }).catch(() => {
                        // Fallback if parsing JSON fails or no specific error message
                        throw new Error('Network response was not ok: ' + response.statusText);
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.response) {
                    modelResponseArea.innerText = data.response;
                } else if (data.error) { // Should be caught by the error block above, but as a fallback
                    modelResponseArea.innerText = "Error: " + data.error;
                } else {
                    modelResponseArea.innerText = "Received an unexpected response.";
                }
            })
            .catch(error => {
                modelResponseArea.classList.remove('loading'); // Ensure loading class is removed on error
                console.error('Error during fetch:', error);
                modelResponseArea.innerText = "Failed to get response: " + error.message;
            });
        });
    }
});
