import os
import sys

# Append project root to sys.path so Django can locate hostel_project package
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hostel_project.settings')

from hostel_project.wsgi import application

# Vercel serverless entrypoint
app = application
