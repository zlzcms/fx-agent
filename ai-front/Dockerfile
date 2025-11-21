FROM node:20-alpine AS build

WORKDIR /fba_ui

# 安装pnpm
RUN npm install -g pnpm@latest

# 复制依赖相关文件（优化缓存）
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/ ./apps/
COPY packages/ ./packages/
COPY internal/ ./internal/
COPY scripts/ ./scripts/

# 安装依赖（使用锁定的版本确保一致性）
RUN pnpm install --frozen-lockfile

# 复制源代码
COPY . .

# 构建应用
RUN pnpm build:antd

FROM nginx:latest

COPY scripts/deploy/nginx.conf /etc/nginx/nginx.conf

COPY --from=build /fba_ui/apps/web-antd/dist /var/www/fba_ui

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
