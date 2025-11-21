<script setup lang="ts">
import { h, onMounted, reactive, ref } from 'vue';

import { Page } from '@vben/common-ui';
import { createIconifyIcon } from '@vben/icons';

import { Alert, Button, Card, Descriptions, message, Space, Tag, Typography } from 'ant-design-vue';

const { Title, Text, Paragraph } = Typography;

// 创建图标组件
const CheckCircleOutlined = createIconifyIcon('ant-design:check-circle-outlined');
const CloseCircleOutlined = createIconifyIcon('ant-design:close-circle-outlined');
const ReloadOutlined = createIconifyIcon('ant-design:reload-outlined');
const CopyOutlined = createIconifyIcon('ant-design:copy-outlined');
const LinkOutlined = createIconifyIcon('ant-design:link-outlined');

// 服务状态
const serviceStatus = reactive({
  mcpService: 'checking',
});

// 服务信息
const serviceInfo = reactive({
  mcpPort: '8009',
  fastApiPort: '8008',
  host: 'localhost',
  protocol: 'http',
  endpoints: {
    health: '/health',
    mcp: '/mcp',
    docs: '/api/v1/docs',
  },
});

// 环境检测
const isProduction = ref(false);
const currentUrl = ref('');
const environmentInfo = ref({
  mode: '',
  nodeEnv: '',
  dev: false,
  prod: false,
});

// 检测环境并更新服务信息
const detectEnvironment = () => {
  // 根据环境变量判断环境
  const mode = import.meta.env.MODE || 'development';
  const nodeEnv = import.meta.env.NODE_ENV || 'development';
  const dev = import.meta.env.DEV || false;
  const prod = import.meta.env.PROD || false;

  environmentInfo.value = { mode, nodeEnv, dev, prod };
  isProduction.value = prod || mode === 'production' || nodeEnv === 'production';
  currentUrl.value = window.location.href;

  if (isProduction.value) {
    // 生产环境配置 - 根据实际线上环境调整
    serviceInfo.host = 'mcp.ai1center.com'; // MCP 服务域名
    serviceInfo.protocol = 'https';
    serviceInfo.mcpPort = ''; // 生产环境使用标准端口
    serviceInfo.fastApiPort = ''; // 生产环境使用标准端口
    serviceInfo.endpoints = {
      health: '/mcp/health', // MCP协议服务健康检查
      mcp: '/mcp', // MCP协议服务端点
      docs: '/api/v1/docs', // FastAPI 服务 Swagger UI 文档
    };
  } else {
    // 开发环境配置
    serviceInfo.host = 'localhost';
    serviceInfo.protocol = 'http';
    serviceInfo.mcpPort = '8009'; // FastMCP 服务端口
    serviceInfo.fastApiPort = '8008'; // FastAPI 服务端口
    serviceInfo.endpoints = {
      health: '/health', // FastMCP 服务健康检查
      mcp: '/mcp', // FastMCP 服务端点
      docs: '/api/v1/docs', // FastAPI 服务 Swagger UI 文档
    };
  }
};

// 连接信息
const connectionInfo = ref({
  mcpUrl: '',
  mcpHealthUrl: '',
  docsUrl: '',
});

// 更新连接信息
const updateConnectionInfo = () => {
  const baseUrl = `${serviceInfo.protocol}://${serviceInfo.host}`;
  const mcpBaseUrl = serviceInfo.mcpPort ? `${baseUrl}:${serviceInfo.mcpPort}` : baseUrl;
  const fastApiBaseUrl = serviceInfo.fastApiPort
    ? `${baseUrl}:${serviceInfo.fastApiPort}`
    : baseUrl;

  connectionInfo.value = {
    mcpUrl: `${mcpBaseUrl}${serviceInfo.endpoints.mcp}`,
    mcpHealthUrl: `${mcpBaseUrl}${serviceInfo.endpoints.health}`,
    docsUrl: `${fastApiBaseUrl}${serviceInfo.endpoints.docs}`,
  };
};

