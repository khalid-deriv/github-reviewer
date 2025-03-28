Here’s a detailed step-by-step blueprint for building the AI-powered GitHub pull request review agent. The plan is broken into iterative chunks, with each chunk further divided into small, testable steps. Each step will include prompts for a code-generation LLM to implement in a test-driven manner.

---

## Step-by-Step Blueprint

### Phase 1: Core Setup and Configuration
1. **Set up the repository structure**:
   - Create a basic folder structure for the project.
   - Include directories for configuration, logs, and core functionality.

2. **Define the YAML configuration file**:
   - Create a YAML schema for specifying directives, exclusions, LLM parameters, and backends.
   - Write a parser to validate and load the configuration.

3. **Implement GitHub API integration**:
   - Set up authentication with GitHub using a personal access token.
   - Write a function to fetch pull request details and diffs.

4. **Set up logging**:
   - Implement a logging system to track activities, errors, and processed files.

---

### Phase 2: LLM Integration
1. **Integrate with LLM backends**:
   - Write a wrapper for interacting with multiple LLM backends (e.g., OpenAI, Azure OpenAI).
   - Include retry logic and fallback mechanisms.

2. **Implement prompt generation**:
   - Create a function to generate prompts for reviewing pull requests.
   - Include repository context, diff details, and directives from the YAML configuration.

3. **Test LLM responses**:
   - Write unit tests to validate the quality and structure of LLM responses.

---

### Phase 3: Pull Request Review Logic
1. **Analyze pull request diffs**:
   - Write a function to parse and analyze diffs.
   - Identify areas for inline comments and suggestions.

2. **Generate inline comments**:
   - Use LLM responses to create inline comments for specific code segments.
   - Format comments according to GitHub's API requirements.

3. **Post comments to GitHub**:
   - Write a function to post comments directly on the pull request using the GitHub API.

---

### Phase 4: Knowledge Base Integration
1. **Set up the RAG knowledge base**:
   - Use a vector database (e.g., Pinecone, Weaviate) to store embeddings of repository files.
   - Write a function to retrieve relevant context for pull requests.

2. **Periodic updates to the knowledge base**:
   - Implement a script to update the knowledge base weekly (or as configured).

---

### Phase 5: Workflow Automation
1. **Create a GitHub Actions workflow**:
   - Write a YAML file to trigger the AI for all pull requests.
   - Include steps to validate the configuration and run the review agent.

2. **Implement dry-run mode**:
   - Add a mode to validate the configuration and test connectivity without posting comments.

---

### Phase 6: Notifications and Finalization
1. **Add email notifications**:
   - Implement a function to send email notifications for critical issues.
   - Use a library like `smtplib` or an external service (e.g., SendGrid).

2. **Finalize and test the system**:
   - Conduct end-to-end testing with real pull requests.
   - Optimize performance and address any edge cases.

---

## Iterative Chunks and Prompts

### Chunk 1: Repository Setup and Configuration
**Prompt 1**:
```text
Create a folder structure for a Python project with the following directories:
- `config/` for configuration files.
- `logs/` for log files.
- `core/` for the main functionality of the project.
Include a `README.md` file in the root directory with a brief description of the project.
```

**Prompt 2**:
```text
Write a YAML schema for the configuration file. The schema should include:
- `directives`: A list of paths to `.md` files containing coding standards.
- `exclusions`: A list of files or directories to exclude.
- `llm_parameters`: Parameters like `temperature`, `max_tokens`, and `model_name`.
- `llm_backends`: A list of LLM backends with their tokens.
- `update_frequency`: A parameter to specify the frequency of knowledge base updates.
```

**Prompt 3**:
```text
Write a Python script to load and validate the YAML configuration file. The script should:
- Check for required fields.
- Validate the structure of the file.
- Raise errors for missing or invalid fields.
```

---

### Chunk 2: GitHub API Integration
**Prompt 4**:
```text
Write a Python function to authenticate with the GitHub API using a personal access token. The function should:
- Accept the token as an argument.
- Return an authenticated session object.
```

**Prompt 5**:
```text
Write a Python function to fetch pull request details using the GitHub API. The function should:
- Accept the repository name and pull request number as arguments.
- Return details like the author, title, and list of changed files.
```

**Prompt 6**:
```text
Write a Python function to fetch the diff of a pull request using the GitHub API. The function should:
- Accept the repository name and pull request number as arguments.
- Return the diff as a string.
```

---

### Chunk 3: Logging System
**Prompt 7**:
```text
Implement a logging system for the project. The system should:
- Write logs to a file in the `logs/` directory.
- Include timestamps and log levels (e.g., INFO, ERROR).
- Log activities like fetching pull request details and processing files.
```

---

### Chunk 4: LLM Integration
**Prompt 8**:
```text
Write a Python wrapper for interacting with multiple LLM backends. The wrapper should:
- Accept backend-specific parameters (e.g., API tokens, model names).
- Include retry logic for failed requests.
- Support switching to a fallback backend if the primary one fails.
```

**Prompt 9**:
```text
Write a function to generate prompts for reviewing pull requests. The function should:
- Accept the repository context, diff details, and directives as arguments.
- Return a formatted prompt string for the LLM.
```

---

### Chunk 5: Pull Request Review Logic
**Prompt 10**:
```text
Write a Python function to parse and analyze pull request diffs. The function should:
- Identify code segments that require comments or suggestions.
- Return a list of segments with their line numbers.
```

**Prompt 11**:
```text
Write a Python function to post inline comments on a pull request using the GitHub API. The function should:
- Accept the repository name, pull request number, and comment details as arguments.
- Post the comments directly on the pull request.
```

---

### Chunk 6: Workflow Automation
**Prompt 12**:
```text
Write a GitHub Actions workflow YAML file to trigger the AI for all pull requests. The workflow should:
- Run on pull request events.
- Validate the configuration file.
- Execute the review agent script.
```

---

**Prompt 13**:
Create a file titled review_agent.py that uses and combines all the functions inside the core folder to be triggered by the github action workflow. This file should contain the main python entrypoint function and will run the PR review

### Chunk 7: Notifications
**Prompt 14**:
```text
Write a Python function to send email notifications for critical issues. The function should:
- Accept the recipient email, subject, and message as arguments.
- Use `smtplib` to send the email.
```

---

This iterative plan ensures incremental progress with strong testing and integration at every stage. Let me know if you'd like to refine any part of this!