"""
Beijerterm Admin Panel
Custom CMS for managing glossaries, terms, and resources
"""
import os
import sys
import json
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import requests

# Add parent directory to path to import build script utilities
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# GitHub OAuth configuration
GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID', '')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET', '')
GITHUB_REPO_OWNER = 'michaelbeijer'
GITHUB_REPO_NAME = 'beijerterm'

# Content paths
BASE_DIR = Path(__file__).parent.parent
CONTENT_DIR = BASE_DIR / 'content'
GLOSSARIES_DIR = CONTENT_DIR / 'glossaries'
TERMS_DIR = CONTENT_DIR / 'terms'
RESOURCES_DIR = CONTENT_DIR / 'resources'


def get_github_token() -> Optional[str]:
    """Get GitHub token from session"""
    return session.get('github_token')


def require_auth(f):
    """Decorator to require GitHub authentication"""
    def wrapper(*args, **kwargs):
        if 'github_token' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


def parse_glossary_markdown(content: str) -> Dict:
    """Parse a glossary markdown file into structured data"""
    if not content.startswith('---'):
        return {'title': 'Unknown', 'source_lang': 'nl', 'target_lang': 'en', 'entries': []}
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {'title': 'Unknown', 'source_lang': 'nl', 'target_lang': 'en', 'entries': []}
    
    # Parse frontmatter
    frontmatter = yaml.safe_load(parts[1])
    
    # Parse markdown table
    table_content = parts[2].strip()
    lines = [line.strip() for line in table_content.split('\n') if line.strip() and '|' in line]
    
    entries = []
    for i, line in enumerate(lines):
        if i == 0:  # Skip header
            continue
        if line.startswith('|-'):  # Skip separator
            continue
        
        # Parse table row
        cells = [cell.strip() for cell in line.split('|')]
        cells = [c for c in cells if c]  # Remove empty cells
        
        if len(cells) >= 2:
            entries.append({
                'source': cells[0],
                'target': cells[1],
                'notes': cells[2] if len(cells) > 2 else ''
            })
    
    return {
        'title': frontmatter.get('title', 'Unknown'),
        'source_lang': frontmatter.get('source_lang', 'nl'),
        'target_lang': frontmatter.get('target_lang', 'en'),
        'entries': entries
    }


def generate_glossary_markdown(data: Dict) -> str:
    """Generate markdown file from glossary data"""
    # Build frontmatter
    frontmatter = yaml.dump({
        'title': data.get('title', 'Unknown'),
        'source_lang': data.get('source_lang', 'nl'),
        'target_lang': data.get('target_lang', 'en')
    }, allow_unicode=True, sort_keys=False)
    
    # Build markdown table
    source_lang = data.get('source_lang', 'nl').upper()
    target_lang = data.get('target_lang', 'en').upper()
    
    table = f"| {source_lang} | {target_lang} | Notes |\n"
    table += "|---|---|---|\n"
    
    for entry in data.get('entries', []):
        source = entry.get('source', '').replace('|', '\\|')
        target = entry.get('target', '').replace('|', '\\|')
        notes = entry.get('notes', '').replace('|', '\\|')
        table += f"| {source} | {target} | {notes} |\n"
    
    return f"---\n{frontmatter}---\n\n{table}"


@app.route('/')
@require_auth
def index():
    """Admin dashboard"""
    stats = {
        'glossaries': len(list(GLOSSARIES_DIR.rglob('*.md'))),
        'terms': len(list(TERMS_DIR.glob('*.md'))),
        'resources': len(list(RESOURCES_DIR.glob('*.md')))
    }
    return render_template('index.html', stats=stats)


@app.route('/login')
def login():
    """GitHub OAuth login page"""
    if 'github_token' in session:
        return redirect(url_for('index'))
    
    # For development, allow bypassing OAuth
    dev_mode = os.environ.get('ADMIN_DEV_MODE') == 'true'
    
    return render_template('login.html', 
                          github_client_id=GITHUB_CLIENT_ID,
                          dev_mode=dev_mode)


@app.route('/auth/github/callback')
def github_callback():
    """Handle GitHub OAuth callback"""
    code = request.args.get('code')
    if not code:
        return 'Error: No authorization code received', 400
    
    # Exchange code for access token
    token_url = 'https://github.com/login/oauth/access_token'
    response = requests.post(token_url, data={
        'client_id': GITHUB_CLIENT_ID,
        'client_secret': GITHUB_CLIENT_SECRET,
        'code': code
    }, headers={'Accept': 'application/json'})
    
    if response.status_code != 200:
        return f'Error getting access token: {response.text}', 400
    
    data = response.json()
    access_token = data.get('access_token')
    
    if not access_token:
        return 'Error: No access token in response', 400
    
    # Store token in session
    session['github_token'] = access_token
    
    # Get user info
    user_response = requests.get('https://api.github.com/user', 
                                 headers={'Authorization': f'token {access_token}'})
    if user_response.status_code == 200:
        user_data = user_response.json()
        session['github_user'] = user_data.get('login')
    
    return redirect(url_for('index'))


