let db = null
const path = require('path')
const fs = require('fs')

const DB_PATH = path.join(__dirname, '..', 'data', 'db.json')

function initDB() {
  const dir = path.dirname(DB_PATH)
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true })
  if (!fs.existsSync(DB_PATH)) {
    fs.writeFileSync(DB_PATH, JSON.stringify({ orders: [] }, null, 2))
  }
  loadDB()
}

function loadDB() {
  db = JSON.parse(fs.readFileSync(DB_PATH, 'utf-8'))
}

function saveDB() {
  fs.writeFileSync(DB_PATH, JSON.stringify(db, null, 2))
}

function getDB() {
  if (!db) loadDB()
  // Intercept writes to auto-save
  return new Proxy(db, {
    get(target, prop) {
      return target[prop]
    }
  })
}

// Save periodically and on process exit
setInterval(() => { if (db) saveDB() }, 5000)
process.on('exit', () => { if (db) saveDB() })

module.exports = { initDB, getDB }
