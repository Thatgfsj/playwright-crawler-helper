#!/usr/bin/env node

/**
 * Thatgfsj Code - AI Coding Assistant
 * Claude Code-like interactive CLI
 */

// 强制 UTF-8 编码 (Windows) - 必须在任何输出之前
if (process.platform === 'win32') {
  try {
    // 执行 chcp 65001 设置代码页
    require('child_process').execSync('chcp 65001', { stdio: 'ignore', windowsHide: true });
  } catch {}
}

import { program } from 'commander';
import chalk from 'chalk';
import ora from 'ora';
import readline from 'readline';
import { fileURLToPath } from 'url';
import { homedir } from 'os';
import { dirname, join } from 'path';
import { existsSync, readdirSync, statSync, mkdirSync, writeFileSync } from 'fs';

import { AIEngine } from './core/ai-engine.js';
import { ToolRegistry } from './core/tool-registry.js';
import { SessionManager } from './core/session.js';
import { ConfigManager } from './core/config.js';
import { FileTool, ShellTool, GitTool, SearchTool } from './tools/index.js';
import { WelcomeScreen } from './repl/welcome.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ============== Global Error Handling ==============

process.on('uncaughtException', (error) => {
  console.error(chalk.red('\n❌ Error:'), error.message);
  process.exit(1);
});

process.on('unhandledRejection', (reason) => {
  console.error(chalk.red('\n❌ Error:'), reason);
  process.exit(1);
});

// ============== CLI Program ==============

// Add init command
program
  .command('init')
  .description('初始化配置/设置向导')
  .action(async () => {
    const { WelcomeScreen } = await import('./repl/welcome.js');
    await WelcomeScreen.interactiveSetup();
  });

program
  .name('gfcode')
  .description('🤖 AI Coding Assistant - Like Claude Code')
  .version('0.2.0')
  .argument('[prompt]', 'Task to execute (omit to start interactive mode)')
  .option('-i, --interactive', 'Start interactive mode')
  .option('-s, --stream', 'Stream output')
  .option('-m, --model <model>', 'Specify model')
  .option('--no-auto', 'Disable auto-read project files')
  .action(async (prompt, options) => {
    // Check for API key and show welcome if needed
    const { WelcomeScreen } = await import('./repl/welcome.js');
    const hasApiKey = checkApiKey();
    
    if (!hasApiKey) {
      WelcomeScreen.show();
    }
    
    // Default to interactive mode if no prompt provided
    if (!prompt && !options.interactive) {
      await startInteractive();
    } else if (prompt) {
      await executeTask(prompt, options);
    } else {
      await startInteractive();
    }
  });

// Helper to check API key
function checkApiKey(): boolean {
  return !!(process.env.SILICONFLOW_API_KEY || 
            process.env.OPENAI_API_KEY || 
            process.env.MINIMAX_API_KEY ||
            process.env.ANTHROPIC_API_KEY ||
            process.env.OLLAMA_BASE_URL);
}

// Parse
program.parse(process.argv);

// ============== Core Functions ==============

/**
 * Get project context
 */
function getProjectContext(): string {
  const cwd = process.cwd();
  const info: string[] = [];
  
  try {
    // Package info
    const pkgPath = join(cwd, 'package.json');
    if (existsSync(pkgPath)) {
      info.push(`📦 Project: ${cwd}`);
      const { readFileSync } = require('fs');
      const pkg = JSON.parse(readFileSync(pkgPath, 'utf-8'));
      info.push(`   Name: ${pkg.name || 'unknown'}`);
      if (pkg.dependencies && Object.keys(pkg.dependencies).length > 0) {
        info.push(`   Deps: ${Object.keys(pkg.dependencies).length} packages`);
      }
    } else {
      info.push(`📁 Working dir: ${cwd}`);
    }
    
    // Count files
    let fileCount = 0;
    const countFiles = (dir: string) => {
      try {
        const items = readdirSync(dir);
        for (const item of items) {
          if (item === 'node_modules' || item === '.git') continue;
          const fullPath = join(dir, item);
          const stat = statSync(fullPath);
          if (stat.isDirectory()) {
            countFiles(fullPath);
          } else if (/\.(ts|js|py|go|rs|java|cpp|c|h)$/.test(item)) {
            fileCount++;
          }
        }
      } catch {}
    };
    countFiles(cwd);
    if (fileCount > 0) {
      info.push(`   Files: ${fileCount} code files`);
    }
  } catch {}
  
  return info.join('\n');
}

/**
 * Execute a task (Claude Code style)
 */
async function executeTask(prompt: string, options: any) {
  console.log(chalk.cyan('\n🤖 Thatgfsj Code\n'));
  console.log(chalk.gray(getProjectContext()));
  console.log(chalk.gray('─'.repeat(40)));
  console.log(chalk.cyan('\n> ') + prompt + '\n');
  
  try {
    const config = await ConfigManager.load();
    if (options.model) config.model = options.model;
    
    const ai = new AIEngine(config);
    const session = new SessionManager();
    const registry = new ToolRegistry();
    
    // Register tools - all available tools
    const shellTool = new ShellTool();
    const fileTool = new FileTool();
    const gitTool = new GitTool();
    const searchTool = new SearchTool();
    
    ai.registerTool(shellTool);
    ai.registerTool(fileTool);
    ai.registerTool(gitTool);
    ai.registerTool(searchTool);
    
    // System prompt - Claude Code style
    const systemPrompt = `You are Thatgfsj Code, an AI coding assistant like Claude Code.
You can read files, write files, and execute shell commands to complete coding tasks.

When working on a task:
1. First understand what files are involved
2. Read necessary files to understand the codebase  
3. Make changes
4. Verify the changes work

Be concise but thorough. Show your reasoning.`;
    
    session.addMessage('system', systemPrompt);
    session.addMessage('user', prompt);
    
    const spinner = ora(chalk.gray('Thinking...')).start();
    const response = await ai.chat(session.getMessages());
    spinner.stop();
    
    console.log(chalk.cyan('\n🤖 Response:\n'));
    console.log(response.content);
    console.log(chalk.gray('\n' + '─'.repeat(40)));
    
  } catch (error: any) {
    console.error(chalk.red(`\n❌ Error: ${error.message}`));
    process.exit(1);
  }
}

