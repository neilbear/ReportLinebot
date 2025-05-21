
// 引入必要的模組
const express = require('express');  // 引入 Express 框架
const path = require('path');  // 引入 Node.js 的 path 模組，用於處理檔案路徑
const sqlite3 = require('sqlite3').verbose();  // 引入 SQLite3 模組，用於處理 SQLite 資料庫

// 建立 Express 應用程式實例
const app = express();
const port = 3000;  // 定義伺服器監聽的埠號

// 解析 JSON 格式的請求主體
app.use(express.json());

// 構建數據庫文件的路徑
const dbPath = path.join(__dirname, 'order.db');

// 建立 SQLite 連線
const db = new sqlite3.Database(dbPath);

// 監聽應用程式的 exit 事件，在應用程式結束時關閉 SQLite 連線
process.on('exit', () => {
    db.close();  // 關閉 SQLite 連線
    console.log('SQLite connection closed');
  });
  
  // 啟動伺服器監聽指定埠號
  app.listen(port, () => {
    console.log(`Express app listening at http://localhost:${port}`);
  });
  