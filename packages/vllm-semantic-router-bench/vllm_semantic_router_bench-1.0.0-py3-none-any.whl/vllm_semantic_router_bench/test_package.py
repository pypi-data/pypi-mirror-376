#!/usr/bin/env python3
"""
Test script to verify the package structure and imports work correctly.
"""


def test_imports():
    """Test that all main imports work correctly."""
    print("🧪 Testing package imports...")

    try:
        # Test main package import
        import vllm_semantic_router_bench

        print(f"✅ Main package: {vllm_semantic_router_bench.__version__}")

        # Test core interfaces
        from vllm_semantic_router_bench import DatasetInfo, DatasetInterface, Question

        print("✅ Core interfaces imported")

        # Test factory
        from vllm_semantic_router_bench import DatasetFactory, list_available_datasets

        print("✅ Factory classes imported")

        # Test dataset factory functionality
        datasets = list_available_datasets()
        print(f"✅ Available datasets: {datasets}")

        # Test creating a dataset
        factory = DatasetFactory()
        dataset = factory.create_dataset("mmlu")
        print("✅ Dataset creation works")

        print("\n🎉 All imports successful!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_cli():
    """Test that CLI entry points are working."""
    print("\n🧪 Testing CLI entry points...")

    try:
        import vllm_semantic_router_bench.cli

        print("✅ CLI module imported")

        # Test that main function exists
        assert hasattr(vllm_semantic_router_bench.cli, "main")
        print("✅ CLI main function exists")

        return True

    except Exception as e:
        print(f"❌ CLI test error: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Testing vLLM Semantic Router Bench Package")
    print("=" * 50)

    success = True
    success &= test_imports()
    success &= test_cli()

    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed! Package is ready for PyPI.")
    else:
        print("❌ Some tests failed. Please fix issues before publishing.")

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
