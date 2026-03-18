/**
 * Welcome Screen - Claude Code style
 */

import chalk from 'chalk';
import readline from 'readline';
import { existsSync, mkdirSync, writeFileSync, readFileSync } from 'fs';
import { join } from 'path';
import { homedir } from 'os';

export class WelcomeScreen {
  /**
   * Check if API key is configured
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
   * Show welcome screen if no API key
   */
  static show(): boolean {
    if (this.hasApiKey()) {
      return false;
    }

    this.printClaudeStyle();
    return true;
  }

  /**
   * Claude Code style welcome
   */
  static printClaudeStyle(): void {
    console.clear();
    
    // Banner
    console.log(chalk.cyan('+') + chalk.white.bold(' Claude Code ') + chalk.cyan('-'.repeat(50)) + '+');
    console.log(chalk.cyan('|') + chalk.yellow(' Tips for getting started').padEnd(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + ' '.repeat(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray(' Welcome to Thatgfsj Code!').padEnd(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray(' Run gfcode init to configure your API').padEnd(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + ' '.repeat(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.green(' Available providers:').padEnd(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray('  - SiliconFlow (recommended) - Qwen, Kimi, DeepSeek').padEnd(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray('  - MiniMax - Moonshot Kimi').padEnd(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray('  - OpenAI - GPT-4o').padEnd(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray('  - Anthropic - Claude').padEnd(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + ' '.repeat(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.cyan(' Quick commands:').padEnd(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray('   gfcode init        - Setup').padEnd(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray('   gfcode "question"  - Ask').padEnd(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray('   gfcode            - Interactive').padEnd(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + ' '.repeat(62) + chalk.cyan('|'));
    
    const model = process.env.MODEL || 'Not configured';
    const cwd = process.cwd().length > 40 ? '...' + process.cwd().slice(-37) : process.cwd();
    console.log(chalk.cyan('|') + chalk.gray(' Model: ' + model).padEnd(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray(' Dir: ' + cwd).padEnd(62) + chalk.cyan('|'));
    console.log(chalk.cyan('+') + '-'.repeat(62) + '+');
    console.log();
    console.log(chalk.gray(' Type "help" for shortcuts'));
    console.log();
  }

  /**
   * Interactive setup wizard
   */
  static async interactiveSetup(): Promise<void> {
    console.clear();
    
    console.log(chalk.cyan('+') + chalk.white.bold(' Thatgfsj Code Setup ') + chalk.cyan('-'.repeat(38)) + '+');
    console.log(chalk.cyan('|') + ' '.repeat(62) + chalk.cyan('|'));
    
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });

    console.log(chalk.cyan('|') + chalk.white(' Select provider:').padEnd(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + ' '.repeat(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.green(' 1. SiliconFlow (recommended)').padEnd(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray(' 2. MiniMax').padEnd(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray(' 3. OpenAI').padEnd(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray(' 4. Anthropic').padEnd(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + ' '.repeat(62) + chalk.cyan('|'));

    const choice = await this.question(rl, chalk.green(' Enter (1-4): '));
    
    const providers: Record<string, { name: string; model: string; url: string }> = {
      '1': { name: 'siliconflow', model: 'Qwen/Qwen2.5-7B-Instruct', url: 'https://siliconflow.cn' },
      '2': { name: 'minimax', model: 'MiniMax-M2.5', url: 'https://platform.minimax.io' },
      '3': { name: 'openai', model: 'gpt-4o-mini', url: 'https://platform.openai.com' },
      '4': { name: 'anthropic', model: 'claude-3-haiku-20240307', url: 'https://www.anthropic.com' }
    };

    const selected = providers[choice] || providers['1'];
    
    console.log(chalk.cyan('|') + ' '.repeat(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.gray(' Get key from: ' + selected.url).padEnd(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + ' '.repeat(62) + chalk.cyan('|'));

    const apiKey = await this.question(rl, chalk.green(' Enter API Key: '));
    
    console.log(chalk.cyan('|') + ' '.repeat(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.yellow(' Saving...').padEnd(62) + chalk.cyan('|'));

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

    console.log(chalk.cyan('|') + ' '.repeat(62) + chalk.cyan('|'));
    console.log(chalk.cyan('|') + chalk.green(' OK! Run gfcode to start').padEnd(62) + chalk.cyan('|'));
    console.log(chalk.cyan('+') + '-'.repeat(62) + '+');
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