// 检查服务状态
const checkServiceStatus = async () => {
  try {
    // 根据环境选择不同的健康检查策略
    const candidates: string[] = [];

    if (isProduction.value) {
      // 生产环境：mcp.ai1center.com
      candidates.push(
        '/health', // API服务健康检查
        '/api/v1/health', // API服务健康检查（备用）
      );
    } else {
      // 开发环境：localhost
      candidates.push(
        '/api/mcp/health', // 开发环境MCP健康检查
        '/api/v1/health', // 开发环境API健康检查
      );
    }

    let healthy = false;
    let usedUrl = '';
    let serviceType = '';

    for (const url of candidates) {
      try {
        const resp = await fetch(url);

        if (resp.ok) {
          const responseText = await resp.text();

          // 检查是否有实际内容返回
          if (responseText && responseText.trim()) {
            try {
              JSON.parse(responseText);
              healthy = true;
              usedUrl = url;
              serviceType = 'API服务';
              break;
            } catch {
              // 非JSON响应，但有内容也算健康
              if (responseText.trim()) {
                healthy = true;
                usedUrl = url;
                serviceType = 'API服务';
                break;
              }
            }
          }
        } else if (resp.status === 401) {
          // 401状态码表示服务运行但需要认证，这也是健康的标志
          healthy = true;
          usedUrl = url;
          serviceType = 'API服务';
          break;
        }
      } catch {
        // 单个探测失败继续尝试下一个
      }
    }

    serviceStatus.mcpService = healthy ? 'healthy' : 'unhealthy';

    // 更新展示的健康检查地址
    if (usedUrl) {
      connectionInfo.value.mcpHealthUrl = usedUrl.startsWith('http')
        ? usedUrl
        : `${window.location.origin}${usedUrl}`;
    }

    if (healthy) {
      message.success(`${serviceType}健康检查通过`);
    } else {
      throw new Error('所有健康检查端点均无响应或返回空内容');
    }
  } catch (error) {
    console.error('检查服务状态失败:', error);
    serviceStatus.mcpService = 'unhealthy';
    message.error('无法连接到 MCP 服务，请检查服务是否正常运行');
  }
};

// 复制到剪贴板
const copyToClipboard = async (text: string, label: string) => {
  try {
    // 检查浏览器是否支持 Clipboard API
    if (!navigator.clipboard) {
      // 降级到传统方法
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.append(textArea);
      textArea.select();
      document.execCommand('copy');
      textArea.remove();
      message.success(`${label} 已复制到剪贴板`);
      return;
    }

    await navigator.clipboard.writeText(text);
    message.success(`${label} 已复制到剪贴板`);
  } catch (error) {
    console.error('复制失败:', error);
    // 尝试降级方法
    try {
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.append(textArea);
      textArea.select();
      document.execCommand('copy');
      textArea.remove();
      message.success(`${label} 已复制到剪贴板`);
    } catch {
      message.error('复制失败，请手动复制');
    }
  }
};

// 获取状态标签
const getStatusTag = (status: string) => {
  const statusMap: Record<string, { color: string; icon: any; text: string }> = {
    healthy: { color: 'success', text: '健康', icon: CheckCircleOutlined },
    connected: { color: 'success', text: '已连接', icon: CheckCircleOutlined },
    unhealthy: { color: 'error', text: '异常', icon: CloseCircleOutlined },
    disconnected: { color: 'error', text: '未连接', icon: CloseCircleOutlined },
    checking: { color: 'processing', text: '检查中', icon: ReloadOutlined },
  };

  const config = statusMap[status] || statusMap.checking;
  if (!config) return null;

  const IconComponent = config.icon;

  return h(
    Tag,
    { color: config.color },
    {
      default: () => [h(IconComponent, { style: 'margin-right: 4px' }), config.text],
    },
  );
};

// 刷新状态
const refreshStatus = () => {
  serviceStatus.mcpService = 'checking';
  checkServiceStatus();
};

// 组件挂载时检查状态
onMounted(() => {
  detectEnvironment();
  updateConnectionInfo();
  checkServiceStatus();
});
</script>

