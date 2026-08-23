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

def send_telegram_message(repo_info, summary):
    """Sends the summary to a Telegram channel/chat."""
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("Telegram credentials not found, skipping Telegram post.")
        return
        
    message = f"🚀 *New Trending Repo*: [{repo_info['name']}]({repo_info['url']})\n\n"
    message += f"⭐ {repo_info['stars']:,} Stars | 💻 {repo_info['language']}\n\n"
    message += f"{summary}"
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Successfully posted to Telegram!")
    except Exception as e:
        print(f"Failed to post to Telegram: {e}")

def generate_html(repo_info, summary):
    """Generates a beautiful HTML page."""
    from datetime import datetime
    today_date = datetime.now().strftime("%B %d, %Y")
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily GitHub Explorer</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #000000;
            --surface-color: #0d1117;
            --border-color: #222222;
            --text-main: #ffffff;
            --text-dim: #8b949e;
            --accent-primary: #2f81f7;
            --accent-success: #238636;
        }}
        body {{
            font-family: 'Inter', -apple-system, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            line-height: 1.6;
        }}
        .app-container {{
            width: 100%;
            max-width: 1024px;
            min-height: 100vh;
            padding: 48px 24px;
            box-sizing: border-box;
        }}
        .top-nav {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 16px;
            margin-bottom: 40px;
        }}
        .logo-area {{
            font-weight: 600;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 12px;
            color: var(--text-dim);
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}
        .logo-icon {{
            color: var(--text-main);
        }}
        .date-badge {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
            color: var(--text-dim);
            background: var(--surface-color);
            padding: 4px 8px;
            border-radius: 4px;
            border: 1px solid var(--border-color);
        }}
        .hero-section {{
            margin-bottom: 32px;
        }}
        .hero-title {{
            font-size: 32px;
            font-weight: 600;
            margin: 0 0 8px 0;
            letter-spacing: -0.02em;
        }}
        .hero-subtitle {{
            font-size: 16px;
            color: var(--text-dim);
            margin: 0;
        }}
        .bento-grid {{
            display: grid;
            grid-template-columns: repeat(12, 1fr);
            gap: 16px;
        }}
        .bento-card {{
            background: var(--bg-color);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 24px;
            display: flex;
            flex-direction: column;
        }}
        .card-large {{
            grid-column: span 8;
        }}
        .card-small {{
            grid-column: span 4;
        }}
        @media (max-width: 768px) {{
            .card-large, .card-small {{
                grid-column: span 12;
            }}
        }}
        .card-header {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--text-dim);
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .summary-text {{
            font-size: 15px;
            color: #dfe2eb;
            white-space: pre-line;
            margin: 0;
        }}
        .stat-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid var(--border-color);
        }}
        .stat-row:last-child {{
            border-bottom: none;
            padding-bottom: 0;
        }}
        .stat-label {{
            color: var(--text-dim);
            font-size: 14px;
        }}
        .stat-value {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 14px;
            color: var(--text-main);
        }}
        .glow-value {{
            color: var(--accent-primary);
            text-shadow: 0 0 8px rgba(47, 129, 247, 0.4);
        }}
        .language-bar-container {{
            width: 100%;
            height: 6px;
            background: var(--surface-color);
            border-radius: 3px;
            margin-top: 8px;
            overflow: hidden;
            display: flex;
        }}
        .language-fill {{
            height: 100%;
            background: var(--accent-success);
            width: 100%;
        }}
        .action-button {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 8px 16px;
            background: var(--surface-color);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            text-decoration: none;
            border-radius: 4px;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
            margin-top: auto;
        }}
        .action-button:hover {{
            border-color: var(--accent-primary);
            background: rgba(47, 129, 247, 0.1);
        }}
    </style>
</head>
<body>
    <div class="app-container">
        <nav class="top-nav">
            <div class="logo-area">
                <span class="logo-icon">▲</span> Daily GitHub Explorer
            </div>
            <div class="date-badge">{today_date}</div>
        </nav>

        <header class="hero-section">
            <h1 class="hero-title">{repo_info['name']}</h1>
            <p class="hero-subtitle">{repo_info['description']}</p>
        </header>

        <div class="bento-grid">
            <!-- AI Summary Card -->
            <div class="bento-card card-large">
                <div class="card-header">
                    <span style="color: var(--accent-primary)">●</span> AI Analysis
                </div>
                <p class="summary-text">{summary}</p>
            </div>

            <!-- Repository Stats Card -->
            <div class="bento-card card-small">
                <div class="card-header">
                    <span style="color: var(--text-dim)">○</span> Technical Metrics
                </div>
                
                <div class="stat-row">
                    <span class="stat-label">Stars</span>
                    <span class="stat-value glow-value">{repo_info['stars']:,}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">Primary Language</span>
                    <span class="stat-value">{repo_info['language']}</span>
                </div>
                
                <div style="margin-top: 16px;">
                    <div class="stat-label" style="font-size: 12px; margin-bottom: 4px;">Language Distribution</div>
                    <div class="language-bar-container">
                        <div class="language-fill"></div>
                    </div>
                </div>

                <a href="{repo_info['url']}" target="_blank" class="action-button" style="margin-top: 32px;">
                    View on GitHub →
                </a>
            </div>
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
        
        print("Attempting to post to Telegram...")
        send_telegram_message(repo_info, summary)
        
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

if __name__ == "__main__":
    print("Running local test...")
    repo_info = fetch_trending_repo()
    print(f"Fetched repo: {repo_info['name']}")
    summary = generate_summary(repo_info)
    print("Generated summary.")
    html_content = generate_html(repo_info, summary)
    
    # Save locally instead of S3
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("Attempting to post to Telegram...")
    send_telegram_message(repo_info, summary)
    
    print("Successfully generated index.html locally! Open it in your browser to take a screenshot.")
