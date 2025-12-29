"""
Security Features Test - Verify all security improvements
"""

from models.tax_data import TaxData
from pathlib import Path
import os

def test_encryption():
    """Test data encryption and decryption"""
    print("Testing Encryption...")
    
    # Create TaxData instance
    tax_data = TaxData()
    tax_data.set('personal_info.first_name', 'John')
    tax_data.set('personal_info.last_name', 'TestUser')
    tax_data.set('personal_info.ssn', '123-45-6789')
    
    # Save encrypted
    filename = tax_data.save_to_file('test_security.enc')
    print(f"✓ Saved encrypted file: {filename}")
    
    # Check file is not plaintext
    with open(filename, 'rb') as f:
        content = f.read(100)
        if b'John' in content or b'TestUser' in content:
            print("✗ FAIL: File contains plaintext data!")
            return False
    print("✓ File is encrypted (no plaintext detected)")
    
    # Check file permissions
    stat_info = os.stat(filename)
    permissions = oct(stat_info.st_mode)[-3:]
    print(f"✓ File permissions: {permissions}")
    
    # Load and verify
    tax_data2 = TaxData()
    tax_data2.load_from_file(filename)
    
    if tax_data2.get('personal_info.first_name') == 'John':
        print("✓ Decryption successful")
    else:
        print("✗ FAIL: Decryption failed")
        return False
    
    # Cleanup
    os.remove(filename)
    print("✓ Test file cleaned up\n")
    return True


def test_input_validation():
    """Test input validation"""
    print("Testing Input Validation...")
    
    tax_data = TaxData()
    
    # Test valid SSN
    try:
        tax_data.set('personal_info.ssn', '123-45-6789')
        print("✓ Valid SSN accepted")
    except ValueError:
        print("✗ FAIL: Valid SSN rejected")
        return False
    
    # Test invalid SSN
    try:
        tax_data.set('personal_info.ssn', '000-00-0000')
        print("✗ FAIL: Invalid SSN accepted")
        return False
    except ValueError:
        print("✓ Invalid SSN rejected")
    
    # Test length limits
    try:
        tax_data.set('personal_info.first_name', 'A' * 100)
        print("✗ FAIL: Overly long name accepted")
        return False
    except ValueError:
        print("✓ Length limit enforced")
    
    # Test negative currency
    try:
        tax_data.set('income.wages', -1000)
        print("✗ FAIL: Negative currency accepted")
        return False
    except ValueError:
        print("✓ Negative currency rejected\n")
    
    return True


def test_path_validation():
    """Test path traversal prevention"""
    print("Testing Path Validation...")
    
    tax_data = TaxData()
    tax_data.set('personal_info.first_name', 'Test')
    
    # Test directory traversal
    try:
        tax_data.save_to_file('../../etc/passwd.enc')
        print("✗ FAIL: Path traversal allowed")
        return False
    except ValueError:
        print("✓ Path traversal blocked")
    
    # Test valid path
    try:
        filename = tax_data.save_to_file('valid_test.enc')
        safe_dir = str(Path.home() / "Documents" / "TaxReturns")
        if safe_dir in filename:
            print(f"✓ File saved to safe directory: {Path(filename).parent}")
        os.remove(filename)
    except Exception as e:
        print(f"✗ FAIL: Valid path rejected: {e}")
        return False
    
    print()
    return True


def test_data_integrity():
    """Test HMAC integrity verification"""
    print("Testing Data Integrity...")
    
    tax_data = TaxData()
    tax_data.set('personal_info.first_name', 'IntegrityTest')
    
    # Save file
    filename = tax_data.save_to_file('integrity_test.enc')
    print("✓ File saved with HMAC")
    
    # Load and verify
    tax_data2 = TaxData()
    try:
        tax_data2.load_from_file(filename)
        print("✓ HMAC verification passed")
    except ValueError:
        print("✗ FAIL: HMAC verification failed on valid file")
        os.remove(filename)
        return False
    
    # Tamper with file
    with open(filename, 'rb') as f:
        data = bytearray(f.read())
    
    # Modify a byte
    if len(data) > 10:
        data[10] = (data[10] + 1) % 256
    
    with open(filename, 'wb') as f:
        f.write(data)
    
    # Try to load tampered file
    tax_data3 = TaxData()
    try:
        tax_data3.load_from_file(filename)
        print("✗ FAIL: Tampered file not detected")
        os.remove(filename)
        return False
    except Exception:
        print("✓ Tampered file detected")
    
    os.remove(filename)
    print()
    return True


def test_backward_compatibility():
    """Test loading legacy JSON files"""
    print("Testing Backward Compatibility...")
    
    # Create legacy JSON file
    import json
    legacy_file = Path.home() / "Documents" / "TaxReturns" / "legacy_test.json"
    legacy_data = {
        "personal_info": {"first_name": "Legacy", "last_name": "User"},
        "metadata": {"tax_year": 2024}
    }
    
    with open(legacy_file, 'w') as f:
        json.dump(legacy_data, f)
    print("✓ Created legacy JSON file")
    
    # Try to load
    tax_data = TaxData()
    try:
        tax_data.load_from_file(str(legacy_file))
        if tax_data.get('personal_info.first_name') == 'Legacy':
            print("✓ Legacy JSON file loaded successfully")
        else:
            print("✗ FAIL: Data not loaded correctly")
            os.remove(legacy_file)
            return False
    except Exception as e:
        print(f"✗ FAIL: Could not load legacy file: {e}")
        os.remove(legacy_file)
        return False
    
    os.remove(legacy_file)
    print()
    return True


def main():
    """Run all security tests"""
    print("=" * 60)
    print("SECURITY FEATURES TEST SUITE")
    print("=" * 60)
    print()
    
    tests = [
        ("Encryption", test_encryption),
        ("Input Validation", test_input_validation),
        ("Path Validation", test_path_validation),
        ("Data Integrity", test_data_integrity),
        ("Backward Compatibility", test_backward_compatibility),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ EXCEPTION in {name}: {e}\n")
            results.append((name, False))
    
    print("=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name:30} {status}")
    
    print()
    total = len(results)
    passed = sum(1 for _, r in results if r)
    
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL SECURITY TESTS PASSED!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
