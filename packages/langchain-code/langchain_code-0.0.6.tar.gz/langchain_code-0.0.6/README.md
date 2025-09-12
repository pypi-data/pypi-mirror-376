<p align="center">
  <img src="https://raw.githubusercontent.com/zamalali/langchain-code/main/assets/logo.png" alt="LangCode Logo" width="160" />
</p>

<h1 align="center">LangCode</h1>

<p align="center">
  <em>The only CLI you'll ever need!</em>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/zamalali/langchain-code/main/assets/cmd.png" alt="LangCode Home Screen" width="100%" />
</p>

**LangCode** is the “one-key” developer CLI that unifies **Gemini**, **Anthropic Claude**, **OpenAI**, and **Ollama** with **ReAct** & **Deep** modes—fully inline, right in your terminal.


## Get Started

1.  **Installation:**
    ```bash
    pip install langchain-code
    ```


**Launch the Interactive Launcher:**
    Just type `langcode` in your terminal and hit Enter. This opens a user-friendly interactive menu where you can easily configure your session and access various functionalities without needing to remember specific command-line arguments. See the image shown above.

---
## Interactive Mode

The interactive mode serves as the central hub for all your coding tasks. It allows you to:

*   **Choose a Command:** Select what you want to do: `chat`, `feature`, `fix`, or `analyze`.
*   **Configure the Engine:** Pick between `react` (fast and efficient) and `deep` (for complex tasks).
*   **Enable Smart Routing:** Let LangCode automatically select the best LLM for each task.
*   **Set the Priority:** Optimize for `cost`, `speed`, or `quality` when using smart routing.
*   **Manage Autopilot:** Enable fully autonomous mode for the Deep Agent (use with caution!).
*   **Toggle Apply Mode:** Allow LangCode to automatically write changes to your file system.
*   **Select an LLM:** Explicitly choose between Anthropic and Google Gemini, or let LangCode decide.
*   **Specify the Project Directory:** Tell LangCode where your codebase is located.
*   **Edit Environment Variables:** Quickly add or modify API keys and other settings in your `.env` file.
*   **Customize Instructions:** Open the `.langcode/langcode.md` file to add project-specific guidelines.
*   **Configure MCP Servers:** Set up Model Context Protocol (MCP) servers for advanced tool integration.
*   **Edit Language Code:** Modify the core language code directly from the main window.
*   **Specify MCP Servers:** Configure Model Context Protocol (MCP) servers for advanced tool integration.
*   **Define a Test Command:** Specify a command to run after making changes (e.g., `pytest -q`).
*   **Access Help:** Press `h` to toggle help and `q` or `Esc` to quit.

## Core Commands

While the interactive launcher is the recommended way to use LangCode, you can also use the following commands directly from the terminal:

*   `langcode chat`: Starts an interactive chat session.
*   `langcode feature`: Implements a new feature.
*   `langcode fix`: Fixes a bug.
*   `langcode analyze`: Analyzes the codebase.
*   `langcode instr`: Opens the project instructions file.

---

## Install & Run

```bash
pip install langchain-code
langcode
```

## Contributing

Issues and PRs are welcome. Please open an issue to discuss substantial changes before submitting a PR. See `CONTRIBUTING.md` for guidelines.

## License

MIT. See [LICENSE](LICENSE).

## Acknowledgments

LangCode draws inspiration from the design and developer experience of Google’s Gemini CLI and Anthropic’s Claude Code, unified into a single, streamlined tool.