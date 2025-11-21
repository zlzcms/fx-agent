<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue';
import { useRouter } from 'vue-router';

import {
  MaterialSymbolsAdd,
  MaterialSymbolsDeleteOutline,
  MaterialSymbolsKeyboardArrowDown,
  MaterialSymbolsKeyboardArrowUp,
} from '@vben/icons';

import { message } from 'ant-design-vue';

import CustomTabs from '#/components/CustomTabs.vue';

// Add loading state variables for API requests
const router = useRouter();
const activeTab = ref('assistant');
const editorTab = ref('edit');

// Update loading states to include variable operations
const loading = reactive({
  submit: false,
  avatar: false,
  dataSourceFetch: false,
  save: false,
  variableOps: false,
  initializing: true,
});

// Define tabs for the CustomTabs component
const tabItems = [
  { key: 'assistant', label: '助理编辑' },
  { key: 'test', label: '模拟测试' },
  { key: 'logs', label: '测试日志' },
];

// Tab change handler
const handleTabChange = (tab: string) => {
  activeTab.value = tab;
};

// Initialize data (simulating API calls when component mounts)
const initializeData = async () => {
  try {
    loading.initializing = true;
    // Simulate API calls to fetch initial data
    await Promise.all([
      new Promise((resolve) => setTimeout(resolve, 1000)), // Fetch models
      new Promise((resolve) => setTimeout(resolve, 800)), // Fetch assistant types
      new Promise((resolve) => setTimeout(resolve, 600)), // Fetch other config data
    ]);
  } catch {
    message.error('初始化数据失败，请刷新页面重试');
  } finally {
    loading.initializing = false;
  }
};

// Call initialize function when component mounts
onMounted(() => {
  initializeData();
});

// Expansion state for collapsible sections
const dataSourceExpanded = ref(true);
const variableExpanded = ref(true);
const outputExpanded = ref(true);

// Form state
const formState = reactive({
  avatar: '',
  modelType: 'deePseeK v3',
  name: '',
  assistantType: '营销',
  description: '全面追踪，精准把握客户每一步，提高销售成功率',
  prompt:
    '#角色:您是一位擅长客户数据分析的CRM助理\n#工作任务: 根据提供的多个数据源JSON数据，进行客户数据分析和总结\n#输出内容:\n1. 客户信息及特性、联系方式、购买历史\n2. 需求分析报告 产品品类，购买偏好\n3. 规范记录沟通内容，下一步行动计划',
  dataPermission: '员工',
  employees: ['员工1', '员工2'],
  selfViewable: true,
  timeRange: '每月',
  executionFrequency: '每天',
  executionTime: null,
  viewers: ['jason', "Eli's"],
  notificationMethods: ['Lark', 'Email'],
  outputMarkdown:
    '# 一级标题\n内容\n\n## 二级标题\n内容\n\n### 三级标题\n内容\n\n|-|-|-|\n\n[表头1|表头2|表头3]\n内容内容内容内容\n1. 内容\n2. 内容\n- 内容\n- 内容',
  includeCharts: true,
  autoExport: false,
  exportFormats: ['excel'],
});

// Add beforeUpload function
const beforeUpload = (file: File) => {
  const isJpgOrPng = file.type === 'image/jpeg' || file.type === 'image/png';
  if (!isJpgOrPng) {
    message.error('You can only upload JPG/PNG file!');
  }
  const isLt2M = file.size / 1024 / 1024 < 2;
  if (!isLt2M) {
    message.error('Image must be smaller than 2MB!');
  }

  if (isJpgOrPng && isLt2M) {
    const reader = new FileReader();
    reader.addEventListener('load', (e) => {
      formState.avatar = e.target?.result as string;
    });
    reader.readAsDataURL(file);
  }
  return false; // Prevent auto upload
};

// Data sources
const selectedSources = ref([
  { id: '1', name: '客户分析数据' },
  { id: '2', name: '交易订单数据' },
]);

