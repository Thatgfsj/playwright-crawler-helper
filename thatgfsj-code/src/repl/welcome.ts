/**
 * Welcome Screen - First-time setup guide
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
    // Check environment variables
    if (process.env.SILICONFLOW_API_KEY || 
        process.env.OPENAI_API_KEY || 
        process.env.MINIMAX_API_KEY ||
        process.env.ANTHROPIC_API_KEY ||
        process.env.OLLAMA_BASE_URL) {
      return true;
    }
    
    // Check config file
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

    this.printWelcome();
    return true;
  }

  /**
   * Print welcome banner
   */
  static printWelcome(): void {
    console.clear();
    
    // Simple banner without ASCII art issues
    console.log(chalk.cyan.bold('\n  +====================================+'));
    console.log(chalk.cyan.bold('  |      Thatgfsj Code v0.2.0        |'));
    console.log(chalk.cyan.bold('  |    AI Coding Assistant           |'));
    console.log(chalk.cyan.bold('  +====================================+\n'));

    console.log(chalk.yellow('  [!] API Key not configured\n'));
    
    // Provider info
    console.log(chalk.cyan('  Available Providers:\n'));
    console.log(chalk.gray('  1. SiliconFlow (recommended)'));
    console.log(chalk.gray('     - Qwen, Kimi, DeepSeek models'));
    console.log(chalk.gray('     - Register: https://siliconflow.cn\n'));
    console.log(chalk.gray('  2. MiniMax'));
    console.log(chalk.gray('     - Moonshot Kimi series'));
    console.log(chalk.gray('     - Register: https://platform.minimax.io\n'));
    console.log(chalk.gray('  3. OpenAI'));
    console.log(chalk.gray('     - GPT-4o, GPT-4o-mini'));
    console.log(chalk.gray('     - Register: https://platform.openai.com\n'));
    console.log(chalk.gray('  4. Anthropic'));
    console.log(chalk.gray('     - Claude 3.5 Sonnet'));
    console.log(chalk.gray('     - Register: https://www.anthropic.com\n'));

    console.log(chalk.cyan('  Quick Start:\n'));
    console.log(chalk.gray('  # Option 1: Set environment variable'));
    console.log(chalk.green('    $env:SILICONFLOW_API_KEY = "your-key"'));
    console.log(chalk.green('    gfcode\n'));
    console.log(chalk.gray('  # Option 2: Run setup wizard'));
    console.log(chalk.green('    gfcode init\n'));

    console.log(chalk.yellow('  [!] Demo mode - AI features disabled\n'));
    
    console.log(chalk.gray('  Press Enter to continue...'));
    
    // Wait for user
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
    
    rl.question('', () => {
      rl.close();
    });
  }

  /**
   * Interactive setup wizard
   */
  static async interactiveSetup(): Promise<void> {
    console.clear();
    
    console.log(chalk.cyan.bold('\n  +====================================+'));
    console.log(chalk.cyan.bold('  |      Thatgfsj Code Setup        |'));
    console.log(chalk.cyan.bold('  +====================================+\n'));

    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });

    // Select provider
    console.log(chalk.cyan('  Select Provider:\n'));
    console.log(chalk.gray('  1. SiliconFlow (recommended)'));
    console.log(chalk.gray('  2. MiniMax'));
    console.log(chalk.gray('  3. OpenAI'));
    console.log(chalk.gray('  4. Anthropic'));
    console.log();

    const choice = await this.question(rl, chalk.green('  Enter (1-4): '));
    
    const providers: Record<string, { name: string; model: string; url: string }> = {
      '1': { name: 'siliconflow', model: 'Qwen/Qwen2.5-7B-Instruct', url: 'https://siliconflow.cn' },
      '2': { name: 'minimax', model: 'MiniMax-M2.5', url: 'https://platform.minimax.io' },
      '3': { name: 'openai', model: 'gpt-4o-mini', url: 'https://platform.openai.com' },
      '4': { name: 'anthropic', model: 'claude-3-haiku-20240307', url: 'https://www.anthropic.com' }
    };

    const selected = providers[choice] || providers['1'];
    
    console.log();
    console.log(chalk.gray(`  Visit ${selected.url} to get API Key\n`));

    const apiKey = await this.question(rl, chalk.green('  Enter API Key: '));
    
    console.log();
    console.log(chalk.cyan('  Saving config...\n'));

    // Save config
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

    console.log(chalk.green('  [✓] Config saved!\n'));
    console.log(chalk.gray('  Run "gfcode" to start\n'));
    
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