<template>
  <Page>
    <div class="space-y-6">
      <!-- 页面标题 -->
      <div class="mb-6">
        <Title :level="2">MCP 服务管理</Title>
        <Paragraph type="secondary">
          Model Context Protocol (MCP) 服务连接状态和配置信息
        </Paragraph>
      </div>

      <!-- 环境信息 -->
      <Card title="环境信息" class="mb-6">
        <div class="flex items-center gap-3 mb-4">
          <Tag :color="isProduction ? 'blue' : 'green'">
            {{ isProduction ? '生产环境' : '开发环境' }}
          </Tag>
          <Text type="secondary"> 当前访问: {{ currentUrl }} </Text>
        </div>
        <div class="mt-3">
          <Descriptions :column="2" size="small">
            <Descriptions.Item label="MODE">
              <Tag>{{ environmentInfo.mode }}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="NODE_ENV">
              <Tag>{{ environmentInfo.nodeEnv }}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="DEV">
              <Tag :color="environmentInfo.dev ? 'green' : 'red'">
                {{ environmentInfo.dev ? 'true' : 'false' }}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="PROD">
              <Tag :color="environmentInfo.prod ? 'blue' : 'red'">
                {{ environmentInfo.prod ? 'true' : 'false' }}
              </Tag>
            </Descriptions.Item>
          </Descriptions>
        </div>
      </Card>

      <!-- 服务状态概览 -->
      <Card title="服务状态" class="mb-6">
        <template #extra>
          <Button type="primary" :icon="h(ReloadOutlined)" @click="refreshStatus">
            刷新状态
          </Button>
        </template>

        <Descriptions :column="1" bordered>
          <Descriptions.Item label="MCP 协议服务">
            <component :is="getStatusTag(serviceStatus.mcpService)" />
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <!-- 连接信息 -->
      <Card title="连接信息" class="mb-6">
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- MCP 服务连接 -->
          <div
            class="p-6 bg-gray-50 border border-gray-200 rounded-lg transition-all duration-300 hover:border-blue-500 hover:shadow-md h-full"
          >
            <div class="flex items-center gap-2 mb-2">
              <LinkOutlined class="text-blue-500 text-base" />
              <span class="font-semibold text-sm text-gray-800 flex-1">MCP 协议服务</span>
              <Button
                type="text"
                size="small"
                :icon="h(CopyOutlined)"
                @click="copyToClipboard(connectionInfo.mcpUrl, 'MCP 服务地址')"
                class="min-w-0 h-auto px-2 py-1 hover:bg-blue-50"
              />
            </div>
            <Text
              code
              class="block mb-1.5 text-xs break-all bg-white p-2 border border-gray-300 rounded min-h-[2.5rem] flex items-center"
            >
              {{ connectionInfo.mcpUrl }}
            </Text>
            <div class="text-xs text-gray-500 leading-relaxed">
              MCP 协议端点，用于与 AI 模型通信
            </div>
          </div>

          <!-- API 文档 -->
          <div
            class="p-6 bg-gray-50 border border-gray-200 rounded-lg transition-all duration-300 hover:border-blue-500 hover:shadow-md h-full"
          >
            <div class="flex items-center gap-2 mb-2">
              <LinkOutlined class="text-blue-500 text-base" />
              <span class="font-semibold text-sm text-gray-800 flex-1"
                >MCP 服务 Swagger UI 文档</span
              >
              <Button
                type="text"
                size="small"
                :icon="h(CopyOutlined)"
                @click="copyToClipboard(connectionInfo.docsUrl, 'MCP 服务 Swagger UI 文档地址')"
                class="min-w-0 h-auto px-2 py-1 hover:bg-blue-50"
              />
            </div>
            <Text
              code
              class="block mb-1.5 text-xs break-all bg-white p-2 border border-gray-300 rounded min-h-[2.5rem] flex items-center"
            >
              {{ connectionInfo.docsUrl }}
            </Text>
            <div class="text-xs text-gray-500 leading-relaxed">
              MCP 服务的 Swagger UI 交互式 API 文档
            </div>
          </div>
        </div>
      </Card>

      <!-- 使用说明 -->
      <Card title="使用说明" class="mb-6">
        <Space direction="vertical" size="middle" class="w-full">
          <Alert
            message="MCP 协议服务"
            description="MCP (Model Context Protocol) 是标准化的 AI 模型上下文通信协议。本服务提供数据查询、统计分析等功能，是 AI 助手与数据仓库之间的桥梁。"
            type="info"
            show-icon
          />

          <Alert
            message="服务架构"
            description="系统采用双服务架构：FastMCP 服务提供 MCP 协议支持，FastAPI 服务提供 REST API 和交互式文档。"
            type="info"
            show-icon
          />

          <Alert
            message="API 文档"
            description="点击上方的 Swagger UI 文档链接，可以查看完整的 API 接口说明，支持在线测试和交互式 API 探索。"
            type="success"
            show-icon
          />

          <Alert
            message="健康监控"
            description="定期检查服务健康状态，确保 API 服务和数据库连接正常。如遇异常，请检查服务日志和网络连接。"
            type="warning"
            show-icon
          />

          <Alert
            message="环境配置"
            description="开发环境使用不同端口提供服务，生产环境通过统一域名对外服务。请确保环境配置正确，端口访问权限设置合理。"
            type="warning"
            show-icon
          />
        </Space>
      </Card>
    </div>
  </Page>
</template>

<style scoped>
:deep(.ant-descriptions-item-label) {
  font-weight: 600;
}

:deep(.ant-card-head-title) {
  font-weight: 600;
}
</style>
