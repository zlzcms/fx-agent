/**
 * @Author: zhujinlong
 * @Date:   2025-06-16 20:19:44
 * @Last Modified by:   zhujinlong
 * @Last Modified time: 2025-06-16 20:28:56
 */
/**
 * Markdown编辑器组件相关类型定义
 */

// 组件相关类型
export interface DocumentConfigItem {
  template: string;
  content: string;
}

export interface MarkdownEditorProps {
  modelValue?: DocumentConfigItem;
  placeholder?: string;
  height?: number | string;
  readonly?: boolean;
}

export interface MarkdownEditorEmits {
  (e: 'change' | 'update:modelValue', value: DocumentConfigItem): void;
}

// 文档模板选项 - 需要在组件中动态生成以支持i18n
export const DOCUMENT_TEMPLATE_KEYS = [
  { labelKey: 'page.components.markdownEditor.standardReport', value: 'standard' },
  { labelKey: 'page.components.markdownEditor.simpleReport', value: 'simple' },
  { labelKey: 'page.components.markdownEditor.detailedReport', value: 'detailed' },
  { labelKey: 'page.components.markdownEditor.customReport', value: 'custom' },
];

// 英文模板内容
export const DEFAULT_TEMPLATES_EN = {
  standard: `# Data Analysis Report

## Overview
This report analyzes selected data sources to provide key metrics and trend insights.

## Data Overview
- Data Source: [[Data Source Name]]
- Analysis Time Range: [[Start Time]] to [[End Time]]
- Total Data Volume: [[Record Count]]

## Key Findings
### Main Metrics
- Metric 1: [[Value]] ([[Change Trend]])
- Metric 2: [[Value]] ([[Change Trend]])
- Metric 3: [[Value]] ([[Change Trend]])

### Trend Analysis
[[Describe main trends and patterns]]

## Detailed Analysis
### Data Distribution
[[Data distribution description]]

### Anomaly Detection
[[Anomaly data point analysis]]

## Conclusions and Recommendations
### Main Conclusions
1. [[Conclusion 1]]
2. [[Conclusion 2]]
3. [[Conclusion 3]]

### Action Recommendations
1. [[Recommendation 1]]
2. [[Recommendation 2]]
3. [[Recommendation 3]]

---
*Report Generated: [[Generation Time]]*`,

  simple: `# Simple Analysis Report

## Data Overview
- Data Source: [[Data Source Name]]
- Time Range: [[Time Range]]

## Key Metrics
| Metric | Value | Change |
|--------|-------|--------|
| Metric 1 | [[Value]] | [[Change]] |
| Metric 2 | [[Value]] | [[Change]] |
| Metric 3 | [[Value]] | [[Change]] |

## Main Findings
[[Brief description of main findings]]

## Recommendations
- [[Recommendation 1]]
- [[Recommendation 2]]
- [[Recommendation 3]]`,

  detailed: `# Detailed Data Analysis Report

## Executive Summary
[[Report summary]]

## 1. Background and Objectives
### 1.1 Analysis Background
[[Analysis background description]]

### 1.2 Analysis Objectives
- Objective 1: [[Description]]
- Objective 2: [[Description]]
- Objective 3: [[Description]]

## 2. Data Description
### 2.1 Data Sources
- **Data Source**: [[Data Source Name]]
- **Data Range**: [[Time Range]]
- **Data Volume**: [[Record Count]]

### 2.2 Data Quality
- **Completeness**: [[Completeness Assessment]]
- **Accuracy**: [[Accuracy Assessment]]
- **Consistency**: [[Consistency Assessment]]

## 3. Analysis Methods
### 3.1 Analysis Framework
[[Analysis framework description]]

### 3.2 Analysis Tools
[[Analysis tools and methods used]]

## 4. Detailed Analysis Results
### 4.1 Descriptive Statistics
[[Basic statistical information]]

### 4.2 Trend Analysis
[[Trend analysis results]]

### 4.3 Correlation Analysis
[[Correlation analysis results]]

### 4.4 Anomaly Detection
[[Anomaly detection results]]

## 5. Key Insights
### 5.1 Main Findings
1. [[Finding 1]]
2. [[Finding 2]]
3. [[Finding 3]]

### 5.2 Business Impact
[[Business impact analysis]]

## 6. Risks and Opportunities
### 6.1 Potential Risks
- [[Risk 1]]
- [[Risk 2]]

### 6.2 Development Opportunities
- [[Opportunity 1]]
- [[Opportunity 2]]

## 7. Recommendations and Action Plan
### 7.1 Short-term Recommendations
1. [[Short-term recommendation 1]]
2. [[Short-term recommendation 2]]

### 7.2 Long-term Recommendations
1. [[Long-term recommendation 1]]
2. [[Long-term recommendation 2]]

### 7.3 Action Plan
| Action Item | Responsible | Timeline | Priority |
|-------------|-------------|----------|----------|
| [[Action 1]] | [[Responsible]] | [[Time]] | [[Priority]] |
| [[Action 2]] | [[Responsible]] | [[Time]] | [[Priority]] |

## 8. Appendix
### 8.1 Data Dictionary
[[Data field descriptions]]

### 8.2 Technical Notes
[[Technical implementation notes]]

---
*Report Generated: [[Generation Time]]*
*Analyst: [[Analyst Name]]*`,

  custom: `# Custom Report Template

Please write your report content according to your needs...

## Suggested Report Structure:
1. Title and Overview
2. Data Description
3. Analysis Results
4. Conclusions and Recommendations

You can use the following Markdown syntax:
- **Bold text**
- *Italic text*
- \`Code\`
- [Links](http://example.com)
- Tables, lists, etc.

> Tip: You can use the toolbar in the editor to quickly insert common Markdown syntax.`,
};