// Variables
const variables = ref([
  { name: '字段1', type: 'string', description: '请输入' },
  { name: '字段2', type: 'number', description: '请选择' },
  { name: '字段3', type: 'date', description: '请输入' },
]);

// Toggle expansion state for each section
const toggleDataSourceExpand = () => {
  dataSourceExpanded.value = !dataSourceExpanded.value;
};

const toggleVariableExpand = () => {
  variableExpanded.value = !variableExpanded.value;
};

const toggleOutputExpand = () => {
  outputExpanded.value = !outputExpanded.value;
};

// Function handlers
const handleSubmit = async () => {
  try {
    loading.submit = true;
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));
    message.success('AI 创建成功');
    router.push('/ai/assistants');
  } catch {
    message.error('创建失败，请重试');
  } finally {
    loading.submit = false;
  }
};

const handleCancel = () => {
  router.go(-1);
};

const showDataSourceModal = async () => {
  try {
    loading.dataSourceFetch = true;
    // Simulate API call to fetch data sources
    await new Promise((resolve) => setTimeout(resolve, 1000));
    message.info('打开数据源选择弹窗');
  } catch {
    message.error('获取数据源失败，请重试');
  } finally {
    loading.dataSourceFetch = false;
  }
};

const removeDataSource = (id: string) => {
  selectedSources.value = selectedSources.value.filter((source) => source.id !== id);
};

// Update addVariable with loading state
const addVariable = async () => {
  try {
    loading.variableOps = true;
    // Simulate API call for validation
    await new Promise((resolve) => setTimeout(resolve, 300));
    variables.value.push({
      name: '',
      type: 'string',
      description: '',
    });
  } finally {
    loading.variableOps = false;
  }
};

// Update deleteVariable with loading state
const deleteVariable = async (index: number) => {
  try {
    loading.variableOps = true;
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 300));
    variables.value.splice(index, 1);
  } finally {
    loading.variableOps = false;
  }
};

const handleAiPolish = async () => {
  try {
    loading.avatar = true;
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));
    message.success('AI润色成功');
  } catch {
    message.error('润色失败，请重试');
  } finally {
    loading.avatar = false;
  }
};

const generateAvatar = async () => {
  try {
    loading.avatar = true;
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));
    message.success('生成头像成功');
  } catch {
    message.error('生成头像失败，请重试');
  } finally {
    loading.avatar = false;
  }
};
</script>

