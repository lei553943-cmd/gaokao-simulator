const SPECS = {
  '1inch': { name: '一寸', width: 295, height: 413 },
  '2inch': { name: '二寸', width: 413, height: 579 },
  'small2inch': { name: '小两寸', width: 390, height: 567 },
  'large2inch': { name: '大两寸', width: 413, height: 626 },
  'idcard': { name: '身份证', width: 358, height: 441 },
  'social': { name: '社保卡', width: 358, height: 441 },
}

Page({
  data: {
    photoPath: '',
    resultPath: '',
    spec: 'small2inch',
    specName: '小两寸',
    color: '#438EDB',
    colorName: '蓝色',
    loading: true,
    processingText: '处理中...',
    specs: [
      { id: '1inch', name: '一寸' },
      { id: '2inch', name: '二寸' },
      { id: 'small2inch', name: '小两寸' },
      { id: 'large2inch', name: '大两寸' },
      { id: 'idcard', name: '身份证' },
      { id: 'social', name: '社保卡' },
    ],
    colors: [
      { name: '白色', value: '#FFFFFF' },
      { name: '蓝色', value: '#438EDB' },
      { name: '红色', value: '#FF3333' },
      { name: '浅蓝', value: '#67C4FF' },
      { name: '灰色', value: '#D0D0D0' },
    ],
  },

  onLoad(options) {
    const photoPath = decodeURIComponent(options.photo)
    const spec = options.spec || 'small2inch'
    const color = decodeURIComponent(options.color || '#438EDB')

    const specItem = this.data.specs.find(s => s.id === spec)
    const colorItem = this.data.colors.find(c => c.value === color)

    this.setData({
      photoPath, spec,
      specName: specItem ? specItem.name : '',
      color,
      colorName: colorItem ? colorItem.name : '',
    })

    this.renderPhoto(photoPath, spec, color)
  },

  renderPhoto(photoPath, spec, color) {
    this.setData({ loading: true, processingText: '处理中...' })

    const specInfo = SPECS[spec]
    const ratio = specInfo.width / specInfo.height

    const finish = (path) => {
      this.setData({ resultPath: path, loading: false })
    }

    wx.getImageInfo({
      src: photoPath,
      success: (imgInfo) => {
        const imgW = imgInfo.width
        const imgH = imgInfo.height
        const imgRatio = imgW / imgH

        let sx, sy, sw, sh
        if (imgRatio > ratio) {
          sh = imgH
          sw = imgH * ratio
          sx = (imgW - sw) / 2
          sy = 0
        } else {
          sw = imgW
          sh = imgW / ratio
          sx = 0
          sy = (imgH - sh) * 0.2
        }

        const canvasW = 600
        const canvasH = Math.round(canvasW / ratio)

        const r = parseInt(color.slice(1, 3), 16)
        const g = parseInt(color.slice(3, 5), 16)
        const b = parseInt(color.slice(5, 7), 16)

        const ctx = wx.createCanvasContext('editCanvas', this)
        ctx.setFillStyle(`rgb(${r},${g},${b})`)
        ctx.fillRect(0, 0, canvasW, canvasH)
        ctx.drawImage(photoPath, sx, sy, sw, sh, 0, 0, canvasW, canvasH)
        ctx.draw(false, () => {
          wx.canvasToTempFilePath({
            canvasId: 'editCanvas',
            destWidth: specInfo.width,
            destHeight: specInfo.height,
            success: (res) => finish(res.tempFilePath),
            fail: () => finish(photoPath)
          }, this)
        })
      },
      fail: () => finish(photoPath)
    })
  },

  onSpecChange(e) {
    const spec = e.currentTarget.dataset.id
    const item = this.data.specs.find(s => s.id === spec)
    this.setData({ spec, specName: item.name })
    this.renderPhoto(this.data.photoPath, spec, this.data.color)
  },

  onColorChange(e) {
    const color = e.currentTarget.dataset.color
    const item = this.data.colors.find(c => c.value === color)
    this.setData({ color, colorName: item.name })
    this.renderPhoto(this.data.photoPath, this.data.spec, color)
  },

  onSave() {
    if (!this.data.resultPath) return
    wx.saveImageToPhotosAlbum({
      filePath: this.data.resultPath,
      success: () => wx.showToast({ title: '已保存到相册', icon: 'success' }),
      fail: () => {
        wx.showModal({
          title: '提示', content: '需要相册权限才能保存图片',
          success: (res) => { if (res.confirm) wx.openSetting() }
        })
      }
    })
  },

  onGoDownload() {
    const app = getApp()
    app.globalData.currentPhoto = this.data.photoPath
    app.globalData.currentResult = this.data.resultPath
    wx.navigateTo({
      url: `/pages/result/result?photo=${encodeURIComponent(this.data.photoPath)}&result=${encodeURIComponent(this.data.resultPath)}&spec=${this.data.spec}&specName=${this.data.specName}&color=${encodeURIComponent(this.data.color)}&colorName=${this.data.colorName}`
    })
  }
})
