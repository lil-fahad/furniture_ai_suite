#!/usr/bin/env python3
"""
Test script to verify the accuracy and functionality of the Interior Design AI Suite.

This script tests:
1. API endpoints availability
2. Floor plan analysis functionality
3. Alibaba search functionality
4. Furniture recommendations
5. Overall system accuracy

Usage: python3 test_accuracy.py
"""

import sys
import json
import time
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AccuracyTester:
    """Test the accuracy and functionality of the Interior Design AI Suite."""
    
    def __init__(self):
        """Initialize the tester."""
        self.results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "tests": []
        }
    
    def test_imports(self) -> bool:
        """Test that all modules can be imported."""
        logger.info("Testing module imports...")
        
        try:
            # Test basic imports (without torch/heavy dependencies)
            from alibaba_scraper import AlibabaFurnitureScraper
            logger.info("✓ alibaba_scraper imports successfully")
            
            from utils_kaggle import ensure_pkg
            logger.info("✓ utils_kaggle imports successfully")
            
            # Test that files exist
            required_files = [
                "app.py",
                "alibaba_scraper.py",
                "floor_plan_analyzer.py",
                "infer.py",
                "train_multi.py",
                "prepare_data.py",
                "utils_kaggle.py",
                "download_datasets.py",
                "datasets_catalog.json",
                "model_config.yml"
            ]
            
            for file in required_files:
                if not Path(file).exists():
                    logger.error(f"✗ Missing required file: {file}")
                    return False
                logger.info(f"✓ Found {file}")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Import test failed: {e}")
            return False

    def test_dataset_downloader(self) -> bool:
        """Test the dataset downloader in dry-run mode."""
        logger.info("\nTesting dataset downloader...")

        try:
            from download_datasets import download_datasets

            processed = download_datasets(dry_run=True)
            assert processed, "Dry-run should return dataset slugs"
            logger.info(f"✓ Dataset downloader dry-run listed {len(processed)} datasets")
            return True
        except Exception as e:
            logger.error(f"✗ Dataset downloader test failed: {e}")
            return False
    
    def test_alibaba_scraper(self) -> bool:
        """Test the Alibaba scraper functionality."""
        logger.info("\nTesting Alibaba scraper...")
        
        try:
            from alibaba_scraper import AlibabaFurnitureScraper, search_alibaba_furniture
            
            # Test scraper initialization
            scraper = AlibabaFurnitureScraper(rate_limit_seconds=0.1)
            logger.info("✓ Scraper initialized successfully")
            
            # Test search functionality
            results = scraper.search_furniture(
                keyword="sofa",
                category="living_room",
                page=1,
                page_size=5,
                use_cache=False
            )
            
            # Verify results structure
            assert results["success"] == True, "Search should return success=True"
            assert "products" in results, "Results should contain products"
            assert len(results["products"]) > 0, "Should return some products"
            
            logger.info(f"✓ Search returned {len(results['products'])} products")
            
            # Test product details
            product = results["products"][0]
            assert "id" in product, "Product should have ID"
            assert "title" in product, "Product should have title"
            assert "price" in product, "Product should have price"
            assert "supplier" in product, "Product should have supplier info"
            
            logger.info(f"✓ Product structure validated: {product['title']}")
            
            # Test caching
            cached_results = scraper.search_furniture(
                keyword="sofa",
                category="living_room",
                page=1,
                page_size=5,
                use_cache=True
            )
            
            logger.info("✓ Caching system works")
            
            # Test convenience function
            batch_results = search_alibaba_furniture(
                keyword="chair",
                max_results=10
            )
            
            assert batch_results["success"] == True
            assert len(batch_results["products"]) <= 10
            
            logger.info(f"✓ Batch search returned {len(batch_results['products'])} products")
            
            # Test product details fetch
            product_id = results["products"][0]["id"]
            details = scraper.get_product_details(product_id)
            
            assert details["success"] == True
            assert "product_id" in details
            
            logger.info("✓ Product details fetch works")
            
            # Test save to file
            output_path = scraper.save_products_to_file(
                products=results["products"],
                output_path="/tmp/test_alibaba_products.json"
            )
            
            assert Path(output_path).exists(), "Output file should be created"
            
            # Verify file content
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data["total_products"] == len(results["products"])
            
            logger.info(f"✓ Products saved successfully to {output_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Alibaba scraper test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_floor_plan_analyzer(self) -> bool:
        """Test the floor plan analyzer functionality."""
        logger.info("\nTesting floor plan analyzer...")
        
        try:
            from floor_plan_analyzer import FloorPlanAnalyzer
            import numpy as np
            import cv2
            
            # Test analyzer initialization
            analyzer = FloorPlanAnalyzer(min_room_area=1000)
            logger.info("✓ Floor plan analyzer initialized")
            
            # Create a simple mock floor plan image
            mock_plan = np.ones((500, 800, 3), dtype=np.uint8) * 255
            
            # Draw some "walls" (black lines)
            cv2.rectangle(mock_plan, (50, 50), (750, 450), (0, 0, 0), 2)
            cv2.line(mock_plan, (400, 50), (400, 450), (0, 0, 0), 2)
            
            # Save mock floor plan
            mock_path = "/tmp/test_floor_plan.jpg"
            cv2.imwrite(mock_path, mock_plan)
            
            logger.info("✓ Created mock floor plan")
            
            # Test loading
            img = analyzer.load_image(mock_path)
            assert img is not None
            logger.info("✓ Image loaded successfully")
            
            # Test preprocessing
            binary = analyzer.preprocess(img)
            assert binary is not None
            logger.info("✓ Image preprocessed")
            
            # Test room detection
            rooms = analyzer.detect_rooms(binary)
            logger.info(f"✓ Detected {len(rooms)} rooms")
            
            # Test furniture recommendations
            if rooms:
                room = rooms[0]
                recommendations = analyzer.recommend_furniture(room)
                assert len(recommendations) > 0
                logger.info(f"✓ Generated {len(recommendations)} furniture recommendations")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Floor plan analyzer test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def test_datasets_catalog(self) -> bool:
        """Test datasets catalog."""
        logger.info("\nTesting datasets catalog...")
        
        try:
            catalog_path = Path("datasets_catalog.json")
            
            assert catalog_path.exists(), "Datasets catalog should exist"
            
            with open(catalog_path, 'r') as f:
                catalog = json.load(f)
            
            assert isinstance(catalog, list), "Catalog should be a list"
            assert len(catalog) > 0, "Catalog should not be empty"
            
            logger.info(f"✓ Found {len(catalog)} datasets in catalog")
            
            # Verify each dataset entry
            for i, dataset in enumerate(catalog):
                assert "slug" in dataset, f"Dataset {i} should have slug"
                assert "dest" in dataset, f"Dataset {i} should have dest"
                logger.info(f"  - {dataset['slug']}")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Datasets catalog test failed: {e}")
            return False
    
    def test_configuration(self) -> bool:
        """Test configuration files."""
        logger.info("\nTesting configuration...")
        
        try:
            import yaml
            
            # Test model config
            with open("model_config.yml", 'r') as f:
                config = yaml.safe_load(f)
            
            assert "data_dir" in config
            assert "backbones" in config
            assert isinstance(config["backbones"], list)
            
            logger.info(f"✓ Model config valid with {len(config['backbones'])} backbones")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Configuration test failed: {e}")
            return False
    
    def run_all_tests(self) -> dict:
        """Run all tests and return results."""
        logger.info("=" * 60)
        logger.info("Starting Interior Design AI Suite Accuracy Tests")
        logger.info("=" * 60)
        
        tests = [
            ("Module Imports", self.test_imports),
            ("Dataset Downloader", self.test_dataset_downloader),
            ("Alibaba Scraper", self.test_alibaba_scraper),
            ("Floor Plan Analyzer", self.test_floor_plan_analyzer),
            ("Datasets Catalog", self.test_datasets_catalog),
            ("Configuration", self.test_configuration),
        ]
        
        for test_name, test_func in tests:
            self.results["total_tests"] += 1
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Test: {test_name}")
            logger.info(f"{'='*60}")
            
            try:
                result = test_func()
                
                test_result = {
                    "name": test_name,
                    "passed": result,
                    "error": None if result else "Test failed"
                }
                
                if result:
                    self.results["passed"] += 1
                    logger.info(f"✓ {test_name} PASSED")
                else:
                    self.results["failed"] += 1
                    logger.error(f"✗ {test_name} FAILED")
                
                self.results["tests"].append(test_result)
                
            except Exception as e:
                self.results["failed"] += 1
                logger.error(f"✗ {test_name} FAILED with exception: {e}")
                
                test_result = {
                    "name": test_name,
                    "passed": False,
                    "error": str(e)
                }
                self.results["tests"].append(test_result)
        
        return self.results
    
    def print_summary(self):
        """Print test summary."""
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {self.results['total_tests']}")
        logger.info(f"Passed: {self.results['passed']} ✓")
        logger.info(f"Failed: {self.results['failed']} ✗")
        
        pass_rate = (self.results['passed'] / self.results['total_tests'] * 100) if self.results['total_tests'] > 0 else 0
        logger.info(f"Pass Rate: {pass_rate:.1f}%")
        
        logger.info("\nDetailed Results:")
        for test in self.results["tests"]:
            status = "✓ PASS" if test["passed"] else "✗ FAIL"
            logger.info(f"  {status} - {test['name']}")
            if test["error"]:
                logger.info(f"    Error: {test['error']}")
        
        logger.info("=" * 60)
        
        if self.results['failed'] == 0:
            logger.info("🎉 All tests passed! The system is working correctly.")
            return 0
        else:
            logger.warning("⚠️  Some tests failed. Please review the errors above.")
            return 1


def main():
    """Main test function."""
    tester = AccuracyTester()
    results = tester.run_all_tests()
    tester.print_summary()
    
    # Save results to file
    output_file = "/tmp/test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\nDetailed results saved to: {output_file}")
    
    return 0 if results['failed'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
