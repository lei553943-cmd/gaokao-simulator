App({
  globalData: {
    userInfo: null,
    currentPhoto: null,
    currentResult: null
  },

  onLaunch() {
    wx.getSystemInfo({
      success: (res) => {
        this.globalData.systemInfo = res
      }
    })
  },

  saveOrder(order) {
    const orders = wx.getStorageSync('idphoto_orders') || []
    orders.push(order)
    wx.setStorageSync('idphoto_orders', orders)
  }
})
