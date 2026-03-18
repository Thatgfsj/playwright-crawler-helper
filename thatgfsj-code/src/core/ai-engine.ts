/**
 * AI Engine - Core AI interaction module
 * Supports multiple providers: MiniMax, SiliconFlow, OpenAI, Anthropic
 */

import chalk from 'chalk';
import { ChatMessage, AIResponse, AIConfig, Tool, ToolCall } from './types.js';

export class AIEngine {
  private config: AIConfig;
  private tools: Map<string, Tool> = new Map();

  constructor(config: AIConfig) {
    this.config = config;
  }

  /**
   * Register tools for function calling
   */
  registerTool(tool: Tool) {
    this.tools.set(tool.name, tool);
  }

  /**
   * Unregister a tool
   */
  unregisterTool(name: string) {
    this.tools.delete(name);
  }

  /**
   * Get registered tools for API
   */
  private getToolsForAPI() {
    return Array.from(this.tools.values()).map(tool => ({
      type: 'function' as const,
      function: {
        name: tool.name,
        description: tool.description,
        parameters: {
          type: 'object',
          properties: tool.parameters.reduce((acc, p) => {
            acc[p.name] = { type: p.type, description: p.description };
            return acc;
          }, {} as any),
          required: tool.parameters.filter(p => p.required).map(p => p.name)
        }
      }
    }));
  }

  /**
   * Send a chat request to AI
   */
  async chat(messages: ChatMessage[], maxIterations: number = 5): Promise<AIResponse> {
    let currentMessages = [...messages];
    let iterations = 0;

    while (iterations < maxIterations) {
      iterations++;
      const response = await this.makeRequest(currentMessages);

      // Check for tool calls
      if (response.tool_calls && response.tool_calls.length > 0) {
        // Add assistant message with tool calls
        currentMessages.push({
          role: 'assistant',
          content: response.content,
          tool_calls: response.tool_calls,
          reasoning_content: response.reasoning_content
        });

        // Execute each tool call
        for (const toolCall of response.tool_calls) {
          const result = await this.executeToolCall(toolCall);
          
          // Add tool result as message
          currentMessages.push({
            role: 'tool',
            content: result.output || result.error || '',
            tool_call_id: toolCall.id,
            name: toolCall.function.name
          });
        }

        // Continue loop to get AI response with tool results
        continue;
      }

      // No tool calls, return the response
      return response;
    }

    // Max iterations reached
    return {
      content: 'Agent loop exceeded maximum iterations. Please try a simpler request.',
      role: 'assistant'
    };
  }

  /**
   * Execute a tool call
   */
  private async executeToolCall(toolCall: ToolCall): Promise<{ output?: string; error?: string }> {
    const { name, arguments: args } = toolCall.function;
    const tool = this.tools.get(name);

    if (!tool) {
      return { error: `Tool "${name}" not found` };
    }

    try {
      const params = JSON.parse(args);
      
      // Create context with confirm callback
      const ctx = {
        confirmAction: async (msg: string): Promise<boolean> => {
          // In CLI mode, we need to prompt user for confirmation
          // For now, we'll auto-deny dangerous commands and auto-allow safe ones
          console.log(chalk.yellow(`\n⚠️  Tool wants to execute: ${msg}`));
          return false; // Default deny - user must confirm
        }
      };
      
      const result = await tool.execute(params, ctx);
      return {
        output: result.success ? (result.output || JSON.stringify(result.data)) : undefined,
        error: result.error
      };
    } catch (error: any) {
      return { error: `Tool execution failed: ${error.message}` };
    }
  }

