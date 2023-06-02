document.addEventListener('DOMContentLoaded', function() {
    // Retrieve Data button click event handler
    var retrieveDataButton = document.getElementById('retrieve-data-button');
    retrieveDataButton.addEventListener('click', function() {
        // Get the entered API keys and secrets
        var startDay = document.getElementById('start-day').value;
        var capitalPerMonth = document.getElementById('capital-per-month').value;
        var apiKeys = document.getElementById('api-keys').value;
        var apiSecrets = document.getElementById('api-secrets').value;
        
        // Loading
        document.getElementById("loading").style.display = "block";
        
        // Make an API request with the entered keys and secrets
        fetch('/retrieve-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                startDay: startDay,
                capitalPerMonth: capitalPerMonth,
                apiKeys: apiKeys,
                apiSecrets: apiSecrets
            })
        })
        .then(function(response) {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('Error: ' + response.status);
            }
        })
        .then(function(data) {
            // Pass the retrieved data to the trade_history route
            var url = '/trade_history';
            window.location.href = url;
        })
        .catch(function(error) {
            console.error(error);
            // Handle the error as needed
        });
    });
});