const SPECS = [
  { id: '1inch', name: '一寸', size: '25×35mm', px: '295×413px', use: '驾照/普通话考试', width: 295, height: 413 },
  { id: '2inch', name: '二寸', size: '35×49mm', px: '413×579px', use: '简历/护照/签证', width: 413, height: 579 },
  { id: 'small2inch', name: '小两寸', size: '33×48mm', px: '390×567px', use: '考研/考公报名', width: 390, height: 567 },
  { id: 'large2inch', name: '大两寸', size: '35×53mm', px: '413×626px', use: '雅思/托福/GRE', width: 413, height: 626 },
  { id: 'idcard', name: '身份证', size: '26×32mm', px: '358×441px', use: '身份证办理', width: 358, height: 441 },
  { id: 'social', name: '社保卡', size: '30×37mm', px: '358×441px', use: '社保卡办理', width: 358, height: 441 },
]

const COLORS = [
  { name: '白色', value: '#FFFFFF' },
  { name: '蓝色', value: '#438EDB' },
  { name: '红色', value: '#FF3333' },
  { name: '浅蓝', value: '#67C4FF' },
  { name: '灰色', value: '#D0D0D0' },
]

Page({
  data: {
    photo: null,
    photoPath: '',
    specs: SPECS,
    colors: COLORS,
    selectedSpec: 'small2inch',
    selectedColor: '#438EDB',
    showCropper: false,
    loading: false,
    statusBarHeight: 0,
  },

  onLoad() {
    const sys = wx.getSystemInfoSync()
    this.setData({ statusBarHeight: sys.statusBarHeight })
  },

  onChoosePhoto() {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      sizeType: ['compressed'],
      success: (res) => {
        const path = res.tempFiles[0].tempFilePath
        this.setData({ photoPath: path, photo: res.tempFiles[0] })
        wx.navigateTo({
          url: `/pages/edit/edit?photo=${encodeURIComponent(path)}&spec=${this.data.selectedSpec}&color=${encodeURIComponent(this.data.selectedColor)}`
        })
      }
    })
  },

  onSpecChange(e) {
    this.setData({ selectedSpec: e.currentTarget.dataset.id })
  },

  onColorChange(e) {
    this.setData({ selectedColor: e.currentTarget.dataset.color })
  },

  onGoOrders() {
    wx.navigateTo({ url: '/pages/orders/orders' })
  }
})
