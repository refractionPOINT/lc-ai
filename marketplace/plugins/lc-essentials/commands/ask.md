---
description: Ask a question about LimaCharlie and get an answer from the documentation. Usage: /lc-essentials:ask <your question>
---

# Ask LimaCharlie Documentation

Answer the following question by searching and reading the LimaCharlie documentation in the `docs/` folder:

**Question:** $ARGUMENTS

## Instructions

1. **Search the documentation** using Grep to find relevant files:
   - Search `docs/limacharlie/` for platform documentation
   - Search `docs/python-sdk/` for Python SDK documentation
   - Search `docs/go-sdk/` for Go SDK documentation
   - Try multiple related keywords to find all relevant content

2. **For adapter or cloud sensor questions**: If the question is about adapters, cloud sensors, USP adapters, or data ingestion from third-party sources, also search the public usp-adapters repository:
   - Use WebFetch to browse https://github.com/refractionPOINT/usp-adapters/
   - Look for specific adapter implementations in the repository
   - Check README files and code for configuration examples and supported formats

3. **Read the most relevant files** (typically 2-5 files) to gather comprehensive information

4. **Provide a clear, helpful answer** based on the documentation:
   - Summarize the key points that answer the question
   - Include relevant code examples if available
   - Reference which documentation files contain more details
   - For adapter questions, include links to relevant files in the usp-adapters repo

Keep the answer focused and practical. If the documentation doesn't cover the topic, say so clearly.
