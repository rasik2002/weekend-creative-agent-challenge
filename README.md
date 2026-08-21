# Daily GitHub Explorer 🚀

An autonomous AI Agent that automatically hunts for trending GitHub repositories and summarizes them using Amazon Bedrock. 

## How it works
This project uses a 100% serverless AWS architecture:
1. **Amazon EventBridge** wakes up the agent every morning at 6:00 AM UTC.
2. **AWS Lambda** executes the core Python logic to fetch trending repos.
3. **Amazon Bedrock (Nova Lite)** analyzes the repository and generates an enthusiastic summary.
4. The agent dynamically generates a beautiful HTML dashboard and deploys it live to an **Amazon S3** static website.
5. The agent hits the **Telegram Bot API** and broadcasts the summary directly to a Telegram channel.

## Live Demo
Check out the live generated dashboard here:
[Live Demo](http://daily-github-explorer-websitebucket-manb48k0shdu.s3-website-us-east-1.amazonaws.com)

## Deployment
This project is built using the AWS Serverless Application Model (SAM).
To deploy it yourself:
```bash
sam build
sam deploy --guided
```

## Architecture Diagram
*(Add your own screenshots or diagrams here!)*
