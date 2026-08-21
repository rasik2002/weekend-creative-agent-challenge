# Comprehensive Deployment Guide: Daily GitHub Explorer

This guide explains exactly how this serverless AI agent was built and how you can deploy it to any AWS account from scratch.

## 🏗️ Architecture Overview
The application is entirely serverless, ensuring it costs practically $0.00 to run:
- **Amazon EventBridge**: Triggers a cron schedule every day at 6:00 AM UTC.
- **AWS Lambda**: Runs the Python code (`app.py`), orchestrates API calls, and generates the HTML.
- **Amazon Bedrock**: Uses the `amazon.nova-lite-v1:0` model to analyze the GitHub repo and write a summary.
- **Amazon S3**: Hosts the dynamically generated HTML dashboard as a public static website.
- **Telegram Bot API**: Receives a push notification broadcast from the Lambda function.

---

## 📋 Prerequisites
Before deploying, ensure you have the following:
1. **AWS Account**: An active AWS account.
2. **AWS SAM CLI**: Installed on your local machine (`winget install Amazon.SAM-CLI` on Windows).
3. **Python 3.11**: Installed locally.
4. **IAM Credentials**: An AWS IAM User with `AdministratorAccess` (Access Key & Secret Key configured locally).

---

## 🚀 Step 1: Enable Amazon Bedrock
By default, AI models in AWS are disabled. 
1. Log into the AWS Console and go to **Amazon Bedrock**.
2. If this is a brand new account, model access is now enabled automatically upon first invocation! Otherwise, go to **Model access** and explicitly enable **Amazon Nova Lite**.

---

## 🤖 Step 2: Set up Telegram Notification (Optional)
If you want the agent to ping your phone:
1. Open the Telegram App and message **@BotFather**.
2. Send `/newbot` and follow the prompts to get your **Bot Token**.
3. Create a Telegram Group, add your bot as an Admin, and retrieve the **Chat ID**.
4. Open `template.yaml` in this project and replace `YOUR_TELEGRAM_BOT_TOKEN_HERE` and `YOUR_TELEGRAM_CHAT_ID_HERE` with your actual credentials.

---

## 🛠️ Step 3: Build & Package Dependencies
Because the Lambda function relies on external libraries (`requests`, `beautifulsoup4`), we need to package them locally before building so SAM can zip them up.

Open your terminal in the project folder and run:
```bash
# Install the python dependencies directly into the source folder
pip install -r src/requirements.txt -t src/

# Tell SAM to build the deployment package
sam build
```

---

## ☁️ Step 4: Deploy to AWS
Once the build is successful, deploy the infrastructure to the cloud:

```bash
sam deploy --guided
```

SAM will ask you a series of questions. Press **Enter** to accept the defaults for everything, except:
- `Deploy this changeset? [y/N]:` (Type **y**)
- `AgentFunctionDailyTriggerPermission may not have authorization defined, Is this okay? [y/N]:` (Type **y**)

---

## 🎉 Step 5: Verify Your Deployment
Once the deployment finishes, the SAM CLI will output two things:
1. The **ARN** of your Lambda Function.
2. The **WebsiteURL** of your S3 Bucket (e.g., `http://daily-github-explorer-websitebucket...s3-website-us-east-1.amazonaws.com`).

**Note on 404 Errors:** 
If you visit the URL immediately, you will get a `404 Not Found` error. This is because the EventBridge schedule hasn't triggered yet! To see it immediately, go to the AWS Lambda Console and manually click "Test" to invoke the function once. 

## 🧹 Step 6: Cleanup
If you ever want to destroy the agent and stop all services, simply run:
```bash
sam delete
```
