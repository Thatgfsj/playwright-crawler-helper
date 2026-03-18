#!/usr/bin/env node

/**
 * Thatgfsj Code - AI Coding Assistant CLI
 * Entry point with global error handling
 */

import { program } from 'commander';
import chalk from 'chalk';
import ora from 'ora';
import readline from 'readline';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { existsSync, mkdirSync } from 'fs';

import { AIEngine } from './core/ai-engine.js';
import { ToolRegistry } from './core/tool-registry.js';
import { SessionManager } from './core/session.js';
import { ConfigManager } from './core/config.js';
import { FileTool } from './tools/file.js';
import { ShellTool } from './tools/shell.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ============== Global Error Handling ==============

process.on('uncaughtException', (error) => {
  console.error(chalk.red('\n❌ Uncaught Error:'), error.message);
  console.error(chalk.gray(error.stack || ''));
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error(chalk.red('\n❌ Unhandled Rejection:'), reason);
  process.exit(1);
});

// ============== CLI Program ==============

program
  .name('thatgfsj')
  .description('🤖 Thatgfsj Code - Your AI Coding Assistant')
  .version('0.1.0');

// Chat command
program
  .command('chat')
  .description('Start interactive chat mode')
  .option('-s, --system <prompt>', 'System prompt')
  .option('-m, --model <model>', 'Specify model')
  .option('--no-stream', 'Disable streaming')
  .action(async (options) => {
    await startChat(options.system, options.model, options.stream);
  });

// Exec command
program
  .command('exec <prompt>')
  .description('Execute a single prompt')
  .option('-s, --stream', 'Stream output')
  .option('-m, --model <model>', 'Specify model')
  .action(async (prompt, options) => {
    await executePrompt(prompt, options.stream, options.model);
  });

// Init command
program
  .command('init')
  .description('Initialize Thatgfsj Code configuration')
  .option('-p, --provider <provider>', 'AI provider', 'siliconflow')
  .action(async (options) => {
    await initialize(options.provider);
  });

// Config command
program
  .command('config')
  .description('Show/manage configuration')
  .option('-s, --set <key=value>', 'Set config value')
  .option('-p, --provider <provider>', 'Switch provider')
  .action(async (options) => {
    await showConfig(options);
  });

// Tools command
program
  .command('tools')
  .description('List available tools')
  .action(() => {
    listTools();
  });

// Providers command
program
  .command('providers')
  .description('List available AI providers')
  .action(() => {
    showProviders();
  });

// Default: show help
program.parse(process.argv);

if (process.argv.length === 2) {
  console.log(chalk.cyan('🤖 Thatgfsj Code v0.1.0'));
  console.log(chalk.gray('  Your AI Coding Assistant\n'));
  console.log(chalk.gray('Usage:'));
  console.log(chalk.gray('  thatgfsj chat          Start interactive mode'));
  console.log(chalk.gray('  thatgjs exec <prompt>  Execute a single prompt'));
  console.log(chalk.gray('  thatgfsj init          Initialize config'));
  console.log(chalk.gray('  thatgfsj config        Show configuration'));
  console.log(chalk.gray('  thatgfsj tools         List tools'));
  console.log(chalk.gray('  thatgfsj providers     List AI providers'));
  console.log(chalk.gray('\nType "thatgfsj --help" for more info'));
}

// ============== Core Functions ==============

/**
 * Start interactive chat mode
 */
async function startChat(systemPrompt?: string, model?: string, stream: boolean = true) {
  console.log(chalk.cyan('\n🤖 Thatgfsj Code - Interactive Mode\n'));
  console.log(chalk.gray('Commands: "exit" to quit, "clear" to clear history, "tools" to list tools\n'));

  try {
    const config = await ConfigManager.load();
    if (model) config.model = model;
    
    const ai = new AIEngine(config);
    const session = new SessionManager();
    const registry = new ToolRegistry();
    
    // Register tools
    const shellTool = new ShellTool();
    const fileTool = new FileTool();
    ai.registerTool(shellTool);
    ai.registerTool(fileTool);
    
    // Setup confirmation callback
    registry.setContext({
      confirmAction: (msg: string) => askConfirmation(msg)
    });

    // Add system prompt
    const defaultSystem = 'You are Thatgfsj Code, a helpful AI coding assistant. You can execute shell commands and file operations when needed.';
    session.addMessage('system', systemPrompt || defaultSystem);

    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      terminal: true
    });

    const prompt = () => {
      rl.question(chalk.green('\n> '), async (input) => {
        const trimmed = input.trim();
        
        // Handle special commands
        if (trimmed === 'exit' || trimmed === 'quit') {
          console.log(chalk.gray('\n👋 Goodbye!'));
          rl.close();
          return;
        }
        
        if (trimmed === 'clear') {
          session.clear();
          console.log(chalk.gray('History cleared.'));
          prompt();
          return;
        }

        if (trimmed === 'tools') {
          console.log(chalk.cyan('\n📦 Available Tools:'));
          for (const t of registry.listAll()) {
            console.log(chalk.gray(`  • ${t.name}: ${t.description}`));
          }
          prompt();
          return;
        }
        
        if (!trimmed) {
          prompt();
          return;
        }

        // Add user message
        session.addMessage('user', trimmed);

        // Show thinking indicator
        const spinner = ora(chalk.gray('Thinking...')).start();

        try {
          const response = await ai.chat(session.getMessages());
          spinner.stop();
          
          // Display response with color
          console.log(chalk.cyan('\n🤖:'), response.content);
          
          // Add assistant message
          session.addMessage('assistant', response.content);
          
          // Truncate if too long
          session.truncate(20);
          
        } catch (error: any) {
          spinner.fail(chalk.red(`Error: ${error.message}`));
        }

        prompt();
      });
    };

    prompt();
  } catch (error: any) {
    console.error(chalk.red(`\n❌ Failed to start chat: ${error.message}`));
    process.exit(1);
  }
}

