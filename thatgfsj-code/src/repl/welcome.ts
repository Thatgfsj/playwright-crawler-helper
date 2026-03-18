/**
 * Welcome Screen - Claude Code 风格
 */

import chalk from 'chalk';
import readline from 'readline';
import { existsSync, mkdirSync, writeFileSync, readFileSync } from 'fs';
import { join } from 'path';
import { homedir } from 'os';

export class WelcomeScreen {
  /**
   * 检查是否已配置 API Key
   */
  static hasApiKey(): boolean {
    if (process.env.SILICONFLOW_API_KEY || 
        process.env.OPENAI_API_KEY || 
        process.env.MINIMAX_API_KEY ||
        process.env.ANTHROPIC_API_KEY ||
        process.env.OLLAMA_BASE_URL) {
      return true;
    }
    
    const configPath = join(homedir(), '.thatgfsj', 'config.json');
    if (existsSync(configPath)) {
      try {
        const config = JSON.parse(readFileSync(configPath, 'utf-8'));
        return !!(config.apiKey);
      } catch {
        return false;
      }
    }
    
    return false;
  }

  /**
   * 如果没有 API Key 则显示欢迎页
   */
  static show(): boolean {
    if (this.hasApiKey()) {
      return false;
    }

    this.printClaudeStyle();
    return true;
  }

  /**
   * Claude Code 风格欢迎页
   */
  static printClaudeStyle(): void {
    console.clear();
    
    const w = 62;
    
    // 标题
    console.log(chalk.cyan('+') + chalk.white.bold(' Claude Code ') + chalk.cyan('-'.repeat(w - 14)) + '+');
    console.log(chalk.cyan('|') + chalk.yellow(' 快速开始指南').padEnd(w) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + ' '.repeat(w) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray(' 欢迎使用 Thatgfsj Code!').padEnd(w) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray(' 运行 gfcode init 配置你的 API Key').padEnd(w) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + ' '.repeat(w) + chalk.cyan('|'));
    
    // 提供商
    console.log(chalk.cyan('|') + chalk.green(' 可用提供商:').padEnd(w) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray('  - SiliconFlow (推荐) - Qwen, Kimi, DeepSeek').padEnd(w) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray('  - MiniMax - Moonshot Kimi 系列').padEnd(w) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray('  - OpenAI - GPT-4o, GPT-4o-mini').padEnd(w) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray('  - Anthropic - Claude 3.5 Sonnet').padEnd(w) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + ' '.repeat(w) + chalk.cyan('|'));
    
    // 快捷命令
    console.log(chalk.cyan('|') + chalk.cyan(' 快捷命令:').padEnd(w) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray('   gfcode init        - 配置 API Key').padEnd(w) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray('   gfcode "问题"     - 提问').padEnd(w) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray('   gfcode            - 交互模式').padEnd(w) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + ' '.repeat(w) + chalk.cyan('|'));
    
    // 当前状态
    const model = process.env.MODEL || '未配置';
    const cwd = process.cwd().length > 38 ? '...' + process.cwd().slice(-35) : process.cwd();
    console.log(chalk.cyan('|') + chalk.gray(' 当前模型: ' + model).padEnd(w) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray(' 工作目录: ' + cwd).padEnd(w) + chalk.cyan('|'));
    console.log(chalk.cyan('+') + '-'.repeat(w) + '+');
    console.log();
    console.log(chalk.gray(' 输入 "help" 查看快捷命令'));
    console.log();
  }

  /**
   * 交互式配置向导
   */
  static async interactiveSetup(): Promise<void> {
    console.clear();
    
    const w = 62;
    console.log(chalk.cyan('+') + chalk.white.bold(' Thatgfsj Code 配置向导 ') + chalk.cyan('-'.repeat(w - 22)) + '+');
    console.log(chalk.cyan('|') + ' '.repeat(w) + chalk.cyan('|'));
    
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });

    console.log(chalk.cyan('|') + chalk.white(' 请选择 AI 提供商:').padEnd(w) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + ' '.repeat(w) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.green(' 1. SiliconFlow (推荐)').padEnd(w) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray(' 2. MiniMax').padEnd(w) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray(' 3. OpenAI').padEnd(w) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray(' 4. Anthropic').padEnd(w) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + ' '.repeat(w) + chalk.cyan('|'));

    const choice = await this.question(rl, chalk.green(' 请选择 (1-4): '));
    
    const providers: Record<string, { name: string; model: string; url: string }> = {
      '1': { name: 'siliconflow', model: 'Qwen/Qwen2.5-7B-Instruct', url: 'https://siliconflow.cn' },
      '2': { name: 'minimax', model: 'MiniMax-M2.5', url: 'https://platform.minimax.io' },
      '3': { name: 'openai', model: 'gpt-4o-mini', url: 'https://platform.openai.com' },
      '4': { name: 'anthropic', model: 'claude-3-haiku-20240307', url: 'https://www.anthropic.com' }
    };

    const selected = providers[choice] || providers['1'];
    
    console.log(chalk.cyan('|') + ' '.repeat(w) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray(' 请访问: ' + selected.url).padEnd(w) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray(' 注册账号并获取 API Key').padEnd(w) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + ' '.repeat(w) + chalk.cyan('|'));

    const apiKey = await this.question(rl, chalk.green(' 请输入 API Key: '));
    
    console.log(chalk.cyan('|') + ' '.repeat(w) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.yellow(' 正在保存配置...').padEnd(w) + chalk.cyan('|'));

    const config = {
      model: selected.model,
      apiKey: apiKey,
      provider: selected.name,
      temperature: 0.7,
      maxTokens: 4096
    };

    const configDir = join(homedir(), '.thatgfsj');
    const configPath = join(configDir, 'config.json');

    if (!existsSync(configDir)) {
      mkdirSync(configDir, { recursive: true });
    }

    writeFileSync(configPath, JSON.stringify(config, null, 2));

    console.log(chalk.cyan('|') + ' '.repeat(w) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.green(' ✓ 配置已保存! 运行 gfcode 开始使用').padEnd(w) + chalk.cyan('|'));
    console.log(chalk.cyan('+') + '-'.repeat(w) + '+');
    console.log();
    
    rl.close();
  }

  private static question(rl: readline.Interface, prompt: string): Promise<string> {
    return new Promise((resolve) => {
      rl.question(prompt, (answer) => {
        resolve(answer.trim());
      });
    });
  }
}
