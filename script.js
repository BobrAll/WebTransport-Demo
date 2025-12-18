const log = msg => {
    document.getElementById("log").textContent += msg + "\n";
};

let transport;
let writer;
let reader;

async function connect() {
    transport = new WebTransport("https://127.0.0.1:4433/");

    await transport.ready;
    log("Соединение по WebTransport настроено успешно!");

    const stream = await transport.createBidirectionalStream();
    writer = stream.writable.getWriter();
    reader = stream.readable.getReader();

    readLoop();
}

async function readLoop() {
    while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        log("← " + new TextDecoder().decode(value));
    }
}

document.getElementById("send").onclick = async () => {
    const text = document.getElementById("msg").value;
    await writer.write(new TextEncoder().encode(text));
    log("→ " + text);
};

connect().catch(err => {
    console.error(err);
    log("Ошибка подключения");
});