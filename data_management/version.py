import subprocess

def get_version():
    """
    Get version from git
    """
    try:
        label = subprocess.check_output(["git", "describe", "--tags"]).strip().decode('utf-8')
    except:
        label = ''

    return label
