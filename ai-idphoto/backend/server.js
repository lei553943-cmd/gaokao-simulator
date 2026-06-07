require('dotenv').config()
const express = require('express')
const cors = require('cors')
const multer = require('multer')
const path = require('path')
const { v4: uuidv4 } = require('uuid')
const { processPhoto } = require('./utils/processor')
const { initDB, getDB } = require('./utils/db')

const app = express()
const PORT = process.env.PORT || 3000

app.use(cors())
app.use(express.json())
app.use('/static', express.static(path.join(__dirname, 'uploads')))

const upload = multer({
  storage: multer.diskStorage({
    destination: path.join(__dirname, 'uploads'),
    filename: (req, file, cb) => {
      cb(null, `${uuidv4()}${path.extname(file.originalname)}`)
    }
  }),
  limits: { fileSize: 10 * 1024 * 1024 },
  fileFilter: (req, file, cb) => {
    const allowed = ['.jpg', '.jpeg', '.png', '.webp']
    const ext = path.extname(file.originalname).toLowerCase()
    cb(null, allowed.includes(ext))
  }
})

// Init DB
initDB()

// Process photo
app.post('/api/process', upload.single('image'), async (req, res) => {
  try {
    if (!req.file) return res.json({ code: 1, msg: '请上传图片' })

    const { spec, color } = req.body
    const result = await processPhoto(req.file.path, { spec, color })

    res.json({
      code: 0,
      data: {
        url: `/static/${path.basename(result.outputPath)}`,
        outputPath: result.outputPath
      }
    })
  } catch (err) {
    console.error('Process error:', err)
    res.json({ code: 1, msg: err.message || '处理失败' })
  }
})

// Save download record
app.post('/api/orders', (req, res) => {
  const { specName, colorName, thumbUrl, resultUrl } = req.body
  const db = getDB()
  const order = {
    id: uuidv4(),
    specName,
    colorName,
    thumbUrl,
    resultUrl,
    time: new Date().toLocaleString('zh-CN'),
    createdAt: Date.now()
  }
  db.orders.push(order)
  res.json({ code: 0, data: order })
})

// List orders
app.get('/api/orders', (req, res) => {
  const db = getDB()
  const orders = [...db.orders].sort((a, b) => b.createdAt - a.createdAt)
  res.json({ code: 0, data: orders })
})

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`)
})
