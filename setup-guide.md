# Developer Environment Setup Guide
## VS Code, Git, Node.js & Claude Code

---

## 1. Install Visual Studio Code

1. Go to [https://code.visualstudio.com](https://code.visualstudio.com)
2. Click **Download for Windows**
3. Run the installer and follow the prompts
4. Recommended options to tick during install:
   - Add "Open with Code" action to Windows Explorer file context menu
   - Add "Open with Code" action to Windows Explorer directory context menu
   - Add to PATH

---

## 2. Install Git for Windows

Git for Windows includes **Git Bash**, which is required for Claude Code.

1. Go to [https://git-scm.com](https://git-scm.com)
2. Click **Download for Windows**
3. Run the installer — the default options are fine
4. On the **"Adjusting your PATH environment"** step, select:
   - ✅ **Git from the command line and also from 3rd-party software**
5. On the **"Configuring the terminal emulator"** step, select:
   - ✅ **Use MinTTY (the default terminal of MSYS2)**
6. Complete the installation

### Configure Git identity (open any terminal and run):

```bash
git config --global user.name "Your Name"
git config --global user.email "your@email.com"
```

---

## 3. Install Node.js

Claude Code requires Node.js version 18 or higher.

1. Go to [https://nodejs.org](https://nodejs.org)
2. Download the **LTS** version (recommended)
3. Run the installer with default options
4. Verify the installation by opening a terminal and running:

```bash
node --version
npm --version
```

Both commands should return a version number.

---

## 4. Configure Git Bash in VS Code

Once Git for Windows is installed, VS Code will detect Git Bash automatically.

1. Open VS Code
2. Open the terminal panel: **Ctrl + `** (backtick)
3. Click the **dropdown arrow** next to the `+` button in the terminal panel
4. You should see **Git Bash** in the list — click it to open a Bash terminal

### Set Git Bash as the default terminal (optional):

1. Open Settings: **Ctrl + ,**
2. Search for: `terminal.integrated.defaultProfile.windows`
3. Set the value to: `Git Bash`

---

## 5. Install Claude Code

Claude Code is installed as a global npm package.

1. Open a terminal (Git Bash or PowerShell)
2. Run the following command:

```bash
npm install -g @anthropic-ai/claude-code
```

3. Verify the installation:

```bash
claude --version
```

---

## 6. Authenticate Claude Code

1. In your terminal, run:

```bash
claude
```

2. Follow the prompt — it will open a browser window
3. Sign in with your **Anthropic account**
4. Once authenticated, return to the terminal — you are ready to use Claude Code

---

## 7. Install the Claude Code VS Code Extension

The VS Code extension provides the chat panel, sidebar, and keyboard shortcuts inside the editor. It requires the CLI (step 5) to be installed and authenticated first.

1. Open VS Code
2. Open Extensions: **Ctrl + Shift + X**
3. Search for **Claude Code**
4. Click **Install**
5. Once installed, the extension automatically connects to the authenticated CLI

You should see the Claude icon appear in the VS Code sidebar.

---

## 8. Clone Your Repository (if needed)

If you need to clone an existing project from GitHub:

1. Open a terminal in VS Code
2. Navigate to the folder where you want the project:

```bash
cd "D:/Development/Python Projects"
```

3. Clone the repository:

```bash
git clone https://github.com/your-username/your-repo.git
```

4. Open the cloned folder in VS Code:

```bash
code your-repo
```

---

## 9. Install Python Dependencies

If the project uses Python (e.g. a Streamlit app), install the required packages after cloning:

1. Make sure **Python** is installed — [https://python.org](https://python.org) (tick **Add to PATH** during install)
2. Navigate to the project folder in the terminal
3. Run:

```bash
pip install -r requirements.txt
```

This installs all dependencies at the exact versions specified in `requirements.txt`.

To start the Streamlit app:

```bash
streamlit run app.py
```

---

## 10. Start Claude Code in Your Project

1. Open your project folder in VS Code
2. Open the terminal: **Ctrl + `**
3. Run:

```bash
claude
```

Claude Code will start in the context of your project folder.

---

## Quick Reference — Key Commands

| Task | Command |
|------|---------|
| Start Claude Code | `claude` |
| Check Node version | `node --version` |
| Check npm version | `npm --version` |
| Check Git version | `git --version` |
| Check Claude version | `claude --version` |
| Update Claude Code | `npm update -g @anthropic-ai/claude-code` |

---

## Troubleshooting

**`claude` command not found after install**
- Close and reopen the terminal to refresh the PATH
- Or run: `npm install -g @anthropic-ai/claude-code` again

**Git Bash not appearing in VS Code terminal list**
- Ensure Git for Windows is fully installed
- Restart VS Code

**Node.js version too old**
- Download the latest LTS from [https://nodejs.org](https://nodejs.org) and reinstall
