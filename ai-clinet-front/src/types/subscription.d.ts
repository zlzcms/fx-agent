// 订阅类型定义
export interface Subscription {
    id: string;
    assistant_id: string;
    user_id: number;
    name: string;
    subscription_type: string;
    execution_frequency: string;
    execution_time?: string;
    execution_minutes?: number;
    execution_hours?: number;
    execution_weekday?: string;
    execution_weekly_time?: string;
    execution_day?: string;
    execution_monthly_time?: string;
    setting?: Record<string, any>;
    created_at?: string;
    updated_at?: string;
}


// 订阅列表响应
export interface SubscriptionListResponse {
    data: Subscription[];
    total?: number;
    page?: number;
    size?: number;
}

// 执行频率枚举
export enum ExecutionFrequency {
    MINUTES = 'minutes',
    HOURLY = 'hourly',
    DAILY = 'daily',
    WEEKLY = 'weekly',
    MONTHLY = 'monthly'
}

// 订阅类型枚举
export enum SubscriptionType {
    REPORT = 'report',
    ALERT = 'alert',
    ANALYSIS = 'analysis'
}