// 中文模板内容
export const DEFAULT_TEMPLATES_ZH = {
  standard: `# 数据分析报告

## 概述
本报告基于选定的数据源进行分析，提供关键指标和趋势洞察。

## 数据概况
- 数据来源：[[数据源名称]]
- 分析时间范围：[[开始时间]] 至 [[结束时间]]
- 数据总量：[[记录数量]]

## 关键发现
### 主要指标
- 指标1：[[数值]] ([[变化趋势]])
- 指标2：[[数值]] ([[变化趋势]])
- 指标3：[[数值]] ([[变化趋势]])

### 趋势分析
[[描述主要趋势和模式]]

## 详细分析
### 数据分布
[[数据分布情况描述]]

### 异常检测
[[异常数据点分析]]

## 结论与建议
### 主要结论
1. [[结论1]]
2. [[结论2]]
3. [[结论3]]

### 行动建议
1. [[建议1]]
2. [[建议2]]
3. [[建议3]]

---
*报告生成时间：[[生成时间]]*`,

  simple: `# 简洁分析报告

## 数据概况
- 数据源：[[数据源名称]]
- 时间范围：[[时间范围]]

## 关键指标
| 指标 | 数值 | 变化 |
|------|------|------|
| 指标1 | [[数值]] | [[变化]] |
| 指标2 | [[数值]] | [[变化]] |
| 指标3 | [[数值]] | [[变化]] |

## 主要发现
[[简要描述主要发现]]

## 建议
- [[建议1]]
- [[建议2]]
- [[建议3]]`,

  detailed: `# 详细数据分析报告

## 执行摘要
[[报告摘要]]

## 1. 背景与目标
### 1.1 分析背景
[[分析背景描述]]

### 1.2 分析目标
- 目标1：[[描述]]
- 目标2：[[描述]]
- 目标3：[[描述]]

## 2. 数据说明
### 2.1 数据来源
- **数据源**：[[数据源名称]]
- **数据范围**：[[时间范围]]
- **数据量**：[[记录数量]]

### 2.2 数据质量
- **完整性**：[[完整性评估]]
- **准确性**：[[准确性评估]]
- **一致性**：[[一致性评估]]

## 3. 分析方法
### 3.1 分析框架
[[分析框架描述]]

### 3.2 分析工具
[[使用的分析工具和方法]]

## 4. 详细分析结果
### 4.1 描述性统计
[[基础统计信息]]

### 4.2 趋势分析
[[趋势分析结果]]

### 4.3 相关性分析
[[相关性分析结果]]

### 4.4 异常检测
[[异常检测结果]]

## 5. 关键洞察
### 5.1 主要发现
1. [[发现1]]
2. [[发现2]]
3. [[发现3]]

### 5.2 业务影响
[[业务影响分析]]

## 6. 风险与机会
### 6.1 潜在风险
- [[风险1]]
- [[风险2]]

### 6.2 发展机会
- [[机会1]]
- [[机会2]]

## 7. 建议与行动计划
### 7.1 短期建议
1. [[短期建议1]]
2. [[短期建议2]]

### 7.2 长期建议
1. [[长期建议1]]
2. [[长期建议2]]

### 7.3 行动计划
| 行动项 | 负责人 | 时间节点 | 优先级 |
|--------|--------|----------|--------|
| [[行动1]] | [[负责人]] | [[时间]] | [[优先级]] |
| [[行动2]] | [[负责人]] | [[时间]] | [[优先级]] |

## 8. 附录
### 8.1 数据字典
[[数据字段说明]]

### 8.2 技术说明
[[技术实现说明]]

---
*报告生成时间：[[生成时间]]*
*分析师：[[分析师姓名]]*`,

  custom: `# 自定义报告模板

请根据您的需求编写报告内容...

## 建议的报告结构：
1. 标题和概述
2. 数据说明
3. 分析结果
4. 结论和建议

您可以使用以下 Markdown 语法：
- **粗体文本**
- *斜体文本*
- \`代码\`
- [链接](http://example.com)
- 表格、列表等

> 提示：您可以在编辑器中使用工具栏快速插入常用的 Markdown 语法。`,
};

// 根据语言获取模板内容的函数
export function getDefaultTemplates(locale: string = 'en') {
  return locale.startsWith('zh') ? DEFAULT_TEMPLATES_ZH : DEFAULT_TEMPLATES_EN;
}
