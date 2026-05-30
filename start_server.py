import os
import subprocess
import sys

# Set environment variables
os.environ['DATABASE_URL'] = 'sqlite:///c:/Workspace/SEO-Audit-Automation-Tool-main/test_db.sqlite'
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
os.environ['OPENAI_API_KEY'] = 'test'
os.environ['SENTRY_DSN'] = ''
os.environ['DATADOG_API_KEY'] = ''
os.environ['SLACK_WEBHOOK'] = ''

# Change to project directory
os.chdir('c:/Workspace/SEO-Audit-Automation-Tool-main')

# Run uvicorn
subprocess.run([sys.executable, '-m', 'uvicorn', 'api:app', '--host', '127.0.0.1', '--port', '8000', '--log-level', 'info'])