/**
 * Handle model switch in interactive mode
 */
async function handleModelSwitch(rl: readline.Interface, currentConfig: any) {
  console.log(chalk.cyan('\n切换模型...\n'));
  
  // Get available models based on current provider
  const models = WelcomeScreen.getModelsForProvider(currentConfig.provider || 'siliconflow');
  
  console.log(chalk.gray('可用模型:\n'));
  models.forEach((model, idx) => {
    const selected = model.id === currentConfig.model ? ' ✓' : '';
    console.log(chalk.gray(`  ${idx + 1}. ${model.name} - ${model.desc}${selected}`));
  });
  
  console.log();
  
  const answer = await new Promise<string>((resolve) => {
    rl.question(chalk.green('选择模型编号: '), resolve);
  });
  
  const idx = parseInt(answer) - 1;
  if (idx >= 0 && idx < models.length) {
    const selected = models[idx];
    
    // Save to config
    const config = { ...currentConfig, model: selected.id };
    const configPath = join(homedir(), '.thatgfsj', 'config.json');
    
    try {
      const dir = join(homedir(), '.thatgfsj');
      if (!existsSync(dir)) {
        mkdirSync(dir, { recursive: true });
      }
      writeFileSync(configPath, JSON.stringify(config, null, 2));
      console.log(chalk.green(`\n✓ 模型已切换为: ${selected.name}\n`));
    } catch (e: any) {
      console.error(chalk.red(`\n保存失败: ${e.message}\n`));
    }
  } else {
    console.log(chalk.yellow('\n无效选择，保持当前模型\n'));
  }
}

/**
 * Start interactive mode (Claude Code style)
 */
async function startInteractive() {
  console.log(chalk.cyan('\n🤖 Thatgfsj Code - Interactive Mode\n'));
  console.log(chalk.gray(getProjectContext()));
  console.log(chalk.gray('─'.repeat(40)));
  console.log(chalk.gray('\nCommands:'));
  console.log(chalk.gray('  exit, Ctrl+C   - Quit'));
  console.log(chalk.gray('  clear          - Clear history'));
  console.log(chalk.gray('  context        - Show project context'));
  console.log(chalk.gray('\n' + '─'.repeat(40) + '\n'));
  
  try {
    const config = await ConfigManager.load();
    const ai = new AIEngine(config);
    const session = new SessionManager();
    
    // Register tools - all available tools
    const shellTool = new ShellTool();
    const fileTool = new FileTool();
    const gitTool = new GitTool();
    const searchTool = new SearchTool();
    
    ai.registerTool(shellTool);
    ai.registerTool(fileTool);
    ai.registerTool(gitTool);
    ai.registerTool(searchTool);
    
    // System prompt
    const defaultSystem = `You are Thatgfsj Code, an AI coding assistant like Claude Code.
You can read files, write files, and execute shell commands.
Be helpful, concise, and show your reasoning.`;
    session.addMessage('system', defaultSystem);

    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
      terminal: true
    });

    const ask = () => {
      rl.question(chalk.green('\n> '), async (input) => {
        const trimmed = input.trim();
        
        if (!trimmed) {
          ask();
          return;
        }
        
        // Commands
        if (trimmed === 'exit' || trimmed === 'quit' || trimmed === '\\x03') {
          console.log(chalk.gray('\n👋 Goodbye!'));
          rl.close();
          return;
        }
        
        if (trimmed === 'clear') {
          session.clear();
          console.clear();
          console.log(chalk.cyan('🤖 Thatgfsj Code - Interactive Mode\n'));
          ask();
          return;
        }
        
        if (trimmed === 'context') {
          console.log(chalk.cyan('\n' + getProjectContext() + '\n'));
          ask();
          return;
        }
        
        // Model switch command
        if (trimmed === '/model' || trimmed === 'model') {
          await handleModelSwitch(rl, config);
          ask();
          return;
        }

        // Add and process
        session.addMessage('user', trimmed);
        
        const spinner = ora(chalk.gray('Thinking...')).start();
        
        try {
          const response = await ai.chat(session.getMessages());
          spinner.stop();
          
          console.log(chalk.cyan('\n🤖:'));
          console.log(response.content);
          
          session.addMessage('assistant', response.content);
          session.truncate(20);
          
        } catch (error: any) {
          spinner.fail(chalk.red(`Error: ${error.message}`));
        }

        ask();
      });
    };

    ask();
    
  } catch (error: any) {
    console.error(chalk.red(`\n❌ Failed to start: ${error.message}`));
    process.exit(1);
  }
}
