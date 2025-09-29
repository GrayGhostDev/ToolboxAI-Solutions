#!/usr/bin/env node
/* Simple Socket.IO connectivity check. Usage:
   node apps/scripts/check-socketio.js http://127.0.0.1:8008 [/socket.io]
*/
const { io } = require('socket.io-client');

const url = process.argv[2] || 'http://127.0.0.1:8008';
const path = process.argv[3] || '/socket.io';

const socket = io(url, { path, transports: ['websocket'], timeout: 5000 });

let done = false;
const finish = (code) => {
  if (!done) {
    done = true;
    try { socket.close(); } catch {}
    process.exit(code);
  }
};

socket.on('connect', () => {
  console.log(`✓ Connected to ${url}${path} (id=${socket.id})`);
  finish(0);
});

socket.on('connect_error', (err) => {
  console.error(`✗ Connect error: ${err && err.message ? err.message : err}`);
  finish(2);
});

setTimeout(() => {
  console.error('✗ Timeout waiting for Socket.IO connection');
  finish(3);
}, 6000);
