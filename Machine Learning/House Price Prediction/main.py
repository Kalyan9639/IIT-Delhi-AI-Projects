"""
Main Execution Script for Bangalore Real Estate Intelligence System.
Provides a user-friendly interface to run the complete ML pipeline.
"""

import os
import sys
import subprocess
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))


def print_header():
    """Print application header."""
    print("\n" + "=" * 80)
    print("🏠 BANGALORE REAL ESTATE INTELLIGENCE SYSTEM")
    print("AI-Powered Real Estate Analytics & Price Prediction Platform")
    print("=" * 80 + "\n")


def check_dependencies():
    """Check if required dependencies are installed."""
    print("Checking dependencies...")
    
    required_packages = [
        'pandas', 'numpy', 'scikit-learn', 'xgboost', 'lightgbm', 
        'catboost', 'shap', 'plotly', 'streamlit', 'folium'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✓ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"  ✗ {package} - NOT INSTALLED")
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Please run: pip install -r requirements.txt")
        return False
    
    print("\n✓ All dependencies satisfied!")
    return True


def run_pipeline():
    """Run the complete ML pipeline."""
    print("\n" + "=" * 80)
    print("RUNNING ML PIPELINE")
    print("=" * 80 + "\n")
    
    try:
        # Import and run the training script
        from train_pipeline import main
        df, model_trainer = main()
        return True
    except Exception as e:
        print(f"\n❌ Error running pipeline: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_streamlit():
    """Run the Streamlit application."""
    print("\n" + "=" * 80)
    print("STARTING STREAMLIT APPLICATION")
    print("=" * 80 + "\n")
    
    try:
        # Check if streamlit is installed
        try:
            import streamlit
        except ImportError:
            print("Streamlit not installed. Installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
        
        # Run streamlit
        streamlit_path = Path(__file__).parent / 'streamlit_app' / 'main.py'
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(streamlit_path)])
        
    except KeyboardInterrupt:
        print("\nStreamlit application stopped.")
    except Exception as e:
        print(f"\n❌ Error running Streamlit: {str(e)}")
        import traceback
        traceback.print_exc()


def show_menu():
    """Display main menu."""
    print("\n" + "=" * 80)
    print("MAIN MENU")
    print("=" * 80)
    print("\nSelect an option:")
    print("  1. Run ML Pipeline (Train Models)")
    print("  2. Start Streamlit Application")
    print("  3. Run Both (Pipeline + App)")
    print("  4. Exit")
    print("=" * 80)


def main():
    """Main function."""
    print_header()
    
    # Check dependencies
    if not check_dependencies():
        print("\nPlease install missing dependencies and try again.")
        return
    
    while True:
        show_menu()
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            print("\n" + "=" * 80)
            print("ML PIPELINE")
            print("=" * 80)
            run_pipeline()
        
        elif choice == '2':
            print("\n" + "=" * 80)
            print("STREAMLIT APPLICATION")
            print("=" * 80)
            run_streamlit()
        
        elif choice == '3':
            print("\n" + "=" * 80)
            print("RUNNING BOTH PIPELINE AND APPLICATION")
            print("=" * 80)
            
            # Run pipeline first
            if run_pipeline():
                # Then run streamlit
                input("\nPress Enter to start Streamlit application...")
                run_streamlit()
            else:
                print("\nPipeline failed. Please check the errors above.")
        
        elif choice == '4':
            print("\nThank you for using Bangalore Real Estate Intelligence System!")
            print("Goodbye! 👋\n")
            break
        
        else:
            print("\n❌ Invalid choice. Please enter 1, 2, 3, or 4.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nApplication interrupted by user.")
        print("Goodbye! 👋\n")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
