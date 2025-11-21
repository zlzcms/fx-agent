# AI Client Front

## 环境配置

项目使用Vite的环境变量系统进行配置管理。环境变量文件包括：

- `.env.development` - 开发环境配置
- `.env.production` - 生产环境配置

### 环境变量说明

| 变量名         | 说明          | 示例                      |
| -------------- | ------------- | ------------------------- |
| VITE_API_HOST  | API服务器地址 | 'http://192.168.1.4:8000' |
| VITE_APP_TITLE | 应用标题      | '开发环境'                |

### 使用方法

在代码中可以通过以下方式访问环境变量：

```javascript
// 访问API地址
const apiHost = import.meta.env.VITE_API_HOST

// 访问应用标题
const appTitle = import.meta.env.VITE_APP_TITLE

// 判断当前环境
const isDev = import.meta.env.MODE === 'development'
```

### 运行不同环境

```bash
# 开发环境
npm run dev

# 生产环境构建
npm run build

# 预览生产环境
npm run preview
```

## docker 部署

** pull code and build **

```
git clone https://git.code.tencent.com/max-ai/ai_client_front.git
git checkout dev
git pull
npm install
npm run build
```

** docker command Test **

```
docker build -t ai-client-front .
docker run -d --name ai-client-front -p 5374:80 -v /home/ai_client_front/dist:/usr/www/html ai-client-front

```

## 同步打包文件到远程服务器上 (14lZxhEuXnU https://client.ai1center.com/

rsync -avz -e ssh ./dist/ root@47.239.101.153:/www/ai/ai-clinet-front/dist/
