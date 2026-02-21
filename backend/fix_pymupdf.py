"""Fix PyMuPDF DLL loading issue on Windows."""
import subprocess
import sys

def fix_pymupdf():
    """Reinstall PyMuPDF with proper binary wheels."""
    print("Fixing PyMuPDF installation...")

    # First uninstall
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "PyMuPDF", "pymupdf", "-y"],
                   capture_output=True)

    # Clear pip cache
    subprocess.run([sys.executable, "-m", "pip", "cache", "purge"],
                   capture_output=True)

    # Install specific version that works on Windows
    print("Installing PyMuPDF 1.23.26...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "PyMuPDF==1.23.26", "--force-reinstall", "--no-cache-dir"],
        capture_output=False,
        text=True
    )

    if result.returncode == 0:
        print("PyMuPDF installed successfully!")
        print("Please restart the backend server.")
    else:
        print("Installation failed. Trying alternative approach...")
        # Try installing from wheel
        result2 = subprocess.run(
            [sys.executable, "-m", "pip", "install", "PyMuPDF", "--only-binary", ":all:", "--force-reinstall"],
            capture_output=False,
            text=True
        )
        if result2.returncode == 0:
            print("PyMuPDF installed successfully!")
        else:
            print("Failed to install PyMuPDF. Please try manually:")
            print("  pip install PyMuPDF==1.23.26 --force-reinstall")

if __name__ == "__main__":
    fix_pymupdf()
