<p style="border:1px; border-style:solid; border-color:black; padding: 1em;">
CS-UH 3260 Software Analytics<br/>
Replication Study Guidelines<br/>
Dr. Sarah Nadi, NYUAD
</p>

# Replication 4 -- CS-UH-3260 Software Analytics


## Overview

This repo contains the scripts and data used for the `Replication 4` assignment, focusing on the paper *Hybrid Automated Program Repair by Combining Large Language Models and Program Analysis*. The scope of our replication includes RQ1 (specifically using `gpt4o-mini` to recreate Table 2) and manually analyzing the repair patches provided in the replication artifact.


### 1. Project Title and Overview

- **Paper Title**: Hybrid Automated Program Repair by Combining Large Language Models and Program Analysis
- **Authors**: HONGYU ZHANG, FENGJIE LI, JIAJUN JIANG, and JIAJUN SUN
- **Replication Team**: Matthias and Arhum
- **Course**: CS-UH 3260 Software Analytics, NYUAD
- **Brief Description**: 
  - The paper develops GiantRepair which improves automated bug fixing by combining large language model–generated patches with systematic validation using Defects4J, increasing the number of correctly repaired bugs
  - We replicate GiantRepair by generating patches with an LLM and evaluating them on Defects4J, reproducing raw fix results

### 2. Repository Structure

Document your repository structure clearly. Organize your repository using the following standard structure:

```
README                    # Documentation for repository
datasets/                 # Original dataset files taken from the GiantRepair GitHub repository
replication_scripts/      # Scripts used in replication
outputs/                  # Your generated results
notes/                    # Notes (patch analysis, explanation of replication scope)
```


### 3. Setup Instructions

- **Prerequisites**: Required software, tools, and versions
  - OS requirements: We conducted this on Ubuntu 24
  - Programming language versions:Python3.9,Java1.8, and Java11
  - Required packages/libraries: Required are present in the repositories as requirments.txt and 
- **Installation Steps**: Step-by-step instructions to set up the environment
  - Setup insturction for GiantRepair and it dependies is provided in their README
  - we cloned all repos in ~. and the congig file we used is provided
  - Please Export you Java paths, Defects4j path and Openai API key

### 4. GenAI Usage

**GenAI Usage**: Briefly document any use of generative AI tools (e.g., ChatGPT, GitHub Copilot, Cursor) during the replication process. Include:

  - ChatGPt and Claude were used in this replication. Their main usage was setting up the Javas and making them work. Claude was specifically used to create the pipeline file called run_all.sh


## Grading Criteria for README

Your README will be evaluated based on the following aspects (Total: 40 points):

### 1. Completeness (10 points)
- [ ] All required sections are present
- [ ] Each section contains sufficient detail
- [ ] Repository structure is fully documented
- [ ] All files and folders are explained
- [ ] GenAI usage is documented (if any AI tools were used)

### 2. Clarity and Organization (5 points)
- [ ] Information is well-organized and easy to follow
- [ ] Instructions are clear and unambiguous
- [ ] Professional writing and formatting
- [ ] Proper use of markdown formatting (headers, code blocks, lists)

### 3. Setup and Reproducibility (10 points)
- [ ] Setup instructions are complete and accurate, i.e., we were able to rerun the scripts following your instructions and obtain the results you reported


## Best Practices

1. **Be Specific**: Include exact versions, paths, and commands rather than vague descriptions
2. **Keep It Updated**: Ensure the README reflects the current state of your repository
3. **Test Your Instructions**: Have someone else (or yourself in a fresh environment) follow the setup instructions
4. **Document AI Usage**: If you used any GenAI tools, be transparent about how they were used (e.g., understanding scripts, exploring datasets, understanding data fields)


## Acknowledgement

This guideline was developed with the assistance of [Cursor](https://www.cursor.com/), an AI-powered code editor. This tool was used to:

- Draft and refine this documentation iteratively