<template>
  <div class="create-ai-page">
    <!-- Top section with tabs and buttons -->
    <div class="top-section">
      <CustomTabs :tabs="tabItems" :active-tab="activeTab" @tab-change="handleTabChange" />

      <div class="action-buttons">
        <a-button type="primary" @click="handleSubmit" :loading="loading.submit">确认发布</a-button>
        <a-button @click="handleCancel" :disabled="loading.submit">取消</a-button>
      </div>
    </div>

    <!-- Main content section with configurations -->
    <a-spin :spinning="loading.initializing" tip="加载中..." size="large" class="global-loading">
      <a-spin :spinning="loading.submit" tip="保存中...">
        <div class="main-content">
          <div class="left-panel">
            <!-- Basic Configuration Section -->
            <a-card class="config-card" :bordered="true">
              <template #title>
                <div class="card-title">基本配置</div>
              </template>

              <a-form
                :model="formState"
                layout="horizontal"
                :label-col="{ span: 6 }"
                :wrapper-col="{ span: 18 }"
              >
                <a-row :gutter="16">
                  <a-col :span="24">
                    <a-form-item label="助手头像">
                      <div class="avatar-uploader-container">
                        <a-upload
                          name="avatar"
                          list-type="picture-card"
                          class="avatar-uploader"
                          :show-upload-list="false"
                          action=""
                          :before-upload="beforeUpload"
                        >
                          <img
                            v-if="formState.avatar"
                            :src="formState.avatar"
                            alt="avatar"
                            class="avatar-image"
                          />
                          <div v-else>
                            <div class="ant-upload-text">上传</div>
                          </div>
                        </a-upload>
                        <a class="ai-generate-btn" @click="generateAvatar">
                          <a-spin :spinning="loading.avatar" size="small">
                            <span class="ai-icon">AI</span>
                            生成头像
                          </a-spin>
                        </a>
                      </div>
                    </a-form-item>
                  </a-col>
                </a-row>

                <a-row :gutter="16">
                  <a-col :span="24">
                    <a-form-item label="模型类型" required>
                      <a-select v-model:value="formState.modelType" placeholder="请选择模型类型">
                        <a-select-option value="deePseeK v3">deePseeK v3</a-select-option>
                        <a-select-option value="GPT-4">GPT-4</a-select-option>
                        <a-select-option value="Claude">Claude</a-select-option>
                      </a-select>
                    </a-form-item>
                  </a-col>
                </a-row>

                <a-row :gutter="16">
                  <a-col :span="24">
                    <a-form-item label="助理名称" required>
                      <a-input v-model:value="formState.name" placeholder="客户生命周期智能助理" />
                    </a-form-item>
                  </a-col>
                </a-row>

                <a-row :gutter="16">
                  <a-col :span="24">
                    <a-form-item label="助理类型">
                      <a-select
                        v-model:value="formState.assistantType"
                        placeholder="请选择助理类型"
                      >
                        <a-select-option value="营销">营销</a-select-option>
                        <a-select-option value="客服">客服</a-select-option>
                        <a-select-option value="销售">销售</a-select-option>
                        <a-select-option value="分析">分析</a-select-option>
                      </a-select>
                    </a-form-item>
                  </a-col>
                </a-row>

                <a-row :gutter="16">
                  <a-col :span="24">
                    <a-form-item label="助理简介" required>
                      <a-textarea
                        v-model:value="formState.description"
                        :rows="2"
                        placeholder="全面追踪，精准把握客户每一步，提高销售成功率"
                      />
                    </a-form-item>
                  </a-col>
                </a-row>

                <a-row :gutter="16">
                  <a-col :span="24">
                    <a-form-item label="提示词" required class="prompt-field">
                      <div class="textarea-wrapper">
                        <a-textarea
                          v-model:value="formState.prompt"
                          :rows="6"
                          placeholder="#角色:您是一位擅长客户数据分析的CRM助理&#10;#工作任务: 根据提供的多个数据源JSON数据，进行客户数据分析和总结&#10;#输出内容:&#10;1. 客户信息及特性、联系方式、购买历史&#10;2. 需求分析报告 产品品类，购买偏好&#10;3. 规范记录沟通内容，下一步行动计划"
                        />
                        <a-button
                          type="primary"
                          class="ai-polish-btn"
                          @click="handleAiPolish"
                          :loading="loading.avatar"
                        >
                          <span v-if="!loading.avatar">AI 润色</span>
                        </a-button>
                      </div>
                    </a-form-item>
                  </a-col>
                </a-row>
              </a-form>
            </a-card>

            <!-- Data Source Configuration Section -->
            <a-card class="config-card" :bordered="true">
              <template #title>
                <div class="card-title-with-action" @click="toggleDataSourceExpand">
                  <span>数据源配置</span>
                  <MaterialSymbolsKeyboardArrowDown v-if="!dataSourceExpanded" />
                  <MaterialSymbolsKeyboardArrowUp v-else />
                </div>
              </template>

              <div v-show="dataSourceExpanded">
                <a-form
                  :model="formState"
                  layout="horizontal"
                  :label-col="{ span: 6 }"
                  :wrapper-col="{ span: 18 }"
                >
                  <!-- 分析数据源 -->
                  <a-form-item label="分析数据源" required>
                    <div class="data-source-selection">
                      <a-tag
                        v-for="source in selectedSources"
                        :key="source.id"
                        closable
                        @close="removeDataSource(source.id)"
                      >
                        {{ source.name }}
                      </a-tag>
                      <a-button
                        type="dashed"
                        @click="showDataSourceModal"
                        :loading="loading.dataSourceFetch"
                      >
                        <MaterialSymbolsAdd v-if="!loading.dataSourceFetch" /> 添加数据源
                      </a-button>
                    </div>
                  </a-form-item>

                  <!-- 数据权限范围 -->
                  <a-form-item label="数据权限范围" required>
                    <div class="permission-selection">
                      <a-select
                        v-model:value="formState.dataPermission"
                        style="width: 30%"
                        placeholder="请选择数据权限类型"
                      >
                        <a-select-option value="员工">按员工</a-select-option>
                        <a-select-option value="路径1">路径1</a-select-option>
                        <a-select-option value="路径2">路径2</a-select-option>
                      </a-select>

                      <a-select
                        v-if="formState.dataPermission === '员工'"
                        v-model:value="formState.employees"
                        mode="multiple"
                        style="width: 68%"
                        placeholder="请选择员工"
                      >
                        <a-select-option value="员工1">员工1</a-select-option>
                        <a-select-option value="员工2">员工2</a-select-option>
                      </a-select>
                    </div>
                  </a-form-item>

                  <!-- 数据时间范围 -->
                  <a-form-item label="数据时间范围" required>
                    <div class="flex-column">
                      <a-select
                        v-model:value="formState.timeRange"
                        style="width: 100%; margin-bottom: 8px"
                        placeholder="请选择时间范围"
                      >
                        <a-select-option value="每天">每天</a-select-option>
                        <a-select-option value="每周">每周</a-select-option>
                        <a-select-option value="每月">每月</a-select-option>
                      </a-select>
                      <span class="hint-text">自定义输入整数值</span>
                    </div>
                  </a-form-item>
                </a-form>

                <!-- Switch to vertical layout for items after data time range -->
                <a-form :model="formState" layout="vertical">
                  <!-- 执行时间 -->
                  <a-form-item label="执行时间" required>
                    <div class="flex-row">
                      <a-select v-model:value="formState.executionFrequency" style="width: 50%">
                        <a-select-option value="每天">每天</a-select-option>
                        <a-select-option value="每周">每周</a-select-option>
                        <a-select-option value="每月">每月</a-select-option>
                      </a-select>
                      <a-time-picker
                        v-model:value="formState.executionTime"
                        format="HH:mm"
                        placeholder="请选择时间"
                        style="width: 50%"
                      />
                    </div>
                  </a-form-item>

                  <!-- 查看人员 -->
                  <a-form-item label="查看人员" required>
                    <div class="tag-selection">
                      <a-select
                        v-model:value="formState.viewers"
                        mode="multiple"
                        style="width: 100%"
                        placeholder="请选择查看人员"
                      >
                        <a-select-option value="jason">jason</a-select-option>
                        <a-select-option value="Eli's">Eli's</a-select-option>
                      </a-select>
                    </div>
                  </a-form-item>

                  <!-- 通知方式 -->
                  <a-form-item label="通知方式" required>
                    <div class="tag-selection">
                      <a-select
                        v-model:value="formState.notificationMethods"
                        mode="multiple"
                        style="width: 100%"
                        placeholder="请选择通知方式"
                      >
                        <a-select-option value="Lark">Lark</a-select-option>
                        <a-select-option value="Email">Email</a-select-option>
                      </a-select>
                    </div>
                  </a-form-item>
                </a-form>
              </div>
            </a-card>

            <!-- Variable Configuration Section -->
            <a-card class="config-card" :bordered="true">
              <template #title>
                <div class="card-title-with-action" @click="toggleVariableExpand">
                  <span>变量配置</span>
                  <MaterialSymbolsKeyboardArrowDown v-if="!variableExpanded" />
                  <MaterialSymbolsKeyboardArrowUp v-else />
                </div>
              </template>

              <div v-show="variableExpanded">
                <div class="table-variables">
                  <div class="table-header">
                    <div class="th field-name">字段名称</div>
                    <div class="th field-type">类型</div>
                    <div class="th field-desc">描述</div>
                    <div class="th field-actions">操作</div>
                  </div>

                  <div v-for="(variable, index) in variables" :key="index" class="table-row">
                    <div class="td field-name">
                      <a-input v-model:value="variable.name" placeholder="请输入" />
                    </div>
                    <div class="td field-type">
                      <a-select v-model:value="variable.type" placeholder="请选择">
                        <a-select-option value="string">文本</a-select-option>
                        <a-select-option value="number">数字</a-select-option>
                        <a-select-option value="date">日期</a-select-option>
                      </a-select>
                    </div>
                    <div class="td field-desc">
                      <a-input v-model:value="variable.description" placeholder="请输入" />
                    </div>
                    <div class="td field-actions">
                      <a-spin :spinning="loading.variableOps" size="small">
                        <MaterialSymbolsDeleteOutline
                          @click="deleteVariable(index)"
                          class="delete-icon"
                          :style="loading.variableOps ? 'cursor: not-allowed; opacity: 0.5;' : ''"
                        />
                      </a-spin>
                    </div>
                  </div>

                  <div class="add-variable">
                    <a-button
                      type="dashed"
                      block
                      @click="addVariable"
                      :loading="loading.variableOps"
                    >
                      <MaterialSymbolsAdd v-if="!loading.variableOps" /> 添加变量
                    </a-button>
                  </div>
                </div>
              </div>
            </a-card>
          </div>

          <div class="right-panel">
            <!-- Output Configuration Section -->
            <a-card class="config-card" :bordered="true">
              <template #title>
                <div class="card-title-with-action" @click="toggleOutputExpand">
                  <span>输出配置</span>
                  <MaterialSymbolsKeyboardArrowDown v-if="!outputExpanded" />
                  <MaterialSymbolsKeyboardArrowUp v-else />
                </div>
              </template>

              <div v-show="outputExpanded">
                <a-form :model="formState" layout="vertical">
                  <a-form-item label="文档输出" required>
                    <div class="markdown-editor">
                      <div class="editor-tabs">
                        <div
                          class="tab-item"
                          :class="{ active: editorTab === 'edit' }"
                          @click="editorTab = 'edit'"
                        >
                          编辑
                        </div>
                        <div
                          class="tab-item"
                          :class="{ active: editorTab === 'preview' }"
                          @click="editorTab = 'preview'"
                        >
                          预览
                        </div>
                        <div
                          class="tab-item"
                          :class="{ active: editorTab === 'split' }"
                          @click="editorTab = 'split'"
                        >
                          分屏
                        </div>
                      </div>

                      <div
                        class="editor-content"
                        v-if="editorTab === 'edit' || editorTab === 'split'"
                      >
                        <div class="editor-toolbar">
                          <span class="toolbar-item">B</span>
                          <span class="toolbar-item"><i>I</i></span>
                          <span class="toolbar-item"><u>U</u></span>
                          <span class="toolbar-item">H1</span>
                          <span class="toolbar-item">H2</span>
                          <span class="toolbar-item">H3</span>
                          <span class="toolbar-item">-</span>
                          <span class="toolbar-item">[x]</span>
                          <span class="toolbar-item">|表格|</span>
                          <span class="toolbar-item">🔗</span>
                          <span class="toolbar-item">📄</span>
                        </div>

                        <a-textarea
                          v-model:value="formState.outputMarkdown"
                          :rows="15"
                          placeholder="请输入Markdown内容"
                        />
                      </div>

                      <div
                        class="preview-content"
                        v-if="editorTab === 'preview' || editorTab === 'split'"
                      >
                        <div class="markdown-preview">
                          <h1>一级标题</h1>
                          <p>内容</p>

                          <h2>二级标题</h2>
                          <p>内容</p>

                          <h3>三级标题</h3>
                          <p>内容</p>

                          <hr />

                          <p>[表头1|表头2|表头3]</p>
                          <p>内容内容内容内容</p>
                          <ol>
                            <li>内容</li>
                            <li>内容</li>
                          </ol>
                          <ul>
                            <li>内容</li>
                            <li>内容</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </a-form-item>
                </a-form>
              </div>
            </a-card>
          </div>
        </div>
      </a-spin>
    </a-spin>
  </div>
