/**
 * Synchrony WhatsApp Bridge
 * 
 * A tiny Node.js server that:
 * 1. Connects to WhatsApp Web via QR code scan
 * 2. Listens to all incoming messages in real-time
 * 3. Batches messages and POSTs them to the FastAPI backend
 * 4. Receives nudge responses and can optionally send them back
 * 
 * This is the "Ears and Mouth" — the Python backend is the "Brain".
 */

const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');

// ── Config ──────────────────────────────────────────────────────────────────
const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const BATCH_SIZE = 10;          // Send to backend every N messages
const BATCH_INTERVAL_MS = 30000; // Or every 30 seconds

// ── State ───────────────────────────────────────────────────────────────────
let messageBuffer = [];
let isProcessing = false;

// ── WhatsApp Client ─────────────────────────────────────────────────────────
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
    },
});

// QR Code for authentication
client.on('qr', (qr) => {
    console.log('\n📱 Scan this QR code with WhatsApp:\n');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('\n✅ Synchrony WhatsApp Bridge is LIVE');
    console.log(`🔗 Connected to backend: ${BACKEND_URL}`);
    console.log('👂 Listening to all incoming messages...\n');
});

client.on('authenticated', () => {
    console.log('🔐 Authenticated successfully');
});

client.on('auth_failure', (msg) => {
    console.error('❌ Authentication failed:', msg);
});

// ── Message Listener ────────────────────────────────────────────────────────
client.on('message_create', async (msg) => {
    // Skip status updates and media-only messages
    if (msg.isStatus || !msg.body) return;

    const contact = await msg.getContact();
    const chat = await msg.getChat();

    const structured = {
        timestamp: new Date(msg.timestamp * 1000).toISOString(),
        sender: contact.pushname || contact.name || msg.from,
        message: msg.body,
        source: 'whatsapp_live',
        chat_name: chat.name || 'DM',
        is_group: chat.isGroup,
    };

    console.log(`📨 [${structured.chat_name}] ${structured.sender}: ${structured.message.substring(0, 60)}...`);

    messageBuffer.push(structured);

    // Flush if buffer is full
    if (messageBuffer.length >= BATCH_SIZE) {
        await flushBuffer();
    }
});

// ── Batch Flush ─────────────────────────────────────────────────────────────
async function flushBuffer() {
    if (isProcessing || messageBuffer.length === 0) return;
    isProcessing = true;

    const batch = [...messageBuffer];
    messageBuffer = [];

    try {
        console.log(`\n🔄 Flushing ${batch.length} messages to backend...`);
        
        const response = await axios.post(`${BACKEND_URL}/analyze`, {
            messages: batch,
            user_id: 'whatsapp_live',
            target_person: 'auto_detect',
        });

        const data = response.data;
        console.log(`  🔥 Heat: ${data.heat}/10 | ❄️ Decay: ${data.decay}/10 | 🎭 ${data.emotion}`);
        console.log(`  🛤️ Route: ${data.route}`);
        
        if (data.nudges && data.nudges.length > 0) {
            console.log(`  💬 Nudges:`);
            data.nudges.forEach((n, i) => console.log(`     ${i + 1}. ${n}`));
        }
    } catch (err) {
        console.error(`  ❌ Backend error: ${err.message}`);
        // Re-queue messages on failure
        messageBuffer = [...batch, ...messageBuffer];
    }

    isProcessing = false;
}

// Periodic flush
setInterval(flushBuffer, BATCH_INTERVAL_MS);

// ── Start ───────────────────────────────────────────────────────────────────
console.log('🤖 Synchrony WhatsApp Bridge starting...');
console.log('   Waiting for QR code...\n');
client.initialize();
