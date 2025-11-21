import { computed, ref } from 'vue';

import {
  getAllAIAssistantsApi,
  getAllAssistantTypesApi,
  getAllPersonnelApi,
  getCountriesApi,
  getSubscriptionNotificationMethodsApi,
  getWarehouseAgentDetailApi,
  getWarehouseAgentsApi,
  getWarehouseCrmUserDetailApi,
  getWarehouseCrmUsersApi,
  getWarehouseUserDetailApi,
  getWarehouseUsersApi,
} from '#/api';

export function useSubscriptionOptions() {
  // Raw options from API
  const assistantTypeOptions = ref<Array<{ label: string; value: string }>>([]);
  const allAssistants = ref<any[]>([]);
  const responsibleOptions = ref<Array<{ email?: string; label: string; value: string }>>([]);
  const notificationMethodOptions = ref<Array<{ label: string; value: string }>>([]);
  const customerOptions = ref<Array<{ label: string; value: string }>>([]);
  const userOptions = ref<Array<{ label: string; value: string }>>([]);
  const agentOptions = ref<Array<{ label: string; value: string }>>([]);
  const countryOptions = ref<Array<{ label: string; value: string }>>([]);

  // 搜索加载状态
  const customerSearchLoading = ref(false);
  const userSearchLoading = ref(false);
  const agentSearchLoading = ref(false);

  // 搜索防抖定时器
  const customerSearchTimer = ref<NodeJS.Timeout | null>(null);
  const userSearchTimer = ref<NodeJS.Timeout | null>(null);
  const agentSearchTimer = ref<NodeJS.Timeout | null>(null);

  const assistantOptionsByType = computed(() => {
    const grouped: Record<string, Array<{ label: string; value: string }>> = {};

    // "All" type includes all assistants
    grouped.all = allAssistants.value.map((item) => ({
      label: item.name,
      value: item.id,
    }));

    // Group by assistant_type_id
    allAssistants.value.forEach((assistant) => {
      const typeId = assistant.assistant_type_id;
      if (typeId) {
        if (!grouped[typeId]) {
          grouped[typeId] = [];
        }
        grouped[typeId].push({
          label: assistant.name,
          value: assistant.id,
        });
      }
    });
    return grouped;
  });

  const getAssistantName = (assistantId: string) => {
    return (
      assistantOptionsByType.value.all?.find((a) => a.value === assistantId)?.label || assistantId
    );
  };

  // Load responsible options
  async function loadResponsibleOptions() {
    try {
      const res = await getAllPersonnelApi({ status: true });
      responsibleOptions.value = (res || []).map((u: any) => ({
        label: u.username || u.email || `人员${u.id}`,
        value: String(u.id),
        email: u.email,
      }));
    } catch (error) {
      console.error('Failed to load responsible options:', error);
      responsibleOptions.value = [];
    }
  }

  // Load notification method options
  async function loadNotificationMethodOptions() {
    try {
      const res = await getSubscriptionNotificationMethodsApi();
      notificationMethodOptions.value = (res || []).map((item: any) => ({
        label: item.name,
        value: String(item.id),
      }));
    } catch (error) {
      console.error('Failed to load notification method options:', error);
      notificationMethodOptions.value = [];
    }
  }

  // Load data range limit options (使用分页接口，只加载前100条以减少初始加载时间)
  async function loadDataRangeLimitOptions() {
    try {
      const [usersRes, agentsRes, countriesRes] = await Promise.all([
        getWarehouseUsersApi({ status: true, page: 1, page_size: 100 }),
        getWarehouseAgentsApi({ status: true, page: 1, page_size: 100 }),
        getCountriesApi(),
      ]);

      customerOptions.value = ((usersRes?.items || []) as any[]).map((user: any) => ({
        label: user.name || user.username || user.email || `用户${user.id}`,
        value: user.id,
      }));

      agentOptions.value = ((agentsRes?.items || []) as any[]).map((agent: any) => ({
        label: agent.name || agent.contact_person || `代理${agent.id}`,
        value: agent.id,
      }));

      countryOptions.value = (countriesRes.countries || []).map((country: any) => ({
        label: country.mark,
        value: country.name,
      }));
    } catch (error) {
      console.error('Failed to load data range limit options:', error);
      customerOptions.value = [];
      agentOptions.value = [];
      countryOptions.value = [];
    }
  }
  async function loadUserOptions() {
    try {
      const res = await getWarehouseCrmUsersApi({ status: true, page: 1, page_size: 100 });
      userOptions.value = ((res?.items || []) as any[]).map((user: any) => ({
        label: user.name || user.username || user.email || `用户${user.id}`,
        value: user.id,
      }));
    } catch (error) {
      console.error('Failed to load user options:', error);
      userOptions.value = [];
    }
  }

  // 搜索客户（远程搜索）
  async function searchCustomers(keyword: string) {
    if (customerSearchTimer.value) {
      clearTimeout(customerSearchTimer.value);
    }
    customerSearchTimer.value = setTimeout(async () => {
      try {
        customerSearchLoading.value = true;
        const keywordTrimmed = keyword?.trim() || '';
        // 如果关键词为空，加载初始数据（前100条）
        if (keywordTrimmed) {
          const res = await getWarehouseUsersApi({
            keyword: keywordTrimmed,
            status: true,
            page: 1,
            page_size: 50,
          });
          customerOptions.value = ((res?.items || []) as any[]).map((user: any) => ({
            label: user.name || user.username || user.email || `用户${user.id}`,
            value: user.id,
          }));
        } else {
          const res = await getWarehouseUsersApi({ status: true, page: 1, page_size: 100 });
          customerOptions.value = ((res?.items || []) as any[]).map((user: any) => ({
            label: user.name || user.username || user.email || `用户${user.id}`,
            value: user.id,
          }));
        }
      } catch (error) {
        console.error('Failed to search customers:', error);
        customerOptions.value = [];
      } finally {
        customerSearchLoading.value = false;
      }
    }, 300);
  }

  // 搜索员工（远程搜索）
  async function searchUsers(keyword: string) {
    if (userSearchTimer.value) {
      clearTimeout(userSearchTimer.value);
    }
    userSearchTimer.value = setTimeout(async () => {
      try {
        userSearchLoading.value = true;
        const keywordTrimmed = keyword?.trim() || '';
        // 如果关键词为空，加载初始数据（前100条）
        if (keywordTrimmed) {
          const res = await getWarehouseCrmUsersApi({
            keyword: keywordTrimmed,
            status: true,
            page: 1,
            page_size: 50,
          });
          userOptions.value = ((res?.items || []) as any[]).map((user: any) => ({
            label: user.name || user.username || user.email || `用户${user.id}`,
            value: user.id,
          }));
        } else {
          const res = await getWarehouseCrmUsersApi({ status: true, page: 1, page_size: 100 });
          userOptions.value = ((res?.items || []) as any[]).map((user: any) => ({
            label: user.name || user.username || user.email || `用户${user.id}`,
            value: user.id,
          }));
        }
      } catch (error) {
        console.error('Failed to search users:', error);
        userOptions.value = [];
      } finally {
        userSearchLoading.value = false;
      }
    }, 300);
  }

  // 搜索代理（远程搜索）
  async function searchAgents(keyword: string) {
    if (agentSearchTimer.value) {
      clearTimeout(agentSearchTimer.value);
    }
    agentSearchTimer.value = setTimeout(async () => {
      try {
        agentSearchLoading.value = true;
        const keywordTrimmed = keyword?.trim() || '';
        // 如果关键词为空，加载初始数据（前100条）
        if (keywordTrimmed) {
          const res = await getWarehouseAgentsApi({
            keyword: keywordTrimmed,
            status: true,
            page: 1,
            page_size: 50,
          });
          agentOptions.value = ((res?.items || []) as any[]).map((agent: any) => ({
            label: agent.name || agent.contact_person || `代理${agent.id}`,
            value: agent.id,
          }));
        } else {
          const res = await getWarehouseAgentsApi({ status: true, page: 1, page_size: 100 });
          agentOptions.value = ((res?.items || []) as any[]).map((agent: any) => ({
            label: agent.name || agent.contact_person || `代理${agent.id}`,
            value: agent.id,
          }));
        }
      } catch (error) {
        console.error('Failed to search agents:', error);
        agentOptions.value = [];
      } finally {
        agentSearchLoading.value = false;
      }
    }, 300);
  }

  // 加载指定ID的用户信息（用于编辑时确保已选中的用户能正确显示）
  async function loadCustomerByIds(ids: string[]) {
    if (!ids || ids.length === 0) return;
    const existingIds = new Set(customerOptions.value.map((opt) => opt.value));
    const missingIds = ids.filter((id) => !existingIds.has(id));
    if (missingIds.length === 0) return;

    try {
      const promises = missingIds.map((id) => getWarehouseUserDetailApi(id).catch(() => null));
      const results = await Promise.all(promises);
      const newOptions = results
        .filter((item): item is any => item !== null)
        .map((user: any) => ({
          label: user.name || user.username || user.email || `用户${user.id}`,
          value: user.id,
        }));
      customerOptions.value = [...customerOptions.value, ...newOptions];
    } catch (error) {
      console.error('Failed to load customers by ids:', error);
    }
  }

  // 加载指定ID的员工信息
  async function loadUserByIds(ids: string[]) {
    if (!ids || ids.length === 0) return;
    const existingIds = new Set(userOptions.value.map((opt) => opt.value));
    const missingIds = ids.filter((id) => !existingIds.has(id));
    if (missingIds.length === 0) return;

    try {
      const promises = missingIds.map((id) => getWarehouseCrmUserDetailApi(id).catch(() => null));
      const results = await Promise.all(promises);
      const newOptions = results
        .filter((item): item is any => item !== null)
        .map((user: any) => ({
          label: user.name || user.username || user.email || `用户${user.id}`,
          value: user.id,
        }));
      userOptions.value = [...userOptions.value, ...newOptions];
    } catch (error) {
      console.error('Failed to load users by ids:', error);
    }
  }

  // 加载指定ID的代理信息
  async function loadAgentByIds(ids: string[]) {
    if (!ids || ids.length === 0) return;
    const existingIds = new Set(agentOptions.value.map((opt) => opt.value));
    const missingIds = ids.filter((id) => !existingIds.has(id));
    if (missingIds.length === 0) return;

    try {
      const promises = missingIds.map((id) => getWarehouseAgentDetailApi(id).catch(() => null));
      const results = await Promise.all(promises);
      const newOptions = results
        .filter((item): item is any => item !== null)
        .map((agent: any) => ({
          label: agent.name || agent.contact_person || `代理${agent.id}`,
          value: agent.id,
        }));
      agentOptions.value = [...agentOptions.value, ...newOptions];
    } catch (error) {
      console.error('Failed to load agents by ids:', error);
    }
  }

  // Unified loading function
  async function loadOptions() {
    try {
      // Load assistants and their types
      const [types, assistants] = await Promise.all([
        getAllAssistantTypesApi(),
        getAllAIAssistantsApi(),
      ]);

      allAssistants.value = assistants || [];
      assistantTypeOptions.value = [
        { label: '全部类型', value: '' },
        ...(types || []).map((item: any) => ({
          label: item.name,
          value: item.id,
        })),
      ];

      // Load all other options
      await Promise.all([
        loadResponsibleOptions(),
        loadNotificationMethodOptions(),
        loadDataRangeLimitOptions(),
        loadUserOptions(),
      ]);
    } catch (error) {
      console.error('Failed to load options:', error);
    }
  }

  return {
    // Reactive Options
    assistantTypeOptions,
    assistantOptionsByType,
    responsibleOptions,
    notificationMethodOptions,
    customerOptions,
    userOptions,
    agentOptions,
    countryOptions,

    // Loading States
    customerSearchLoading,
    userSearchLoading,
    agentSearchLoading,

    // Methods
    loadOptions,
    loadResponsibleOptions,
    loadNotificationMethodOptions,
    loadDataRangeLimitOptions,
    getAssistantName,
    searchCustomers,
    searchUsers,
    searchAgents,
    loadCustomerByIds,
    loadUserByIds,
    loadAgentByIds,
  };
}
