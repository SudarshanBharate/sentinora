const websocket = new WebSocket('ws://127.0.0.1:8000/ws/chat/');

websocket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    const responseElement = document.getElementById("response");

    if (data.is_toxic) {
        alert("Warning: This message is considered toxic!");
        responseElement.className = "alert alert-danger";
    } else {
        responseElement.className = "alert alert-info";
    }

    responseElement.textContent = `Message: ${data.message}, Toxicity Level: ${data.toxicity_level}`;
};

document.getElementById("send").addEventListener("click", () => {
    const message = document.getElementById("message").value;
    if (message) {
        websocket.send(JSON.stringify({ message: message }));
        document.getElementById("message").value = "";  // Clear input
    }
});
