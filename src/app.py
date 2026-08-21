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
    today_date = datetime.now().strftime("%B %d")
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily GitHub Explorer</title>
    <style>
        :root {{
            --bg-color: #f8f9fa;
            --text-main: #111827;
            --text-light: #6b7280;
            --accent-green: #10b981;
            --border-color: #e5e7eb;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
        }}
        .app-container {{
            background-color: #ffffff;
            width: 100%;
            max-width: 480px;
            min-height: 100vh;
            padding: 32px 24px;
            box-sizing: border-box;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }}
        .header-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 24px;
        }}
        .logo-area {{
            font-weight: 700;
            font-size: 1.2rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .logo-icon {{
            width: 24px;
            height: 24px;
            background-color: var(--text-main);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
        }}
        .menu-btn {{
            border: 1px solid var(--border-color);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
        }}
        .tags-row {{
            display: flex;
            gap: 12px;
            margin-bottom: 32px;
            overflow-x: auto;
            padding-bottom: 8px;
        }}
        .tag {{
            padding: 8px 16px;
            border-radius: 20px;
            border: 1px solid var(--border-color);
            font-size: 0.9rem;
            color: var(--text-main);
            white-space: nowrap;
        }}
        .tag.active {{
            background-color: var(--accent-green);
            color: white;
            border-color: var(--accent-green);
        }}
        .date {{
            font-family: "Georgia", serif;
            font-size: 3rem;
            margin: 0 0 24px 0;
            font-weight: 400;
            letter-spacing: -1px;
        }}
        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border: 1px solid var(--border-color);
            border-radius: 20px;
            font-size: 0.85rem;
            margin-bottom: 24px;
        }}
        .status-dot {{
            width: 8px;
            height: 8px;
            background-color: var(--accent-green);
            border-radius: 50%;
        }}
        .title {{
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.2;
            margin: 0 0 24px 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}
        .hero-image {{
            width: 100%;
            height: 240px;
            background-color: #f3f4f6;
            border-radius: 16px;
            margin-bottom: 24px;
            background-image: url('https://images.unsplash.com/photo-1618401471353-b98afee0b2eb?q=80&w=1000&auto=format&fit=crop');
            background-size: cover;
            background-position: center;
        }}
        .content {{
            font-size: 1.1rem;
            line-height: 1.6;
            color: var(--text-light);
            margin-bottom: 32px;
            white-space: pre-line;
        }}
        .author-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 24px;
            border-top: 1px solid var(--border-color);
        }}
        .author-info {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .author-avatar {{
            width: 40px;
            height: 40px;
            background-color: var(--border-color);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
        }}
        .author-details {{
            display: flex;
            flex-direction: column;
        }}
        .author-name {{
            font-weight: 600;
            font-size: 0.95rem;
        }}
        .meta-text {{
            font-size: 0.8rem;
            color: var(--text-light);
        }}
        .actions {{
            display: flex;
            gap: 12px;
        }}
        .action-btn {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            border: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-main);
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="app-container">
        <div class="header-top">
            <div class="logo-area">
                <div class="logo-icon">▲</div>
                RepoScout
            </div>
            <div class="menu-btn">≡</div>
        </div>
        
        <div class="tags-row">
            <div class="tag active">All</div>
            <div class="tag">Trending</div>
            <div class="tag">{repo_info['language']}</div>
            <div class="tag">GitHub</div>
        </div>

        <h1 class="date">{today_date}</h1>
        
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div class="status-badge">
                <div class="status-dot"></div>
                New today
            </div>
            <a href="{repo_info['url']}" target="_blank" style="color: var(--text-main); text-decoration: none; font-size: 0.9rem; font-weight: 600;">View repo →</a>
        </div>

        <h2 class="title">{repo_info['name']}</h2>
        
        <div class="hero-image"></div>
        
        <div class="content">
            {summary}
        </div>
        
        <div class="author-row">
            <div class="author-info">
                <div class="author-avatar">🤖</div>
                <div class="author-details">
                    <span class="author-name">Agent Explorer</span>
                    <span class="meta-text">⭐ {repo_info['stars']:,} Stars • 1 min read</span>
                </div>
            </div>
            <div class="actions">
                <a href="{repo_info['url']}" target="_blank" class="action-btn">↗</a>
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
