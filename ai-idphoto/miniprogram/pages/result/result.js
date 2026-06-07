Page({
  data: {
    photoPath: '',
    resultPath: '',
    spec: '',
    specName: '',
    color: '',
    colorName: '',
    unlocked: false,
    adLoaded: false,
    adUnitId: 'adunit-xxxxxxxxxxxxxxxx', // 替换为你的激励视频广告单元ID
  },

  onLoad(options) {
    this.setData({
      photoPath: decodeURIComponent(options.photo || ''),
      resultPath: decodeURIComponent(options.result || ''),
      spec: options.spec || '',
      specName: options.specName || '',
      color: options.color || '',
      colorName: options.colorName || '',
    })
    this.initAd()
  },

  initAd() {
    if (!wx.createRewardedVideoAd) {
      console.warn('当前版本不支持激励视频广告')
      return
    }
    this.videoAd = wx.createRewardedVideoAd({ adUnitId: this.data.adUnitId })
    this.videoAd.onLoad(() => this.setData({ adLoaded: true }))
    this.videoAd.onError((err) => {
      console.error('广告加载失败:', err)
      // Fallback: allow download anyway if ad fails
      this.setData({ unlocked: true })
    })
    this.videoAd.onClose((res) => {
      if (res && res.isEnded) {
        this.setData({ unlocked: true })
        getApp().saveOrder({
          id: Date.now().toString(),
          specName: this.data.specName,
          colorName: this.data.colorName,
          thumbUrl: this.data.resultPath,
          resultUrl: this.data.resultPath,
          time: new Date().toLocaleString('zh-CN')
        })
        wx.showToast({ title: '已解锁高清下载', icon: 'success' })
      } else {
        wx.showToast({ title: '完整观看广告才能解锁哦', icon: 'none' })
      }
    })
  },

  onWatchAd() {
    if (this.data.unlocked) {
      this.onDownload()
      return
    }
    if (!this.videoAd) {
      // Dev fallback: no ad SDK available
      this.setData({ unlocked: true })
      wx.showToast({ title: '已解锁高清下载', icon: 'success' })
      return
    }
    this.videoAd.show().catch(() => {
      this.videoAd.load().then(() => this.videoAd.show()).catch(() => {
        // Ad not ready, fallback
        this.setData({ unlocked: true })
        wx.showToast({ title: '已解锁高清下载', icon: 'success' })
      })
    })
  },

  onDownload() {
    if (!this.data.unlocked) {
      return
    }
    wx.saveImageToPhotosAlbum({
      filePath: this.data.resultPath,
      success: () => {
        wx.showToast({ title: '已保存高清原图', icon: 'success' })
        getApp().saveOrder({
          id: Date.now().toString(),
          specName: this.data.specName,
          colorName: this.data.colorName,
          thumbUrl: this.data.resultPath,
          resultUrl: this.data.resultPath,
          time: new Date().toLocaleString('zh-CN')
        })
      },
      fail: () => {
        wx.showModal({
          title: '提示',
          content: '需要相册权限才能保存图片',
          success: (res) => {
            if (res.confirm) wx.openSetting()
          }
        })
      }
    })
  },

  onSkipPay() {
    // TODO: 替换为真实微信支付
    wx.showModal({
      title: '付费下载',
      content: '支付 ¥1.99 即可无水印高清下载。支付功能即将开放，敬请期待。',
      showCancel: true,
      cancelText: '观看广告',
      confirmText: '去支付',
      success: (res) => {
        if (res.confirm) {
          wx.showToast({ title: '支付功能即将开放', icon: 'none' })
        } else {
          this.onWatchAd()
        }
      }
    })
  },

  onStartOver() {
    wx.navigateBack({
      delta: 2,
      fail: () => wx.navigateTo({ url: '/pages/index/index' })
    })
  }
})