@app.route('/auth/dev-login', methods=['POST'])
def dev_login():
    """Development mode login (bypass OAuth)"""
    if os.environ.get('ADMIN_DEV_MODE') != 'true':
        return 'Dev mode not enabled', 403
    
    session['github_token'] = 'dev-token'
    session['github_user'] = 'dev-user'
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('login'))


@app.route('/glossaries')
@require_auth
def glossaries():
    """List all glossaries"""
    glossary_files = sorted(GLOSSARIES_DIR.rglob('*.md'))
    glossaries_data = []
    
    for file in glossary_files:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Parse frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    # Count entries in markdown table
                    table_content = parts[2].strip()
                    entry_count = len([line for line in table_content.split('\n') if line.strip() and '|' in line]) - 1  # Subtract header
                    
                    glossaries_data.append({
                        'filename': file.stem,
                        'title': frontmatter.get('title', file.stem),
                        'source_lang': frontmatter.get('source_lang', 'nl'),
                        'target_lang': frontmatter.get('target_lang', 'en'),
                        'entry_count': max(0, entry_count)
                    })
    
    return render_template('glossaries.html', glossaries=glossaries_data)


@app.route('/glossaries/<filename>')
@require_auth
def edit_glossary(filename):
    """Edit a specific glossary"""
    # Search recursively for the glossary file in subdirectories
    file_path = None
    for md_file in GLOSSARIES_DIR.rglob(f'{filename}.md'):
        file_path = md_file
        break
    
    if not file_path or not file_path.exists():
        return 'Glossary not found', 404
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse frontmatter and table
    data = parse_glossary_markdown(content)
    
    return render_template('glossary_editor.html', 
                          filename=filename,
                          glossary=data)


@app.route('/api/glossaries/<filename>', methods=['GET', 'POST'])
@require_auth
def api_glossary(filename):
    """Get or update a specific glossary (JSON)"""
    # Search recursively for the glossary file in subdirectories
    file_path = None
    for md_file in GLOSSARIES_DIR.rglob(f'{filename}.md'):
        file_path = md_file
        break
    
    if request.method == 'GET':
        if not file_path or not file_path.exists():
            return jsonify({'error': 'Glossary not found'}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        data = parse_glossary_markdown(content)
        return jsonify(data)
    
    elif request.method == 'POST':
        # Save glossary changes
        data = request.json
        
        # Convert back to markdown format
        markdown = generate_glossary_markdown(data)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        # TODO: Commit to GitHub
        
        return jsonify({'success': True})


@app.route('/terms')
@require_auth
def terms():
    """List all term pages"""
    term_files = sorted(TERMS_DIR.glob('*.md'))
    terms_data = []
    
    for file in term_files:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Extract frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    terms_data.append({
                        'filename': file.stem,
                        'title': frontmatter.get('title', file.stem),
                        'description': frontmatter.get('description', '')
                    })
    
    return render_template('terms.html', terms=terms_data)


@app.route('/terms/<filename>')
@require_auth
def edit_term(filename):
    """Edit a specific term page"""
    file_path = TERMS_DIR / f'{filename}.md'
    
    if not file_path.exists():
        return 'Term not found', 404
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return render_template('term_editor.html', 
                          filename=filename,
                          content=content)


@app.route('/api/terms/<filename>', methods=['GET', 'POST'])
@require_auth
def api_term(filename):
    """API endpoint for term data"""
    file_path = TERMS_DIR / f'{filename}.md'
    
    if request.method == 'GET':
        if not file_path.exists():
            return jsonify({'error': 'Term not found'}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({'content': content})
    
    elif request.method == 'POST':
        # Save term changes
        content = request.json.get('content', '')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # TODO: Commit to GitHub
        
        return jsonify({'success': True})


@app.route('/resources')
@require_auth
def resources():
    """List all resource pages"""
    resource_files = sorted(RESOURCES_DIR.glob('*.md'))
    resources_data = []
    
    for file in resource_files:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Extract frontmatter if present
            title = file.stem
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    title = frontmatter.get('title', title)
            
            resources_data.append({
                'filename': file.stem,
                'title': title
            })
    
    return render_template('resources.html', resources=resources_data)


@app.route('/resources/<filename>')
@require_auth
def edit_resource(filename):
    """Edit a specific resource page"""
    file_path = RESOURCES_DIR / f'{filename}.md'
    
    if not file_path.exists():
        return 'Resource not found', 404
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return render_template('resource_editor.html', 
                          filename=filename,
                          content=content)


@app.route('/api/resources/<filename>', methods=['GET', 'POST'])
@require_auth
def api_resource(filename):
    """API endpoint for resource data"""
    file_path = RESOURCES_DIR / f'{filename}.md'
    
    if request.method == 'GET':
        if not file_path.exists():
            return jsonify({'error': 'Resource not found'}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({'content': content})
    
    elif request.method == 'POST':
        # Save resource changes
        content = request.json.get('content', '')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # TODO: Commit to GitHub
        
        return jsonify({'success': True})


if __name__ == '__main__':
    # For development
    port = int(os.environ.get('ADMIN_PORT', 5000))
    debug = os.environ.get('ADMIN_DEBUG', 'true').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
