import json
import os
import random
import boto3
import requests
from datetime import datetime, timedelta

# Initialize boto3 clients
bedrock = boto3.client(service_name='bedrock-runtime')
s3 = boto3.client('s3')

def fetch_trending_repo():
    """Fetches a list of repositories created recently that are popular."""
    # We query GitHub for repos created in the last 7 days sorted by stars
    date_a_week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    url = f"https://api.github.com/search/repositories?q=created:>{date_a_week_ago}&sort=stars&order=desc"
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "DailyGitHubExplorerAgent"
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    
    items = data.get('items', [])
    if not items:
        raise Exception("No repos found")
        
    # Pick a random one from the top 10
    repo = random.choice(items[:10])
    
    return {
        'name': repo['full_name'],
        'description': repo['description'] or "No description provided.",
        'url': repo['html_url'],
        'stars': repo['stargazers_count'],
        'language': repo['language'] or "Unknown"
    }

def generate_summary(repo_info):
    """Uses Bedrock to generate a fun, engaging summary."""
    prompt = f"""You are an enthusiastic developer advocate. I will give you a trending GitHub repository.
Write a fun, short (2 paragraph) summary of what this repo does and why developers should care about it.

Repo Name: {repo_info['name']}
Language: {repo_info['language']}
Description: {repo_info['description']}
Stars: {repo_info['stars']}

Output ONLY the summary text, nothing else. Make it engaging!"""

    try:
        # Using Amazon Nova Lite as specified in the challenge.
        # Ensure you have requested model access to Nova Lite in your AWS region.
        # If you prefer Anthropic Claude, you can change this to: anthropic.claude-3-haiku-20240307-v1:0
        model_id = "amazon.nova-lite-v1:0"
        
        # We use the new Bedrock Converse API as it normalizes input/output across all models
        response = bedrock.converse(
            modelId=model_id,
            messages=[{
                "role": "user",
                "content": [{"text": prompt}]
            }],
            inferenceConfig={
                "maxTokens": 500,
                "temperature": 0.7
            }
        )
        
        summary = response['output']['message']['content'][0]['text']
        return summary
    except Exception as e:
        print(f"Bedrock invocation failed, falling back to basic summary. Error: {e}")
        return f"This repository, {repo_info['name']}, is built in {repo_info['language']} and has {repo_info['stars']} stars! The author describes it as: {repo_info['description']}. Go check it out!"

def generate_html(repo_info, summary):
    """Generates a beautiful HTML page."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily GitHub Explorer</title>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent: #3b82f6;
            --accent-hover: #60a5fa;
        }}
        body {{
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            background: var(--card-bg);
            border-radius: 16px;
            padding: 40px;
            max-width: 600px;
            width: 100%;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            border: 1px solid #334155;
            transition: transform 0.3s ease;
        }}
        .container:hover {{
            transform: translateY(-5px);
        }}
        h1 {{
            font-size: 1.5rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 20px;
            font-weight: 600;
        }}
        .repo-name {{
            font-size: 2.5rem;
            margin: 0 0 10px 0;
            background: linear-gradient(to right, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .stats {{
            display: flex;
            gap: 15px;
            margin-bottom: 25px;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}
        .stat-badge {{
            background: rgba(255,255,255,0.05);
            padding: 4px 12px;
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .summary {{
            font-size: 1.1rem;
            line-height: 1.7;
            margin-bottom: 30px;
            white-space: pre-line;
        }}
        .btn {{
            display: inline-block;
            background-color: var(--accent);
            color: white;
            text-decoration: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 600;
            transition: background-color 0.2s;
        }}
        .btn:hover {{
            background-color: var(--accent-hover);
        }}
        .footer {{
            margin-top: 30px;
            font-size: 0.8rem;
            color: var(--text-secondary);
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Trending Repo of the Day</h1>
        <h2 class="repo-name">{repo_info['name']}</h2>
        <div class="stats">
            <span class="stat-badge">⭐ {repo_info['stars']:,} Stars</span>
            <span class="stat-badge">💻 {repo_info['language']}</span>
        </div>
        <div class="summary">
            {summary}
        </div>
        <a href="{repo_info['url']}" target="_blank" class="btn">View on GitHub</a>
        
        <div class="footer">
            Generated autonomously by Daily GitHub Explorer on AWS.
        </div>
    </div>
</body>
</html>"""
    return html

def lambda_handler(event, context):
    try:
        bucket_name = os.environ['BUCKET_NAME']
        
        print("Fetching trending repo...")
        repo_info = fetch_trending_repo()
        
        print(f"Generating summary for {repo_info['name']}...")
        summary = generate_summary(repo_info)
        
        print("Generating HTML...")
        html_content = generate_html(repo_info, summary)
        
        print(f"Uploading to S3 bucket {bucket_name}...")
        s3.put_object(
            Bucket=bucket_name,
            Key='index.html',
            Body=html_content,
            ContentType='text/html',
            CacheControl='max-age=0' # Don't cache so we see the new one every day
        )
        
        website_url = f"http://{bucket_name}.s3-website-{os.environ.get('AWS_REGION', 'us-east-1')}.amazonaws.com"
        print(f"Successfully generated and uploaded today's site! View it at: {website_url}")
        
        return {
            'statusCode': 200,
            'body': json.dumps('Success! Site generated.')
        }
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
