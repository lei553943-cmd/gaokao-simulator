Page({
  data: {
    orders: []
  },

  onShow() {
    const orders = wx.getStorageSync('idphoto_orders') || []
    this.setData({ orders: orders.reverse() })
  },

  onDownload(e) {
    const url = e.currentTarget.dataset.url
    if (!url) return
    wx.saveImageToPhotosAlbum({
      filePath: url,
      success: () => wx.showToast({ title: '已保存', icon: 'success' }),
      fail: () => {
        wx.showModal({
          title: '提示', content: '需要相册权限',
          success: (r) => { if (r.confirm) wx.openSetting() }
        })
      }
    })
  },

  onDelete(e) {
    const id = e.currentTarget.dataset.id
    const orders = (wx.getStorageSync('idphoto_orders') || [])
      .filter(o => o.id !== id)
    wx.setStorageSync('idphoto_orders', orders)
    this.setData({ orders: orders.reverse() })
  },

  onMakePhoto() {
    wx.navigateTo({ url: '/pages/index/index' })
  }
})
