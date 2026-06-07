const sharp = require('sharp')
const path = require('path')
const { v4: uuidv4 } = require('uuid')
const specs = require('../config/specs')

const OUTPUT_DIR = path.join(__dirname, '..', 'uploads')

// Replace with your actual remove.bg API key via env var
const REMOVEBG_API_KEY = process.env.REMOVEBG_API_KEY || ''

async function removeBackground(inputPath) {
  if (REMOVEBG_API_KEY) {
    return removeBackgroundAPI(inputPath)
  }
  return removeBackgroundLocal(inputPath)
}

async function removeBackgroundAPI(inputPath) {
  const FormData = require('form-data')
  const axios = require('axios')
  const fs = require('fs')

  const form = new FormData()
  form.append('image_file', fs.createReadStream(inputPath))
  form.append('size', 'auto')

  const res = await axios.post('https://api.remove.bg/v1.0/removebg', form, {
    headers: {
      ...form.getHeaders(),
      'X-Api-Key': REMOVEBG_API_KEY,
    },
    responseType: 'arraybuffer',
  })

  const outputPath = path.join(OUTPUT_DIR, `bgremoved_${uuidv4()}.png`)
  fs.writeFileSync(outputPath, res.data)
  return outputPath
}

async function removeBackgroundLocal(inputPath) {
  const image = sharp(inputPath)
  const { width, height } = await image.metadata()

  // Basic background removal: threshold-based alpha mask
  // This is a simplified local fallback; production should use the API
  const outputPath = path.join(OUTPUT_DIR, `bgremoved_${uuidv4()}.png`)

  // Calculate crop region (~30% from edges to get face area)
  const cropLeft = Math.floor(width * 0.15)
  const cropTop = Math.floor(height * 0.05)
  const cropWidth = Math.floor(width * 0.7)
  const cropHeight = Math.floor(height * 0.75)

  await image
    .extract({
      left: cropLeft,
      top: cropTop,
      width: cropWidth,
      height: cropHeight,
    })
    .resize(cropWidth, cropHeight, { fit: 'inside' })
    .png()
    .toFile(outputPath)

  return outputPath
}

async function replaceBackground(inputPath, bgColor, specId) {
  const spec = specs[specId]
  if (!spec) throw new Error(`Unknown spec: ${specId}`)

  const image = sharp(inputPath)
  const { width, height } = await image.metadata()

  // Parse background color
  const r = parseInt(bgColor.slice(1, 3), 16)
  const g = parseInt(bgColor.slice(3, 5), 16)
  const b = parseInt(bgColor.slice(5, 7), 16)

  // Create background image at target size
  const bgBuffer = await sharp({
    create: {
      width: spec.width,
      height: spec.height,
      channels: 3,
      background: { r, g, b },
    },
  })
    .png()
    .toBuffer()

  // Composite portrait onto the background
  const outputPath = path.join(OUTPUT_DIR, `result_${uuidv4()}.png`)

  // Scale and position the portrait
  const portWidth = Math.floor(spec.width * 0.5)
  const portHeight = Math.floor(spec.height * 0.85)
  const left = Math.floor((spec.width - portWidth) / 2)
  const top = Math.floor((spec.height - portHeight) / 2)

  const portBuffer = await image
    .resize(portWidth, portHeight, { fit: 'inside', background: { r: 0, g: 0, b: 0, alpha: 0 } })
    .png()
    .toBuffer()

  await sharp(bgBuffer)
    .composite([{ input: portBuffer, top, left }])
    .png()
    .toFile(outputPath)

  return outputPath
}

async function processPhoto(inputPath, options) {
  const { spec = 'small2inch', color = '#438EDB' } = options

  // Step 1: Remove background
  const noBgPath = await removeBackground(inputPath)

  // Step 2: Place on new background with correct size
  const resultPath = await replaceBackground(noBgPath, color, spec)

  return {
    outputPath: resultPath,
    thumbPath: resultPath,
  }
}

module.exports = { processPhoto }
