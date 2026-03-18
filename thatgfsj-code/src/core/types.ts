/**
 * Type definitions for Thatgfsj Code
 */

export type Role = 'system' | 'user' | 'assistant' | 'tool';

export interface ChatMessage {
  role: Role;
  content: string;
  name?: string;
  tool_calls?: ToolCall[];
  tool_call_id?: string;
}

export interface ToolCall {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string;
  };
}

export interface AIResponse {
  content: string;
  role: 'assistant';
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  tool_calls?: ToolCall[];
}

export interface AIConfig {
  model: string;
  apiKey?: string;
  temperature?: number;
  maxTokens?: number;
  baseUrl?: string;
  provider?: 'minimax' | 'openai' | 'siliconflow' | 'anthropic' | 'custom';
}

export interface Tool {
  name: string;
  description: string;
  parameters: ToolParameter[];
  execute: (params: Record<string, any>, ctx?: ToolContext) => Promise<ToolResult>;
}

export interface ToolContext {
  sessionId?: string;
  confirmAction?: (msg: string) => Promise<boolean>;
}

export interface ToolParameter {
  name: string;
  type: string;
  description: string;
  required: boolean;
}

export interface ToolResult {
  success: boolean;
  output?: string;
  error?: string;
  data?: any;
}

export interface Session {
  id: string;
  messages: ChatMessage[];
  createdAt: Date;
  lastActiveAt: Date;
}

export interface Config {
  model: string;
  apiKey: string;
  temperature: number;
  maxTokens: number;
  provider?: AIConfig['provider'];
  baseUrl?: string;
}

// Provider configurations
export const PROVIDERS = {
  minimax: {
    name: 'MiniMax',
    baseUrl: 'https://api.minimax.chat/v1',
    defaultModel: 'MiniMax-M2.5',
    envKeys: ['MINIMAX_API_KEY', 'OPENAI_API_KEY']
  },
  siliconflow: {
    name: 'SiliconFlow (硅基流动)',
    baseUrl: 'https://api.siliconflow.cn/v1',
    defaultModel: 'Qwen/Qwen2.5-7B-Instruct',
    envKeys: ['SILICONFLOW_API_KEY', 'OPENAI_API_KEY']
  },
  openai: {
    name: 'OpenAI',
    baseUrl: 'https://api.openai.com/v1',
    defaultModel: 'gpt-4o-mini',
    envKeys: ['OPENAI_API_KEY']
  },
  anthropic: {
    name: 'Anthropic',
    baseUrl: 'https://api.anthropic.com/v1',
    defaultModel: 'claude-3-haiku-20240307',
    envKeys: ['ANTHROPIC_API_KEY']
  }
} as const;
