# 多阶段构建：构建阶段
FROM node:20-alpine AS builder

# 设置工作目录
WORKDIR /app

# 安装pnpm（单独一层，可以被缓存）
RUN npm install -g pnpm

# 复制package文件和lockfile，利用Docker缓存
COPY package.json pnpm-lock.yaml ./

# 安装依赖（只有依赖变化时才会重新执行）
RUN pnpm install --frozen-lockfile

# 复制源代码（放在依赖安装之后，避免代码变化导致重新安装依赖）
COPY . .

# 构建应用
RUN pnpm run build

FROM nginx:latest

# 设置时区
RUN apt-get update && apt-get install -y tzdata && \
    ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 复制nginx配置文件（先复制配置，后复制构建结果）
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 复制构建结果
COPY --from=builder /app/dist /usr/share/nginx/html

# 暴露端口
EXPOSE 8080

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"]