/**
 * Execute a single prompt
 */
async function executePrompt(prompt: string, stream?: boolean, model?: string) {
  const spinner = ora('Executing...').start();
  
  try {
    const config = await ConfigManager.load();
    if (model) config.model = model;
    
    const ai = new AIEngine(config);
    const session = new SessionManager();
    
    // Register tools
    const shellTool = new ShellTool();
    const fileTool = new FileTool();
    ai.registerTool(shellTool);
    ai.registerTool(fileTool);
    
    session.addMessage('user', prompt);
    
    const response = await ai.chat(session.getMessages());
    spinner.stop();
    
    console.log(chalk.cyan('\n🤖:'), response.content);
    
  } catch (error: any) {
    spinner.fail(chalk.red(`Error: ${error.message}`));
    process.exit(1);
  }
}

/**
 * Initialize configuration
 */
async function initialize(provider: string = 'siliconflow') {
  console.log(chalk.cyan('\n🚀 Initializing Thatgfsj Code...\n'));
  
  const configDir = join(process.env.HOME || process.env.USERPROFILE || '', '.thatgfsj');
  const configFile = join(configDir, 'config.json');
  
  if (!existsSync(configDir)) {
    mkdirSync(configDir, { recursive: true });
  }
  
  // Get default config for provider
  const defaultConfig = {
    model: 'Qwen/Qwen2.5-7B-Instruct',
    apiKey: '',
    temperature: 0.7,
    maxTokens: 4096,
    provider: provider,
    baseUrl: provider === 'siliconflow' ? 'https://api.siliconflow.cn/v1' 
               : provider === 'minimax' ? 'https://api.minimax.chat/v1'
               : provider === 'openai' ? 'https://api.openai.com/v1'
               : 'https://api.siliconflow.cn/v1'
  };
  
  const { writeFileSync } = await import('fs');
  writeFileSync(configFile, JSON.stringify(defaultConfig, null, 2));
  
  console.log(chalk.green('✅ Initialized successfully!'));
  console.log(chalk.gray(`Config saved to: ${configFile}`));
  console.log(chalk.gray(`\nProvider: ${provider}`));
  console.log(chalk.gray('Please set your API key:'));
  
  if (provider === 'siliconflow') {
    console.log(chalk.gray('  export SILICONFLOW_API_KEY=your_key'));
  } else if (provider === 'minimax') {
    console.log(chalk.gray('  export MINIMAX_API_KEY=your_key'));
  } else if (provider === 'openai') {
    console.log(chalk.gray('  export OPENAI_API_KEY=your_key'));
  } else if (provider === 'anthropic') {
    console.log(chalk.gray('  export ANTHROPIC_API_KEY=your_key'));
  }
  
  console.log(chalk.gray('\nOr edit the config file directly.\n'));
}

/**
 * Show/manage configuration
 */
async function showConfig(options: any) {
  console.log(chalk.cyan('\n⚙️  Current Configuration\n'));
  
  try {
    const config = await ConfigManager.load();
    
    console.log(chalk.gray(`Config file: ~/.thatgfsj/config.json`));
    console.log(chalk.gray(`Provider: ${config.provider || 'siliconflow'}`));
    console.log(chalk.gray(`Model: ${config.model}`));
    console.log(chalk.gray(`Base URL: ${config.baseUrl}`));
    console.log(chalk.gray(`API Key: ${config.apiKey ? '***' + config.apiKey.slice(-4) : 'Not set (use env var)'}`));
    console.log(chalk.gray(`Temperature: ${config.temperature}`));
    console.log(chalk.gray(`Max Tokens: ${config.maxTokens}\n`));
  } catch (error: any) {
    console.log(chalk.yellow('No config found. Run "thatgfsj init" first.\n'));
  }
}

/**
 * List available tools
 */
function listTools() {
  console.log(chalk.cyan('\n📦 Available Tools:\n'));
  console.log(chalk.gray('  shell   - Execute shell commands'));
  console.log(chalk.gray('  file    - Read, write, list files\n'));
}

/**
 * Show available providers
 */
function showProviders() {
  console.log(chalk.cyan('\n🌐 Available AI Providers:\n'));
  console.log(chalk.gray('  siliconflow  - 硅基流动 (default, free tier available)'));
  console.log(chalk.gray('  minimax     - MiniMax M2.5'));
  console.log(chalk.gray('  openai      - OpenAI GPT'));
  console.log(chalk.gray('  anthropic   - Anthropic Claude\n'));
  console.log(chalk.gray('Usage: thatgfsj init -p siliconflow\n'));
}

/**
 * Ask for user confirmation (for dangerous shell commands)
 */
function askConfirmation(msg: string): Promise<boolean> {
  return new Promise((resolve) => {
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      terminal: true
    });
    
    rl.question(chalk.yellow(`\n⚠️  ${msg}\n`) + chalk.yellow('> '), (answer) => {
      rl.close();
      resolve(answer.toLowerCase().startsWith('y'));
    });
  });
}
