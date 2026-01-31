"""Test script for DeepFurniture dataset integration.

This script demonstrates and tests the DeepFurniture dataset cloning functionality
without requiring actual network access to Hugging Face.
"""
import json
import logging
from pathlib import Path
from utils_kaggle import huggingface_clone, folder_has_content, DEFAULT_MIN_FILES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_catalog_entry():
    """Test that DeepFurniture is properly registered in the catalog."""
    logger.info("Test 1: Checking datasets_catalog.json")
    
    catalog_path = Path("datasets_catalog.json")
    if not catalog_path.exists():
        logger.error("✗ datasets_catalog.json not found")
        return False
    
    catalog = json.loads(catalog_path.read_text())
    
    # Find DeepFurniture entry
    deepfurniture_entry = None
    for item in catalog:
        if item.get("source") == "huggingface" and "DeepFurniture" in item.get("repo_url", ""):
            deepfurniture_entry = item
            break
    
    if deepfurniture_entry:
        logger.info("✓ DeepFurniture entry found in catalog")
        logger.info(f"  - Source: {deepfurniture_entry.get('source')}")
        logger.info(f"  - Repo URL: {deepfurniture_entry.get('repo_url')}")
        logger.info(f"  - Destination: {deepfurniture_entry.get('dest')}")
        logger.info(f"  - Description: {deepfurniture_entry.get('description')}")
        return True
    else:
        logger.error("✗ DeepFurniture entry not found in catalog")
        return False


def test_skip_logic():
    """Test the skip_if_exists logic."""
    logger.info("\nTest 2: Testing skip_if_exists logic")
    
    # Create a test directory with enough files
    test_dir = Path("data/raw/test_skip_logic")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Create test files (one more than DEFAULT_MIN_FILES to ensure skip logic triggers)
    for i in range(DEFAULT_MIN_FILES + 1):
        (test_dir / f"test{i}.txt").write_text(f"test content {i}")
    
    # Test folder_has_content
    has_content = folder_has_content(str(test_dir), min_files=DEFAULT_MIN_FILES)
    
    if has_content:
        logger.info("✓ folder_has_content correctly detected existing files")
    else:
        logger.error("✗ folder_has_content failed to detect files")
        return False
    
    # Test skip logic
    try:
        huggingface_clone(
            "https://example.com/test",
            str(test_dir),
            skip_if_exists=True
        )
        logger.info("✓ Skip logic works - existing directory was skipped")
        
        # Clean up
        import shutil
        shutil.rmtree(test_dir)
        
        return True
    except Exception as e:
        logger.error(f"✗ Skip logic failed: {e}")
        return False


def test_function_signature():
    """Test that the huggingface_clone function has correct signature."""
    logger.info("\nTest 3: Checking function signature")
    
    import inspect
    sig = inspect.signature(huggingface_clone)
    params = list(sig.parameters.keys())
    
    expected_params = ["repo_url", "dest", "skip_if_exists", "min_files"]
    
    if params == expected_params:
        logger.info("✓ Function signature is correct")
        logger.info(f"  Parameters: {', '.join(params)}")
        return True
    else:
        logger.error(f"✗ Function signature mismatch")
        logger.error(f"  Expected: {expected_params}")
        logger.error(f"  Got: {params}")
        return False


def test_git_availability():
    """Test that git is available in the environment."""
    logger.info("\nTest 4: Checking git availability")
    
    from shutil import which
    
    if which("git"):
        logger.info("✓ Git is available")
        
        # Get git version
        import subprocess
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True
        )
        logger.info(f"  Version: {result.stdout.strip()}")
        return True
    else:
        logger.error("✗ Git is not available")
        return False


def main():
    """Run all tests."""
    logger.info("=" * 70)
    logger.info("DeepFurniture Integration Test Suite")
    logger.info("=" * 70)
    
    tests = [
        ("Catalog Entry", test_catalog_entry),
        ("Skip Logic", test_skip_logic),
        ("Function Signature", test_function_signature),
        ("Git Availability", test_git_availability),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"✗ Test '{test_name}' raised exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    logger.info("\n" + "=" * 70)
    logger.info("Test Summary")
    logger.info("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"{test_name:.<40} {status}")
    
    logger.info("-" * 70)
    logger.info(f"Total: {passed}/{total} tests passed")
    logger.info("=" * 70)
    
    if passed == total:
        logger.info("\n🎉 All tests passed! The DeepFurniture integration is ready.")
        logger.info("\nUsage:")
        logger.info("  1. Via CLI: python clone_deepfurniture.py")
        logger.info("  2. Via API: POST /clone-deepfurniture")
        logger.info("  3. Via /download endpoint (processes all datasets)")
    else:
        logger.warning(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