</template>

<style scoped>
.create-ai-page {
  padding: 20px;
  background-color: white;
}

.top-section {
  margin-bottom: 20px;
}

.custom-tabs {
  margin-bottom: 16px;
}

.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 16px;
}

.main-content {
  display: flex;
  gap: 20px;
}

.left-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 50%;
}

.right-panel {
  width: 50%;
}

.config-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 500;
}

.icon-wrapper {
  margin-right: 8px;
}

.ai-generate {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #1890ff;
  cursor: pointer;
}

.ai-icon {
  display: inline-block;
  padding: 0 4px;
  margin-right: 4px;
  font-size: 12px;
  line-height: 16px;
  color: white;
  background-color: #1890ff;
  border-radius: 2px;
}

/* Add styles for the avatar uploader */
.avatar-uploader-container {
  display: flex;
  gap: 16px;
  align-items: center;
}

/* Add styles for horizontal form layout */
:deep(.ant-form-item-label) {
  text-align: right;
}

:deep(.ant-form-item) {
  margin-bottom: 16px;
}

/* Special handling for data source selection in horizontal layout */
:deep(.ant-form-item-control) .data-source-selection {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  width: 100%;
}

.avatar-uploader {
  width: 104px;
  height: 104px;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.ai-generate-btn {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #1890ff;
  cursor: pointer;
}

.card-title-with-action {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
}

.prompt-field {
  position: relative;
}

.textarea-wrapper {
  position: relative;
}

.ai-polish-btn {
  position: absolute;
  right: 8px;
  bottom: 8px;
  z-index: 1;
}

.data-source-selection {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.permission-selection {
  display: flex;
  gap: 8px;
}

.tag-selection {
  width: 100%;
}

.flex-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.flex-column {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hint-text {
  font-size: 12px;
  color: #999;
}

.table-variables {
  margin-bottom: 16px;
}

.table-header {
  display: flex;
  padding: 8px 0;
  font-weight: 500;
  background-color: #fafafa;
  border-bottom: 1px solid #e8e8e8;
}

.table-row {
  display: flex;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.th,
.td {
  padding: 0 8px;
}

.field-name {
  flex: 2;
}

.field-type {
  flex: 1;
}

.field-desc {
  flex: 2;
}

.field-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 50px;
}

.delete-icon {
  color: #ff4d4f;
  cursor: pointer;
}

.add-variable {
  margin-top: 16px;
}

.markdown-editor {
  border: 1px solid #d9d9d9;
  border-radius: 2px;
}

.editor-tabs {
  display: flex;
  border-bottom: 1px solid #d9d9d9;
}

.tab-item {
  padding: 8px 16px;
  cursor: pointer;
}

.tab-item.active {
  color: #1890ff;
  border-bottom: 2px solid #1890ff;
}

.editor-toolbar {
  display: flex;
  padding: 8px;
  background-color: #fafafa;
  border-bottom: 1px solid #d9d9d9;
}

.toolbar-item {
  padding: 4px 8px;
  margin-right: 4px;
  cursor: pointer;
  border-radius: 2px;
}

.toolbar-item:hover {
  background-color: #f0f0f0;
}

.preview-content {
  padding: 16px;
  background-color: #fff;
}

.markdown-preview h1,
.markdown-preview h2,
.markdown-preview h3 {
  margin-top: 16px;
  margin-bottom: 8px;
}

.markdown-preview h1 {
  font-size: 20px;
}

.markdown-preview h2 {
  font-size: 18px;
}

.markdown-preview h3 {
  font-size: 16px;
}

.markdown-preview p,
.markdown-preview ul,
.markdown-preview ol {
  margin-bottom: 8px;
}

.markdown-preview hr {
  margin: 16px 0;
  border: 0;
  border-top: 1px solid #eee;
}

/* Add styles for global loading */
.global-loading {
  width: 100%;
}

:deep(.ant-spin-nested-loading) {
  width: 100%;
}

:deep(.ant-spin-container) {
  width: 100%;
}
</style>
