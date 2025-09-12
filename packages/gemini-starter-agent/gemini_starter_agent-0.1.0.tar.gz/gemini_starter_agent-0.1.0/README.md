Gemini Starter Agent 🚀 - Simplifying Gemini Chat Completions in the OpenAI Agents SDK
======================================================================================

[https://img.shields.io/badge/python-3.13+-blue](https://img.shields.io/badge/python-3.13+-blue)[https://img.shields.io/badge/License-MIT-yellow.svg](https://img.shields.io/badge/License-MIT-yellow.svg)

Gemini Starter Agent is a Python CLI tool to quickly bootstrap AI agents using the Gemini API and OpenAI Agent SDK. It leverages [UV](https://uv-pypi.org/) for project scaffolding, virtual environment management, and dependency handling.

Features
--------

*   Quick scaffolding of a Gemini AI agent project.
    
*   Automatic creation of virtual environments.
    
*   Easy dependency installation (openai-agents, python-dotenv).
    
*   Generates a ready-to-run main.py for your agent.
    
*   Friendly CLI prompts for agent name, purpose, and API key.
    
*   PEP-621 compliant pyproject.toml scripts for easy CLI execution.
    
*   Cross-platform support.
    

Installation
------------
Install the package via pip:

```bash
pip install gemini-starter-agent
```

Usage
-----

Run the CLI to generate a new Gemini agent:

```bash
`pip install gemini-starter-agent   `

```

You will be prompted for:

*   Project name (default: agent)
    
*   Gemini API key
    
*   Gemini model (choose from default or enter your own)
    
*   Agent name (default: Helpful Assistant)
    
*   Agent purpose/instructions
    

After completion, your project structure will look like:

```Plain 
`   /your-project-name/  ├── src/  │   └── your_project_name/  │       ├── __init__.py  │       └── main.py  ├── .env  ├── pyproject.toml  └── ...   `

```

Example main.py
---------------

Here is how the generated main.py will look:

```python
``   import asyncio  import os  from dotenv import load_dotenv  # the openai-agents runtime packages are installed by `uv add`  from agents import Agent, Runner, RunConfig, OpenAIChatCompletionsModel, set_tracing_disabled  from openai import AsyncOpenAI  # Load environment variables  load_dotenv()  GEMINI_MODEL = os.getenv("GEMINI_MODEL")  GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  BASE_URL = os.getenv("BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")  # Disable tracing for cleaner output  set_tracing_disabled(True)  client: AsyncOpenAI = AsyncOpenAI(api_key=GEMINI_API_KEY, base_url=BASE_URL)  model: OpenAIChatCompletionsModel = OpenAIChatCompletionsModel(GEMINI_MODEL, client)  agent: Agent = Agent(      name="{agent_name}",      instructions="{agent_purpose}",      model=model,  )  async def main() -> None:      """Entry point for the agent CLI."""       prompt = "What is Agentic AI in haikus"  # enter a prompt here      result = await Runner.run(agent, prompt, run_config=RunConfig(model))      print(result.final_output)  if __name__ == '__main__':      asyncio.run(main())   ``

```
Running Your Agent
------------------

Change into the project folder:


Run the agent using UV scripts:

bash

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   uv run helpful-assistant                # friendly script   `
Environment Variables
---------------------

The .env file is automatically generated and contains:

env

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   GEMINI_API_KEY=your_api_key_here  GEMINI_MODEL=your_model_here  BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/   `

Contributing
------------
*   Submit bug reports or feature requests via GitHub Issues.
    
*   Fork the repository and create pull requests for improvements.
    
*   Ensure code style consistency and add documentation for new features.
    

License
-------

This project is licensed under the **MIT License**. See the [LICENSE](https://license/) file for details.

Author
------

**Marjan Ahmed**

*   Email: [marjanahmed.dev@gmail.com](https://mailto:marjanahmed.dev@gmail.com/)
    
*   GitHub: [https://github.com/marjan-ahmed](https://github.com/marjan-ahmed)