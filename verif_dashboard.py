""" Generates a Verification Dashboard that shows status at a glance """

import argparse
import subprocess
import datetime
import os
import xml.etree.ElementTree as ET
import glob
import re
from ucis import CoverageReportBuilder
from ucis.xml.xml_reader import XmlReader

def get_signature():
    """Get git branch, short commit hash, and timestamp"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")        
    try:
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], text=True).strip()
        commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], text=True).strip()
    except subprocess.CalledProcessError:
        branch = "unknown"
        commit = "unknown"
    return {
        "branch": branch,
        "commit": commit,
        "timestamp": timestamp
    }

def get_test_metrics(sim_dir="sim"):
    """
    Extract test metrics from CocoTB XML result files.
    The metrics include: total tests, passed tests, failed tests, and total time.
    """

    # Find all XML result files
    xml_pattern = os.path.join(sim_dir, "*_results.xml")
    xml_files = glob.glob(xml_pattern)
    
    if not xml_files:
        # No XML files found
        return {"total_tests": 0, "passed_tests": 0, "failed_tests": 0, "total_time": 0.0}

    # Initialize counters
    total_tests = 0
    failed_tests = 0
    total_time = 0.0

    # Parse each XML file
    for xml_file in xml_files:
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Count all testcases
            testcases = root.findall(".//testcase")
            total_tests += len(testcases)

            for testcase in testcases:
                # Check for failure
                if testcase.find("failure") is not None:
                    failed_tests += 1

                # Collect time (default to 0.0 if not present or invalid)
                time_attr = testcase.get("time", "0.0")
                try:
                    total_time += float(time_attr)
                except (ValueError, TypeError):
                    print(f"Warning: Invalid time value '{time_attr}' in {xml_file}")
                    continue
            
        except Exception as e:
            print(f"Warning: Error processing {xml_file}: {e}")
            continue
    
    passed_tests = total_tests - failed_tests
    
    return {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "total_time": round(total_time, 3)
    }

def get_code_coverage(sim_dir="sim"):
    """
    Merge Verilator .dat coverage files and extract total code coverage percentage.
    Creates merged_code_cov.dat in the sim directory and keeps it.
    """
    
    # Find all .dat coverage files
    dat_pattern = os.path.join(sim_dir, "*_code_cov.dat")
    dat_files = glob.glob(dat_pattern)
    
    if not dat_files:
        print("Warning: No .dat coverage files found")
        return {"code_coverage": 0.0}
    
    # Define merged coverage file path
    merged_file = os.path.join(sim_dir, "merged_code_cov.dat")
    
    try:
        # Merge .dat files
        merge_cmd = ["verilator_coverage", "--write", merged_file] + dat_files
        result = subprocess.run(merge_cmd, capture_output=True, text=True, cwd=sim_dir)
        
        if result.returncode != 0:
            print(f"Warning: verilator_coverage merge failed: {result.stderr}")
            return {"code_coverage": 0.0}
        
        # Extract coverage percentage from merged file
        report_cmd = ["verilator_coverage", merged_file, "--annotate", "/tmp/ann_tmp", "--annotate-min", "1"]
        result = subprocess.run(report_cmd, capture_output=True, text=True, cwd=sim_dir)
        
        if result.returncode != 0:
            print(f"Warning: verilator_coverage report failed: {result.stderr}")
            return {"code_coverage": 0.0}
        
        # Parse coverage percentage from output using regex
        # Look for "Total coverage (31/42) 73.00%"
        match = re.search(r'Total coverage.*?(\d+\.?\d*)%', result.stdout)
        if match:
            return {"code_coverage": round(float(match.group(1)), 2)}

        return {"code_coverage": 0.0}
        
    except FileNotFoundError:
        print("Warning: verilator_coverage tool not found")
        return {"code_coverage": 0.0}
    except Exception as e:
        print(f"Warning: Error processing code coverage: {e}")
        return {"code_coverage": 0.0}

def get_functional_coverage(sim_dir="sim"):
    """
    Merge UCIS XML functional coverage files and extract total functional coverage percentage.
    Creates merged_func_cov.xml in the sim directory and keeps it.
    """
    
    # Find all functional coverage XML files
    xml_pattern = os.path.join(sim_dir, "*_func_cov.xml")
    xml_files = glob.glob(xml_pattern)
    
    if not xml_files:
        print("Warning: No functional coverage XML files found")
        return {"functional_coverage": 0.0}
    
    # Define merged functional coverage file path
    merged_file = os.path.join(sim_dir, "merged_func_cov.xml")
    
    try:
        # Merge XML files using pyucis merge command
        merge_cmd = ["pyucis", "merge", "--out", merged_file] + xml_files
        result = subprocess.run(merge_cmd, capture_output=True, text=True, cwd=sim_dir)
        
        if result.returncode != 0:
            print(f"Warning: pyucis merge failed: {result.stderr}")
            return {"functional_coverage": 0.0}
        
        # Read merged XML file and extract coverage
        xml_reader = XmlReader()
        db = xml_reader.read(merged_file)
        cov_report = CoverageReportBuilder.build(db)
        functional_coverage = int(cov_report.coverage)
        
        return {"functional_coverage": round(functional_coverage, 2)}

    except Exception as e:
        print(f"Warning: Error processing functional coverage: {e}")
        return {"functional_coverage": 0.0}

def generate_dashboard(sim_dir="sim"):
    """
    Generate the complete verification dashboard with signature and metrics.
    """
    print("=" * 50)
    print("Generating Verification Dashboard...")
    print("=" * 50)
    
    # Get signature
    signature = get_signature()
    print(f"Git Info: {signature['branch']}@{signature['commit']}")
    print(f"Generated: {signature['timestamp']}")
    print("=" * 50)

    # Get test metrics
    print("Collecting test metrics...")
    test_metrics = get_test_metrics(sim_dir)
    
    # Get code coverage
    print("Processing code coverage...")
    code_cov = get_code_coverage(sim_dir)
    
    # Get functional coverage
    print("Processing functional coverage...")
    func_cov = get_functional_coverage(sim_dir)

    print("=" * 50)
    
    # Display test metrics
    print("TEST METRICS:")
    print(f"   Total Tests:     {test_metrics['total_tests']}")
    print(f"   Passed Tests:    {test_metrics['passed_tests']}")
    print(f"   Failed Tests:    {test_metrics['failed_tests']}")
    if test_metrics['total_tests'] > 0:
        pass_rate = (test_metrics['passed_tests'] / test_metrics['total_tests']) * 100
        print(f"   Pass Rate:       {pass_rate:.2f}%")
    else:
        print(f"   Pass Rate:       N/A")
    print(f"   Total Time:      {test_metrics['total_time']}s")
    
    # Display coverage metrics
    print("\nCOVERAGE METRICS:")
    print(f"   Code Coverage:       {code_cov['code_coverage']}%")
    print(f"   Functional Coverage: {func_cov['functional_coverage']}%")    
    print("=" * 50)
    

def main():
    parser = argparse.ArgumentParser(description="Generate Verification Dashboard")
    parser.add_argument("--sim-dir", default="sim", 
                       help="Directory containing simulation results (default: sim)")
    
    args = parser.parse_args()

    generate_dashboard(args.sim_dir)

# When the script is run directly, invoke the main function
if __name__ == "__main__":
    main()