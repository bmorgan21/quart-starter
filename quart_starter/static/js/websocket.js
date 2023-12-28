function initWS(url, onmessageCallback) {
    let ws = null;

    function connect() {
        const ws = new WebSocket(url);

        ws.onmessage = function (e) {
            onmessageCallback(event.data);
        };

        ws.onclose = function (e) {
            console.log('Socket is closed. Reconnect will be attempted in 1 second.', e.reason);
            setTimeout(function () {
                connect();
            }, 1000);
        };

        ws.onerror = function (err) {
            console.error('Socket encountered error: ', err.message, 'Closing socket');
            ws.close();
        };

        return ws;
    }

    function send(message) {
        return ws.send(message);
    }

    ws = connect();

    return { send: send };
}