"""
Test Setup - Verify all dependencies are installed correctly
Run this after installing packages to confirm everything works
"""

import sys

def test_python_version():
    """Check Python version"""
    print("Testing Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f" Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f" Python {version.major}.{version.minor}.{version.micro} - Need 3.10+")
        return False


def test_imports():
    """Test if all required packages can be imported"""
    print("\nTesting package imports...")
    
    packages = {
        'selenium': 'Selenium',
        'pandas': 'Pandas',
        'openpyxl': 'Openpyxl',
        'dotenv': 'Python-dotenv',
        'PIL': 'Pillow'
    }
    
    all_ok = True
    
    for package, name in packages.items():
        try:
            if package == 'dotenv':
                from dotenv import load_dotenv
            elif package == 'PIL':
                from PIL import Image
            else:
                __import__(package)
            
            # Get version if possible
            try:
                if package == 'dotenv':
                    import dotenv
                    mod = dotenv
                elif package == 'PIL':
                    import PIL
                    mod = PIL
                else:
                    mod = __import__(package)
                
                version = getattr(mod, '__version__', 'installed')
                print(f"{name}: {version}")
            except:
                print(f" {name}: installed")
                
        except ImportError:
            print(f"{name}: NOT INSTALLED")
            all_ok = False
    
    return all_ok


def test_webdriver():
    """Test Selenium WebDriver"""
    print("\nTesting Selenium WebDriver...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        
        print("  Installing ChromeDriver (first time may take a moment)...")
        
        # Set up driver
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run without opening window
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        
        # Test navigation
        driver.get("https://www.google.com")
        title = driver.title
        driver.quit()
        
        print(f" ChromeDriver working! (tested with: {title})")
        return True
        
    except Exception as e:
        print(f" ChromeDriver error: {e}")
        print("   Make sure Chrome browser is installed!")
        return False


def test_file_structure():
    """Check if project structure exists"""
    print("\nChecking project structure...")
    
    import os
    from pathlib import Path
    
    required_dirs = [
        'src',
        'src/playbooks',
        'src/utils',
        'tests',
        'data',
        'screenshots',
        'logs'
    ]
    
    required_files = [
        '.env',
        '.gitignore',
        'README.md'
    ]
    
    all_ok = True
    
    for directory in required_dirs:
        if Path(directory).exists():
            print(f"{directory}/")
        else:
            print(f" {directory}/ - MISSING")
            all_ok = False
    
    for file in required_files:
        if Path(file).exists():
            print(f" {file}")
        else:
            print(f"  {file} - missing (optional)")
    
    return all_ok


def test_excel_operations():
    """Test Excel read/write"""
    print("\nTesting Excel operations...")
    
    try:
        import pandas as pd
        from pathlib import Path
        
        # Create test Excel file
        test_file = Path('data/test.xlsx')
        test_file.parent.mkdir(exist_ok=True)
        
        # Create DataFrame
        df = pd.DataFrame({
            'Column1': [1, 2, 3],
            'Column2': ['A', 'B', 'C']
        })
        
        # Write to Excel
        df.to_excel(test_file, index=False, engine='openpyxl')
        
        # Read back
        df_read = pd.read_excel(test_file, engine='openpyxl')
        
        # Verify
        if df.equals(df_read):
            print(" Excel read/write working!")
            
            # Clean up
            test_file.unlink()
            return True
        else:
            print(" Excel data mismatch")
            return False
            
    except Exception as e:
        print(f"Excel operations failed: {e}")
        return False


def print_summary(results):
    """Print summary of tests"""
    print("\n" + "=" * 60)
    print("SETUP TEST SUMMARY")
    print("=" * 60)
    
    all_passed = all(results.values())
    
    for test_name, passed in results.items():
        status = " PASS" if passed else " FAIL"
        print(f"{status} - {test_name}")
    
    print("=" * 60)
    
    if all_passed:
        print("\n All tests passed! You're ready for Day 2!")
        print("\nNext steps:")
        print("1. Fill in credentials in .env file")
        print("2. Manually test login to 3-5 portals")
        print("3. Create job_queue.xlsx in data/ folder")
        print("\nThen proceed to Day 2: Building Excel Manager")
    else:
        print("\n  Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Missing packages: pip install selenium webdriver-manager pandas openpyxl python-dotenv pillow")
        print("- ChromeDriver issues: Make sure Chrome browser is installed")
        print("- Missing directories: Run setup_project.py")
    
    print()


def main():
    """Run all tests"""
    print("=" * 60)
    print("Vosyn Automation - Setup Verification")
    print("=" * 60)
    print()
    
    results = {}
    
    # Run tests
    results['Python Version'] = test_python_version()
    results['Package Imports'] = test_imports()
    results['Project Structure'] = test_file_structure()
    results['Excel Operations'] = test_excel_operations()
    results['Selenium WebDriver'] = test_webdriver()
    
    # Print summary
    print_summary(results)


if __name__ == "__main__":
    main()