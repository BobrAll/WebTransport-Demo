const log = msg => {
    document.getElementById("log").textContent += msg + "\n";
};

let transport;
let streamWriter;
let dgramWriter;

async function connect() {
    transport = new WebTransport("https://127.0.0.1:4433/");
    await transport.ready;
    log("WebTransport connected!");

    const stream = await transport.createBidirectionalStream();
    streamWriter = stream.writable.getWriter();
    readStreamLoop(stream.readable.getReader());

    dgramWriter = transport.datagrams.writable.getWriter();
    readDatagramLoop(transport.datagrams.readable.getReader());
}

async function readStreamLoop(reader) {
    while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        log("Stream ← " + new TextDecoder().decode(value));
    }
}

async function readDatagramLoop(reader) {
    while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        log("Dgram ← " + new TextDecoder().decode(value));
    }
}

document.getElementById("send-stream").onclick = async () => {
    const text = document.getElementById("msg-stream").value;
    await streamWriter.write(new TextEncoder().encode(text));
    log("Stream → " + text);
};

document.getElementById("send-dgram").onclick = async () => {
    const text = document.getElementById("msg-dgram").value;
    await dgramWriter.write(new TextEncoder().encode(text));
    log("Dgram → " + text);
};

connect().catch(err => {
    console.error(err);
    log("Ошибка подключения: " + err);
});
