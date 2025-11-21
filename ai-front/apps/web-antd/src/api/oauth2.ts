/**
 * @Author: zhujinlong
 * @Date:   2025-06-07 18:18:33
 * @Last Modified by:   zhujinlong
 * @Last Modified time: 2025-06-08 12:18:57
 */
import { requestClient } from '#/api/request';

export interface OAuth2CallBackParams {
  code: string;
  state?: string;
  code_verifier?: string;
}

export async function getOAuth2LinuxDo() {
  return requestClient.get<string>('/api/v1/oauth2/linux-do');
}

export async function getOAuth2LinuxDoCallback(params: OAuth2CallBackParams) {
  return requestClient.get('/api/v1/oauth2/linux-do/callback', { params });
}