  /**
   * Make API request
   */
  private async makeRequest(messages: ChatMessage[]): Promise<AIResponse> {
    const apiKey = this.config.apiKey || this.getApiKey();
    
    if (!apiKey) {
      return this.mockResponse(messages);
    }

    // Use Anthropic format for Anthropic and MiniMax providers
    const isAnthropicFormat = this.config.provider === 'anthropic' || this.config.provider === 'minimax';
    const isStreaming = false;

    try {
      const requestBody = isAnthropicFormat
        ? this.buildAnthropicRequest(messages)
        : this.buildOpenAIRequest(messages, isStreaming);

      const headers: Record<string, string> = isAnthropicFormat
        ? {
            'Content-Type': 'application/json',
            'x-api-key': apiKey,
            'anthropic-version': '2023-06-01'
          }
        : {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`
          };

      const response = await fetch(`${this.config.baseUrl}/chat/completions`, {
        method: 'POST',
        headers,
        body: JSON.stringify(requestBody)
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`API Error: ${response.status} - ${error}`);
      }

      const data = await response.json();

      if (isAnthropicFormat) {
        return {
          content: data.content[0]?.text || '',
          role: 'assistant',
          usage: {
            prompt_tokens: data.usage?.input_tokens || 0,
            completion_tokens: data.usage?.output_tokens || 0,
            total_tokens: (data.usage?.input_tokens || 0) + (data.usage?.output_tokens || 0)
          }
        };
      }

      return {
        content: data.choices[0]?.message?.content || '',
        role: 'assistant',
        tool_calls: data.choices[0]?.message?.tool_calls,
        usage: data.usage,
        reasoning_content: data.choices[0]?.message?.reasoning_content
      };
    } catch (error: any) {
      console.warn('API call failed, using mock response:', error.message);
      return this.mockResponse(messages);
    }
  }

  /**
   * Build OpenAI-compatible request body
   */
  private buildOpenAIRequest(messages: ChatMessage[], stream: boolean) {
    const tools = this.getToolsForAPI();
    
    return {
      model: this.config.model || 'Qwen/Qwen2.5-7B-Instruct',
      messages: messages.map(m => ({
        role: m.role,
        content: m.content,
        name: m.name,
        tool_call_id: m.tool_call_id,
        tool_calls: m.tool_calls,
        reasoning_content: m.reasoning_content
      })),
      temperature: this.config.temperature || 0.7,
      max_tokens: this.config.maxTokens || 4096,
      stream,
      ...(tools.length > 0 && { tools })
    };
  }

  /**
   * Build Anthropic request body
   */
  private buildAnthropicRequest(messages: ChatMessage[]) {
    // Convert messages to Anthropic format
    const anthropicMessages = messages
      .filter(m => m.role !== 'system')
      .map(m => ({
        role: m.role === 'assistant' ? 'assistant' : 'user',
        content: m.content
      }));

    return {
      model: this.config.model || 'claude-3-haiku-20240307',
      messages: anthropicMessages,
      max_tokens: this.config.maxTokens || 4096,
      temperature: this.config.temperature || 0.7
    };
  }

  /**
   * Get API key from environment based on provider
   */
  private getApiKey(): string {
    const provider = this.config.provider || 'siliconflow';
    
    const envKeys: Record<string, string[]> = {
      siliconflow: ['SILICONFLOW_API_KEY', 'OPENAI_API_KEY'],
      minimax: ['MINIMAX_API_KEY', 'OPENAI_API_KEY'],
      openai: ['OPENAI_API_KEY'],
      anthropic: ['ANTHROPIC_API_KEY']
    };

    for (const key of envKeys[provider] || []) {
      if (process.env[key]) return process.env[key];
    }

    return '';
  }

  /**
   * Stream chat response
   */
  async *streamChat(messages: ChatMessage[]): AsyncGenerator<string> {
    const apiKey = this.config.apiKey || this.getApiKey();
    
    if (!apiKey) {
      const response = await this.mockResponse(messages);
      for (const char of response.content) {
        yield char;
        await new Promise(r => setTimeout(r, 20));
      }
      return;
    }

    // Use Anthropic format for Anthropic and MiniMax providers
    const isAnthropicFormat = this.config.provider === 'anthropic' || this.config.provider === 'minimax';

    const requestBody = isAnthropicFormat
      ? this.buildAnthropicRequest(messages)
      : this.buildOpenAIRequest(messages, true);

    const headers: Record<string, string> = isAnthropicFormat
      ? {
          'Content-Type': 'application/json',
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01'
        }
      : {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`
        };

    const response = await fetch(`${this.config.baseUrl}/chat/completions`, {
      method: 'POST',
      headers,
      body: JSON.stringify(requestBody)
    });

    if (!response.ok || !response.body) {
      throw new Error(`Stream Error: ${response.status}`);
    }

    const decoder = new TextDecoder();
    const reader = response.body.getReader();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ') && line !== 'data: [DONE]') {
            try {
              const data = JSON.parse(line.slice(6));
              const content = data.choices[0]?.delta?.content;
              if (content) yield content;
            } catch {
              // Skip invalid JSON
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  /**
   * Mock response for demo/testing
   */
  private async mockResponse(messages: ChatMessage[]): Promise<AIResponse> {
    const lastMessage = messages[messages.length - 1]?.content || '';
    
    let response = 'Hello! I am Thatgfsj Code, your AI coding assistant.\n\n';
    
    if (lastMessage.toLowerCase().includes('hello') || lastMessage.toLowerCase().includes('hi')) {
      response = 'Hi there! How can I help you today?';
    } else if (lastMessage.toLowerCase().includes('who are you')) {
      response = 'I am Thatgfsj Code, an AI assistant built with Node.js. I can help you with coding, file operations, shell commands, and more!';
    } else if (lastMessage.toLowerCase().includes('help')) {
      response = `I can help you with:

📁 File Operations
  - Read, write, and manage files
  - Search for code patterns

🔧 Shell Commands
  - Execute system commands
  - Run build scripts

💻 Code Assistance
  - Explain code
  - Write new code
  - Debug issues

Just tell me what you need!`;
    } else {
      response = `I understand you said: "${lastMessage}"

This is a demo response. To enable full AI capabilities:
1. Run "thatgfsj init" to create config
2. Set your API key: export SILICONFLOW_API_KEY=your_key
3. Supported providers: siliconflow, minimax, openai, anthropic

How can I help you further?`;
    }

    return {
      content: response,
      role: 'assistant'
    };
  }
}
