import os
import sys
import subprocess
import time
import urllib.request
import urllib.error

os.environ['DATABASE_URL'] = 'sqlite:///c:/Workspace/SEO-Audit-Automation-Tool-main/test_db.sqlite'
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
os.environ['OPENAI_API_KEY'] = 'test'
os.environ['SENTRY_DSN'] = ''
os.environ['DATADOG_API_KEY'] = ''
os.environ['SLACK_WEBHOOK'] = ''

cwd = 'c:/Workspace/SEO-Audit-Automation-Tool-main'
cmd = [sys.executable, '-m', 'uvicorn', 'api:app', '--host', '127.0.0.1', '--port', '8000', '--log-level', 'info']
proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

start_time = time.time()
startup_output = []
started = False

while time.time() - start_time < 45:
    line = proc.stdout.readline()
    if line:
        startup_output.append(line)
        if 'Application startup complete.' in line or 'Uvicorn running on http' in line:
            started = True
            break
        if 'Traceback' in line:
            break
    else:
        time.sleep(0.1)

print('STARTED:', started)
print('RETURNCODE:', proc.poll())
print('\n'.join(startup_output[-20:]))

if not started:
    proc.terminate()
    proc.wait(timeout=5)
    sys.exit(1)

try:
    req = urllib.request.Request('http://127.0.0.1:8000/health')
    with urllib.request.urlopen(req, timeout=10) as response:
        print('STATUS', response.status)
        print(response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print('HTTPError', e.code)
    print(e.read().decode('utf-8'))
except Exception as exc:
    print('REQUEST_FAILED', str(exc))
else:
    # Capture trailing server logs for the request
    tail_lines = []
    tail_deadline = time.time() + 5
    while time.time() < tail_deadline:
        line = proc.stdout.readline()
        if line:
            tail_lines.append(line)
        else:
            time.sleep(0.1)

    print('TAIL_LOGS:')
    print(''.join(tail_lines))
finally:
    proc.terminate()
    proc.wait(timeout=5)
    print('SERVER_STOPPED', proc.returncode)
