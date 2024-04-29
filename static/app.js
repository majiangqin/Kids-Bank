
function updateBalanceDisplay() {
    // Fetch the current balance from the server
    fetch('/balance')
        .then(response => response.json())
        .then(data => {
            document.getElementById('balance').innerText = `Balance: $${data.balance}`;
        })
        .catch(error => console.error('Error:', error));
}

function deposit(amount) {
    // Send a POST request to the server to deposit money
    fetch('/deposit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ amount: amount })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('balance').innerText = `Balance: $${data.balance}`;
    })
    .catch(error => console.error('Error:', error));
}

function withdraw(amount) {
    // Send a POST request to the server to withdraw money
    fetch('/withdraw', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ amount: amount })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            document.getElementById('balance').innerText = `Balance: $${data.balance}`;
        }
    })
    .catch(error => console.error('Error:', error));
}

// Update the display on page load
document.addEventListener('DOMContentLoaded', updateBalanceDisplay);
