import {timeAgo} from './timeago.js';

const table = document.querySelector('#devices');
const body = table.tBodies[0];
const template = document.querySelector('#device-row');
const listStatus = document.querySelector('#list-status');
const controlError = document.querySelector('#control-error');
const rows = new Map();
let writeVersion = 0;

function showStatus(element, message) {
  element.hidden = !message;
  if (element.textContent !== message) element.textContent = message;
}

async function request(path, method = 'GET') {
  const response = await fetch(path, {method, signal: AbortSignal.timeout(10000)});
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response;
}

function bindControl(input, property, label, action) {
  let current;
  input.addEventListener('change', async () => {
    const selection = input[property];
    input.disabled = true;
    showStatus(controlError, '');
    try {
      await request(action(selection), 'POST');
      current = selection;
      writeVersion++;
    } catch (error) {
      input[property] = current;
      showStatus(controlError, `Could not change ${input.getAttribute('aria-label')}: ${error.message}`);
    } finally {
      input.disabled = false;
    }
  });
  return (value, name) => {
    input.setAttribute('aria-label', `${label} for ${name}`);
    if (!input.disabled && current !== value) input[property] = value;
    current = value;
  };
}

function createRow(id) {
  const element = template.content.firstElementChild.cloneNode(true);
  const [name, room, ip, sku, power, color, identifier, updated, source] = element.cells;
  const time = updated.firstElementChild;
  const badge = source.firstElementChild;
  const base = `/api/device/${encodeURIComponent(id)}`;
  const setPower = bindControl(power.querySelector('input'), 'checked', 'power',
    (on) => `${base}/power/${on ? 'on' : 'off'}`);
  const setColor = bindControl(color.querySelector('input'), 'value', 'color',
    (value) => `${base}/color/${encodeURIComponent(value)}`);
  identifier.firstElementChild.textContent = id;
  return {
    element,
    update(device) {
      const state = device.state;
      name.textContent = device.name;
      room.textContent = device.room;
      ip.textContent = device.ip;
      sku.textContent = device.sku;
      setPower(state?.on ?? false, device.name);
      const {r, g, b} = state?.color ?? {r: 0, g: 0, b: 0};
      setColor(`#${[r, g, b].map((part) => part.toString(16).padStart(2, '0')).join('')}`, device.name);
      const date = new Date(state?.updated ?? NaN);
      time.textContent = timeAgo(date);
      time.dateTime = time.textContent ? state.updated : '';
      time.title = time.textContent ? date.toLocaleString() : '';
      badge.textContent = state?.source ?? '';
      badge.hidden = !badge.textContent;
    },
  };
}

function updateRows(devices) {
  const removed = new Set(rows.keys());
  let next = body.firstElementChild;
  for (const device of devices) {
    let row = rows.get(device.id);
    if (!row) {
      row = createRow(device.id);
      rows.set(device.id, row);
    }
    row.update(device);
    removed.delete(device.id);
    if (row.element !== next) body.insertBefore(row.element, next);
    next = row.element.nextElementSibling;
  }
  for (const id of removed) {
    rows.get(id).element.remove();
    rows.delete(id);
  }
  table.hidden = devices.length === 0;
  showStatus(listStatus, devices.length ? '' : 'No devices found.');
}

async function refresh() {
  const version = writeVersion;
  try {
    const response = await request('/api/devices');
    const devices = await response.json();
    // Do not overwrite a completed command with a list requested before it.
    if (version === writeVersion) updateRows(devices);
  } catch (error) {
    showStatus(listStatus, `Could not load devices: ${error.message}. Retrying…`);
  } finally {
    setTimeout(refresh, 5000);
  }
}

refresh();
