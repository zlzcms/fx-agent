// 工具函数入口

/**
 * 格式化日期为 yyyy-mm-dd 格式
 * @param {Date|string|number} date Date对象、日期字符串或时间戳
 * @returns {string} yyyy-mm-dd字符串
 */
export function formatDate(date) {
  if (typeof date == 'string') {
    date = new Date(date)
  }
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
}

/**
 * 格式化日期时间为 yyyy-mm-dd hh:mm:ss 格式
 * @param {Date|string|number} date Date对象、日期字符串或时间戳
 * @returns {string} yyyy-mm-dd hh:mm:ss字符串
 */
export function formatDateTime(date) {
  // 处理不同类型的输入
  if (!date) {
    date = new Date()
  } else if (typeof date === 'string') {
    date = new Date(date)
  } else if (typeof date === 'number') {
    date = new Date(date)
  }

  // 检查日期是否有效
  if (isNaN(date.getTime())) {
    return ''
  }

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')

  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

/**
 * 格式化时间为 hh:mm:ss 格式
 * @param {Date|string|number} date Date对象、日期字符串或时间戳
 * @returns {string} hh:mm:ss字符串
 */
export function formatTime(date) {
  if (!date) {
    date = new Date()
  } else if (typeof date === 'string') {
    date = new Date(date)
  } else if (typeof date === 'number') {
    date = new Date(date)
  }

  if (isNaN(date.getTime())) {
    return ''
  }

  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')

  return `${hours}:${minutes}:${seconds}`
}

/**
 * 自定义格式化日期
 * @param {Date|string|number} date Date对象、日期字符串或时间戳
 * @param {string} format 格式字符串，支持 YYYY、MM、DD、HH、mm、ss
 * @returns {string} 格式化后的日期字符串
 *
 * @example
 * formatCustomDate(new Date(), 'YYYY-MM-DD HH:mm:ss') // 2025-08-19 20:53:32
 * formatCustomDate(new Date(), 'YYYY年MM月DD日 HH:mm') // 2025年08月19日 20:53
 * formatCustomDate(new Date(), 'MM/DD/YYYY') // 08/19/2025
 */
export function formatCustomDate(date, format = 'YYYY-MM-DD HH:mm:ss') {
  if (!date) {
    date = new Date()
  } else if (typeof date === 'string') {
    date = new Date(date)
  } else if (typeof date === 'number') {
    date = new Date(date)
  }

  if (isNaN(date.getTime())) {
    return ''
  }

  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')

  return format
    .replace(/YYYY/g, year)
    .replace(/MM/g, month)
    .replace(/DD/g, day)
    .replace(/HH/g, hours)
    .replace(/mm/g, minutes)
    .replace(/ss/g, seconds)
}

/**
 *
 * 根据文件名后缀获取文件类型
 * @param {string} filename 文件名
 * @returns {string} 文件类型 ：md, text, csv, xls, xlsx, json, pdf, doc, docx, ppt，html
 */
export function getFileType(filename) {
  const ext = filename.split('.').pop().toLowerCase()
  return ext
}

/**
 * 文件大小单位转换函数
 * @param {number} size 文件大小
 * @returns {string} 文件大小 ：KB, MB, GB, TB
 */
export function formatFileSize(size) {
  if (size < 1024) {
    return size + 'B'
  }
  if (size < 1024 * 1024) {
    return (size / 1024).toFixed(2) + 'KB'
  }
  if (size < 1024 * 1024 * 1024) {
    return (size / 1024 / 1024).toFixed(2) + 'MB'
  }
  if (size < 1024 * 1024 * 1024 * 1024) {
    return (size / 1024 / 1024 / 1024).toFixed(2) + 'GB'
  }
  return (size / 1024 / 1024 / 1024 / 1024).toFixed(2) + 'TB'
}

/**
 *
 * 根据路径加载文件内容 以‘/assets/’开头的通过 fetch 获取文件内容，其他通过 axios 获取文件内容
 * @param {string} path 文件路径
 * @returns {string} 文件内容
 */
export function loadFileContent(path) {
  if (path.startsWith('/assets/')) {
    const file = fetch(path).then(res => res.text())
    return file
  } else {
    const file = axios.get(path).then(res => res.data)
    return file
  }
}
